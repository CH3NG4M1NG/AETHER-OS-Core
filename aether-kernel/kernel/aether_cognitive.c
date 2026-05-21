// SPDX-License-Identifier: GPL-2.0
/*
 * AETHER Cognitive Engine — Kernel Module
 * Part of AETHER OS — AGI Foundation Framework
 *
 * This module registers AETHER as a first-class kernel component.
 * Exposes /proc/aether/ interface for user-space communication.
 * Hooks into kernel scheduler and memory subsystems.
 *
 * Author: AETHER OS Project
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <linux/sched.h>
#include <linux/sched/signal.h>
#include <linux/mm.h>
#include <linux/slab.h>
#include <linux/pid.h>
#include <linux/uaccess.h>
#include <linux/spinlock.h>
#include <linux/list.h>
#include <linux/timer.h>
#include <linux/jiffies.h>
#include <linux/ktime.h>
#include <linux/atomic.h>
#include <linux/rwsem.h>
#include <linux/hashtable.h>
#include <linux/jhash.h>
#include <linux/workqueue.h>
#include <linux/notifier.h>

#include "aether_types.h"

#define AETHER_VERSION      "1.0.0"
#define AETHER_PROC_ROOT    "aether"
#define AETHER_MAX_CONTEXTS 256
#define AETHER_HASH_BITS    8

MODULE_LICENSE("GPL v2");
MODULE_AUTHOR("AETHER OS Project");
MODULE_DESCRIPTION("AETHER Cognitive Engine — AGI Foundation Kernel Module");
MODULE_VERSION(AETHER_VERSION);

/* ── Global State ── */
static struct proc_dir_entry *aether_proc_root;
static DEFINE_RWLOCK(aether_state_lock);
static DEFINE_HASHTABLE(aether_context_table, AETHER_HASH_BITS);

/* Cognitive state exposed to userspace */
static struct aether_cognitive_state {
    atomic_t        active_contexts;
    atomic_t        total_inferences;
    atomic_t        memory_pressure;    /* 0-100 */
    atomic_t        cognitive_load;     /* 0-100 */
    atomic64_t      uptime_ns;
    ktime_t         boot_time;
    char            current_mode[32];   /* conversational/reasoning/coding/etc */
    spinlock_t      mode_lock;
} aether_state;

/* Per-process cognitive context */
struct aether_proc_context {
    pid_t               pid;
    char                comm[TASK_COMM_LEN];
    int                 priority_boost;     /* -20 to +20 */
    enum aether_proc_type type;
    unsigned long       last_seen;
    struct hlist_node   hash_node;
    struct rcu_head     rcu;
};

/* Workqueue for async cognitive processing */
static struct workqueue_struct *aether_wq;

/* ── Proc Interface ── */

/* /proc/aether/status */
static int aether_status_show(struct seq_file *m, void *v)
{
    ktime_t now = ktime_get();
    s64 uptime_ms = ktime_to_ms(ktime_sub(now, aether_state.boot_time));

    seq_printf(m, "AETHER OS Cognitive Engine v%s\n", AETHER_VERSION);
    seq_printf(m, "uptime_ms=%lld\n", uptime_ms);
    seq_printf(m, "active_contexts=%d\n",
               atomic_read(&aether_state.active_contexts));
    seq_printf(m, "total_inferences=%d\n",
               atomic_read(&aether_state.total_inferences));
    seq_printf(m, "memory_pressure=%d\n",
               atomic_read(&aether_state.memory_pressure));
    seq_printf(m, "cognitive_load=%d\n",
               atomic_read(&aether_state.cognitive_load));

    spin_lock(&aether_state.mode_lock);
    seq_printf(m, "current_mode=%s\n", aether_state.current_mode);
    spin_unlock(&aether_state.mode_lock);

    return 0;
}

static int aether_status_open(struct inode *inode, struct file *file)
{
    return single_open(file, aether_status_show, NULL);
}

static const struct proc_ops aether_status_ops = {
    .proc_open    = aether_status_open,
    .proc_read    = seq_read,
    .proc_lseek   = seq_lseek,
    .proc_release = single_release,
};

