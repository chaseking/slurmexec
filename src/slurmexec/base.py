import subprocess
from pathlib import Path
from functools import wraps
import inspect

from .util import get_env_var, load_func_argparser

__all__ = ["get_slurm_id", "is_this_a_slurm_job", "slurm_job", "slurm_exec", "set_slurm_debug"]

_IS_SLURM_DEBUG = False

def set_slurm_debug(debug: bool = True):
    """Sets slurm debug mode, allowing slurm jobs to be executed locally for debugging.

    Args:
        debug (bool, optional): Debug mode. Defaults to True.
    """
    global _IS_SLURM_DEBUG
    _IS_SLURM_DEBUG = debug

    if debug:
        print()
        print("=======================================================")
        print("|   NOTICE - Slurm running in debug mode.")
        print("|   All slurm tasks will be immediately executed")
        print("|   rather than queued on Slurm.")
        print("=======================================================")
        print()

def get_slurm_id():
    if _IS_SLURM_DEBUG:
        return "SLURM_DEBUG"
    else:
        return get_env_var("SLURM_JOB_ID")

def is_this_a_slurm_job():
    global _IS_SLURM_DEBUG
    return get_env_var("SLURM_JOB_ID") is not None or _IS_SLURM_DEBUG

class SlurmExecutableBuilder:
    """Class used to build a slurm executable command."""
    def __init__(self, job_name, full_job_name=None, script_dir=None):
        self.job_name = job_name
        self.full_job_name = full_job_name

        if script_dir is None:
            self._dir = Path.home() / "slurm" / job_name
        if type(script_dir) is not Path:
            self._dir = Path(script_dir).expanduser()
        else:
            self._dir = script_dir
        
        self.script_file = self._dir / f"_slurm_script.sh"
        
        self._args = {
            "--job-name": job_name,
        }
        self._commands = []

        self.output(f"%x_%j.log") # %x is job name, %A is job id assigned by slurm

        if full_job_name is None:
            self.command(f"echo '# Executing job \"{job_name}\" in a task generated using SlurmExecutableBuilder.'")
        else:
            self.command(f"echo '# Executing job \"{job_name}\" ({full_job_name}) in a task generated using SlurmExecutableBuilder.'")
    
    def arg(self, arg: str, value: any):
        self._args[arg] = value
        return self
    
    def args(self, args: dict[str, any]):
        for k, v in args.items():
            self._args[k] = v
        return self

    def output(self, filename):
        out = str(self._dir / filename)
        self.arg("--output", out)
        self.arg("--error", out)
        return self

    def command(self, command: str | list[str]):
        if isinstance(command, str):
            self._commands.append(command)
        else:
            self._commands.extend(command)
        return self

    def sbatch(self):
        args = "\n".join([
            f"#SBATCH {arg}={value}" if arg.startswith("--")
            else f"#SBATCH {arg} {value}"
            for arg, value in self._args.items()
        ])
        commands = "\n".join(self._commands)

        script = f"""#!/bin/bash -l
# The -l flag makes the script run as if it were executed on the login node;
# this makes it so ~/.bashrc is loaded and the conda env loads properly.
#
# This script was created by a slurmexec SlurmExecutableBuilder
#
{args}

{commands}

# End of script
"""
        
        # Write script to file
        self.script_file.parent.mkdir(parents=True, exist_ok=True)
        self.script_file.write_text(script)
        # with open(self.script_file, "w+") as file: # w+ creates if not exists, otherwise truncates
        #     file.write(script)
        
        # Execute file
        try:
            output = subprocess.check_output(["sbatch", self.script_file], stderr=subprocess.STDOUT)
        except Exception as e:
            raise RuntimeError(f"Failed to execute slurm task: {e}")

        print()
        print("*===============================================================================*")
        print(f"|   Executing Slurm job with name \"{self.job_name}\"...")
        if self.full_job_name is not None:
            print(f"|      ({self.full_job_name})")
        print("|")
        output = output.decode().strip() # parse binary; strip newlines
        
        if output.startswith("Submitted batch job"):
            job_id = output.rsplit(" ", maxsplit=1)[-1] # last item
            print("|   Status: SUCCESS")
            print(f"|   Slurm job id: {job_id}")
            print(f"|   Script file: {self.script_file}")
            print(f"|   Log file: {self._args['--output'].replace('%x', self.job_name).replace('%A', job_id).replace('%j', job_id)}")
        else:
            print("|   Status: FAIL [!!!]")
            print(f"|   Script file: {self.script_file}")
            print(f"|   Error: Bad sbatch output:")
            
            for line in output.split("\n"):
                print(f"|   {line}")
        
        print("|")
        print("*===============================================================================*")
        print()
        

