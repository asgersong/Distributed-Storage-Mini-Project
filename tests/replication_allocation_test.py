import time
import requests
import numpy as np
import matplotlib.pyplot as plt
import tqdm

# Example configuration parameters
NO_NODES = [3, 6, 12, 24]
NO_REPLICAS = 3
FILE_SIZES = [1e5, 1e6, 1e7]  # 100 KB, 1 MB, 10 MB, (100 MB)
NO_FILES = 100
NODE_SELECTION_STRATEGY = "Buddy"

def send_store_request(file_bytes):
    """Send store request to the lead node"""
    response = requests.post("http://localhost:4000/store", data=file_bytes)
    return response.json()["file_id"]

# Mock storage and download functions
def store_file(file_bytes):
    """Store file and generate redundancy"""
    start_time = time.time()
    file_id = send_store_request(file_bytes)
    redundancy_time = time.time() - start_time
    return redundancy_time, file_id


def download_file(file_id):
    """Download file"""
    start_time = time.time()
    response = requests.get(f"http://localhost:4000/retrieve?file_id={file_id}")
    download_time = time.time() - start_time
    return download_time


def generate_file(size):
    """Generate a file with the given size in bytes"""
    return np.random.bytes(size)


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


def perform_tests():
    """Perform tests for different file sizes and return results"""
    results = {}

    for file_size in tqdm.tqdm(FILE_SIZES, desc=f"Testing different file sizes"):
        print(f"\n\nTesting for file size: {file_size / 1000} KB")
        store_times, download_times = run_tests_for_file_size(file_size)

        avg_store_time, median_store_time = generate_histogram_and_summary(
            store_times,
            f"[{int(file_size/1000)}KB]",
            title="Store Operation",
            fig_number=1,
        )
        avg_download_time, median_download_time = generate_histogram_and_summary(
            download_times,
            f"[{int(file_size/1000)}KB]",
            title="Retrieve Operation",
            fig_number=2,
        )

        results[file_size] = {
            "store_times": store_times,
            "download_times": download_times,
            "avg_store_time": avg_store_time,
            "median_store_time": median_store_time,
            "avg_download_time": avg_download_time,
            "median_download_time": median_download_time,
        }

    plt.show()
    return results


if __name__ == "__main__":
    results = perform_tests()

    # Print results summary
    for file_size, result in results.items():
        print(f"\nFile size: {file_size / 1000} KB")
        print(f"\tAverage store time: {result['avg_store_time']:.4f}s")
        print(f"\tMedian store time: {result['median_store_time']:.4f}s")
        print(f"\tAverage download time: {result['avg_download_time']:.4f}s")
        print(f"\tMedian download time: {result['median_download_time']:.4f}s")
