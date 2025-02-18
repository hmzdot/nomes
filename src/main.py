from flask import Flask, request, jsonify
from agent import Agent
from action import ExecuteShellCommand, WriteFile

app = Flask(__name__)

# Initialize agent globally so it's reused across requests
agent = Agent(
    actions=[ExecuteShellCommand(), WriteFile()],
    max_call_depth=10,
)
print("Log file created: ", agent.logger.log_file)


@app.route("/query", methods=["POST"])
def handle_query():
    try:
        data = request.get_json()

        if not data or "query" not in data:
            return jsonify({"error": "Missing query parameter"}), 400

        response = agent.query(data["query"])
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=6060)