def slurm_job(func):
    """
    Function decorator to be applied to a function representing a Slurm job.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if is_this_a_slurm_job():
            return func(*args, **kwargs)
        else:
            raise RuntimeError(f"Function {func.__name__} cannot be run outside of a slurm job. Please use slurm_exec() to run this job.")

        # try:
        # except:
        #     traceback.print_exc()
        #     return None
    wrapper._is_slurm_job = True # Tags the function as a slurm job
    return wrapper


def slurm_exec(func, n_parallel_jobs=1, script_dir=None, job_name=None, slurm_args=None, pre_run_commands=None):
    """Runs a slurm job. Used in the main method of a .py file.
    Specifically, if called from within a slurm task, `func` will be called.
    Otherwise, it creates a new slurm task specified by the arguments.

    Args:
        func (function): Function to call
        n_parallel_jobs (int, optional): Number of parallel jobs. If 2 or more, then will be run as an array. Defaults to 1.
        script_dir (str, optional): Script directory. Defaults to ~/slurm/job_name, where job_name is the name of func.
        slurm_args (dict, optional): Slurm batch arguments. Defaults to {}.
        pre_run_commands (list, optional): List of commands to run before the main command (e.g., activate environment). None by default.

    Raises:
        ValueError: If func is not an @slurm_job
    """
    if not hasattr(func, "_is_slurm_job"):
        raise ValueError(f"Function {func.__name__} must be decorated with @slurm_job")
    
    if slurm_args is None:
        slurm_args = {}
    if pre_run_commands is None:
        pre_run_commands = []
    
    if job_name is None:
        job_name = func.__name__
    if script_dir is None:
        script_dir = f"~/slurm/{job_name}"

    # First we check if this function was called from a slurm task
    # This is identified by whether a slurm-id argument is passed
    # parser = argparse.ArgumentParser()
    parser = load_func_argparser(func)
    parser.add_argument("--n_parallel_jobs", type=int, default=n_parallel_jobs, help="If >1 then will be run as a slurm array task.")
    parser.add_argument("--out_dir", type=str, default=script_dir, help="Directory to save the slurm script.")
    parser.add_argument("--job_name", type=str, default=job_name, help="Name of the slurm job.")
    exec_args, unk_args = parser.parse_known_args()
    exec_args = vars(exec_args)  # convert to dict

    # remove keys that shouldn't be passed to the function
    n_parallel_jobs = exec_args.pop("n_parallel_jobs")
    script_dir = exec_args.pop("out_dir")
    job_name = exec_args.pop("job_name")

    if is_this_a_slurm_job():
        # This was executed from within a slurm job; call function directly
        func(**exec_args)
    else:
        # This function was executed by a user, with the intention to start a slurm task
        # Parse function arguments and use these as arguments when executing the task
        is_array_task = n_parallel_jobs > 1

        # Load slurm batch arguments
        default_slurm_args = {
            # "--ntasks": 1,
            # "--cpus-per-task": 1,
            # "--mem-per-cpu": "1G"
            # "--time": "1-00:00:00",  # default 1 day
        }

        if is_array_task:
            default_slurm_args["--array"] = f"1-{n_parallel_jobs}"

        # slurm_args = {(f"--{k}" if not k.startswith("--") else k): v for k, v in slurm_args.items()}
        slurm_args = default_slurm_args | slurm_args

        # Pass any unknown command line arguments to slurm_args
        if unk_args:
            slurm_unk_args = {
                unk_args[i]: unk_args[i+1]
                for i in range(0, len(unk_args), 2)
            }
            print(f"Passing `{' '.join(unk_args)}` as arguments to SBATCH.")
            slurm_args = slurm_args | slurm_unk_args


        # Load job name: "{filename}-{func_name}"
        func_file = Path(inspect.getfile(func.__wrapped__))  # the file of the function (wrapped used because otherwise it would return the decorator file)
        full_job_name = f"{func.__name__}() in {func_file}"
        
        if job_name is None:
            func_filename = func_file.name
            func_filename = func_filename[:func_filename.rindex(".")]
            job_name = f"{func_filename}-{func.__name__}"

        slurm = SlurmExecutableBuilder(job_name, full_job_name=full_job_name, script_dir=script_dir)
        slurm.args(slurm_args)

        # Set output file name as "{job id}_{array task id}"
        # %A is the slurm array parent job id
        # %a is the array task id
        # %x is the job name but we're saving that in the folder
        # %j is the job ID
        slurm.output("%A_%a.out" if is_array_task else "%j.out")
        
        slurm.command([
            # Print some info about the cluster
            'echo "# Slurm job name: $SLURM_JOB_NAME"',
            'echo "# Slurm node: $SLURM_JOB_NODELIST"',
            'echo "# Slurm cluster: $SLURM_CLUSTER_NAME"',
            'echo "# Slurm job id: $SLURM_JOB_ID"'
        ])
        
        if is_array_task:
            slurm.command([
                'echo "# Slurm array parent job id: $SLURM_ARRAY_JOB_ID"',
                'echo "# Slurm array task id: $SLURM_ARRAY_TASK_ID"',
            ])
        
        slurm.command([
            'echo "# Job start time: $(date)"',
            'echo'
        ])

        slurm.command(pre_run_commands)
        
        python_file = str(func_file)
        exec_args_str = " ".join([f"--{a} {v}" for a, v in exec_args.items()])
        slurm.command(f"python {python_file} {exec_args_str}")

        # Finally execute the sbatch
        slurm.sbatch()