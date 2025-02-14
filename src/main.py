from agent import Agent
from action import ExecuteShellCommand

if __name__ == "__main__":
    import sys

    agent = Agent(
        actions=[ExecuteShellCommand()],
        max_call_depth=2,
    )
    print("Log file created: ", agent.logger.log_file)
    print(agent.query(sys.argv[1]))
