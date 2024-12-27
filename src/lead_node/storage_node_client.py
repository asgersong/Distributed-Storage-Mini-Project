import requests

def upload_fragment_to_node(node, node_ip, file_id, frag_idx, fragment):
    """Upload a fragment to a storage node"""
    try:
        # node_ip = self.storage_nodes[node - 1]["ip"]
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

def download_fragment_from_node(node, node_ip, file_id, frag_idx):
    """Download a fragment from a storage node"""
    # node_ip = self.storage_nodes[node - 1]["ip"]
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
