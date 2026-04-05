#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>

#define MAX_INPUT 1024
#define MAX_ARGS 64

int main() {
    char input[MAX_INPUT];
    char *args[MAX_ARGS];
    pid_t pid;
    int status;

    while (1) {
        printf("mysh> ");
        if (fgets(input, sizeof(input), stdin) == NULL) {
            perror("fgets error");
            break;
        }

        input[strcspn(input, "\n")] = '\0';

        if (strcmp(input, "exit") == 0)
            break;

        int i = 0;
        char *token = strtok(input, " ");
        while (token != NULL && i < MAX_ARGS - 1) {
            args[i++] = token;
            token = strtok(NULL, " ");
        }
        args[i] = NULL;

        if (args[0] == NULL)
            continue;

        pid = fork();

        if (pid < 0) {
            perror("fork error");
            continue;
        } else if (pid == 0) {
            execvp(args[0], args);
            perror("exec error");
            exit(EXIT_FAILURE);
        } else {
            waitpid(pid, &status, 0);
        }
    }

    printf("Выход из интерпретатора.\n");
    return 0;
}
