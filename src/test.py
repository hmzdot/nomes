from main import Session, ActionCall
from prompt import SYSTEM_MESSAGE


def test_parse_response():
    print("Only <end> in the response:")
    print(Session()._parse_response("<end>"))

    print("Only text in the response:")
    print(Session()._parse_response("Hello, how are you?"))

    print("Text and action call in the response:")
    print(
        Session()._parse_response(
            """
            <action_name>(param1, param2) => result</action_name>
            """.strip()
        )
    )

    print("Text and action call in the response:")
    print(
        Session()._parse_response(
            """
            <action_name>(param1, param2) => result</action_name>
            Hello, how are you?
            """.strip()
        )
    )


def test_make_context():
    print("Empty context:")
    print(Session()._make_context())

    print("Context with one message:")
    session = Session()
    session.messages.append("Hello, how are you?")
    print(session._make_context())

    print("Context with one message and one action call:")
    session = Session()
    session.messages.append("Hello, how are you?")
    session.call_results.append(
        (ActionCall("execute_shell_command", ["command"], ["ls"]), "result")
    )
    print(session._make_context())


def test_prepare_llm_request():
    session = Session()
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


if __name__ == "__main__":
    # test_parse_response()
    # test_make_context()
    # test_prepare_llm_request()
    pass
