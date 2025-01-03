import os
import json
import numpy as np
import matplotlib.pyplot as plt


def plot_histograms(data, node_counts, strategies, operation, file_sizes):
    """
    Plot histograms of store or download times grouped by strategies and file sizes in subplots.

    :param data: The processed data dictionary.
    :param node_counts: List of node counts.
    :param strategies: List of node selection strategies.
    :param operation: 'store' or 'download'.
    :param file_sizes: List of file sizes.
    """

    readable_sizes = {100000.0: "100kb", 1000000.0: "1mb", 10000000.0: "10mb", 100000000.0: "100mb"}

    num_strategies = len(strategies)
    num_file_sizes = len(file_sizes)

    # Create a figure for the operation
    fig, axes = plt.subplots(
        num_file_sizes, num_strategies, figsize=(15, 12), sharex=True, sharey=True
    )
    fig.suptitle(
        f"{operation.capitalize()} Times Across Strategies and File Sizes", fontsize=16
    )

    for i, file_size in enumerate(file_sizes):
        for j, strategy in enumerate(strategies):
            ax = axes[i, j]
            legends = []

            for nodes in node_counts:
                key = f"('{strategy}', {file_size})"
                if key in data[nodes]:
                    times = np.array(data[nodes][key][operation])

                    median = np.median(times)
                    avg = np.mean(times)

                    ax.hist(
                        times,
                        bins=20,
                        alpha=0.5,
                        edgecolor="black",
                    )

                    legends.append(
                        f"{nodes} Nodes: Median {median:.2f} ms, Avg {avg:.2f} ms"
                    )

            ax.set_title(f"{strategy.capitalize()}, File Size {readable_sizes[file_size]}", fontsize=10)
            ax.grid(axis="y", linestyle="--", alpha=0.7)
            if i == num_file_sizes - 1:
                ax.set_xlabel("Time (ms)", fontsize=9)
            if j == 0:
                ax.set_ylabel("Frequency", fontsize=9)

            ax.legend(legends, loc="upper right", fontsize=8)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()


if __name__ == "__main__":
    SUFFIX = "nodes_replication_allocation_test_results.json"
    OUT_DIR = "tests/out/"

    # Parameters
    node_counts = ["3", "6", "12", "24"]
    strategies = ["random", "min_copy_sets", "buddy"]
    operations = ["store_times", "download_times"]
    file_sizes = [100000.0, 1000000.0, 10000000.0, 100000000.0]

    # Load files
    files = [f for f in os.listdir(OUT_DIR) if f.endswith(SUFFIX)]

    all_data = {}
    for file, no_nodes in zip(files, node_counts):
        with open(os.path.join(OUT_DIR, file), "r", encoding="utf-8") as f:
            data = json.load(f)
            all_data[no_nodes] = data

    # Generate plots for store and download times
    for operation in operations:
        plot_histograms(all_data, node_counts, strategies, operation, file_sizes)
