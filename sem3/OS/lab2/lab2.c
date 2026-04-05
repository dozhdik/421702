#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/wait.h>

void print_process_info(const char* msg) {
    pid_t my_pid = getpid();
    pid_t parent_pid = getppid();
    printf("%s PID: %d, Parent PID: %d\n", msg, my_pid, parent_pid);
}

int main() {
    printf("=== Запуск программы (вариант 5: 0 1 1 2 2 3 3) ===\n");
    print_process_info("Основной процесс запущен");

    pid_t pids[7] = {0};
    pids[0] = getpid(); 

    if ((pids[1] = fork()) == 0) {
        print_process_info("Процесс 2 запущен");
        if ((pids[3] = fork()) == 0) {
            print_process_info("Процесс 4 запущен");
            print_process_info("Процесс 4 завершает работу");
            exit(0);
        }
        if ((pids[4] = fork()) == 0) {
            print_process_info("Процесс 5 запущен");
            printf("Процесс 5 выполняет exec('ps')\n");
            execlp("ps", "ps", NULL);
            perror("execlp failed");
            exit(1);
        }
        waitpid(pids[3], NULL, 0);
        waitpid(pids[4], NULL, 0);
        print_process_info("Процесс 2 завершает работу");
        exit(0);
    }

    if ((pids[2] = fork()) == 0) {
        print_process_info("Процесс 3 запущен");
        if ((pids[5] = fork()) == 0) {
            print_process_info("Процесс 6 запущен");
            print_process_info("Процесс 6 завершает работу");
            exit(0);
        }
        if ((pids[6] = fork()) == 0) {
            print_process_info("Процесс 7 запущен");
            print_process_info("Процесс 7 завершает работу");
            exit(0);
        }
        waitpid(pids[5], NULL, 0);
        waitpid(pids[6], NULL, 0);
        print_process_info("Процесс 3 завершает работу");
        exit(0);
    }

    waitpid(pids[1], NULL, 0);
    waitpid(pids[2], NULL, 0);

    print_process_info("Основной процесс завершает работу");
    return 0;
}