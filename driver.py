import server
import client
import threading


def startServers(hosts, ports):
    # Spawn 5 servers
    server1 = server.Server(hosts, ports, 0, 5)
    server2 = server.Server(hosts, ports, 1, 5)
    server3 = server.Server(hosts, ports, 2, 5)
    server4 = server.Server(hosts, ports, 3, 5)
    server5 = server.Server(hosts, ports, 4, 5)
    threading.Thread(target=server1.startListening, args=[], daemon=True).start()
    threading.Thread(target=server2.startListening, args=[], daemon=True).start()
    threading.Thread(target=server3.startListening, args=[], daemon=True).start()
    threading.Thread(target=server4.startListening, args=[], daemon=True).start()
    threading.Thread(target=server5.startListening, args=[], daemon=True).start()
    return server1, server2, server3, server4, server5


def test_case_1(server_1, client_1):
    print("Test Case 1: Commit Changes as Quorum is achieved")
    threading.Event().wait(1)
    client_1.establishConnection(0)
    threading.Event().wait(1)
    print("Established Connection with Server 0")
    client_1.updateDataRequest("1", "1")
    threading.Event().wait(1)
    print("Sent Update Request-1")
    data = client1.receiveData()
    client_1.closeConnection()
    expectedData = "Changes committed"
    try:
        assert data == expectedData
        print("-----------------TEST-CASE-1-PASSED-----------------")
    except:
        print("-----------------TEST-CASE-1-FAILED-----------------")

def test_case_2(server_1, client_1):
    print("Test Case 2: Commit Rejected as Quorum is not achieved")
    threading.Event().wait(1)
    client_1.establishConnection(0)
    print("Established Connection with Server 0")
    #
    dummy_client1 = client.Client(hosts, ports)
    dummy_client2 = client.Client(hosts, ports)
    dummy_client1.establishConnection(1)
    dummy_client2.establishConnection(2)
    threading.Event().wait(1)
    #
    client_1.updateDataRequest("1", "1")
    print("Sent Update Request-1")
    threading.Event().wait(1)
    data = client_1.receiveData()
    client_1.closeConnection()
    dummy_client1.closeConnection()
    dummy_client2.closeConnection()
    expectedData = "Changes discarded, quorum not achieved"
    try:
        assert data == expectedData
        print("-----------------TEST-CASE-2-PASSED-----------------")
    except:
        print("-----------------TEST-CASE-2-FAILED-----------------")

def test_case_3(server_1, client_1):
    print("Test Case 3: Read as Quorum is achieved")
    threading.Event().wait(1)
    client_1.establishConnection(0)
    threading.Event().wait(1)
    print("Established Connection with Server 0")
    client_1.readDataRequest("1")
    print("Sent Read Request")
    threading.Event().wait(1)
    data = client1.receiveData()
    client_1.closeConnection()
    expectedData = "1"
    try:
        assert data == expectedData
        print("-----------------TEST-CASE-3-PASSED-----------------")
    except:
        print("-----------------TEST-CASE-3-FAILED-----------------")
if __name__ == '__main__':
    hosts, ports = ["localhost", "localhost", "localhost", "localhost", "localhost"], [9953, 9982, 9959, 9964, 9985]
    server1, server2, server3, server4, server5 = startServers(hosts, ports)
    server1.startElections()
    client1 = client.Client(hosts, ports)
    threading.Event().wait(2)
    test_case_1(server1, client1)
    threading.Event().wait(1)
    test_case_2(server1, client1)
    threading.Event().wait(1)
    test_case_3(server1, client1)
