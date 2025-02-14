from action import ACTIONS


class ActionCall:
    def __init__(self, action_name: str, action_params: list[str]):
        self.action_name = action_name
        self.action_params = action_params

    def __repr__(self):
        return f"ActionCall(action_name={self.action_name}, action_params={self.action_params})"


class ModelResponse:
    """Parsed response from the LLM."""

    def __init__(self, text: str, action_calls: list[ActionCall], completed: bool):
        self.text = text
        self.action_calls = action_calls
        self.completed = completed


class Session:
    messages: list[str]
    call_results: list[tuple[ActionCall, str, str]]
    call_count: int
    max_call_count: int

    def __init__(self, max_call_count: int = 10):
        self.messages = []
        self.call_results = []
        self.call_count = 0
        self.max_call_count = max_call_count

    def _parse_prompt(self, prompt: str) -> ModelResponse:
        pass

    def _make_context(self) -> str:
        """Make context from the previous messages and calls."""
        context = ""
        context += "Previous messages:\n"
        for message in self.messages:
            context += f"{message}\n"

        context += "Previous calls:\n"
        for call_result in self.call_results:
            action_call, action_params_str, action_result = call_result
            action_name = action_call.action_name

            context += f"<{action_name}>({action_params_str}) => {action_result}\n"

        return context

    def _make_llm_request(self, _context: str, _query: str) -> ModelResponse:
        pass

    def query(self, prompt: str) -> str:
        while self.call_count < self.max_call_count:
            context = self._make_context()
            response = self._make_llm_request(context, prompt)

            if response.completed:
                return response.text

            for action_call in response.action_calls:
                action_name = action_call.action_name
                action_params = action_call.action_params

                action = ACTIONS[action_name]
                result = action.execute(*action_params)

                action_params_str = ",".join(
                    f"{param}={value}"
                    for param, value in zip(action.parameters, action_params)
                )
                self.call_results.append((action_call, action_params_str, result))

            self.messages.append(f"User: {prompt}")
            if len(response.text) > 0:
                self.messages.append(f"You: {response.text}")
            self.call_count += 1


def main():
    pass


if __name__ == "__main__":
    main()
