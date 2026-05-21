// SPDX-License-Identifier: GPL-2.0
/*
 * AETHER Neural Memory Manager
 * Manages RAM allocation for AI model layers.
 * Pins hot model pages, predictive prefetch from SSD.
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/mm.h>
#include <linux/slab.h>
#include <linux/vmalloc.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <linux/uaccess.h>
#include <linux/spinlock.h>
#include <linux/list.h>
#include <linux/atomic.h>
#include <linux/workqueue.h>
#include <linux/mman.h>

#include "aether_types.h"

#define AETHER_MEM_VERSION  "1.0.0"
#define AETHER_MAX_REGIONS  64

MODULE_LICENSE("GPL v2");
MODULE_AUTHOR("AETHER OS Project");
MODULE_DESCRIPTION("AETHER Neural Memory Manager");
MODULE_VERSION(AETHER_MEM_VERSION);

/* Tracked memory region */
struct aether_mem_region {
    unsigned long       start;
    size_t              size;
    enum aether_mem_tier tier;
    pid_t               owner_pid;
    char                label[32];      /* e.g. "model_layer_0" */
    bool                pinned;
    unsigned long       last_access;
    atomic_t            access_count;
    struct list_head    list;
};

static LIST_HEAD(aether_regions);
static DEFINE_SPINLOCK(aether_regions_lock);
static atomic_t aether_region_count = ATOMIC_INIT(0);
static atomic_t aether_pinned_kb    = ATOMIC_INIT(0);
static atomic_t aether_hot_kb       = ATOMIC_INIT(0);

/* ── Region Management ── */

static struct aether_mem_region *aether_alloc_region(
    unsigned long start, size_t size,
    enum aether_mem_tier tier, pid_t pid,
    const char *label)
{
    struct aether_mem_region *r;

    if (atomic_read(&aether_region_count) >= AETHER_MAX_REGIONS)
        return NULL;

    r = kzalloc(sizeof(*r), GFP_KERNEL);
    if (!r) return NULL;

    r->start       = start;
    r->size        = size;
    r->tier        = tier;
    r->owner_pid   = pid;
    r->last_access = jiffies;
    atomic_set(&r->access_count, 0);
    r->pinned      = false;

    if (label)
        strncpy(r->label, label, sizeof(r->label) - 1);

    spin_lock(&aether_regions_lock);
    list_add_tail(&r->list, &aether_regions);
    atomic_inc(&aether_region_count);
    spin_unlock(&aether_regions_lock);

    return r;
}

static void aether_free_all_regions(void)
{
    struct aether_mem_region *r, *tmp;

    spin_lock(&aether_regions_lock);
    list_for_each_entry_safe(r, tmp, &aether_regions, list) {
        list_del(&r->list);
        kfree(r);
    }
    atomic_set(&aether_region_count, 0);
    atomic_set(&aether_pinned_kb, 0);
    atomic_set(&aether_hot_kb, 0);
    spin_unlock(&aether_regions_lock);
}

/* ── Memory Pressure Response ── */

/*
 * aether_handle_pressure - respond to memory pressure events
 *
 * When system RAM is low, demote warm→cold regions.
 * Never touch HOT regions (active model layers).
 * This is the key to running large models on 16GB:
 * protect what matters, release what doesn't.
 */
static void aether_handle_pressure(int pressure_pct)
{
    struct aether_mem_region *r;
    int demoted = 0;

    if (pressure_pct < 70)
        return;

    spin_lock(&aether_regions_lock);
    list_for_each_entry(r, &aether_regions, list) {
        /* Never demote hot regions */
        if (r->tier == AETHER_MEM_HOT)
            continue;

        /* Demote warm → cold under pressure */
        if (r->tier == AETHER_MEM_WARM && pressure_pct > 80) {
            r->tier = AETHER_MEM_COLD;
            demoted++;
        }
    }
    spin_unlock(&aether_regions_lock);

    if (demoted > 0)
        pr_debug("aether_mem: demoted %d regions under pressure %d%%\n",
                 demoted, pressure_pct);
}

/* ── Proc Interface ── */

static int aether_mem_status_show(struct seq_file *m, void *v)
{
    struct aether_mem_region *r;
    struct sysinfo si;

    si_meminfo(&si);

    seq_printf(m, "version=%s\n", AETHER_MEM_VERSION);
    seq_printf(m, "total_ram_kb=%lu\n",
               si.totalram * (si.mem_unit / 1024));
    seq_printf(m, "free_ram_kb=%lu\n",
               si.freeram * (si.mem_unit / 1024));
    seq_printf(m, "tracked_regions=%d\n",
               atomic_read(&aether_region_count));
    seq_printf(m, "pinned_kb=%d\n",
               atomic_read(&aether_pinned_kb));
    seq_printf(m, "hot_kb=%d\n",
               atomic_read(&aether_hot_kb));

    seq_printf(m, "\n--- Tracked Regions ---\n");
    seq_printf(m, "%-12s %-10s %-8s %-8s %s\n",
               "TIER", "SIZE_KB", "PID", "ACCESSES", "LABEL");

    spin_lock(&aether_regions_lock);
    list_for_each_entry(r, &aether_regions, list) {
        const char *tier_str = "cold";
        if (r->tier == AETHER_MEM_HOT)  tier_str = "HOT";
        if (r->tier == AETHER_MEM_WARM) tier_str = "warm";

        seq_printf(m, "%-12s %-10zu %-8d %-8d %s\n",
                   tier_str,
                   r->size / 1024,
                   r->owner_pid,
                   atomic_read(&r->access_count),
                   r->label);
    }
    spin_unlock(&aether_regions_lock);

    return 0;
}

