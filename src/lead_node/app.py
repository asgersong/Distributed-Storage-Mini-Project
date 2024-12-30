from flask import Flask, request, jsonify
from file_handler import FileHandler

app = Flask(__name__)
file_handler = FileHandler()


# Web Page
@app.route("/")
def index():
    return "Welcome to the Distributed Storage System!"


@app.route("/store", methods=["POST"])
def store_endpoint():
    file_bytes = request.get_data()
    print("Received file length from get_data():", len(file_bytes))

    file_id = file_handler.store_file(file_bytes)
    return jsonify({"file_id": file_id})


@app.route("/retrieve", methods=["GET"])
def retrieve_endpoint():
    file_id = request.args.get("file_id")
    file_data = file_handler.retrieve_file(file_id)
    return file_data


@app.route("/delete_pods", methods=["POST"])
def delete_pods_endpoint():
    s = int(request.get_data())
    reply = file_handler.kill_storage_nodes(s)
    return jsonify({"message": f"Killed {s} storage nodes",
                    "killed_nodes": reply})

@app.route("/quantify_file_loss", methods=["GET"])
def quantify_file_loss_endpoint():
    reply = file_handler.quantify_file_loss()
    return jsonify(reply)

@app.route("/change_replication_strategy", methods=["POST"])
def change_replication_strategy_endpoint():
    strategy = request.get_data().decode("utf-8")
    reply = file_handler.change_replication_strategy(strategy)
    return jsonify(reply)

@app.route("/set_replicas", methods=["POST"])
def set_replicas_endpoint():
    replicas = int(request.get_data())
    reply = file_handler.set_replicas(replicas)
    return jsonify(reply)

@app.route("/set_fragments", methods=["POST"])
def set_fragments_endpoint():
    fragments = int(request.get_data())
    reply = file_handler.set_fragments(fragments)
    return jsonify(reply)

@app.route("/reset_metadata", methods=["POST"])
def reset_metadata_endpoint():
    reply = file_handler.reset_metadata()
    return jsonify(reply)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000)
