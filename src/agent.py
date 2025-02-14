import openai
from prompt import SYSTEM_MESSAGE
from action import Action
from logger import Logger
import re
import codecs

OpenAI = openai.OpenAI()


class ActionCall:
    def __init__(self, name: str, params: list[str], args: list[str]):
        self.name = name
        self.params = params
        self.args = args

    def params_str(self) -> str:
        return ",".join(f"{k}={v}" for k, v in zip(self.params, self.args))

    def __repr__(self):
        return f"{self.name}({self.params_str()})"


class ModelResponse:
    """Parsed response from the LLM."""

    def __init__(self, text: str, action_calls: list[ActionCall], completed: bool):
        self.text = text
        self.action_calls = action_calls
        self.completed = completed

    def __repr__(self):
        return f"ModelResponse:\n{self.text}\nCalls: {self.action_calls}\nCompleted: {self.completed}"


class Agent:
    messages: list[str]
    call_results: list[tuple[ActionCall, str, str]]
    call_depth: int
    max_call_depth: int
    actions: dict[str, Action]
    logger: Logger

    def __init__(self, actions: list[Action] = [], max_call_depth: int = 10):
        self.messages = []
        self.call_results = []
        self.call_depth = 0
        self.max_call_depth = max_call_depth
        self.actions = {action.name: action for action in actions}
        self.logger = Logger()

    def _parse_response(self, prompt: str) -> ModelResponse:
        """Extracts the text and action calls from the LLM response using regex."""
        # Check for <end> tag and remove it
        finished = bool(re.search(r"<end>", prompt))
        prompt = re.sub(r"<end>", "", prompt)

        # Find and process action calls
        action_calls = []

        def process_action(match):
            action_name = match.group(1)
            args_str = match.group(2)

            # Extract quoted arguments, handling escaped quotes
            args = []
            pattern = r'"((?:[^"\\]|\\.)*)"'
            for arg_match in re.finditer(pattern, args_str):
                # De-escape the captured argument
                arg = codecs.decode(arg_match.group(1), "unicode_escape")
                args.append(arg)

            action = self.actions.get(action_name)
            if action:
                action_calls.append(ActionCall(action_name, action.parameters, args))
            return ""  # Remove the action call from the text

        # Pattern matches <action_name>("arg1", "arg2", ...)</action_name>
        action_pattern = r"<(\w+)>\(([^)]+)\)</\1>"
        text = re.sub(action_pattern, process_action, prompt)

        # Clean up any remaining whitespace/empty lines
        text = "\n".join(line for line in text.split("\n") if line.strip())

        return ModelResponse(
            text=text.strip(),
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
        self.logger.log(response)
        return self._parse_response(response)

    def query(self, prompt: str) -> str:
        while self.call_depth < self.max_call_depth:
            self.logger.log(f"Call depth: {self.call_depth}")
            context = self._make_context()
            self.logger.log(context)

            response = self._make_llm_request(context, prompt)
            self.logger.log(response.__repr__())

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

            if response.completed:
                return response.text

            self.call_depth += 1

        return "Max call depth reached"
