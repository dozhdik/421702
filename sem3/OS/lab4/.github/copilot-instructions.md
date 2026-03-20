**Overview**

This repository implements a simple virtual memory simulator in C (page table, allocation, LRU page replacement).
Key sources: `mmemory.h` (API + constants), `mmemory.c` (implementation), `main.c` (CLI/test harness), and `test_mmemory.c` (unit tests).

**How the project is organized**

- **`mmemory.h`**: public API and constants (`PAGE_SIZE`, `VIRTUAL_PAGES`, `PHYSICAL_FRAMES`). Note: the `page_table` array is statically sized to `VIRTUAL_PAGES`.
- **`mmemory.c`**: core logic — physical memory allocation, `mm_init`, `mm_alloc`/`mm_free`, `mm_read`/`mm_write`, and LRU via `last_use` timestamps.
- **`main.c`**: interactive menu used to exercise the manager (allocation, read/write, tests, stats).
- **`test_mmemory.c`**: small unit tests that compile/run with `mmemory.c` and use `assert()`.

**Build & test commands**

Use plain `gcc` in this repo. Example commands used when working locally:

```bash
# build the CLI
gcc -g main.c mmemory.c -o program

# run the interactive program
./program

# build and run unit tests
gcc -g test_mmemory.c mmemory.c -o test_mmemory && ./test_mmemory
```

Note: VS Code has an existing task (`C/C++: gcc build active file`) that compiles the active file with `gcc -g`. Use it for quick single-file builds.

**Critical APIs & return conventions**

- `mm_init(MemoryManager *mm, unsigned int phys_frames, unsigned int virt_pages)` — initialize manager; pass 0 to use defaults from the header.
- `mm_destroy(MemoryManager *mm)` — frees `phys_mem`.
- `mm_alloc(MemoryManager *mm, unsigned int pages_count)` — allocates a contiguous run of virtual pages, returns start VPN or `-1`.
- `mm_free(MemoryManager *mm, int start_page)` — frees an allocated block starting at `start_page`.
- `mm_read` / `mm_write` — return `0` on success, `-1` on error (`vpn` out of range or internal failure).
- `mm_get_stats` — reads `hits`/`misses` counters stored inside `MemoryManager`.

**Project-specific patterns & gotchas (important for code changes)**

- LRU is implemented via `PageTableEntry.last_use` and a global `mm->time` incremented on each access — replacement picks the lowest `last_use`.
- `phys_mem` is a heap allocation sized `physical_frames * PAGE_SIZE` (see `mm_init`). Access math uses `(size_t)frame * PAGE_SIZE + offset`.
- The page table is a fixed array `PageTableEntry page_table[VIRTUAL_PAGES]` (compile-time size). `mm_init` sets `mm->virtual_pages` to the requested number, but the array size remains `VIRTUAL_PAGES`. Never pass `virt_pages > VIRTUAL_PAGES` — the code will index out of bounds.
- `mm_alloc` only marks `allocated` flags but `mm_read`/`mm_write` do not validate `allocated` before loading a page; tests and `main.c` call `mm_alloc` first. Be careful when adding checks or changing semantics.
- `mm_free` clears `phys_mem` bytes for frames freed; ensure you preserve that behavior if changing free logic.

**Where to look for examples**

- Contiguous allocation: see `mm_alloc` in `mmemory.c` and how `main.c` calls `mm_alloc` then uses the returned start page.
- Page replacement + stats: `ensure_page_loaded`, `choose_victim`, `find_free_frame` in `mmemory.c`; `test_mmemory.c` asserts `hits`/`misses` counts.

**Safe modification checklist for contributors/agents**

- If changing `VIRTUAL_PAGES` or `PAGE_SIZE`, update `mmemory.h` and run `test_mmemory.c` to validate indexing and memory math.
- If making `page_table` dynamically sized, update all initialization and access sites and run tests — current code assumes static array size.
- Keep `mm_get_stats` and the counters (`mm->hits`/`mm->misses`) semantics intact unless intentionally changing observable behavior; tests assert on them.

**Suggested agent behaviors when editing**

- Reference concrete lines: use `mmemory.c`'s `ensure_page_loaded` when modifying page replacement or zeroing memory.
- When adding new public APIs, mirror existing style in `mmemory.h` (C-style declarations, short names starting with `mm_`).
- Run unit tests after changes: `gcc -g test_mmemory.c mmemory.c -o test_mmemory && ./test_mmemory` and fix breakages before proposing patches.

If anything is unclear or you want this guidance expanded (e.g., adding examples for common refactors), tell me which parts to elaborate and I'll iterate.
