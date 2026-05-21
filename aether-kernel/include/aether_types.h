/* SPDX-License-Identifier: GPL-2.0 */
/*
 * AETHER OS — Shared Kernel Types
 * AGI Foundation Framework
 */

#ifndef _AETHER_TYPES_H
#define _AETHER_TYPES_H

#include <linux/types.h>

/* Process types AETHER tracks */
enum aether_proc_type {
    AETHER_PROC_UNKNOWN      = 0,
    AETHER_PROC_AI_INFERENCE = 1,  /* Ollama, llama.cpp — highest priority */
    AETHER_PROC_AI_DAEMON    = 2,  /* AETHER daemon itself */
    AETHER_PROC_CODING       = 3,  /* IDE, compiler */
    AETHER_PROC_REASONING    = 4,  /* Analysis tasks */
    AETHER_PROC_BACKGROUND   = 5,  /* Low priority background */
    AETHER_PROC_GAMING       = 6,  /* Games — AI yields completely */
    AETHER_PROC_SYSTEM       = 7,  /* System processes */
};

/* Cognitive modes */
enum aether_cognitive_mode {
    AETHER_MODE_IDLE           = 0,
    AETHER_MODE_CONVERSATIONAL = 1,
    AETHER_MODE_REASONING      = 2,
    AETHER_MODE_CODING         = 3,
    AETHER_MODE_CREATIVE       = 4,
    AETHER_MODE_KNOWLEDGE      = 5,
    AETHER_MODE_DREAMING       = 6,  /* Background consolidation */
};

/* Memory tiers */
enum aether_mem_tier {
    AETHER_MEM_HOT   = 0,  /* Active model layers — never swap */
    AETHER_MEM_WARM  = 1,  /* Frequently used — prefer keep */
    AETHER_MEM_COLD  = 2,  /* Rarely used — ok to swap */
};

/* Scheduler hints */
struct aether_sched_hint {
    enum aether_proc_type   type;
    int                     priority_delta;  /* adjust nice value */
    bool                    yield_to_game;   /* immediately yield if game detected */
    bool                    pin_cpu;         /* try to pin to specific cores */
    int                     preferred_cpu;
};

/* Memory management hint */
struct aether_mem_hint {
    unsigned long   start_addr;
    size_t          size;
    enum aether_mem_tier tier;
    bool            do_pin;      /* mlock equivalent */
    bool            prefetch;    /* advise kernel to prefetch */
};

/* Inline helper */
static inline const char *aether_proc_type_str(enum aether_proc_type t)
{
    switch (t) {
    case AETHER_PROC_AI_INFERENCE: return "ai_inference";
    case AETHER_PROC_AI_DAEMON:    return "ai_daemon";
    case AETHER_PROC_CODING:       return "coding";
    case AETHER_PROC_REASONING:    return "reasoning";
    case AETHER_PROC_BACKGROUND:   return "background";
    case AETHER_PROC_GAMING:       return "gaming";
    case AETHER_PROC_SYSTEM:       return "system";
    default:                       return "unknown";
    }
}

static inline const char *aether_mode_str(enum aether_cognitive_mode m)
{
    switch (m) {
    case AETHER_MODE_IDLE:           return "idle";
    case AETHER_MODE_CONVERSATIONAL: return "conversational";
    case AETHER_MODE_REASONING:      return "reasoning";
    case AETHER_MODE_CODING:         return "coding";
    case AETHER_MODE_CREATIVE:       return "creative";
    case AETHER_MODE_KNOWLEDGE:      return "knowledge";
    case AETHER_MODE_DREAMING:       return "dreaming";
    default:                         return "unknown";
    }
}

#endif /* _AETHER_TYPES_H */
