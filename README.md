# Distributed Storage Mini Project
The aim of this project is to design and implement a distributed file storage system that leverages redundancy allocation schemes to ensure efficient and robust data management. Distributed storage systems provide a scalable and resilient solution for storing large volumes of data by distributing fragments across multiple nodes. This project focuses on understanding the performance trade-offs associated with different node selection and replication strategies, incorporating the theoretical principles and practical tools covered in coursework.

## System Architecture
The system includes two main types of nodes:

- **Lead Node**:
  - Manages file fragmentation, replication, and retrieval.
  - Maintains metadata about fragment locations.
- **Storage Nodes**:
  - Store and retrieve file fragments.
  - Participate in node selection strategies.

The system communicates through a REST API, facilitating file upload, download, and system monitoring.

## Results
For a detailed analysis of the system’s performance, see the [report](report/Distributed_Storage_Mini_Project.pdf). The report includes:
* Metrics on file storage and retrieval times.
* Robustness evaluation against node failures.
* Comparative analysis of replication strategies.


## Contributions
This project was collaboratively developed by a team of students from Aarhus University. Each team member participated in system design, implementation, and testing.
