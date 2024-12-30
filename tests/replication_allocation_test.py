import requests
import matplotlib.pyplot as plt
import tqdm
import json

from shared_utils import generate_file, download_file, store_file, URL
import os

RANDOM_SELECTION = "random"
MIN_COPY_SETS_SELECTION = "min_copy_sets"
BUDDY_SELECTION = "buddy"

# Example configuration parameters
NO_NODES = 3  # 3, 6, 12, 24
NO_REPLICAS = 3
FILE_SIZES = [1e5, 1e6, 1e7, 1e8]  # 100 KB, 1 MB, 10 MB, (100 MB)
NO_FILES = 100
NODE_SELECTION_STRATEGIES = [BUDDY_SELECTION, MIN_COPY_SETS_SELECTION, RANDOM_SELECTION]


def run_tests_for_file_size(file_size):
    """Run tests for the given file size and return store and download times"""
    store_times = []
    download_times = []

    file_bytes = generate_file(file_size)
    for _ in tqdm.tqdm(range(NO_FILES), desc="Processing files"):
        # Store file and measure time
        store_time, file_id = store_file(file_bytes)
        store_times.append(store_time)

        # Download file and measure time
        download_time = download_file(file_id)
        download_times.append(download_time)

    return store_times, download_times


def generate_histogram_and_summary(times, label, title, fig_number):
    """Generate histogram and summary statistics for the given times"""
    plt.figure(fig_number)
    plt.hist(times, bins=20, alpha=0.7, label=label)
    plt.xlabel("Time (s)")
    plt.ylabel("Frequency")
    plt.title(f"Histogram of {title}")
    plt.legend(loc="upper right")

    avg_time = sum(times) / len(times)
    median_time = sorted(times)[len(times) // 2]

    plt.axvline(
        avg_time, color="r", linestyle="dashed", linewidth=2, label=f"Average {label}"
    )
    plt.axvline(
        median_time, color="g", linestyle="dashed", linewidth=2, label=f"Median {label}"
    )

    return avg_time, median_time


def change_replication_strategy(node_selection_strategy):
    """Change the replication strategy to the given strategy"""
    res = requests.post(
        f"{URL}/change_replication_strategy", data=node_selection_strategy
    )
    print(f"Response: {res.text}")


def perform_tests():
    """Perform tests for different file sizes and return results"""
    results = {}

    for node_selection_strategy in tqdm.tqdm(
        NODE_SELECTION_STRATEGIES, desc="Testing different node selection strategies"
    ):
        print(f"\n\nTesting for node selection strategy: {node_selection_strategy}")
        change_replication_strategy(node_selection_strategy)

        for file_size in tqdm.tqdm(FILE_SIZES, desc=f"Testing different file sizes"):
            print(f"\n\nTesting for file size: {file_size / 1000} KB")
            store_times, download_times = run_tests_for_file_size(file_size)

            results[(node_selection_strategy, file_size)] = {
                "store_times": store_times,
                "download_times": download_times,
            }

    return results


if __name__ == "__main__":
    results = perform_tests()
    os.makedirs("tests/out", exist_ok=True)
    # Convert tuple keys to strings
    results_str_keys = {str(k): v for k, v in results.items()}
    with open(
        f"tests/out/{NO_NODES}_nodes_replication_allocation_test_results.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(results_str_keys, f)
