/* SPDX-License-Identifier: GPL-2.0 */
/*
 * AETHER OS — Exported Kernel Symbols
 * Cross-module function declarations
 */

#ifndef _AETHER_EXPORTS_H
#define _AETHER_EXPORTS_H

#include "aether_types.h"

/* From aether_cognitive.c */
int aether_register_process(pid_t pid, enum aether_proc_type type,
                            int priority_boost);
void aether_unregister_process(pid_t pid);
struct aether_proc_context *aether_find_context(pid_t pid);

#endif /* _AETHER_EXPORTS_H */
