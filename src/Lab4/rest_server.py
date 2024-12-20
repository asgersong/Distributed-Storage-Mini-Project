"""
Aarhus University - Distributed Storage course - Lab 4

REST Server, starter template for Week 4
"""
import math
import random
import time
from base64 import b64decode
from logging import exception
import zmq
import io
import messages_pb2

from flask import Flask, make_response, request, send_file

from utilities.database import get_db, close_db
from utilities.random_string import random_string
# from utilities.write_file import write_file

# Constants
N = 4 # Number of storage nodes
NO_CHUNKS = 4
K = 4 # Number of copies of each chunk


#initiate ZMQ sockets
context = zmq.Context()

# socket to send tasks to storage nodes
send_task_socket = context.socket(zmq.PUSH)
send_task_socket.bind("tcp://*:5557")

# socket to receive messages from storage nodes
response_socket = context.socket(zmq.PULL)
response_socket.bind("tcp://*:5558")

# publisher socket for data request broadcasts
data_req_socket = context.socket(zmq.PUB)
data_req_socket.bind("tcp://*:5559")

# wait for all workers to start and connect
time.sleep(1)
print("Listening to ZMQ messages on tcp://*:5558")

""" REST API endpoints"""

# Instantiate the Flask app (must be before the endpoint functions)
app = Flask(__name__)
# Close the DB connection after serving the request
app.teardown_appcontext(close_db)


@app.route("/")
def hello():
    return make_response({"message": "Hello World!"})

@app.route("/files", methods=["GET"])
def list_files():
    db = get_db()
    cursor = db.execute("SELECT * FROM `file`")
    if not cursor:
        return make_response({"message": "Error connecting to the database"}, 500)

    files = cursor.fetchall()
    files = [dict(file) for file in files]

    return make_response({"files": files})

@app.route("/files/<int:file_id>", methods=["GET"])
def download_file(file_id):

    db = get_db()
    cursor = db.execute("SELECT * FROM `file` WHERE `id`=?", [file_id])
    if not cursor:
        return make_response({"message": "Error connecting to the database"}, 500)

    f = cursor.fetchone()
    # Convert to a Python dictionary
    f = dict(f)

    print("File requested: {}".format(f))

    all_chunk_names = f["chunk_names"].split(';')
    random_chunk_names = [random.choice(chunk_names.split(',')) for chunk_names in all_chunk_names] 

    # request the chunks from the storage nodes 
    for chunk_name in random_chunk_names:
        task = messages_pb2.getdata_request()
        task.filename = chunk_name
        data_req_socket.send(
            task.SerializeToString()
        )

    # receive the chunks from the storage nodes
    file_data_parts = [None for _ in range(NO_CHUNKS)] 

    for _ in range(NO_CHUNKS):
        result = response_socket.recv_multipart()
        # first frame: file name (string)
        filename_received = result[0].decode('utf-8')
        # second frame: file data (bytes)
        chunk_data = result[1]

        print(f'Received {filename_received}')

        if filename_received in random_chunk_names:
            file_data_parts[random_chunk_names.index(filename_received)] = chunk_data

    print("Received all parts")

    # reconstruct the file and serve it
    file_data = b''.join(file_data_parts)
    return send_file(io.BytesIO(file_data), mimetype=f['content_type'])
    
    
# HTTP HEAD requests are served by the GET endpoint of the same URL,
# so we'll introduce a new endpoint URL for requesting file metadata.
@app.route("/files/<int:file_id>/info", methods=["GET"])
def get_file_metadata(file_id):

    db = get_db()
    cursor = db.execute("SELECT * FROM `file` WHERE `id`=?", [file_id])
    if not cursor:
        return make_response({"message": "Error connecting to the database"}, 500)

    f = cursor.fetchone()
    if not f:
        return make_response({"message": "File {} not found".format(file_id)}, 404)

    # Convert to a Python dictionary
    f = dict(f)
    print("File: %s" % f)

    return make_response(f)

@app.route("/files/<int:file_id>", methods=["DELETE"])
def delete_file(file_id):

    db = get_db()
    cursor = db.execute("SELECT * FROM `file` WHERE `id`=?", [file_id])
    if not cursor:
        return make_response({"message": "Error connecting to the database"}, 500)

    f = cursor.fetchone()
    if not f:
        return make_response({"message": "File {} not found".format(file_id)}, 404)

    # Convert to a Python dictionary
    f = dict(f)
    print("File to delete: %s" % f)

    # Delete the file contents with os.remove()
    from os import remove

    remove(f["blob_name"])

    # Delete the file record from the DB
    db.execute("DELETE FROM `file` WHERE `id`=?", [file_id])
    db.commit()

    # Return empty 200 Ok response
    return make_response("")

@app.route("/files", methods=["POST"])
def add_files():
    payload = request.get_json()
    filename = payload.get("filename")
    content_type = payload.get("content_type")

    file_data = b64decode(payload.get("contents_b64"))
    size = len(file_data)

    # Split the file into four chunks
    file_data_chunks = [file_data[i:i + math.ceil(size / NO_CHUNKS)] for i in range(0, size, math.ceil(size / NO_CHUNKS))]

    # generate k names for each chunk
    file_chunk_names = [[random_string(8) for _ in range(K)] for _ in range(len(file_data_chunks))]


    # TODO: task 1.2: choosing who to send to in different ways (random, minCopySets, Buddy)
    # send k 'store data' protobuf messages with each chunk
    for i, chunk_names in enumerate(file_chunk_names):
        for name in chunk_names:
            task = messages_pb2.storedata_request()
            task.filename = name
            send_task_socket.send_multipart([
                task.SerializeToString(),
                file_data_chunks[i]
            ])
            
    # wait for N responses from storage nodes
    for task_no in range(N):
        resp = response_socket.recv_string()
        print(f'Response {task_no}: {resp}')

    # Insert the File record in the DB
    db = get_db()
    cursor = db.execute(
        "INSERT INTO `file`(`filename`, `size`, `content_type`, `chunk_names`) VALUES (?,?,?,?)",
        (filename, size, content_type, ';'.join([','.join(chunk_names) for chunk_names in file_chunk_names]))
    )
    db.commit()

    # Return the ID of the new file record with HTTP 201 (Created) status code
    return make_response({"id": cursor.lastrowid}, 201)


@app.errorhandler(500)
def server_error(e):
    exception("Internal error: %s", e)
    return make_response({"error": str(e)}, 500)

if __name__ == "__main__":
    app.run(host="localhost", port=9000)
