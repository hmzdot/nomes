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
    def execute(self, *args) -> str:
        print(f">>> {self.name}({args})")


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
        status = "Success" if result.returncode == 0 else "Failed"
        return f"{status}({result.returncode}): {result.stdout}"


class WriteFile(Action):
    def __init__(self):
        super().__init__(
            name="write_file",
            description="Write multiline text to a file",
            parameters=["file_path", "content"],
        )

    def execute(self, file_path: str, content: str) -> str:
        super().execute(file_path, content)
        with open(file_path, "w") as file:
            bytes_written = file.write(content)
        return f"{bytes_written} bytes written to {file_path}"
