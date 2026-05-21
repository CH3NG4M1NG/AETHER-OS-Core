// SPDX-License-Identifier: GPL-2.0
/*
 * AETHER AI-Aware Scheduler Hook
 * Intercepts scheduler decisions to prioritize AI workloads
 * and yield completely when gaming is detected.
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/sched.h>
#include <linux/sched/signal.h>
#include <linux/sched/task.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <linux/uaccess.h>
#include <linux/spinlock.h>
#include <linux/atomic.h>
#include <linux/ktime.h>
#include <linux/workqueue.h>
#include <linux/hashtable.h>
#include <linux/jhash.h>
#include <linux/string.h>
#include <linux/pid.h>

#include "aether_types.h"

#define AETHER_SCHED_VERSION    "1.0.0"
#define AETHER_SCHED_HASH_BITS  8

MODULE_LICENSE("GPL v2");
MODULE_AUTHOR("AETHER OS Project");
MODULE_DESCRIPTION("AETHER AI-Aware Process Scheduler");
MODULE_VERSION(AETHER_SCHED_VERSION);

/* ── Scheduler State ── */

static struct {
    atomic_t    gaming_mode;        /* 1 = game detected, AI yields */
    atomic_t    ai_active;          /* 1 = AI inference running */
    atomic_t    managed_procs;      /* number of AETHER-managed processes */
    atomic_t    priority_adjustments; /* total adjustments made */
    spinlock_t  lock;
    char        active_game[64];    /* name of detected game */
    char        ai_process[64];     /* name of AI process */
} aether_sched_state;

/* Process priority table */
/* prio_table and lock reserved for future use */

struct aether_prio_entry {
    pid_t               pid;
    char                comm[TASK_COMM_LEN];
    int                 original_nice;
    int                 target_nice;
    enum aether_proc_type type;
    bool                applied;
    struct hlist_node   node;
};

/* Known AI process names */
static const char *ai_process_names[] = {
    "ollama", "llama.cpp", "llama-server",
    "python3", "python",    /* AI daemons */
    "aether",
    NULL
};

/* Known game patterns (simplified) */
static const char *game_patterns[] = {
    "steam", "wine", "proton",
    "gamemode", "gamescope",
    NULL
};

/* ── Process Classification ── */

static __maybe_unused enum aether_proc_type aether_classify_process(struct task_struct *task)
{
    const char *name = task->comm;
    int i;

    /* Check AI processes */
    for (i = 0; ai_process_names[i]; i++) {
        if (strstr(name, ai_process_names[i]))
            return AETHER_PROC_AI_INFERENCE;
    }

    /* Check game processes */
    for (i = 0; game_patterns[i]; i++) {
        if (strstr(name, game_patterns[i]))
            return AETHER_PROC_GAMING;
    }

    /* Compiler/build tools */
    if (!strcmp(name, "gcc") || !strcmp(name, "g++") ||
        !strcmp(name, "make") || !strcmp(name, "cmake") ||
        !strcmp(name, "cargo") || !strcmp(name, "rustc"))
        return AETHER_PROC_CODING;

    return AETHER_PROC_UNKNOWN;
}

/* ── Priority Management ── */

/*
 * aether_suggest_nice - suggest nice value for a process
 *
 * Returns the suggested nice value delta based on AETHER's
 * understanding of what the user is currently doing.
 *
 * Key insight: when gaming, AI processes get nice +15 (very low priority)
 * When AI is the focus, inference gets nice -5 (higher priority)
 * This is done as a suggestion — actual scheduling still Linux's job.
 */
static int aether_suggest_nice(enum aether_proc_type type)
{
    int gaming = atomic_read(&aether_sched_state.gaming_mode);
    int ai_active = atomic_read(&aether_sched_state.ai_active);

    switch (type) {
    case AETHER_PROC_AI_INFERENCE:
        if (gaming) return +15;      /* yield to game completely */
        if (ai_active) return -5;    /* boost inference */
        return 0;

    case AETHER_PROC_AI_DAEMON:
        if (gaming) return +19;      /* almost idle when gaming */
        return +5;                   /* slightly below normal otherwise */

    case AETHER_PROC_CODING:
        if (gaming) return +10;
        return -2;                   /* small boost for dev work */

    case AETHER_PROC_GAMING:
        return -10;                  /* always boost games */

    case AETHER_PROC_BACKGROUND:
        return +10;                  /* deprioritize background */

    default:
        return 0;
    }
}

static void aether_apply_priority(pid_t pid, int nice_delta)
{
    struct task_struct *task;
    int new_nice;

    rcu_read_lock();
    task = pid_task(find_vpid(pid), PIDTYPE_PID);
    if (task) {
        get_task_struct(task);
        rcu_read_unlock();

        new_nice = clamp(task_nice(task) + nice_delta, -20, 19);
        set_user_nice(task, new_nice);
        atomic_inc(&aether_sched_state.priority_adjustments);
        put_task_struct(task);
    } else {
        rcu_read_unlock();
    }
}

/* ── Gaming Mode Detection ── */

static void aether_detect_gaming(void)
{
    struct task_struct *task;
    bool game_found = false;
    int i;

    rcu_read_lock();
    for_each_process(task) {
        for (i = 0; game_patterns[i]; i++) {
            if (strstr(task->comm, game_patterns[i])) {
                game_found = true;
                spin_lock(&aether_sched_state.lock);
                strncpy(aether_sched_state.active_game,
                        task->comm,
                        sizeof(aether_sched_state.active_game) - 1);
                spin_unlock(&aether_sched_state.lock);
                break;
            }
        }
        if (game_found) break;
    }
    rcu_read_unlock();

    if (game_found != atomic_read(&aether_sched_state.gaming_mode)) {
        atomic_set(&aether_sched_state.gaming_mode, game_found ? 1 : 0);
        if (game_found)
            pr_info("aether_sched: GAMING MODE — AI yields to game\n");
        else
            pr_info("aether_sched: Game exited — AI resumes normal priority\n");
    }
}

