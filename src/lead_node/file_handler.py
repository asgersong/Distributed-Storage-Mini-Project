import random
import threading
import math
import time
import json

from config import NO_FRAGMENTS, NODE_SELECTION_STRATEGY, NO_REPLICAS
from node_selection import RandomSelection, MinCopySetsSelection, BuddySelection
from node_selection import RANDOM_SELECTION, MIN_COPY_SETS_SELECTION, BUDDY_SELECTION

from storage_node_client import upload_fragment_to_node, download_fragment_from_node

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
        # self.__setup_node_strategy()
        self.__node_monitor_thread = threading.Thread(
            target=self.__monitor_storage_nodes, daemon=True, kwargs={"period": 5}
        )
        self.__ticker = threading.Event()
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
        self.__upload_fragments(file_id, fragments, assigned_nodes)

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
                frag = download_fragment_from_node(node, node["ip"], file_id, frag_idx)
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

    def change_replication_strategy(self, strategy):
        global NODE_SELECTION_STRATEGY
        NODE_SELECTION_STRATEGY = strategy
        try:
            self.__setup_node_strategy()
            print(f"Changed replication strategy to {strategy}")
            return {"message": f"Changed replication strategy to {strategy}"}
        except Exception as e:
            print(f"Failed to change replication strategy to {strategy}: {e}")
            return {
                "message": f"Failed to change replication strategy to {strategy}: {e}, use valid strategy: random, min_copy_sets, buddy"
            }

    def __upload_fragments(self, file_id, fragments, assigned_nodes):
        threads = [] # Threads makes sense since we dont have to wait for one fragment to be uploaded to start the next one
        for replica_idx in range(NO_REPLICAS):
            for frag_idx, fragment in enumerate(fragments):
                node = assigned_nodes[replica_idx][frag_idx]
                print(
                    f"Uploading replica {replica_idx} of fragment {frag_idx} to node {node}, fragment length={len(fragment)}"
                )
                t = threading.Thread(
                    target=upload_fragment_to_node,
                    args=(node, node["ip"], file_id, frag_idx, fragment),
                )
                t.start()
                threads.append(t)
        for t in threads:
            t.join()

    def __setup_node_strategy(self):
        if NODE_SELECTION_STRATEGY == RANDOM_SELECTION:
            self.node_selector = RandomSelection(
                self.storage_nodes, NO_FRAGMENTS, NO_REPLICAS
            )
        elif NODE_SELECTION_STRATEGY == MIN_COPY_SETS_SELECTION:
            self.node_selector = MinCopySetsSelection(
                self.storage_nodes, NO_FRAGMENTS, NO_REPLICAS
            )
        elif NODE_SELECTION_STRATEGY == BUDDY_SELECTION:
            self.node_selector = BuddySelection(
                self.storage_nodes, NO_FRAGMENTS, NO_REPLICAS
            )
        else:
            raise NotImplementedError(
                f"Invalid node selection strategy: {NODE_SELECTION_STRATEGY}"
            )

    def __get_storage_node_pods(
        self, namespace="default", timeout=5, poll_interval=0.5
    ):
        """Get the names and IPs of storage-node pods."""
        pod_list = v1.list_namespaced_pod(namespace, label_selector="app=storage-node")
        pods = []
        start_time = time.time()
        for pod in pod_list.items:
            while pod.status.phase != "Running":
                elapsed_time = time.time() - start_time
                if elapsed_time > timeout:
                    print(f"Timeout waiting for pod {pod.metadata.name} to be Running")
                    break
                print(f"Waiting for pod {pod.metadata.name} to be Running")
                try:
                    pod = v1.read_namespaced_pod(pod.metadata.name, namespace)
                except Exception as e:
                    print(f"Error getting pod {pod.metadata.name}: {e}")
                    break
            if pod.status.phase == "Running" and not pod.metadata.deletion_timestamp:
                pods.append({"name": pod.metadata.name, "ip": pod.status.pod_ip})
        if pods != self.storage_nodes:
            print("Storage nodes updated:", pods)
            self.storage_nodes = pods
            self.__setup_node_strategy()

    def kill_storage_nodes(self, s, namespace="default"):
        """kill s random storage node pods"""
        if s >= len(self.storage_nodes):
            error_str = "Cannot kill all or more than number of storage nodes"
            print(error_str)
            return
        pods_to_delete = random.sample(self.storage_nodes, k=s)
        killed_nodes = []
        for pod in pods_to_delete:
            v1.delete_namespaced_pod(pod["name"], namespace)
            print(f"Killed storage node pod {pod['name']}")
            killed_nodes.append(pod)
        return killed_nodes
    
    def set_replicas(self, replicas):
        global NO_REPLICAS
        NO_REPLICAS = replicas
        try:
            self.__setup_node_strategy()
            print(f"Changed number of replicas to {replicas}")
            return {"message": f"Changed number of replicas to {replicas}"}
        except Exception as e:
            print(f"Failed to change number of replicas to {replicas}: {e}")
            return {
                "message": f"Failed to change number of replicas to {replicas}: {e}"
            }
            
    def set_fragments(self, fragments):
        global NO_FRAGMENTS
        NO_FRAGMENTS = fragments
        try:
            self.__setup_node_strategy()
            print(f"Changed number of fragments to {fragments}")
            return {"message": f"Changed number of fragments to {fragments}"}
        except Exception as e:
            print(f"Failed to change number of fragments to {fragments}: {e}")
            return {
                "message": f"Failed to change number of fragments to {fragments}: {e}"
            }

    def quantify_file_loss(self):
        self.__get_storage_node_pods()
        files_lost = 0

        # Iterate over all files and their replica metadata
        for file_id, replicas in file_metadata.items():
            print(f"Checking file_id={file_id} with replicas: {replicas}")

            # Track the fragments successfully found across all replicas
            fragments_found = set()

            for replica in replicas:
                for frag_idx, fragment_node in enumerate(replica):
                    # Check if the fragment node exists in the current storage nodes
                    if any(
                        node["name"] == fragment_node["name"]
                        for node in self.storage_nodes
                    ):
                        fragments_found.add(frag_idx)

            # If the number of found fragments is less than expected, the file is lost
            if len(fragments_found) < NO_FRAGMENTS:
                print(
                    f"File {file_id} is lost (found {len(fragments_found)} of {NO_FRAGMENTS} fragments)"
                )
                files_lost += 1
            else:
                print(f"File {file_id} is intact (found all {NO_FRAGMENTS} fragments)")

        total_files = len(file_metadata)
        print(f"Files lost: {files_lost}/{total_files}")
        return {"files_lost": files_lost, "total_files": total_files, "node_count": len(self.storage_nodes)}
    
    def reset_metadata(self):
        global file_metadata
        file_metadata = {}
        return {"message": "Metadata reset successfully"}

    def __monitor_storage_nodes(self, period):
        while not self.__ticker.wait(period):
            self.__get_storage_node_pods()