/* /proc/aether/control — write commands from userspace */
static ssize_t aether_control_write(struct file *file,
                                     const char __user *buf,
                                     size_t count, loff_t *ppos)
{
    char cmd[128];
    size_t len = min(count, sizeof(cmd) - 1);

    if (copy_from_user(cmd, buf, len))
        return -EFAULT;

    cmd[len] = '\0';

    /* Strip newline */
    if (len > 0 && cmd[len-1] == '\n')
        cmd[len-1] = '\0';

    /* Parse commands from AETHER userspace daemon */
    if (strncmp(cmd, "mode:", 5) == 0) {
        spin_lock(&aether_state.mode_lock);
        strncpy(aether_state.current_mode, cmd + 5,
                sizeof(aether_state.current_mode) - 1);
        spin_unlock(&aether_state.mode_lock);
        pr_debug("aether: mode changed to '%s'\n", cmd + 5);

    } else if (strncmp(cmd, "inference_done", 14) == 0) {
        atomic_inc(&aether_state.total_inferences);

    } else if (strncmp(cmd, "pressure:", 9) == 0) {
        int val;
        if (kstrtoint(cmd + 9, 10, &val) == 0)
            atomic_set(&aether_state.memory_pressure,
                       clamp(val, 0, 100));

    } else if (strncmp(cmd, "load:", 5) == 0) {
        int val;
        if (kstrtoint(cmd + 5, 10, &val) == 0)
            atomic_set(&aether_state.cognitive_load,
                       clamp(val, 0, 100));

    } else {
        pr_warn("aether: unknown command: %s\n", cmd);
    }

    return count;
}

static int aether_control_open(struct inode *inode, struct file *file)
{
    return 0;
}

static const struct proc_ops aether_control_ops = {
    .proc_open  = aether_control_open,
    .proc_write = aether_control_write,
    .proc_read  = NULL,
};

/* /proc/aether/processes — list tracked processes */
static int aether_procs_show(struct seq_file *m, void *v)
{
    struct aether_proc_context *ctx;
    int bkt;

    seq_printf(m, "%-8s %-16s %-8s %-12s\n",
               "PID", "COMM", "BOOST", "TYPE");

    read_lock(&aether_state_lock);
    hash_for_each_rcu(aether_context_table, bkt, ctx, hash_node) {
        seq_printf(m, "%-8d %-16s %-8d %-12s\n",
                   ctx->pid, ctx->comm,
                   ctx->priority_boost,
                   aether_proc_type_str(ctx->type));
    }
    read_unlock(&aether_state_lock);

    return 0;
}

static int aether_procs_open(struct inode *inode, struct file *file)
{
    return single_open(file, aether_procs_show, NULL);
}

static const struct proc_ops aether_procs_ops = {
    .proc_open    = aether_procs_open,
    .proc_read    = seq_read,
    .proc_lseek   = seq_lseek,
    .proc_release = single_release,
};

/* /proc/aether/memory — memory subsystem state */
static int aether_memory_show(struct seq_file *m, void *v)
{
    struct sysinfo si;
    si_meminfo(&si);

    seq_printf(m, "total_kb=%lu\n",
               si.totalram * (si.mem_unit / 1024));
    seq_printf(m, "free_kb=%lu\n",
               si.freeram * (si.mem_unit / 1024));
    seq_printf(m, "available_kb=%lu\n",
               si_mem_available() * (PAGE_SIZE / 1024));
    seq_printf(m, "pressure=%d\n",
               atomic_read(&aether_state.memory_pressure));
    seq_printf(m, "aether_pinned_kb=0\n"); /* TODO: track pinned pages */

    return 0;
}

static int aether_memory_open(struct inode *inode, struct file *file)
{
    return single_open(file, aether_memory_show, NULL);
}

static const struct proc_ops aether_memory_ops = {
    .proc_open    = aether_memory_open,
    .proc_read    = seq_read,
    .proc_lseek   = seq_lseek,
    .proc_release = single_release,
};

/* ── Process Context Management ── */

static struct aether_proc_context *aether_find_context(pid_t pid)
{
    struct aether_proc_context *ctx;
    u32 key = jhash_1word(pid, 0);

    hash_for_each_possible_rcu(aether_context_table, ctx, hash_node, key) {
        if (ctx->pid == pid)
            return ctx;
    }
    return NULL;
}

static int aether_register_process(pid_t pid, enum aether_proc_type type,
                                    int priority_boost)
{
    struct aether_proc_context *ctx;
    struct task_struct *task;
    u32 key;

    ctx = kzalloc(sizeof(*ctx), GFP_KERNEL);
    if (!ctx)
        return -ENOMEM;

    ctx->pid = pid;
    ctx->type = type;
    ctx->priority_boost = clamp(priority_boost, -20, 20);
    ctx->last_seen = jiffies;

    /* Get process name */
    rcu_read_lock();
    task = pid_task(find_vpid(pid), PIDTYPE_PID);
    if (task)
        get_task_comm(ctx->comm, task);
    else
        strncpy(ctx->comm, "unknown", TASK_COMM_LEN);
    rcu_read_unlock();

    key = jhash_1word(pid, 0);

    write_lock(&aether_state_lock);
    hash_add_rcu(aether_context_table, &ctx->hash_node, key);
    atomic_inc(&aether_state.active_contexts);
    write_unlock(&aether_state_lock);

    pr_debug("aether: registered process %d (%s) type=%d boost=%d\n",
             pid, ctx->comm, type, priority_boost);

    return 0;
}

