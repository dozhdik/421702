#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "mmemory.h"

MemoryManager mm;
int mm_initialized = 0;

/* ===== ТЕСТЫ ===== */

void seq_access_test(unsigned int accesses, unsigned int working_set) {
    unsigned int max_addr = working_set * PAGE_SIZE;
    for (unsigned int i = 0; i < accesses; i++) {
        uint32_t addr = (i % max_addr);
        mm_write(&mm, addr, (uint8_t)(i & 0xFF));

        uint8_t v;
        mm_read(&mm, addr, &v);
    }
}

void random_access_test(unsigned int accesses) {
    for (unsigned int i = 0; i < accesses; i++) {
        uint32_t page = rand() % mm.virtual_pages;
        uint32_t offset = rand() % PAGE_SIZE;
        uint32_t addr = page * PAGE_SIZE + offset;
        mm_write(&mm, addr, (uint8_t)(i & 0xFF));
    }
}

void temporal_locality_test(unsigned int accesses, unsigned int hot_pages, unsigned int cold_pages) {
    for (unsigned int i = 0; i < accesses; i++) {
        unsigned int page;
        if ((rand() % 100) < 80)
            page = rand() % hot_pages;
        else
            page = hot_pages + rand() % cold_pages;

        uint32_t addr = page * PAGE_SIZE + (rand() % PAGE_SIZE);
        mm_write(&mm, addr, (uint8_t)(i & 0xFF));
    }
}

/* ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===== */

void print_page_table() {
    printf("\n===== Таблица страниц =====\n");
    printf("VPN\tValid\tFrame\tLastUse\tAllocated\n");
    for (unsigned int i = 0; i < mm.virtual_pages; i++) {
        PageTableEntry *e = &mm.page_table[i];
        printf("%u\t%d\t%d\t%lu\t%d\n", i, e->valid, e->frame, e->last_use, e->allocated);
    }
}

void print_frames() {
    printf("\n===== Состояние фреймов =====\n");

    for (unsigned int f = 0; f < mm.physical_frames; f++) {
        int used_by = -1;
        for (unsigned int p = 0; p < mm.virtual_pages; p++) {
            if (mm.page_table[p].valid && mm.page_table[p].frame == (int)f) {
                used_by = p;
                break;
            }
        }
        printf("Frame %u: %s (VPN=%d)\n",
               f,
               used_by == -1 ? "Свободен" : "Занят",
               used_by);
    }
}

void print_stats() {
    unsigned long hits, misses;
    mm_get_stats(&mm, &hits, &misses);

    printf("\n===== Статистика =====\n");
    printf("Попадания (hits):   %lu\n", hits);
    printf("Промахи (misses):   %lu\n", misses);
    printf("Hit ratio:          %.3f\n",
           hits + misses == 0 ? 0.0 : (double)hits / (hits + misses));
}

/* ===== МЕНЮ ===== */

void menu() {
    printf("\n===== МЕНЮ =====\n");
    printf("1. Инициализировать менеджер памяти\n");
    printf("2. Выделить виртуальный блок\n");
    printf("3. Освободить блок\n");
    printf("4. Записать байт\n");
    printf("5. Прочитать байт\n");
    printf("6. Последовательный тест\n");
    printf("7. Случайный тест\n");
    printf("8. Тест временной локальности\n");
    printf("9. Показать таблицу страниц\n");
    printf("10. Показать фреймы\n");
    printf("11. Показать статистику\n");
    printf("12. Сбросить статистику\n");
    printf("0. Выход\n");
    printf("Выбор: ");
}

int main() {
    srand((unsigned int)time(NULL));

    int choice;
    while (1) {
        menu();
        scanf("%d", &choice);

        if (choice == 0) break;

        switch (choice) {

        case 1: {
            int pf, vp;
            printf("Введите количество фреймов: ");
            scanf("%d", &pf);
            printf("Введите количество виртуальных страниц: ");
            scanf("%d", &vp);
            mm_init(&mm, pf, vp);
            mm_initialized = 1;
            printf("Менеджер памяти инициализирован.\n");
        } break;

        case 2: {
            if (!mm_initialized) { printf("Сначала инициализируйте менеджер.\n"); break; }
            int pages;
            printf("Сколько страниц выделить? ");
            scanf("%d", &pages);
            int start = mm_alloc(&mm, pages);
            if (start >= 0)
                printf("Блок выделен. Стартовая страница = %d\n", start);
            else
                printf("Ошибка: нет места.\n");
        } break;

        case 3: {
            if (!mm_initialized) { printf("Сначала инициализируйте менеджер.\n"); break; }
            int sp;
            printf("Введите стартовую страницу: ");
            scanf("%d", &sp);
            mm_free(&mm, sp);
            printf("Блок освобождён.\n");
        } break;

        case 4: {
            if (!mm_initialized) { printf("Сначала инициализируйте менеджер.\n"); break; }

            uint32_t addr;
            int val;
            printf("Введите виртуальный адрес: ");
            scanf("%u", &addr);
            printf("Введите значение (0-255): ");
            scanf("%d", &val);

            mm_write(&mm, addr, (uint8_t)val);
            printf("Записано.\n");
        } break;

        case 5: {
            if (!mm_initialized) { printf("Сначала инициализируйте менеджер.\n"); break; }

            uint32_t addr;
            uint8_t out;
            printf("Введите виртуальный адрес: ");
            scanf("%u", &addr);

            if (mm_read(&mm, addr, &out) == 0)
                printf("Значение: %u\n", out);
            else
                printf("Ошибка — неверный адрес.\n");
        } break;

        case 6: {
            if (!mm_initialized) { printf("Сначала инициализируйте менеджер.\n"); break; }
            int a, ws;
            printf("Введите количество обращений: ");
            scanf("%d", &a);
            printf("Введите working set (страниц): ");
            scanf("%d", &ws);
            mm.hits = mm.misses = 0;
            seq_access_test(a, ws);
            printf("Тест завершён.\n");
        } break;

        case 7: {
            int a;
            printf("Введите количество обращений: ");
            scanf("%d", &a);
            mm.hits = mm.misses = 0;
            random_access_test(a);
            printf("Тест завершён.\n");
        } break;

        case 8: {
            int a, hot, cold;
            printf("Введите количество обращений: ");
            scanf("%d", &a);
            printf("Сколько hot-pages: ");
            scanf("%d", &hot);
            printf("Сколько cold-pages: ");
            scanf("%d", &cold);

            mm.hits = mm.misses = 0;
            temporal_locality_test(a, hot, cold);
            printf("Тест завершён.\n");
        } break;

        case 9:
            if (!mm_initialized) { printf("Сначала инициализируйте менеджер.\n"); break; }
            print_page_table();
            break;

        case 10:
            if (!mm_initialized) { printf("Сначала инициализируйте менеджер.\n"); break; }
            print_frames();
            break;

        case 11:
            if (!mm_initialized) { printf("Сначала инициализируйте менеджер.\n"); break; }
            print_stats();
            break;

        case 12:
            if (!mm_initialized) { printf("Сначала инициализируйте менеджер.\n"); break; }
            mm.hits = mm.misses = 0;
            printf("Статистика сброшена.\n");
            break;

        default:
            printf("Неизвестная команда.\n");
        }
    }

    if (mm_initialized) mm_destroy(&mm);

    printf("Выход.\n");
    return 0;
}