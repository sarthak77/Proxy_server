import sys
import os
import socket
import threading
import time

class Server:
    def __init__(self, config):
        """Setting up the proxy server."""
        self.config = config
        self.cache = {}
        self.count = 0
        try:
            self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except:
            print("ERROR: Couldn't create socket")
            sys.exit(0)

        try:
            self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except:
            print("ERROR: Couldnt setup socket address for reusability")
            sys.exit(0)

        try:
            self.serverSocket.bind((self.config['HOST_NAME'], self.config['BIND_PORT']))
        except:
            print("ERROR: Couldn't bind socket with port")
            sys.exit(0)

        try:
            self.serverSocket.listen(10)
            print("Proxy server listening on port " + str(self.config['BIND_PORT']))
        except:
            print("ERROR: Couldn't get server to listen")
            sys.exit(0)

        while True:
            try:
                (conn, addr) = self.serverSocket.accept()
                try:
                    threading.Thread(target=self.requestHandler, args = [conn, addr]).start()
                    print("Thread initialized")
                except:
                    print("ERROR: Failed to initialize thread")
                    sys.exit(0)
                print("Connection accepted from " + str(addr))
            except:
                print("ERROR : Error in accepting Clients / Keyboard interrupt Caught")
                sys.exit(0)

    def requestHandler(self, conn, addr):
        try:
            client_req = conn.recv(self.config['MAX_REQUEST_LEN'])
        except:
            print("ERROR: Couldn't receive request from client")
            sys.exit(0)
        req = client_req.split("\n")
        url = req[0].split(" ")[1]
        if self.cached(url, conn, client_req):
            print("Page is cached")
            self.reqServer(conn, client_req, True)
        else:
            print("Page isn't cached")
            self.reqServer(conn, client_req)
        print("Exiting thread")
        print("\n\n")
        sys.exit(0)

    def reqServer(self, conn, client_req, fl=False):
        req = client_req.split("\n")
        url = req[0].split(" ")[1]
        host = req[1].split(":")[1][1:]
        port = int(req[1].split(":")[2])
        ourl = url

        if fl:
            req.insert(2, "If-Modified-Since: %s" % (time.strftime('%a %b %d %H:%M:%S %Z %Y', time.localtime(self.cache[ourl]))))

        print ("Opening socket to end server at" + host + ":" + str(port))

        try:
            sock = socket.socket()
        except:
            print("ERROR: Failed to create socket to end server")
            sys.exit(0)

        try:
            sock.connect((host, port))
        except:
            print("ERROR: Failed to connect to end server")
            sys.exit(0)

        http_pos = url.find("://")
        if http_pos != -1:
            url = url[(http_pos + 3):]

        file_i = url.find("/")
        url = url[file_i:]

        req[0] = "GET " + url + " HTTP/1.1"

        new_request = ""
        for i in req:
            new_request += (i + "\r\n")

        print("Forwarding request to end server " + url)
        try:
            sock.send(new_request)
            print(new_request)
        except:
            print("ERROR: Failed to send request to end server")
            sys.exit(0)

        try:
            response = sock.recv(self.config['MAX_REQUEST_LEN'])
            print(response)
        except:
            print("ERROR: No response received from end server")
            sys.exit(0)

        try:
            print("Forwarding response to client")
            if "404" in response.split(" "):
                print("ERROR: File doesn't exist")
                conn.send("ERROR: File doesn't exist")
                conn.close()
                sys.exit(0)
            if "304" in response.split(" "):
                temp = response.split("\r\n")
                temp2 = temp[0].split(" ")
                temp2[1] = "200"
                temp2[2] = "OK"
                temp2 = " ".join(temp2)
                temp[0] = temp2
                response = "\r\n".join(temp)
                conn.send(response)
                self.sendLocalFile(ourl, conn)
                conn.close()
                return
            else:
                conn.send(response)
        except:
            print("ERROR: Failed to send response back to client")
            sys.exit(0)

        url_spl = url.split("/")
        url_file = url_spl[len(url_spl)-1]
        print("Recieving data from origin server and forwarding to client")
        with open(url_file, 'wb') as f:
            while True:
                data = sock.recv(self.config['MAX_REQUEST_LEN'])
                print(data.split('\n')[1])
                if not data:
                    breaks
                f.write(data)
                conn.send(data)

        print("Closing connection to client")
        try:
            conn.close()
        except:
            print("ERROR: Couldn't close connection")
            sys.exit(0)

    def cached(self, url, conn, client_req):
        print("Checking if requested page is cached")
        t = "time"
        cache_flag = True

        orig_url = url
        url_spl = url.split("/")
        url_file = url_spl[len(url_spl)-1]

        if url not in self.cache:
            entry = time.time()
            self.count += 1
            if self.count > 3:
                urll = next(iter(self.cache))
                self.cache.pop(next(iter(self.cache)))
                self.count -= 1
                urll_spl = urll.split("/")
                urll_file = urll_spl[len(urll_spl)-1]
                os.remove(urll_file)
            self.cache[orig_url] = entry
            cache_flag = False
        else:
            cache_flag = True
        return cache_flag

    def sendLocalFile(self, url, conn):
        url_spl = url.split("/")
        url_file = url_spl[len(url_spl)-1]
        with open(url_file, 'r') as f:
            while True:
                data = f.read(self.config['MAX_REQUEST_LEN'])
                if not data:
                    break
                try:
                    conn.send(data)
                except:
                    print("ERROR: Failed to send data")
                    sys.exit(0)
        print("Closing connection to client")
        try:
            conn.close()
        except:
            print("ERROR: Failed to close connection")
            sys.exit(0)

config = {
'HOST_NAME': '127.0.0.1',
'MAX_REQUEST_LEN': 99999,
'BIND_PORT': 12346,
'CONNECTION_TIMEOUT': 10
}

s2 = Server(config)