/* ── Proc Interface ── */

static int aether_sched_status_show(struct seq_file *m, void *v)
{
    seq_printf(m, "version=%s\n", AETHER_SCHED_VERSION);
    seq_printf(m, "gaming_mode=%d\n",
               atomic_read(&aether_sched_state.gaming_mode));
    seq_printf(m, "ai_active=%d\n",
               atomic_read(&aether_sched_state.ai_active));
    seq_printf(m, "managed_procs=%d\n",
               atomic_read(&aether_sched_state.managed_procs));
    seq_printf(m, "total_adjustments=%d\n",
               atomic_read(&aether_sched_state.priority_adjustments));

    spin_lock(&aether_sched_state.lock);
    if (aether_sched_state.active_game[0])
        seq_printf(m, "active_game=%s\n", aether_sched_state.active_game);
    if (aether_sched_state.ai_process[0])
        seq_printf(m, "ai_process=%s\n", aether_sched_state.ai_process);
    spin_unlock(&aether_sched_state.lock);

    return 0;
}

static int aether_sched_status_open(struct inode *inode, struct file *file)
{
    return single_open(file, aether_sched_status_show, NULL);
}

/* Control interface: userspace daemon sends commands */
static ssize_t aether_sched_control_write(struct file *file,
                                           const char __user *buf,
                                           size_t count, loff_t *ppos)
{
    char cmd[256];
    size_t len = min(count, sizeof(cmd) - 1);
    pid_t pid;
    int type, nice;

    if (copy_from_user(cmd, buf, len))
        return -EFAULT;
    cmd[len] = '\0';
    if (len > 0 && cmd[len-1] == '\n')
        cmd[len-1] = '\0';

    if (strncmp(cmd, "ai_start:", 9) == 0) {
        /* ai_start:<pid> */
        if (kstrtoint(cmd + 9, 10, &pid) == 0) {
            atomic_set(&aether_sched_state.ai_active, 1);
            aether_apply_priority(pid,
                aether_suggest_nice(AETHER_PROC_AI_INFERENCE));
            atomic_inc(&aether_sched_state.managed_procs);
        }

    } else if (strncmp(cmd, "ai_stop", 7) == 0) {
        atomic_set(&aether_sched_state.ai_active, 0);

    } else if (strncmp(cmd, "register:", 9) == 0) {
        /* register:<pid>:<type>:<nice_delta> */
        if (sscanf(cmd + 9, "%d:%d:%d", &pid, &type, &nice) == 3) {
            aether_apply_priority(pid, nice);
            atomic_inc(&aether_sched_state.managed_procs);
        }

    } else if (strncmp(cmd, "scan_gaming", 11) == 0) {
        aether_detect_gaming();
    }

    return count;
}

static const struct proc_ops aether_sched_status_ops = {
    .proc_open    = aether_sched_status_open,
    .proc_read    = seq_read,
    .proc_lseek   = seq_lseek,
    .proc_release = single_release,
};

static const struct proc_ops aether_sched_control_ops = {
    .proc_open  = aether_sched_status_open, /* reuse */
    .proc_write = aether_sched_control_write,
};

/* ── Periodic Work ── */

static void aether_sched_scan(struct work_struct *work);
static DECLARE_DELAYED_WORK(aether_sched_work, aether_sched_scan);
static struct workqueue_struct *aether_sched_wq;

static void aether_sched_scan(struct work_struct *work)
{
    aether_detect_gaming();
    queue_delayed_work(aether_sched_wq, &aether_sched_work, HZ * 3);
}

/* ── Module Init/Exit ── */

static struct proc_dir_entry *aether_sched_proc;

static int __init aether_scheduler_init(void)
{
    struct proc_dir_entry *root, *entry;

    pr_info("AETHER Scheduler v%s loading...\n", AETHER_SCHED_VERSION);

    memset(&aether_sched_state, 0, sizeof(aether_sched_state));
    spin_lock_init(&aether_sched_state.lock);

    aether_sched_wq = create_singlethread_workqueue("aether_scheduler");
    if (!aether_sched_wq)
        return -ENOMEM;

    /* Create /proc/aether/scheduler/ */
    root = proc_mkdir("scheduler", NULL); /* attach to /proc/aether later */
    if (!root) {
        destroy_workqueue(aether_sched_wq);
        return -ENOMEM;
    }
    aether_sched_proc = root;

    entry = proc_create("status", 0444, root, &aether_sched_status_ops);
    if (!entry) goto err;

    entry = proc_create("control", 0200, root, &aether_sched_control_ops);
    if (!entry) goto err;

    queue_delayed_work(aether_sched_wq, &aether_sched_work, HZ * 3);

    pr_info("AETHER Scheduler: online. Gaming detection active.\n");
    return 0;

err:
    remove_proc_subtree("scheduler", NULL);
    destroy_workqueue(aether_sched_wq);
    return -ENOMEM;
}

static void __exit aether_scheduler_exit(void)
{
    cancel_delayed_work_sync(&aether_sched_work);
    destroy_workqueue(aether_sched_wq);
    remove_proc_subtree("scheduler", NULL);
    pr_info("AETHER Scheduler: offline.\n");
}

module_init(aether_scheduler_init);
module_exit(aether_scheduler_exit);
