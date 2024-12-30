import json
import matplotlib.pyplot as plt

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


if __name__ == '__main__':
    file_name = "out/3_nodes_replication_allocation_test_results.json"
    with open(file_name, 'r') as f:
        data = json.load(f)
