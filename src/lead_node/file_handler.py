import random
import threading
import math
import requests

from config import NO_FRAGMENTS, NODE_SELECTION_STRATEGY, NO_REPLICAS, NODES_TO_KILL
from node_selection import RandomSelection, MinCopySetsSelection, BuddySelection
from node_selection import RANDOM_SELECTION, MIN_COPY_SETS_SELECTION, BUDDY_SELECTION

from kubernetes import client, config


# Configure access to the Kubernetes cluster
config.load_incluster_config()  # Use this if running inside the cluster
# config.load_kube_config()  # Use this for local testing with kubeconfig

# Create an API client for CoreV1
v1 = client.CoreV1Api()

# Global State (in-memory for demo) should be stored persistently in a real system
file_metadata = {}


class FileHandler:
    """Handles file storage and retrieval"""

    def __init__(self):
        self.node_selector = None
        self.storage_nodes = []
        self.__setup_node_strategy()
        self.__node_monitor_thread = threading.Thread(
            target=self.__monitor_storage_nodes, daemon=True, kwargs={"period": 1}
        )
        self.__ticker = threading.Event()
        self.__nodes_been_killed = False
        self.__node_monitor_thread.start()

    def store_file(self, file_bytes):
        """ "Store a file and return its file_id"""

        # Generate a unique file_id not in file_metadata
        file_id = "file_" + str(random.randint(1000, 9999))
        while file_id in file_metadata:
            file_id = "file_" + str(random.randint(1000, 9999))

        # Split into fragments
        base_fragment_size = math.floor(len(file_bytes) / NO_FRAGMENTS)
        remainder = len(file_bytes) % NO_FRAGMENTS
        fragments = []
        start = 0
        for i in range(NO_FRAGMENTS):
            end = start + base_fragment_size + (1 if i < remainder else 0)
            fragments.append(file_bytes[start:end])
            start = end

        print(f"Storing file_id={file_id}, total size={len(file_bytes)} bytes")
        print("Fragments sizes:", [len(f) for f in fragments])

        # Choose nodes for each fragment
        assigned_nodes = self.node_selector.choose_nodes()
        print(f"Assigned nodes for {file_id}:", assigned_nodes)

        # Upload fragments to nodes
        threads = []
        for replica_idx in range(NO_REPLICAS):
            for frag_idx, fragment in enumerate(fragments):
                node = assigned_nodes[replica_idx][frag_idx]
                print(
                    f"Uploading replica {replica_idx} of fragment {frag_idx} to node {node}, fragment length={len(fragment)}"
                )
                t = threading.Thread(
                    target=self.__upload_fragment_to_node,
                    args=(node, file_id, frag_idx, fragment),
                )
                t.start()
                threads.append(t)
        for t in threads:
            t.join()

        file_metadata[file_id] = assigned_nodes
        return file_id

    def retrieve_file(self, file_id):
        """Retrieve a file given its file_id"""
        assigned_nodes = file_metadata.get(file_id)
        if not assigned_nodes:
            print(f"No metadata found for file_id={file_id}")
            return b""

        print(f"Retrieving file_id={file_id}, assigned_nodes:", assigned_nodes)
        fragments = [None for _ in range(NO_FRAGMENTS)]
        for frag_idx in range(NO_FRAGMENTS):
            fragment_found = False
            for nodes_list in assigned_nodes:  # Check each replica for the fragment
                node = nodes_list[frag_idx]
                # TODO: Check that node is in storage_nodes
                frag = self.__download_fragment_from_node(node, file_id, frag_idx)
                if frag:
                    print(
                        f"Retrieved fragment {frag_idx} from {node}, length={len(frag)}"
                    )
                    fragments[frag_idx] = frag
                    fragment_found = True
                    break

            if not fragment_found:
                print(f"Fragment {frag_idx} not found for file_id={file_id}")
                return b""  # Return empty bytes if any fragment is missing

        # Check final file size after reassembly
        reassembled = b"".join(fragments)
        print(f"Reassembled file_id={file_id} with total length={len(reassembled)}")
        return reassembled

    def __setup_node_strategy(self):
        if NODE_SELECTION_STRATEGY == RANDOM_SELECTION:
            self.node_selector = RandomSelection(
                len(self.storage_nodes), NO_FRAGMENTS, NO_REPLICAS
            )
        elif NODE_SELECTION_STRATEGY == MIN_COPY_SETS_SELECTION:
            self.node_selector = MinCopySetsSelection(
                len(self.storage_nodes), NO_FRAGMENTS, NO_REPLICAS
            )
        elif NODE_SELECTION_STRATEGY == BUDDY_SELECTION:
            self.node_selector = BuddySelection(
                len(self.storage_nodes), NO_FRAGMENTS, NO_REPLICAS
            )
        else:
            raise NotImplementedError(
                f"Invalid node selection strategy: {NODE_SELECTION_STRATEGY}"
            )

    def __upload_fragment_to_node(self, node, file_id, frag_idx, fragment):
        try:
            node_ip = self.storage_nodes[node - 1]["ip"]
            url = f"http://{node_ip}:5000/upload_fragment?file_id={file_id}&frag_idx={frag_idx}"
            r = requests.post(url, data=fragment)
            if r.status_code != 200:
                print(
                    f"Failed to upload fragment {frag_idx} of {file_id} to {node}, status code={r.status_code}"
                )
            else:
                print(
                    f"Successfully uploaded fragment {frag_idx} of {file_id} to {node}"
                )
        except Exception as e:
            print(f"Upload error for fragment {frag_idx} of {file_id} to {node}: {e}")

    def __download_fragment_from_node(self, node, file_id, frag_idx):
        node_ip = self.storage_nodes[node - 1]["ip"]
        url = (
            f"http://{node_ip}:5000/get_fragment?file_id={file_id}&frag_idx={frag_idx}"
        )
        try:
            r = requests.get(url)
            if r.status_code == 200:
                print(
                    f"Downloaded fragment {frag_idx} of {file_id} from {node}, size={len(r.content)}"
                )
                return r.content
            else:
                print(
                    f"Fragment {frag_idx} of {file_id} not found on {node}, status code={r.status_code}"
                )
        except Exception as e:
            print(
                f"Download error for fragment {frag_idx} of {file_id} from {node}: {e}"
            )
        return None

    def __get_storage_node_pods(self, namespace="default"):
        """Get the names and IPs of storage-node pods."""
        pod_list = v1.list_namespaced_pod(namespace, label_selector="app=storage-node")
        pods = []
        for pod in pod_list.items:
            while pod.status.phase != "Running":
                print(f"Waiting for pod {pod.metadata.name} to be Running")
                pod = v1.read_namespaced_pod(pod.metadata.name, namespace)
            if pod.status.phase == "Running":
                pods.append({"name": pod.metadata.name, "ip": pod.status.pod_ip})
        if len(pods) != len(self.storage_nodes):
            print("Storage nodes updated:", pods)
            self.storage_nodes = pods
            self.__setup_node_strategy()

    def __kill_storage_nodes(self, s, namespace="default"):
        """kill s random storage node pods"""
        if s >= len(self.storage_nodes):
            print("Cannot kill all or more than number of storage nodes")
            return
        for _ in range(s):
            pod = random.choice(self.storage_nodes)
            v1.delete_namespaced_pod(pod["name"], namespace)
            print(f"Killed storage node pod {pod['name']}")
        self.__nodes_been_killed = True

    def __monitor_storage_nodes(self, period):
        while not self.__ticker.wait(period):
            self.__get_storage_node_pods()
            if not self.__nodes_been_killed:
                self.__kill_storage_nodes(NODES_TO_KILL)
