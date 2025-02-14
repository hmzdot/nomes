import subprocess
from abc import abstractmethod


class Action:
    def __init__(self, name, description, parameters):
        self.name = name
        self.description = description
        self.parameters = parameters

    def __str__(self):
        return f"{self.name}: {self.description}"

    @abstractmethod
    def execute(self, *args, **kwargs) -> str:
        print(f"[exec] {self.name}: {[*args]} ")


class ExecuteShellCommand(Action):
    def __init__(self):
        super().__init__(
            name="execute_shell_command",
            description="Execute a shell command",
            parameters=["command"],
        )

    def execute(self, command: str) -> str:
        super().execute(command)
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return f"(Return Code: {result.returncode}) {result.stdout}"


ACTIONS = {
    "execute_shell_command": ExecuteShellCommand(),
}