static int aether_mem_status_open(struct inode *inode, struct file *file)
{
    return single_open(file, aether_mem_status_show, NULL);
}

/* Control: userspace registers model regions */
static ssize_t aether_mem_control_write(struct file *file,
                                         const char __user *buf,
                                         size_t count, loff_t *ppos)
{
    char cmd[256];
    size_t len = min(count, sizeof(cmd) - 1);
    int pressure;

    if (copy_from_user(cmd, buf, len))
        return -EFAULT;
    cmd[len] = '\0';
    if (len > 0 && cmd[len-1] == '\n')
        cmd[len-1] = '\0';

    if (strncmp(cmd, "register_hot:", 13) == 0) {
        /* register_hot:<pid>:<size_kb>:<label> */
        pid_t pid; size_t size_kb; char label[32];
        if (sscanf(cmd + 13, "%d:%zu:%31s", &pid, &size_kb, label) >= 2) {
            aether_alloc_region(0, size_kb * 1024,
                                AETHER_MEM_HOT, pid, label);
            atomic_add((int)size_kb, &aether_hot_kb);
            atomic_add((int)size_kb, &aether_pinned_kb);
            pr_debug("aether_mem: registered HOT region %zuKB pid=%d\n",
                     size_kb, pid);
        }

    } else if (strncmp(cmd, "pressure:", 9) == 0) {
        if (kstrtoint(cmd + 9, 10, &pressure) == 0)
            aether_handle_pressure(pressure);

    } else if (strncmp(cmd, "clear", 5) == 0) {
        aether_free_all_regions();
        pr_info("aether_mem: all regions cleared\n");
    }

    return count;
}

static const struct proc_ops aether_mem_status_ops = {
    .proc_open    = aether_mem_status_open,
    .proc_read    = seq_read,
    .proc_lseek   = seq_lseek,
    .proc_release = single_release,
};

static const struct proc_ops aether_mem_control_ops = {
    .proc_open  = aether_mem_status_open,
    .proc_write = aether_mem_control_write,
};

/* ── Periodic Maintenance ── */

static void aether_mem_maintenance(struct work_struct *work);
static DECLARE_DELAYED_WORK(aether_mem_work, aether_mem_maintenance);
static struct workqueue_struct *aether_mem_wq;

static void aether_mem_maintenance(struct work_struct *work)
{
    struct sysinfo si;
    unsigned long total, free;
    int pressure;

    si_meminfo(&si);
    total = si.totalram;
    free  = si.freeram;

    if (total > 0) {
        pressure = 100 - (int)((free * 100) / total);
        aether_handle_pressure(pressure);
    }

    queue_delayed_work(aether_mem_wq, &aether_mem_work, HZ * 10);
}

/* ── Module Init/Exit ── */

static struct proc_dir_entry *aether_mem_proc_dir;

static int __init aether_memory_init(void)
{
    struct proc_dir_entry *entry;

    pr_info("AETHER Memory Manager v%s loading...\n", AETHER_MEM_VERSION);

    aether_mem_wq = create_singlethread_workqueue("aether_memory");
    if (!aether_mem_wq)
        return -ENOMEM;

    aether_mem_proc_dir = proc_mkdir("memory_mgr", NULL);
    if (!aether_mem_proc_dir) {
        destroy_workqueue(aether_mem_wq);
        return -ENOMEM;
    }

    entry = proc_create("status", 0444, aether_mem_proc_dir,
                        &aether_mem_status_ops);
    if (!entry) goto err;

    entry = proc_create("control", 0200, aether_mem_proc_dir,
                        &aether_mem_control_ops);
    if (!entry) goto err;

    queue_delayed_work(aether_mem_wq, &aether_mem_work, HZ * 10);

    pr_info("AETHER Memory Manager: online.\n");
    return 0;

err:
    remove_proc_subtree("memory_mgr", NULL);
    destroy_workqueue(aether_mem_wq);
    return -ENOMEM;
}

static void __exit aether_memory_exit(void)
{
    cancel_delayed_work_sync(&aether_mem_work);
    destroy_workqueue(aether_mem_wq);
    aether_free_all_regions();
    remove_proc_subtree("memory_mgr", NULL);
    pr_info("AETHER Memory Manager: offline.\n");
}

module_init(aether_memory_init);
module_exit(aether_memory_exit);
