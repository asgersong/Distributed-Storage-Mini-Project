"""
Aarhus University - Distributed Storage course - Lab 4

REST Server, starter template for Week 4
"""
import time
import zmq
import math
import random
import messages_pb2
import io
from flask import Flask, make_response, request, send_file

from utilities.database import get_db, close_db
from utilities.random_string import random_string
from utilities.write_file import write_file

# Constants
N = 4 # Number of storage nodes
k = 2 # Number of chunks per file

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

"""
REST API
"""

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
    # Convert files from sqlite3.Row object (which is not JSON-encodable) to
    # a standard Python dictionary simply by casting
    files = [dict(file) for file in files]

    return make_response({"files": files})


#


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

    # select one chunk of each half
    part1_filenames = f["part1_filenames"].split(',')
    part2_filenames = f["part2_filenames"].split(',')
    part1_filename = part1_filenames[random.randint(0, len(part1_filenames) - 1)]
    part2_filename = part2_filenames[random.randint(0, len(part2_filenames) - 1)]

    # request both chunks in parallel
    task1 = messages_pb2.getdata_request()
    task1.filename = part1_filename
    data_req_socket.send(
        task1.SerializeToString()
    )
    task2 = messages_pb2.getdata_request()
    task2.filename = part2_filename
    data_req_socket.send(
        task2.SerializeToString()
    )

    # receive both chunks and insert hem
    file_data_parts = [None, None]
    for _ in range(2):
        result = response_socket.recv_multipart()
        # first frame: file name (string)
        filename_received = result[0].decode('utf-8')
        # second frame: file data (bytes)
        chunk_data = result[1]

        print(f'Received {filename_received}')

        if filename_received == part1_filename:
            file_data_parts[0] = chunk_data

        if filename_received == part2_filename:
            file_data_parts[1] = chunk_data

    print("Received both parts")

    # combine the parts and serve the file
    file_data = file_data_parts[0] + file_data_parts[1]
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


#


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


#



@app.route("/files", methods=["POST"])
def add_files():
    payload = request.get_json()
    filename = payload.get("filename")
    content_type = payload.get("content_type")
    from base64 import b64decode

    file_data = b64decode(payload.get("contents_b64"))
    size = len(file_data)

    num_fragments = 4

    # Split the file into four chunks
    file_data_chunks = [file_data[i:i + math.ceil(size / num_fragments)] for i in range(0, size, math.ceil(size / num_fragments))]

    # generate k names for each chunk
    file_chunk_names = [[random_string(8) for _ in range(k)] for _ in range(len(file_data_chunks))]



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
        "INSERT INTO `file`(`filename`, `size`, `content_type`, `chunk_names`) VALUES (?,?,?,?,?)",
        (filename, size, content_type, ','.join(file_data_1_names), ','.join(file_data_2_names))
    )
    db.commit()


    
    # Return the ID of the new file record with HTTP 201 (Created) status code


    # generate two random chunk names for each half
    file_data_1_names = [random_string(8), random_string(8)]
    file_data_2_names = [random_string(8), random_string(8)]
    print("File data 1 names: %s" % file_data_1_names)
    print("File data 2 names: %s" % file_data_2_names)

    # send 2 'store data' protobuf messages with the first half of the file
    for name in file_data_1_names:
        task = messages_pb2.storedata_request()
        task.filename = name
        send_task_scoket.send_multipart([
            task.SerializeToString(),
            file_data_1
        ])

    # send 2 'store data' protobuf messages with the second half of the file
    for name in file_data_2_names:
        task = messages_pb2.storedata_request()
        task.filename = name
        send_task_scoket.send_multipart([
            task.SerializeToString(),
            file_data_2
        ])




    # Insert the File record in the DB
    db = get_db()
    cursor = db.execute(
        "INSERT INTO `file`(`filename`, `size`, `content_type`, `part1_filenames`, `part2_filenames`) VALUES (?,?,?,?,?)",
        (filename, size, content_type, ','.join(file_data_1_names), ','.join(file_data_2_names))
    )
    db.commit()

    # Return the ID of the new file record with HTTP 201 (Created) status code
    return make_response({"id": cursor.lastrowid}, 201)


#


@app.errorhandler(500)
def server_error(e):
    from logging import exception

    exception("Internal error: %s", e)

    return make_response({"error": str(e)}, 500)


# Start the Flask app (must be after the endpoint functions)
host_local_computer = "localhost"  # Listen for connections on the local computer
host_local_network = "0.0.0.0"  # Listen for connections on the local network
app.run(host=host_local_computer, port=9000)
