from flask import Flask, request, jsonify
from kubernetes import client, config
import requests
import random
import os

app = Flask(__name__)

# Load Kubernetes configuration
config.load_kube_config()
apps_v1 = client.AppsV1Api()
core_v1 = client.CoreV1Api()

NAMESPACE = "nomes"
BASE_IMAGE = "nomes-sandbox"

active_agents = {}


def generate_random_port():
    """Generate a random port number in a safe range"""
    return random.randint(30000, 32767)


@app.route("/create_agent", methods=["POST"])
def create_agent():
    agent_id = request.json.get("agent_id")

    if not agent_id:
        return jsonify({"error": "Missing agent_id"}), 400

    if agent_id in active_agents:
        return jsonify(
            {
                "message": "Agent already exists",
                "agent_id": agent_id,
                "port": active_agents[agent_id]["port"],
            }
        )

    port = generate_random_port()
    deployment_name = f"agent-{agent_id}"
    service_name = f"agent-service-{agent_id}"

    openai_api_key = os.environ.get("OPENAI_API_KEY", "")

    container = client.V1Container(
        name=deployment_name,
        image=BASE_IMAGE,
        image_pull_policy="Never",  # Prevent Kubernetes from pulling the image
        ports=[client.V1ContainerPort(container_port=6060)],
        env=[client.V1EnvVar(name="OPENAI_API_KEY", value=openai_api_key)],
        resources=client.V1ResourceRequirements(
            limits={"memory": "512Mi", "cpu": "500m"},
            requests={"memory": "256Mi", "cpu": "250m"},
        ),
    )

    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": deployment_name}),
        spec=client.V1PodSpec(containers=[container]),
    )

    deployment = client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=deployment_name),
        spec=client.V1DeploymentSpec(
            replicas=1,
            template=template,
            selector={"matchLabels": {"app": deployment_name}},
        ),
    )

    service = client.V1Service(
        api_version="v1",
        kind="Service",
        metadata=client.V1ObjectMeta(name=service_name),
        spec=client.V1ServiceSpec(
            selector={"app": deployment_name},
            ports=[
                client.V1ServicePort(
                    protocol="TCP",
                    port=6060,
                    target_port=6060,
                    node_port=port,
                )
            ],
            type="NodePort",
        ),
    )

    apps_v1.create_namespaced_deployment(namespace=NAMESPACE, body=deployment)
    core_v1.create_namespaced_service(namespace=NAMESPACE, body=service)

    active_agents[agent_id] = {
        "deployment": deployment_name,
        "service": service_name,
        "port": port,
    }

    return jsonify({"message": "Agent created", "agent_id": agent_id, "port": port})


@app.route("/delete_agent/<agent_id>", methods=["DELETE"])
def delete_agent(agent_id):
    if agent_id not in active_agents:
        return jsonify({"error": "Agent not found"}), 404

    deployment_name = active_agents[agent_id]["deployment"]
    service_name = active_agents[agent_id]["service"]

    apps_v1.delete_namespaced_deployment(
        name=deployment_name,
        namespace=NAMESPACE,
        body=client.V1DeleteOptions(),
    )
    core_v1.delete_namespaced_service(name=service_name, namespace=NAMESPACE)

    del active_agents[agent_id]

    return jsonify({"message": "Agent deleted", "agent_id": agent_id})


@app.route("/query_agent/<agent_id>", methods=["POST"])
def query_agent(agent_id):
    if agent_id not in active_agents:
        return jsonify({"error": "Agent not found"}), 404

    query = request.json.get("query")
    if not query:
        return jsonify({"error": "Missing query"}), 400

    agent_port = active_agents[agent_id]["port"]
    agent_url = f"http://localhost:{agent_port}/query"

    try:
        response = requests.post(agent_url, json={"query": query})
        return response.json()
    except requests.exceptions.RequestException as e:
        return (
            jsonify({"error": "Failed to connect to agent", "details": str(e)}),
            500,
        )


@app.route("/list_agents", methods=["GET"])
def list_agents():
    return jsonify(active_agents)


@app.route("/agent_logs/<agent_id>", methods=["GET"])
def get_agent_logs(agent_id):
    if agent_id not in active_agents:
        return jsonify({"error": "Agent not found"}), 404

    deployment_name = active_agents[agent_id]["deployment"]

    try:
        pods = core_v1.list_namespaced_pod(
            namespace=NAMESPACE,
            label_selector=f"app={deployment_name}",
        )

        if not pods.items:
            return jsonify({"error": "No pods found for this agent"}), 404

        # We only have 1 replica, so we can just get the first pod
        pod_name = pods.items[0].metadata.name
        logs = core_v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=NAMESPACE,
            container=deployment_name,
        )

        return jsonify({"agent_id": agent_id, "pod_name": pod_name, "logs": logs})

    except Exception as e:
        return jsonify({"error": "Failed to fetch logs", "details": str(e)}), 500


def create_namespace(namespace: str):
    try:
        core_v1.create_namespace(
            body=client.V1Namespace(
                metadata=client.V1ObjectMeta(name=namespace),
            )
        )
    except Exception:
        print(f"Namespace {namespace} already exists")


if __name__ == "__main__":
    create_namespace("nomes")
    app.run(host="0.0.0.0", port=8080)
