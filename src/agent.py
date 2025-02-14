import openai
from prompt import SYSTEM_MESSAGE
from action import Action

OpenAI = openai.OpenAI()


class ActionCall:
    def __init__(self, name: str, params: list[str], args: list[str]):
        self.name = name
        self.params = params
        self.args = args

    def params_str(self) -> str:
        return ",".join(f"{k}={v}" for k, v in zip(self.params, self.args))

    def __repr__(self):
        return f"ActionCall(name={self.name}, params={self.params_str()})"


class ModelResponse:
    """Parsed response from the LLM."""

    def __init__(self, text: str, action_calls: list[ActionCall], completed: bool):
        self.text = text
        self.action_calls = action_calls
        self.completed = completed

    def __repr__(self):
        return f"ModelResponse(text={self.text}, action_calls={self.action_calls}, completed={self.completed})"


class Agent:
    messages: list[str]
    call_results: list[tuple[ActionCall, str, str]]
    call_depth: int
    max_call_depth: int
    actions: dict[str, Action]

    def __init__(self, actions: list[Action] = [], max_call_depth: int = 10):
        self.messages = []
        self.call_results = []
        self.call_depth = 0
        self.max_call_depth = max_call_depth
        self.actions = {action.name: action for action in actions}

    def _parse_response(self, prompt: str) -> ModelResponse:
        """Extracts the text and action calls from the LLM response."""
        # Initialize variables
        text = []
        action_calls = []
        finished = False

        # Split the response into lines for easier processing
        lines = prompt.strip().split("\n")

        for line in lines:
            if "<end>" in line:
                finished = True
                line = line.replace("<end>", "")

            # Check for action calls using the format <action_name>(params)</action_name>
            if line.strip().startswith("<") and ">" in line and "</" in line:
                start_tag = line.index(">") + 1
                end_tag = line.index("</")
                action_content = line[start_tag:end_tag].strip()

                # Extract action name and parameters
                action_name = line[1 : line.index(">")].strip()
                action = self.actions.get(action_name)
                if action is None:
                    print(f"Action {action_name} not found")
                    continue

                args_str = action_content[
                    action_content.index("(") + 1 : action_content.rindex(")")
                ]
                args = [param.strip() for param in args_str.split(",") if param.strip()]

                action_calls.append(ActionCall(action_name, action.parameters, args))
            else:
                text.append(line)

        return ModelResponse(
            text="\n".join(text).strip(),
            action_calls=action_calls,
            completed=finished,
        )

    def _make_action_list(self) -> str:
        """Make a list of actions that the LLM can call."""
        actions = "Available actions:\n"
        for action in self.actions.values():
            actions += f"{action.name}("
            for param in action.parameters:
                actions += f"{param}={type(param)}, "
            actions += ")\n"
        return actions

    def _make_context(self) -> str:
        """Make context from the previous messages and calls."""
        context = "<context>\n"
        if len(self.messages) > 0:
            context += "<messages>\n"
            for message in self.messages:
                context += f"{message}\n"
            context += "</messages>\n"

        if len(self.call_results) > 0:
            context += "<calls>\n"
            for call_result in self.call_results:
                action_call, action_result = call_result
                action_name = action_call.name
                context += f"<{action_name}>"
                context += f"({action_call.params_str()}) => {action_result}"
                context += f"</{action_name}>\n"
            context += "</calls>\n"

        context += "</context>\n"
        return context

    def _make_llm_request(self, context: str, query: str) -> ModelResponse:
        actions = self._make_action_list()
        query = f"<query>{query}</query>\n"

        response = OpenAI.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": actions},
                {"role": "user", "content": context},
                {"role": "user", "content": query},
            ],
        )
        response = response.choices[0].message.content
        return self._parse_response(response)

    def query(self, prompt: str) -> str:
        while self.call_depth < self.max_call_depth:
            context = self._make_context()
            response = self._make_llm_request(context, prompt)

            if response.completed:
                return response.text

            for action_call in response.action_calls:
                action_name = action_call.name
                action_args = action_call.args

                action = self.actions.get(action_name)
                if action is None:
                    print(f"Action {action_name} not found")
                    continue

                result = action.execute(*action_args)

                self.call_results.append((action_call, result))

            self.messages.append(f"User: {prompt}")
            if len(response.text) > 0:
                self.messages.append(f"You: {response.text}")
            self.call_depth += 1

        return "Max call depth reached"
