#ifndef MMEMORY_H
#define MMEMORY_H

#include <stdint.h>
#include <stddef.h>

#define PAGE_SIZE 4096U
#define VIRTUAL_PAGES 1024U   
#define PHYSICAL_FRAMES 64U  

typedef struct {
    int frame;                 
    int valid;                
    unsigned long last_use;   
    int allocated;            
} PageTableEntry;

typedef struct {
    uint8_t *phys_mem;                     
    PageTableEntry page_table[VIRTUAL_PAGES];
    unsigned long time;                     
    unsigned long hits;                    
    unsigned long misses;                 
    unsigned int physical_frames;           
    unsigned int virtual_pages;             
} MemoryManager;

void mm_init(MemoryManager *mm, unsigned int phys_frames, unsigned int virt_pages);

void mm_destroy(MemoryManager *mm);

int mm_alloc(MemoryManager *mm, unsigned int pages_count);

void mm_free(MemoryManager *mm, int start_page);

int mm_read(MemoryManager *mm, uint32_t addr, uint8_t *out);

int mm_write(MemoryManager *mm, uint32_t addr, uint8_t value);

void mm_get_stats(MemoryManager *mm, unsigned long *hits, unsigned long *misses);

#endif /* MMEMORY_H */