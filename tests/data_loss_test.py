import tqdm

from replication_allocation_test import send_store_request, generate_file

def store_n_files(n, file_size):
    """Store n files with the given size"""

    file_ids = []
    file_bytes = generate_file(file_size)
    for _ in tqdm.tqdm(range(n), desc="Processing files"):
        # Store file and measure time
        file_id = send_store_request(file_bytes)
        file_ids.append(file_id)

    return file_ids

if __name__ == "__main__":
    n = 100
    file_size = 10 ** 3 # 1 KB
    ids = store_n_files(n, file_size)
    print(ids)