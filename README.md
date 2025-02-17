# Nomes

AI agents from first principles

## Build and Run

⚠️ **WARNING**: This agent has full shell access and can execute arbitrary commands. Only run it in a controlled environment with appropriate security measures. Never expose it directly to untrusted input or public networks.

With `uv` installed:

```bash
git clone git@github.com:hmzdot/nomes.git
cd nomes

# Install dependencies
uv sync

# Set OpenAI API Key
export OPENAI_API_KEY=sk-proj-xxx

# Run the agent
uv run src/main.py "Your prompt here"
```

## Input/Output Format

### Input

The agent accepts a JSON object with:

- `query`: The user's request/question
- `available_actions`: List of actions the agent can perform, each with:
  - `name`: Action identifier
  - `description`: What the action does
  - `params`: Required parameters
- `context`: Previous conversation history and action results

### Output

The agent responds with a JSON object containing:

- `text`: Natural language response
- `action_calls`: List of actions to execute, each with:
  - `name`: Action to perform
  - `args`: Arguments for the action
- `completed`: Boolean indicating if the response is complete

## Example Usage

The `example/` folder demonstrates a conversation where a user requests creating a tic-tac-toe game:

1. User asks to create a tic-tac-toe game
2. Agent first creates a directory using `execute_shell_command`
3. Agent then writes the game code using `write_file`
4. The conversation shows how the agent breaks down complex tasks into steps and provides feedback

See [example/logs.txt](./example/logs.txt) for the full conversation flow and [example/tic-tac-toe/](./example/tic-tac-toe/) for the resulting implementation.
