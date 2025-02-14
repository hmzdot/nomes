from action import ExecuteShellCommand
from agent import Agent, ActionCall
from prompt import SYSTEM_MESSAGE

RESPONSE_1 = """
Sure, I'll create the file, add the code, and run it. 

1. Creating the file `index.js`.
2. Adding the code to print "Hello, world!".
3. Running the file.

Let's start with creating the file and adding the code. 

<execute_shell_command>("echo 'console.log(\\"Hello, world!\\");' > index.js")</execute_shell_command>
"""


def test_parse_response():
    print("Only <end> in the response:")
    print(Agent()._parse_response("<end>"))

    print("Only text in the response:")
    print(Agent()._parse_response("Hello, how are you?"))

    print("Text and action call in the response:")
    print(
        Agent()._parse_response(
            """
            <action_name>(param1, param2) => result</action_name>
            """.strip()
        )
    )

    print("Text and action call in the response:")
    print(
        Agent()._parse_response(
            """
            <action_name>(param1, param2) => result</action_name>
            Hello, how are you?
            """.strip()
        )
    )

    print("Response 1")
    parsed = Agent(actions=[ExecuteShellCommand()]).parse_input(RESPONSE_1)
    print(parsed.action_calls[0].args)


def test_make_context():
    print("Empty context:")
    print(Agent()._make_context())

    print("Context with one message:")
    session = Agent()
    session.messages.append("Hello, how are you?")
    print(session._make_context())

    print("Context with one message and one action call:")
    session = Agent()
    session.messages.append("Hello, how are you?")
    session.call_results.append(
        (ActionCall("execute_shell_command", ["command"], ["ls"]), "result")
    )
    print(session._make_context())


def test_prepare_llm_request():
    session = Agent()
    session.messages.append("Hello, how are you?")
    session.call_results.append(
        (ActionCall("execute_shell_command", ["command"], ["ls"]), "result")
    )
    ctx = session._make_context()
    query = "What is the output of the ls command?"
    query = f"<query>{query}</query>\n"
    print(
        [
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": ctx},
            {"role": "user", "content": query},
        ]
    )


def test_execute_shell_command():
    print(ExecuteShellCommand().execute("ls"))


if __name__ == "__main__":
    test_parse_response()
    # test_make_context()
    # test_prepare_llm_request()
    # test_execute_shell_command()
    print("OK")
