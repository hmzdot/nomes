from agent import Agent
from action import ExecuteShellCommand

if __name__ == "__main__":
    import sys

    session = Agent(
        actions=[ExecuteShellCommand()],
        max_call_depth=2,
    )
    print(session.query(sys.argv[1]))
