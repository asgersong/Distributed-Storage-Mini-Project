from flask import Flask, request, jsonify
import requests
import random
import os
import threading

app = Flask(__name__)

# Global State (in-memory for demo)
file_metadata = {}
# For demonstration, we assume a fixed set of storage nodes. 
# In docker-compose we can scale storage nodes as services like storage_node1, storage_node2, ...
# We'll read from an environment variable or a pre-known list.
STORAGE_NODES = os.environ.get("STORAGE_NODES", "storage_node1:5000,storage_node2:5000,storage_node3:5000,storage_node4:5000").split(",")

# Web Page
@app.route('/')
def index():
    return "Welcome to the Distributed Storage System!"

@app.route('/store', methods=['POST'])
def store_endpoint():
    file_bytes = request.get_data()
    print("Received file length from get_data():", len(file_bytes))
    k = int(request.args.get('k', 2))
    N = int(request.args.get('N', 4))
    strategy = request.args.get('strategy', 'random')
    
    file_id = store_file(file_bytes, k, N, strategy)
    return jsonify({"file_id": file_id})

@app.route('/retrieve', methods=['GET'])
def retrieve_endpoint():
    file_id = request.args.get('file_id')
    file_data = retrieve_file(file_id)
    return file_data

def store_file(file_bytes, k, N, strategy):
    file_id = "file_" + str(random.randint(1000,9999))
    
    # Split into 4 fragments
    fragment_size = len(file_bytes)//4
    fragments = [
        file_bytes[0:fragment_size],
        file_bytes[fragment_size:2*fragment_size],
        file_bytes[2*fragment_size:3*fragment_size],
        file_bytes[3*fragment_size:]
    ]

    print(f"Storing file_id={file_id}, total size={len(file_bytes)} bytes")
    print("Fragments sizes:", [len(f) for f in fragments])

    assigned_nodes = choose_nodes_for_replicas(k, N, strategy)
    print(f"Assigned nodes for {file_id}:", assigned_nodes)

    threads = []
    for replica_idx in range(k):
        for frag_idx, fragment in enumerate(fragments):
            node = assigned_nodes[replica_idx][frag_idx]
            print(f"Uploading fragment {frag_idx} of replica {replica_idx} to {node}, fragment length={len(fragment)}")
            t = threading.Thread(target=upload_fragment_to_node, args=(node, file_id, frag_idx, fragment))
            t.start()
            threads.append(t)
    for t in threads:
        t.join()
    
    file_metadata[file_id] = assigned_nodes
    return file_id

def retrieve_file(file_id):
    assigned_nodes = file_metadata.get(file_id)
    if not assigned_nodes:
        print(f"No metadata found for file_id={file_id}")
        return b''

    print(f"Retrieving file_id={file_id}, assigned_nodes:", assigned_nodes)
    fragments = [None]*4
    for frag_idx in range(4):
        fragment_found = False
        for nodes_list in assigned_nodes:
            for node in nodes_list:
                frag = download_fragment_from_node(node, file_id, frag_idx)
                if frag is not None:
                    print(f"Retrieved fragment {frag_idx} from {node}, length={len(frag)}")
                    fragments[frag_idx] = frag
                    fragment_found = True
                    break
            if fragment_found:
                break
        if not fragment_found:
            print(f"Fragment {frag_idx} not found for file_id={file_id}")
            return b''

    # Check final file size after reassembly
    reassembled = b''.join(fragments)
    print(f"Reassembled file_id={file_id} with total length={len(reassembled)}")
    return reassembled

def choose_nodes_for_replicas(k, N, strategy):
    # For simplicity, assume we have enough nodes in STORAGE_NODES
    # We'll just pick from them
    all_nodes = STORAGE_NODES
    
    if strategy == 'random':
        return choose_nodes_random(k, N, all_nodes)
    # Implement min_copysets or buddy as needed
    # For now, we just do random for demonstration
    return choose_nodes_random(k, N, all_nodes)

def choose_nodes_random(k, N, all_nodes):
    chosen = []
    for _ in range(k):
        # pick N distinct nodes for the set, then pick 4 distinct for fragments
        selected_nodes = random.sample(all_nodes, N)
        # Just pick the first 4 for fragments (a simplification)
        fragment_nodes = random.sample(selected_nodes, 4)
        chosen.append(fragment_nodes)
    return chosen

def upload_fragment_to_node(node, file_id, frag_idx, fragment):
    try:
        url = f"http://{node}/upload_fragment?file_id={file_id}&frag_idx={frag_idx}"
        r = requests.post(url, data=fragment)
        if r.status_code != 200:
            print(f"Failed to upload fragment {frag_idx} of {file_id} to {node}, status code={r.status_code}")
        else:
            print(f"Successfully uploaded fragment {frag_idx} of {file_id} to {node}")
    except Exception as e:
        print(f"Upload error for fragment {frag_idx} of {file_id} to {node}: {e}")

def download_fragment_from_node(node, file_id, frag_idx):
    url = f"http://{node}/get_fragment?file_id={file_id}&frag_idx={frag_idx}"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            print(f"Downloaded fragment {frag_idx} of {file_id} from {node}, size={len(r.content)}")
            return r.content
        else:
            print(f"Fragment {frag_idx} of {file_id} not found on {node}, status code={r.status_code}")
    except Exception as e:
        print(f"Download error for fragment {frag_idx} of {file_id} from {node}: {e}")
    return None

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000)