from agent import Agent
from action import ExecuteShellCommand, WriteFile

if __name__ == "__main__":
    import sys

    agent = Agent(
        actions=[ExecuteShellCommand(), WriteFile()],
        max_call_depth=10,
    )
    print("Log file created: ", agent.logger.log_file)
    print(agent.query(sys.argv[1]))
