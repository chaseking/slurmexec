# 01 Basic example
This basic example walks through a simple countdown running on Slurm.

By default it will execute only on Slurm. If you wish to test it locally, uncomment the `set_slurm_debug()` line in `main.py` and it will run locally.

Use `python main.py -h` to view arguments, which by default are copied from the function declaration.

## Executing on slurm
```bash
(myenv) [chase@slurm-login-node slurmexec]$ python examples/01_basic_example/main.py

*===============================================================================*
|   Executing Slurm job with name "my_countdown_task"...
|      (countdown() in /share/users/chase/Documents/slurmexec/examples/01_basic_example/main.py)
|
|   Status: SUCCESS
|   Slurm job id: 3378805
|   Script file: /home/chase/slurm/my_countdown_task/_slurm_script.sh
|   Log file: /home/chase/slurm/my_countdown_task/3378805.out
|
*===============================================================================*
```
Here is an example output (from the log file above)
```
> cat /home/chase/slurm/my_countdown_task/3378804.out

# Executing job "my_countdown_task" (countdown() in /share/chase/Documents/slurmexec/examples/01_basic_example/main.py) in a task generated using SlurmExecutableBuilder.
# Slurm job name: my_countdown_task
# Slurm node: ax03
# Slurm cluster: axon
# Slurm job id: 3378805
# Job start time: Thu May 30 15:05:36 EDT 2024

Put your commands to execute before this python file here
Starting countdown task with slurm ID: 3378805
10...
9...
8...
7...
6...
5...
4...
3...
2...
1...
Done!
```