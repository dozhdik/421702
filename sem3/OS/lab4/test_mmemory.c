#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "mmemory.h"

void test_mm_init_and_destroy(void) {
    MemoryManager mm;
    mm_init(&mm, 4, 16); 

    assert(mm.physical_frames == 4);
    assert(mm.virtual_pages == 16);
    assert(mm.phys_mem != NULL);
    assert(mm.hits == 0);
    assert(mm.misses == 0);

    for (unsigned int i = 0; i < 16; ++i) {
        assert(mm.page_table[i].frame == -1);
        assert(mm.page_table[i].valid == 0);
        assert(mm.page_table[i].allocated == 0);
    }

    mm_destroy(&mm);
    printf("✅ test_mm_init_and_destroy passed\n");
}

void test_mm_alloc_free(void) {
    MemoryManager mm;
    mm_init(&mm, 4, 16);

    int start = mm_alloc(&mm, 3);
    assert(start >= 0);
    assert(start + 2 < 16);

    for (int i = 0; i < 3; ++i) {
        assert(mm.page_table[start + i].allocated == 1);
    }

    mm_free(&mm, start);

    for (int i = 0; i < 3; ++i) {
        assert(mm.page_table[start + i].allocated == 0);
        assert(mm.page_table[start + i].valid == 0); 
    }

    mm_destroy(&mm);
    printf("✅ test_mm_alloc_free passed\n");
}

void test_mm_read_write_basic(void) {
    MemoryManager mm;
    mm_init(&mm, 2, 8);

    int page = mm_alloc(&mm, 1);
    assert(page >= 0);

    uint32_t addr = (uint32_t)page * PAGE_SIZE + 100;
    uint8_t val = 42;

    int res = mm_write(&mm, addr, val);
    assert(res == 0);

    uint8_t read_val;
    res = mm_read(&mm, addr, &read_val);
    assert(res == 0);
    assert(read_val == val);

    mm_destroy(&mm);
    printf("✅ test_mm_read_write_basic passed\n");
}

void test_page_fault_and_lru(void) {
    MemoryManager mm;
    mm_init(&mm, 2, 4);

    int p0 = mm_alloc(&mm, 1); 
    int p1 = mm_alloc(&mm, 1); 
    int p2 = mm_alloc(&mm, 1); 

    assert(p0 == 0);
    assert(p1 == 1);
    assert(p2 == 2);

    mm_write(&mm, 0 * PAGE_SIZE, 10);
    mm_write(&mm, 1 * PAGE_SIZE, 20);

    unsigned long hits, misses;
    mm_get_stats(&mm, &hits, &misses);
    assert(misses == 2);
    assert(hits == 0);

    uint8_t v;
    mm_read(&mm, 0 * PAGE_SIZE, &v);
    mm_get_stats(&mm, &hits, &misses);
    assert(hits == 1);
    assert(misses == 2);

    mm_write(&mm, 2 * PAGE_SIZE, 30);
    mm_get_stats(&mm, &hits, &misses);
    assert(misses == 3); 

    assert(mm.page_table[0].valid == 1);
    assert(mm.page_table[1].valid == 0);
    assert(mm.page_table[2].valid == 1);

    mm_destroy(&mm);
    printf("✅ test_page_fault_and_lru passed\n");
}

int main(void) {
    printf("=== Запуск юнит-тестов ===\n");

    test_mm_init_and_destroy();
    test_mm_alloc_free();
    test_mm_read_write_basic();
    test_page_fault_and_lru();

    printf("✅ Все тесты пройдены!\n");
    return 0;
}