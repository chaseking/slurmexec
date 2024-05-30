from slurmexec import *

# This sets debug mode, allowing tasks to be executed locally for testing.
set_slurm_debug()

if is_this_a_slurm_job():
    # Since this python file is executed on the slurm login node, large imports
    # may result in an out-of-memory error. Therefore it is good practice to put
    # any imports inside an `is_this_a_slurm_job()` conditional.
    import time

# Now we define the slurm task in a function
# Any arguments (including their type and default value) are parsed from the
# command line. Therefore it is good practice to give argument types and
# defaults, when possible.
@slurm_job
def countdown(start: int = 10):
    print(f"Starting countdown task with slurm ID: {get_slurm_id()}")

    ticker = start
    
    while ticker > 0:
        print(f"{ticker}...")
        time.sleep(1)
        ticker -= 1
    
    print("Done!")

if __name__ == "__main__":
    slurm_exec(
        func = countdown,
        job_name = "my_countdown_task",  # if not supplied the function name is used (here "countdown")
        pre_run_commands = [
            "echo 'Put your commands to execute before this python file here'"
            # e.g., "conda activate myenv"...
        ]
    )