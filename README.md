<!-- ABOUT THE PROJECT -->

## About The Project

In this application, any replica can commit updates. A client can send an add_update(key,value) request to any replica and the replica will update its local data store only when it achieves a quorum. We define a quorum as the majority of members within a set of nodes. For a size of N nodes, a quorum requires votes from at least Nw members, where Nw >= (N/2)+1.

A leader is responsible for achieving a quorum on any add_update request to the state. The Bully algorithm is used to elect a leader. Each replica will be assigned a unique id on startup and leader election will be held (i) on startup (ii) or, when the leader becomes unresponsive. Note that the replicas will forward the add_update request to the leader, which will achieve quorum.  
Once the leader replica achieves a quorum (e.g., majority vote), it will COMMIT the changes from the add_update request to its local data store. And, send COMMIT changes to other replicas. On receiving the COMMIT message for that entry, all replicas commit the updates to their local data store.

Similarly, any read(key) will require a quorum before the value is sent to the client. A client can connect to any replica to read the value. The replica will randomly select NR replicas and request for values. If there is no disagreement in value among the replicas, it will send the value to the client. Else it will randomly select NR replicas and repeat until replicas reach an agreement. The NR is selected as such that NR + NW > N.

#### Testing

Includes a driver test program that will spawns the servers and client to test the following scenarios.

- Test that shows that the system only commits changes when quorum is achieved

- Test the read function works as intended

<p align="right">(<a href="#top">back to top</a>)</p>

### Built With

- [Python](https://www.python.org/)
- [Socket](https://docs.python.org/3/library/socket.html)

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- GETTING STARTED -->

## Getting Started

These are the instructions on setting up your project locally.

### Prerequisites

Following are the prerequisites for running the project:

- Python

### Installation

_For running the project please follow the following commands._

1. Clone the repo
   ```sh
   git clone https://github.com/karandeepParashar/DistributedDatabase-Quorum.git
   ```
2. Enter the project directory.
   ```sh
   cd DistributedDatabase-Quorum
   ```
3. run the server

   ```js
   python .\server.py --hosts "localhost" "localhost" "localhost" "localhost" "localhost" --ports 9953 9982 9959 9963 9985
   ```

4. Open seperate terminal for each client and run

   ```js
   python .\client.py --hosts "localhost" "localhost" "localhost" "localhost" "localhost" --ports 9953 9982 9959 9963 9985
   ```

5. Run the driver test cases
   ```js
   python .\driver.py
   ```

<p align="right">(<a href="#top">back to top</a>)</p>
