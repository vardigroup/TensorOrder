/******************************************
Copyright (c) 2019, Jeffrey Dudek
******************************************/

#include <array>
#include <chrono>
#include <cstdio>
#include <iostream>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

#include <string.h>
#include <stdio.h>
#include <unistd.h>
#include <sched.h>
#include <errno.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <poll.h>

#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <stdlib.h>
#include <stdio.h>
#include <fcntl.h>

#include <sys/prctl.h>

/**
 * return the list of cores allocated to this process
 */
std::vector<unsigned short int> find_cores() {
    cpu_set_t mask;
    std::vector<unsigned short int> cores;
    sched_getaffinity(0,sizeof(cpu_set_t),&mask);

    for(unsigned short int i=0; i < sizeof(cpu_set_t)<<3; ++i) {
        if(CPU_ISSET(i,&mask)) {
            cores.push_back(i);
        }
    }
    return cores;
}

std::vector<char *> split(const std::string command) {
    std::vector<char *> result;
    
    std::string word;
    size_t i = 0;
    do
    {
        while(i < command.length() && isspace(command[i])) {
            ++i;
        }
        word.clear();
        while(i < command.length() && !isspace(command[i])) {
            word += command[i++];
        }

        if(!word.empty()) {
            result.push_back(strdup(word.c_str()));
        }
    }
    while(i < command.length());
    result.push_back(nullptr);
    return result;
}

void run_solver(int id, int pipe, std::mutex *output_mtx) {
    std::array<char, 512> buffer;
    std::string decomposition;

    FILE* output = fdopen(pipe, "r");    
    while (fgets(buffer.data(), buffer.size(), output) != nullptr) {
        decomposition += buffer.data();

        // A line containing only "=" indicates a separation in the tree decomposition,
        // so atomically print the entire tree decomposition. 
        if (buffer[0] == '=' && buffer[1] == '\n' && buffer[2] == '\0') {
            output_mtx->lock();
            std::cout << "c Portfolio: " << id << std::endl;
            using namespace std::chrono;
            std::cout << "c Finished " << duration_cast<milliseconds>(system_clock::now().time_since_epoch()).count() << std::endl;
            std::cout << decomposition << std::flush;
            output_mtx->unlock();
            decomposition.clear();
        }
    }

    // If we reach EOF with remaining decomposition, output it.
    if (decomposition.size() > 0) {
        output_mtx->lock();
        std::cout << "c Portfolio: " << id << std::endl;
        std::cout << decomposition;
        std::cout << "=" << std::endl;
        output_mtx->unlock();
    }
}

int main(int argc, char *argv[]) {
    if (argc == 2 && (strcmp(argv[1], "-h") == 0 || strcmp(argv[1], "--help") == 0)) {
        std::cout << argv[0] << " [GRAPH] [SOLVER]*" << std::endl;
        std::cout << "Run all SOLVER commands in parallel with the file [GRAPH] as stdin." << std::endl;
        std::cout << "Prints all decompositions output by the SOLVERs, separated by '=\\n'." << std::endl;
        return 0;
    }

    // No solvers provided
    if(argc <= 2) {
        return 0;
    }
    size_t num_solvers = static_cast<size_t>(argc - 2);
    
    // Load the cores available for use
    std::vector<unsigned short int> cores = find_cores();
    if(cores.size() == 0) {
        std::cout << "c Portfolio: No cores available" << std::endl;
        return 1;
    }

    // Fork a instance of each solver, and store a fd to observe results of each 
    std::vector<pid_t> pids(num_solvers);
    std::vector<int> pipes(num_solvers);
	
    pid_t ppid_before_fork = getpid();
    for (size_t i = 0; i < num_solvers; i++) {
        pid_t pid = 0;
        int solver_result_pipe[2];
        pipe(solver_result_pipe);

        pid = fork();
        if (pid == 0)
        {
			int r = prctl(PR_SET_PDEATHSIG, SIGTERM);
            if (r == -1) { perror(0); exit(1); }
            // test in case the original parent exited just
            // before the prctl() call
            if (getppid() != ppid_before_fork)
                exit(1);
			
            // Redirect solver results to the new pipe
            close(solver_result_pipe[0]);
            dup2(solver_result_pipe[1], STDOUT_FILENO);
            dup2(solver_result_pipe[1], STDERR_FILENO);
            
            // Open the provided graph as STDIN
            int graph_fd = open(argv[1], O_RDONLY);
            dup2(graph_fd, STDIN_FILENO);
            close(graph_fd);

            /*
            // Set the affinity to a single available core, in round-robin
            cpu_set_t cpuset;
            CPU_ZERO(&cpuset);
            CPU_SET(cores[i % cores.size()], &cpuset);
            int rc = sched_setaffinity(0, sizeof(cpuset), &cpuset);
            if (rc != 0) {
                std::cout << "c Portfolio: Error setting affinity of " << i << ": " << rc << std::endl;
            }
            */

            std::vector<char *> solver_command = split(argv[i+2]);
            execvp(solver_command[0], &solver_command[0]);
            std::cout << "c Failed to start solver " << i << ": " << errno << std::endl;
            return 0;
        }

        close(solver_result_pipe[1]);
        pids[i] = pid;
        pipes[i] = solver_result_pipe[0];
    }

    // Start a thread to observe the output of each solver
    using namespace std::chrono;
    std::cout << "c Solvers started " << duration_cast<milliseconds>(system_clock::now().time_since_epoch()).count() << std::endl;
    std::vector<std::thread> gatherers(num_solvers);
    std::mutex output_mtx;
    for (size_t i = 0; i < num_solvers; i++) {
        gatherers[i] = std::thread(run_solver, i, pipes[i], &output_mtx);
    }

    // Wait for all solvers to finish
    int status;
    for (size_t i = 0; i < num_solvers; i++) {
        waitpid(pids[i], &status, 0);
        gatherers[i].join();
    }
    return 0;
}
