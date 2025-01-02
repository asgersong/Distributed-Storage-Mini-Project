import os
import sys
import json

import matplotlib.pyplot as plt
import tqdm

from shared_utils import generate_file, download_file, store_file, change_replication_strategy, reset_metadata

RANDOM_SELECTION = "random"
MIN_COPY_SETS_SELECTION = "min_copy_sets"
BUDDY_SELECTION = "buddy"

# configuration parameters
NO_NODES = 24  # 3, 6, 12, 24
NO_REPLICAS = 3 # default
FILE_SIZES = [1e5, 1e6, 1e7, 1e8]  # 100 KB, 1 MB, 10 MB, 100 MB
NO_FILES = 100
NODE_SELECTION_STRATEGIES = [MIN_COPY_SETS_SELECTION, BUDDY_SELECTION, RANDOM_SELECTION]

# get cli first argument
if len(sys.argv) > 1:
    selection_strategy = int(sys.argv[1])
    if selection_strategy == 0:
        NODE_SELECTION_STRATEGIES = [RANDOM_SELECTION]
    elif selection_strategy == 1:
        NODE_SELECTION_STRATEGIES = [MIN_COPY_SETS_SELECTION]
    elif selection_strategy == 2:
        NODE_SELECTION_STRATEGIES = [BUDDY_SELECTION]

print(f"Testing: {NODE_SELECTION_STRATEGIES}")


def run_tests_for_file_size(file_size):
    """Run tests for the given file size and return store and download times"""
    store_times = []
    download_times = []

    file_bytes = generate_file(file_size)
    # NO_FILES = 20 if file_size == 1e8 else 100
    for _ in tqdm.tqdm(range(NO_FILES), desc="Processing files", leave=False):
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


def perform_tests():
    """Perform tests for different file sizes and return results"""
    results = {}

    for node_selection_strategy in tqdm.tqdm(
        NODE_SELECTION_STRATEGIES, desc="Testing different node selection strategies"
    ):
        print(f"\n\nTesting for node selection strategy: {node_selection_strategy}")
        _ = change_replication_strategy(node_selection_strategy)

        for file_size in tqdm.tqdm(FILE_SIZES, desc="Testing different file sizes"):
            print(f"\n\nTesting for file size: {file_size / 1000} KB")
            store_times, download_times = run_tests_for_file_size(file_size)

            results[(node_selection_strategy, file_size)] = {
                "store_times": store_times,
                "download_times": download_times,
            }
        
            # Reset metadata
            r = reset_metadata()
            print(r.text)

    return results


if __name__ == "__main__":
    results = perform_tests()
    os.makedirs("tests/out", exist_ok=True)
    # Convert tuple keys to strings
    results_str_keys = {str(k): v for k, v in results.items()}
    with open(
        f"tests/out/{NO_NODES}_{NODE_SELECTION_STRATEGIES[0]}_nodes_replication_allocation_test_results.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(results_str_keys, f)
