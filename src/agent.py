import openai
from prompt import SYSTEM_MESSAGE
from action import Action
from logger import Logger
import json
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

    def _parse_response(self, input_str: str) -> ModelResponse:
        input_str = input_str.replace("```json", "").replace("```", "")
        input_str = json.loads(input_str)

        text: str = input_str["text"]
        action_calls: list[dict] = input_str["action_calls"]
        completed: bool = input_str["completed"]

        actions = []
        for action_call in action_calls:
            action_name = action_call["name"]
            args = action_call["args"]
            args = [codecs.decode(arg, "unicode_escape") for arg in args]

            available_action = self.actions.get(action_name)
            if available_action is None:
                print(f"Action {action_name} not found")
                continue
            actions.append(ActionCall(action_name, available_action.parameters, args))

        return ModelResponse(
            text=text,
            action_calls=actions,
            completed=completed,
        )

    def _make_query_dict(self, query: str) -> str:
        query_dict = {}
        query_dict["query"] = query

        query_dict["available_actions"] = [
            {
                "name": action.name,
                "description": action.description,
                "params": action.parameters,
            }
            for action in self.actions.values()
        ]

        ctx = {}
        ctx["messages"] = self.messages
        ctx["calls"] = self.call_results
        query_dict["context"] = ctx

        return json.dumps(query_dict)

    def _make_llm_request(self, query: str) -> ModelResponse:
        query_dict = self._make_query_dict(query)
        self.logger.log(query_dict)

        response = OpenAI.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": query_dict},
            ],
        )
        response = response.choices[0].message.content
        self.logger.log(response)
        return self._parse_response(response)

    def query(self, prompt: str) -> str:
        while self.call_depth < self.max_call_depth:
            self.logger.log(f"Call depth: {self.call_depth}")
            response = self._make_llm_request(prompt)
            self.logger.log(response.__repr__())

            for action_call in response.action_calls:
                action_name = action_call.name
                action_args = action_call.args

                action = self.actions.get(action_name)
                if action is None:
                    print(f"Action {action_name} not found")
                    continue

                result = action.execute(*action_args)

                self.call_results.append(
                    {
                        "name": action_name,
                        "args": action_args,
                        "result": result,
                    }
                )

            self.messages.append({"role": "user", "message": prompt})
            if len(response.text) > 0:
                self.messages.append({"role": "assistant", "message": response.text})

            if response.completed:
                return response.text

            self.call_depth += 1

        return "Max call depth reached"
