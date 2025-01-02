import time
import tqdm
import requests
import json

from shared_utils import send_store_request, generate_file

RANDOM_SELECTION = "random"
MIN_COPY_SETS_SELECTION = "min_copy_sets"
BUDDY_SELECTION = "buddy"

# N is determined by the deployment and is changed manually (12, 24, 36)
N = 36  # currently testing
K = 3  # default value
STRATEGIES = [MIN_COPY_SETS_SELECTION, RANDOM_SELECTION, BUDDY_SELECTION]
S = [2, 3, 4, 6, 8, 10]


def store_n_files(n, file_size):
    """Store n files with the given size"""

    file_ids = []
    file_bytes = generate_file(file_size)
    for _ in tqdm.tqdm(range(n), desc="Storing files", leave=False):
        # Store file and measure time
        file_id = send_store_request(file_bytes)
        file_ids.append(file_id)

    return file_ids


def run_tests():
    results = {}
    for strategy in tqdm.tqdm(STRATEGIES, desc="Processing strategies", leave=True):
        for s in tqdm.tqdm(S, desc="Processing S values", leave=False):
            try:
                
                requests.post("http://localhost:4000/reset_metadata", timeout=10)
                # Change strategy
                
                response = requests.get("http://localhost:4000/quantify_file_loss", timeout=10)
                response = response.json()
                while (response['node_count'] != N):
                    time.sleep(0.1)
                    response = requests.get("http://localhost:4000/quantify_file_loss", timeout=10)
                    response = response.json()
                requests.post(
                    "http://localhost:4000/change_replication_strategy", data=strategy, timeout=10
                )
                # Store n files
                _ = store_n_files(100, 10)  # 100 files of 10 bytes
                # Kill s nodes
                requests.post("http://localhost:4000/delete_pods", data=str(s), timeout=10)
                # Quantify file loss
                time.sleep(2)
                response = requests.get("http://localhost:4000/quantify_file_loss", timeout=10)
                response = response.json()
                if (strategy, N) not in results:
                    results[(strategy, N)] = []
                results[(strategy, N)].append({s: response['files_lost']})

            except requests.exceptions.RequestException as e:
                print(f"error: {str(e)}")
            
    return results


if __name__ == "__main__":
    results = run_tests()
    print(results)
    with open(f"tests/out/results_nodes_{N}.json", "w", encoding="utf-8") as f:
        json.dump({str(k): v for k, v in results.items()}, f)