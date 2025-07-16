# openhands/graphs/synchronous_runtime.py
from openhands.graphs.schemas import Action, AgentFinishAction, AgentDelegateAction, Observation, NullObservation, CmdOutputObservation, CmdRunAction
import subprocess

class SyncRuntime:
    """
    A completely self-contained, synchronous runtime that executes commands locally.
    This class has NO dependency on the old runtime or event system.
    """
    def __init__(self):
        print("INFO: Self-Contained Synchronous Runtime Initialized.")

    def execute(self, action: Action) -> Observation:
        """
        Executes an action and returns the corresponding observation.
        """
        if not isinstance(action, CmdRunAction):
            return NullObservation(content=f"Action of type {type(action).__name__} is not executable.")

        try:
            process = subprocess.Popen(
                action.command,
                shell=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(timeout=action.timeout)
            return CmdOutputObservation(
                command_id=process.pid,
                command=action.command,
                exit_code=process.returncode,
                content=stdout + stderr
            )
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            return CmdOutputObservation(
                command=action.command,
                exit_code=-1,
                content=f"Command timed out.\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
            )
        except Exception as e:
            return CmdOutputObservation(
                command=action.command,
                exit_code=-1,
                content=f"An error occurred: {e}"
            )