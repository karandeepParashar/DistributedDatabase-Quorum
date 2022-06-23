# python .\server.py --hosts "localhost" "localhost" "localhost" "localhost" "localhost" --ports 9953 9982 9959 9963 9985
import socket
import pickle
import logging
import threading
import argparse
import time


class Server:
    #initiating the leader and socket variables
    def __init__(self, hosts, ports, i, n):
        self.leader = None
        self.hosts, self.ports = hosts, ports
        self.index = i
        self.vectorClock = [0] * n
        self.data = {}
        self.socket = self.initiateServer(hosts[i], ports[i], n)

    #Depending on the replica or leader different routes are taken
    def startListening(self):
        flag = True
        while flag:
            try:
                if self.leader and self.leader == self.index:
                    self.leadTheServers()
                else:
                    self.acceptConnections()
            except:
                logging.info(f"[{self.index}] Check previous logs to backtrack the error. Request Failed.")

    #this method initiates the server
    def initiateServer(self, host, port, n):
        logMsg = "[" + str(self.index) + "]" + "[1]" + "::Initiating Server"
        logging.info(logMsg)
        print("Welcome to the Server: ", self.index)
        sock = socket.socket()
        print("Socket created")
        sock.bind((host, port))
        sock.listen(n)
        logMsg = "[" + str(self.index) + "]" + "[2]" + "::Socket created"
        logging.info(logMsg)
        return sock

    # this method tackles the client request and routes it to a helper method for further processing
    def clientRequestHandler(self, conn):
        logging.info(f"[{self.index}]::Entered Client message deciphering mechanism")
        request = conn.recv(1024 * 1000)
        reply = self.clientRequestHandlerHelper(request)
        return reply
    
    # this method decifers the request type and forwards to other methods
    def clientRequestHandlerHelper(self, request):
        request = pickle.loads(request)
        if type(request) == tuple:
            logging.info(f"[{self.index}]:: Add/Update Request from Client")
            reply = self.contactLeader(request)
        elif type(request) == str:
            logging.info(f"[{self.index}]:: Read Request from Client")
            reply = self.readHandler(request)
        return reply
    
    #This method is used to update the leader after the elections
    def leaderRequestHandler(self, conn):
        self.leader = int(pickle.loads(conn.recv(1024 * 100)))
        logging.info(f"[{self.index}] ELECTIONS: Updated Leader to {self.leader}")
        reply = pickle.dumps("Received")
        return reply
    
    # this method is used to forward the client request to leader
    def contactLeaderHelper(self, request, leader):
        if not leader:
            leader = socket.socket()
            leader.settimeout(2)
            leader.connect((self.hosts[self.leader], self.ports[self.leader]))
            logging.info(f"[{self.index}]:: REPLICA: Connection Established With Leader")
        reply = None
        leader.send(pickle.dumps(f"Replica-{self.index}"))
        time.sleep(0.5)
        leader.send(pickle.dumps(request))
        logging.info(f"[{self.index}]:: REPLICA: Forwarded the client request to Leader")
        reply = pickle.loads(leader.recv(1024 * 100))
        logging.info(f"[{self.index}]:: REPLICA: Received reply from the Leader")
        if reply == "COMMIT":
            key, value = request[0], request[1]
            self.data[key] = value
            reply = pickle.dumps("Changes committed")
        else:
            reply = pickle.dumps("Changes discarded, quorum not achieved")
        leader.close()
        return reply
    
    # this takes teh client request and establishes connection with leader
    def contactLeader(self, request):
        logging.info(f"[{self.index}]:: REPLICA: Contacting leader with Client Request")
        try:
            leader = socket.socket()
            leader.settimeout(2)
            leader.connect((self.hosts[self.leader], self.ports[self.leader]))
            logging.info(f"[{self.index}]:: REPLICA: Connection Established With Leader")
        except:
            leader = None
            self.startElections()
        reply = self.contactLeaderHelper(request, leader)
        return reply

    #this method handles the quorum requests from leader or replica
    def quorumRequestHandler(self, conn):
        key = pickle.loads(conn.recv(1024 * 1000))
        value = self.data[key] if key in self.data else "_None_"
        reply = pickle.dumps(value)
        return reply

    # this handles the leader's commit request
    def commitRequestHandler(self, conn):
        key, value = pickle.loads(conn.recv(1024 * 1000))
        self.data[key] = value
        reply = pickle.dumps("Commit Successful")
        return reply

    # this is the router for replica servers
    def replicaRouter(self, conn_type, conn, index):
        reply = None
        if conn_type == "Client":
            reply = self.clientRequestHandler(conn)
        elif conn_type == "Election_Begin":
            reply = pickle.dumps("Ok")
        elif conn_type == "Leader":
            reply = self.leaderRequestHandler(conn)
        elif conn_type == "Quorum":
            reply = self.quorumRequestHandler(conn)
        elif conn_type == "COMMIT":
            reply = self.commitRequestHandler(conn)
        return reply

    # this method accepts connections and then redirect them to replica router
    def acceptConnections(self):
        logging.info(f"[{self.index}]:: REPLICA: Waiting for requests")
        conn, address = self.socket.accept()
        connType = pickle.loads(conn.recv(1024 * 1000))
        connType = connType.split("-")
        connType, index = connType[0], connType[1] if len(connType) == 2 else None
        index = int(index) if index else None
        logMsg = "[" + str(self.index) + "]" + "[4]" + "::Connected with " + str(address) + "-" + str(connType)
        logging.info(logMsg)
        reply = self.replicaRouter(connType, conn, index)
        conn.send(reply)
        conn.close()
        logging.info(f"[{self.index}]:: Closing current connection")
        if connType == "Election_Begin":
            self.startElections()
    
    # handles read requests by acheiving quorum
    def readHandler(self, key):
        replyData = None
        attempts = 0
        while replyData is None and attempts <= 5:
            replyData = self.achieveQuorum(key)
            print(replyData)
            attempts += 1
        logging.info(f"{[self.index]}:: Server sending reply to Client::\"{replyData}\"")
        return pickle.dumps(replyData)

    # this starts the elections
    def startElections(self):
        logging.info(f"[{self.index}] ELECTIONS: Elections started by server with id:" + str(self.index))
        # send start of Elections to all higher Id servers
        iAmLeader = True
        for i in range(self.index + 1, len(self.hosts)):
            try:
                logging.info(f"[{self.index}] ELECTIONS: Attempting connection with " + str(i))
                replicas = socket.socket()
                replicas.settimeout(0.5)
                replicas.connect((self.hosts[i], self.ports[i]))
                replicas.send(pickle.dumps(f"Election_Begin-{self.index}"))
                msg = pickle.loads(replicas.recv(1024 * 100))
                if msg == "Ok":
                    logging.info(f"[{self.index}] ELECTIONS: Server [{self.index}] Received Ok message from [{i}]. "
                                 f"Dropping Out")
                    iAmLeader = False
                    break
            except:
                logging.info(f"[{self.index}] Election: Could not establish connection with {i}")
        if iAmLeader:
            self.sendIWon()
            self.leader = self.index

    # intiated by the leader when he wins a election
    def sendIWon(self):
        logging.info(f"[{self.index}] ELECTION: Won by Server: " + str(self.index))
        print(f"[{self.index}] ELECTION: Won by Server: " + str(self.index))
        for i in range(len(self.hosts)):
            if i == self.index:
                continue
            try:
                logging.info(f"[{self.index}] Sending Election Won Message to Server: {i}")
                replicas = socket.socket()
                replicas.settimeout(0.5)
                replicas.connect((self.hosts[i], self.ports[i]))
                replicas.send(pickle.dumps(f"Leader-{self.index}"))
                replicas.send(pickle.dumps(self.index))
                msg = pickle.loads(replicas.recv(1024 * 100))
            except:
                logging.info(f"[{self.index}] Election: Could not update Leader for Server: {i}")

    # this is the router if the current server is the leader
    def leaderRequestRouter(self, conn_type, conn, index):
        reply = None
        if conn_type == "Client":
            reply = self.directClientLeader(conn)
        elif conn_type == "Replica":
            reply = self.replicaRequestHandler(conn, index)
        elif conn_type == "Election_Begin":
            reply = pickle.dumps("Ok")
        elif conn_type == "Leader":
            reply = self.leaderRequestHandler(conn)
        return reply

    #Here leader waits for connections
    def leadTheServers(self):
        logging.info(f"[{self.index}]:: LEADER: Waiting for requests")
        conn, address = self.socket.accept()
        connType = pickle.loads(conn.recv(1024 * 1000))
        connType = connType.split("-")
        connType, index = connType[0], connType[1] if len(connType) == 2 else None
        reply = self.leaderRequestRouter(connType, conn, index)
        conn.send(pickle.dumps(reply))
        conn.close()
        logging.info(f"[{self.index}]:: Closing current connection")
        if connType == "Election_Begin":
            self.startElections()

    # leader establish connection with replica for add update request
    def replicaRequestHandler(self, conn, index):
        logging.info(f"[{self.index}]:: LEADER: Connection Established With a Replica")
        request = conn.recv(1024 * 1000)
        request = pickle.loads(request)
        if type(request) == str:
            reply = self.readHandler(request)
        else:
            key, value = request[0], request[1]
            logging.info(f"[{self.index}]:: LEADER: Received forwarded request")
            quorum = self.achieveQuorum(key)
            if quorum is not None:
                self.data[key] = value
                reply = "COMMIT"
                self.sendCommitToAll(request, index)
            else:
                reply = "DISCARD"
        return reply

    # quorum attempt is made in this method
    def achieveQuorum(self, key):
        logging.info(f"[{self.index}]:: Quorum Mechanism Initiated")
        votes = {}
        if key in self.data:
            votes[self.data[key]] = 1
        else:
            votes["_None_"] = 1
        for i in range(len(self.hosts)):
            if i == self.index:
                continue
            try:
                logging.info(f"[{self.index}] QUORUM: Attempting connection with " + str(i))
                print(f"[{self.index}] QUORUM: Attempting connection with Replica: " + str(i))
                replicas = socket.socket()
                replicas.settimeout(0.5)
                replicas.connect((self.hosts[i], self.ports[i]))
                replicas.send(pickle.dumps(f"Quorum-{self.index}"))
                replicas.send(pickle.dumps(key))
                reply = pickle.loads(replicas.recv(1024 * 100))
                if reply in votes:
                    votes[reply] += 1
                else:
                    votes[reply] = 1
                if votes[reply] >= ((len(self.hosts)//2) + 1):
                    logging.info(f"Quorum achieved by {votes[reply]} out of {len(self.hosts)}")
                    print(f"Quorum achieved by {votes[reply]} out of {len(self.hosts)}")
                    replicas.close()
                    return reply
                replicas.close()
            except:
                replicas.close()
                print(f"[{self.index}] QUORUM: Could not establish connection with {i}")
                logging.info(f"[{self.index}] QUORUM: Could not establish connection with {i}")
        print(f"Quorum failed by {votes}")
        return None

    # if quorum is sucess this method send commit to all replicas
    def sendCommitToAll(self, request, index):
        for i in range(len(self.hosts)):
            if i == self.index or i == int(index):
                continue
            try:
                logging.info(f"[{self.index}] COMMIT: Attempting connection with " + str(i))
                replicas = socket.socket()
                replicas.settimeout(0.5)
                replicas.connect((self.hosts[i], self.ports[i]))
                replicas.send(pickle.dumps(f"COMMIT-{self.index}"))
                replicas.send(pickle.dumps(request))
                pickle.loads(replicas.recv(1024 * 100))
                replicas.close()
            except:
                logging.info(f"[{self.index}] COMMIT: Could not establish connection with {i}")
        return False

    def directClientLeader(self, conn):
        return self.replicaRequestHandler(conn, self.index)


if __name__ == '__main__':
    # Take command Line arguments
    parser = argparse.ArgumentParser(description="Replicated Database Vector Clock by Karandeep Parashar")
    parser.add_argument('--hosts', nargs="+", help='Hosts', default=["localhost", "localhost", "localhost"])
    parser.add_argument('--ports', nargs="+", help="Ports", default=[9990, 9980, 9999])
    args = parser.parse_args()
    # Initiate Server Logs
    logging.basicConfig(filename='server_logs.log', level=logging.INFO)
    logging.info("\n\nNEW SESSION")
    hosts, ports = args.hosts, args.ports
    ports = [int(element) for element in ports]
    n = len(hosts)
    # Run servers in a Loop
    for i in range(1, n):
        server = Server(hosts, ports, i, n)
        serverThread = threading.Thread(target=server.startListening, args=[], daemon=True)
        serverThread.start()
    server = Server(hosts, ports, 0, n)
    server.startElections()
    server.startListening()
