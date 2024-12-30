import time
import numpy as np
import requests

URL = "http://localhost:4000"

def send_store_request(file_bytes):
    """Send store request to the lead node"""
    response = requests.post(f"{URL}/store", data=file_bytes)
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
    response = requests.get(f"{URL}/retrieve?file_id={file_id}")
    download_time = time.time() - start_time
    return download_time

def generate_file(size):
    """Generate a file with the given size in bytes"""
    return np.random.bytes(size)
