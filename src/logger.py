import os
import uuid


class Logger:
    def __init__(self):
        self.id = uuid.uuid4()
        os.makedirs("logs", exist_ok=True)
        self.log_file = f"logs/{self.id}.txt"

    def log(self, message: str):
        with open(self.log_file, "a") as f:
            f.write(message + "\n\n")