static void aether_context_free_rcu(struct rcu_head *head)
{
    struct aether_proc_context *ctx =
        container_of(head, struct aether_proc_context, rcu);
    kfree(ctx);
}

static void aether_unregister_process(pid_t pid)
{
    struct aether_proc_context *ctx;
    u32 key = jhash_1word(pid, 0);

    write_lock(&aether_state_lock);
    hash_for_each_possible(aether_context_table, ctx, hash_node, key) {
        if (ctx->pid == pid) {
            hash_del_rcu(&ctx->hash_node);
            atomic_dec(&aether_state.active_contexts);
            call_rcu(&ctx->rcu, aether_context_free_rcu);
            break;
        }
    }
    write_unlock(&aether_state_lock);
}

/* ── Periodic Cognitive Update Work ── */

static void aether_cognitive_update(struct work_struct *work);
static DECLARE_DELAYED_WORK(aether_update_work, aether_cognitive_update);

static void aether_cognitive_update(struct work_struct *work)
{
    struct sysinfo si;
    unsigned long total, free;
    int pressure;

    /* Update memory pressure */
    si_meminfo(&si);
    total = si.totalram;
    free  = si.freeram;

    if (total > 0)
        pressure = 100 - (int)((free * 100) / total);
    else
        pressure = 0;

    atomic_set(&aether_state.memory_pressure, pressure);

    /* Update uptime */
    atomic64_set(&aether_state.uptime_ns,
                 ktime_to_ns(ktime_sub(ktime_get(),
                             aether_state.boot_time)));

    /* Reschedule every 5 seconds */
    queue_delayed_work(aether_wq, &aether_update_work, HZ * 5);
}

/* ── Module Init / Exit ── */

static int __init aether_cognitive_init(void)
{
    struct proc_dir_entry *entry;

    pr_info("AETHER Cognitive Engine v%s loading...\n", AETHER_VERSION);

    /* Init state */
    memset(&aether_state, 0, sizeof(aether_state));
    aether_state.boot_time = ktime_get();
    spin_lock_init(&aether_state.mode_lock);
    strncpy(aether_state.current_mode, "idle",
            sizeof(aether_state.current_mode));
    hash_init(aether_context_table);

    /* Create workqueue */
    aether_wq = create_singlethread_workqueue("aether_cognitive");
    if (!aether_wq) {
        pr_err("aether: failed to create workqueue\n");
        return -ENOMEM;
    }

    /* Create /proc/aether/ */
    aether_proc_root = proc_mkdir(AETHER_PROC_ROOT, NULL);
    if (!aether_proc_root) {
        pr_err("aether: failed to create /proc/aether\n");
        destroy_workqueue(aether_wq);
        return -ENOMEM;
    }

    /* Create proc entries */
    entry = proc_create("status", 0444, aether_proc_root,
                        &aether_status_ops);
    if (!entry) goto err_proc;

    entry = proc_create("control", 0200, aether_proc_root,
                        &aether_control_ops);
    if (!entry) goto err_proc;

    entry = proc_create("processes", 0444, aether_proc_root,
                        &aether_procs_ops);
    if (!entry) goto err_proc;

    entry = proc_create("memory", 0444, aether_proc_root,
                        &aether_memory_ops);
    if (!entry) goto err_proc;

    /* Start periodic update */
    queue_delayed_work(aether_wq, &aether_update_work, HZ * 5);

    pr_info("AETHER: /proc/aether/ created\n");
    pr_info("AETHER: Cognitive Engine online. AGI Foundation active.\n");

    return 0;

err_proc:
    pr_err("aether: failed to create proc entries\n");
    remove_proc_subtree(AETHER_PROC_ROOT, NULL);
    destroy_workqueue(aether_wq);
    return -ENOMEM;
}

static void __exit aether_cognitive_exit(void)
{
    struct aether_proc_context *ctx;
    struct hlist_node *tmp;
    int bkt;

    pr_info("AETHER: Cognitive Engine shutting down...\n");

    /* Stop workqueue */
    cancel_delayed_work_sync(&aether_update_work);
    destroy_workqueue(aether_wq);

    /* Remove proc entries */
    remove_proc_subtree(AETHER_PROC_ROOT, NULL);

    /* Free all contexts */
    write_lock(&aether_state_lock);
    hash_for_each_safe(aether_context_table, bkt, tmp, ctx, hash_node) {
        hash_del(&ctx->hash_node);
        kfree(ctx);
    }
    write_unlock(&aether_state_lock);

    pr_info("AETHER: Cognitive Engine offline.\n");
}

module_init(aether_cognitive_init);
module_exit(aether_cognitive_exit);

/* Export symbols for other AETHER modules */
/* Symbols exported for other AETHER modules */
/* Symbols available within this module only */
