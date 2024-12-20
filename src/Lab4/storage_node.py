import sys
import os
import zmq
import messages_pb2


from utilities.file_utils import write_file

data_folder = sys.argv[1] if len(sys.argv) > 1 else "./"
if data_folder != "./":
    try:
        os.makedirs('./'+data_folder)
    except FileExistsError as _:
        pass

print(f"Data folder: {data_folder}")

context = zmq.Context()

# socket to receive store chunk messages from the controller
pull_address = "tcp://localhost:5557"
receiver = context.socket(zmq.PULL)
receiver.connect(pull_address)
print(f'Listeting on: {pull_address}')

# socket to send results to the controller
sender = context.socket(zmq.PUSH)
sender.connect("tcp://localhost:5558")

# socket to receive get chunk messages from the controller
subscriber = context.socket(zmq.SUB)
subscriber.connect("tcp://localhost:5559")

# receive every message (empty subscription)
subscriber.setsockopt_string(zmq.SUBSCRIBE, '')

# use a Poller to monitor two sockets at the same time
poller = zmq.Poller()
poller.register(receiver, zmq.POLLIN)
poller.register(subscriber, zmq.POLLIN)

while True:
    try:
        # poll all sockets
        socks = dict(poller.poll())
    except KeyboardInterrupt:
        break

    # at this point one or more sockets have data
    if receiver in socks:
        msg = receiver.recv_multipart()
        task = messages_pb2.storedata_request()
        task.ParseFromString(msg[0])
        data = msg[1]
        print(f'Chunk to save: {task.filename}, size: {len(data)} bytes')
        chunk_local_path = data_folder + '/' + task.filename
        write_file(data, chunk_local_path)
        print(f'Chunk saved at: {chunk_local_path}')
        sender.send_string(task.filename)

    if subscriber in socks:
        msg = subscriber.recv()
        task = messages_pb2.getdata_request()
        task.ParseFromString(msg)
        filename = task.filename
        print(f'Chunk requested: {filename}')
        # try to load the file
        try:
            with open(data_folder+'/'+filename, 'rb') as f:
                print(f'Chunk found: {filename}, sending it back')
                sender.send_multipart([
                    bytes(filename, 'utf-8'),
                    f.read()
                ])
        except FileNotFoundError:
            pass
