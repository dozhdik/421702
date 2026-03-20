#include "mmemory.h"
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <stdio.h>

static int find_free_frame(MemoryManager *mm) {
    for (unsigned int f = 0; f < mm->physical_frames; ++f) {
        int used = 0;
        for (unsigned int p = 0; p < mm->virtual_pages; ++p) {
            if (mm->page_table[p].valid &&
                mm->page_table[p].frame == (int)f) 
            {
                used = 1;
                break;
            }
        }
        if (!used) return (int)f;
    }
    return -1;
}

static int choose_victim(MemoryManager *mm) {
    unsigned long min_time = ULONG_MAX;
    int victim = -1;

    for (unsigned int p = 0; p < mm->virtual_pages; ++p) {
        if (mm->page_table[p].valid) {
            if (mm->page_table[p].last_use < min_time) {
                min_time = mm->page_table[p].last_use;
                victim = (int)p;
            }
        }
    }
    return victim;
}

void mm_init(MemoryManager *mm, unsigned int phys_frames, unsigned int virt_pages) {
    if (!mm) return;
    if (phys_frames == 0) phys_frames = PHYSICAL_FRAMES;
    if (virt_pages == 0) virt_pages = VIRTUAL_PAGES;

    mm->physical_frames = phys_frames;
    mm->virtual_pages   = virt_pages;

    mm->phys_mem = calloc((size_t)phys_frames, PAGE_SIZE);
    mm->time = 1;
    mm->hits = mm->misses = 0;

    for (unsigned int i = 0; i < mm->virtual_pages; ++i) {
        mm->page_table[i].frame = -1;
        mm->page_table[i].valid = 0;
        mm->page_table[i].last_use = 0;
        mm->page_table[i].allocated = 0;
    }
}

void mm_destroy(MemoryManager *mm) {
    if (!mm) return;
    free(mm->phys_mem);
    mm->phys_mem = NULL;
}

int mm_alloc(MemoryManager *mm, unsigned int pages_count) {
    if (!mm || pages_count == 0) return -1;

    unsigned int consecutive = 0;

    for (unsigned int i = 0; i < mm->virtual_pages; ++i) {
        if (!mm->page_table[i].allocated) {
            consecutive++;
            if (consecutive == pages_count) {
                unsigned int start = i + 1 - pages_count;
                for (unsigned int j = start; j <= i; ++j)
                    mm->page_table[j].allocated = 1;
                return (int)start;
            }
        } else {
            consecutive = 0;
        }
    }
    return -1;
}

void mm_free(MemoryManager *mm, int start_page) {
    if (!mm || start_page < 0 || (unsigned)start_page >= mm->virtual_pages)
        return;

    for (unsigned int p = (unsigned)start_page; p < mm->virtual_pages; ++p) {
        if (!mm->page_table[p].allocated)
            break;

        if (mm->page_table[p].valid) {
            int f = mm->page_table[p].frame;
            mm->page_table[p].valid = 0;
            mm->page_table[p].frame = -1;

            if (f >= 0)
                memset(mm->phys_mem + (size_t)f * PAGE_SIZE, 0, PAGE_SIZE);
        }
        mm->page_table[p].allocated = 0;
    }
}

static int ensure_page_loaded(MemoryManager *mm, unsigned int vpn) {
    if (vpn >= mm->virtual_pages) return -1;

    if (mm->page_table[vpn].valid) {
        mm->page_table[vpn].last_use = mm->time++;
        mm->hits++;
        return mm->page_table[vpn].frame;
    }

    mm->misses++;

    int free_frame = find_free_frame(mm);
    if (free_frame >= 0) {
        mm->page_table[vpn].frame = free_frame;
        mm->page_table[vpn].valid = 1;
        mm->page_table[vpn].last_use = mm->time++;
        memset(mm->phys_mem + (size_t)free_frame * PAGE_SIZE, 0, PAGE_SIZE);
        return free_frame;
    }

    int victim = choose_victim(mm);
    if (victim < 0) return -1;

    int victim_frame = mm->page_table[victim].frame;
    mm->page_table[victim].valid = 0;
    mm->page_table[victim].frame = -1;

    mm->page_table[vpn].frame = victim_frame;
    mm->page_table[vpn].valid = 1;
    mm->page_table[vpn].last_use = mm->time++;

    memset(mm->phys_mem + (size_t)victim_frame * PAGE_SIZE, 0, PAGE_SIZE);

    return victim_frame;
}

int mm_read(MemoryManager *mm, uint32_t addr, uint8_t *out) {
    if (!mm || !out) return -1;

    unsigned int vpn = addr / PAGE_SIZE;
    unsigned int offset = addr % PAGE_SIZE;

    if (vpn >= mm->virtual_pages) return -1;

    int frame = ensure_page_loaded(mm, vpn);
    if (frame < 0) return -1;

    *out = mm->phys_mem[(size_t)frame * PAGE_SIZE + offset];
    return 0;
}

int mm_write(MemoryManager *mm, uint32_t addr, uint8_t value) {
    if (!mm) return -1;

    unsigned int vpn = addr / PAGE_SIZE;
    unsigned int offset = addr % PAGE_SIZE;

    if (vpn >= mm->virtual_pages) return -1;

    int frame = ensure_page_loaded(mm, vpn);
    if (frame < 0) return -1;

    mm->phys_mem[(size_t)frame * PAGE_SIZE + offset] = value;
    return 0;
}

void mm_get_stats(MemoryManager *mm, unsigned long *hits, unsigned long *misses) {
    if (hits) *hits = mm->hits;
    if (misses) *misses = mm->misses;
}
