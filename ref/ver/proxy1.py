# Importing modules
import socket
import threading
import thread
import sys
import os
import datetime
import thread
import time
import json
from netaddr import IPNetwork

#------------------------------GLOBAL_VARIABLES_DECLARED--------------------------------#

cachedir="./cache"#where to store cached files
blkfile="blacklist.txt"#file containing blacklisted IP's
upfile="up.txt"#file containing admin details

blockedIP=[]#list of blocked IP's
userdetails=[]#list of admins

buffsize=4096#size of buffer
cachelimit=3#max files that can be stored in the cache
cachetime=300#time limit of cache

logs={}
locks={}

# Take input
try:
    proxy_port=int(sys.argv[1])
except:
    print "Usage:: python proxy.py <port>"
    print "Example:: python proxy.py 12346"
    raise SystemExit

# Store blocked IP's in array
temp=[]
file=open(blkfile,"r")
for x in file:
    x=x[:-1]
    temp.append(x)
for x in temp:
    for ip in IPNetwork(x):
        blockedIP.append('%s' % ip)
file.close()

# Store username and pwds
file=open(upfile,"r")
for x in file:
    userdetails.append(x)
file.close()

# Empty cache directory in the beginning
for file in os.listdir(cachedir):
    os.remove(cachedir + "/" + file)

#---------------------------------------------------------------------------------------#

# def applylock(doc):

#     #if already applied
#     if doc in locks:
#         lock = locks[doc]
#     else:
#         #create lock object
#         lock = threading.Lock()

#         #store for fututre ref
#         locks[doc] = lock
    
#     #acquire the lock
#     lock.acquire()

# def removelock(doc):

#     if doc in locks:
#         lock = locks[doc]
#         lock.release()#release the lock
    
#     else:
#         print "Lock problem"#error handling
#         sys.exit()

def lockingfunc(doc,action):
    
    if action == "apply":

        #if already applied
        if doc in locks:
            lock = locks[doc]
        else:
            #create lock object
            lock = threading.Lock()

            #store for fututre ref
            locks[doc] = lock

        #acquire the lock
        lock.acquire()

    elif action=="release":

        if doc in locks:
            lock = locks[doc]
            lock.release()#release the lock

        else:
            print "Lock problem"#error handling
            sys.exit()


def get_cache_space():
    """Frees cache"""

    #list of cached files
    cachefiles = os.listdir(cachedir)
    
    #if already space is there
    if len(cachefiles) < cachelimit:
        return

    #locking
    for file in cachefiles:
        applylock(file)

    last_mtime = min(logs[file][-1]["datetime"] for file in cachefiles)
    file_to_del = [file for file in cachefiles if logs[file][-1]["datetime"] == last_mtime][0]

    os.remove(cachedir + "/" + file_to_del)


    #unlocking
    for file in cachefiles:
        removelock(file)




def cache_preprocessing(client_addr,parsed_details):

    #locking
    applylock(parsed_details["total_url"])

    #details of current file being referred
    temp=parsed_details["total_url"]

    # Add to logs
    if not temp in logs:
        logs[temp]=[]
    t = time.strptime(time.ctime(), "%a %b %d %H:%M:%S %Y")
    # dt = time.time()
    temp2={"datetime":t, "client":json.dumps(client_addr)}
    logs[temp].append(temp2)    


    #check if caching required or not
    if(len(logs[temp])<=cachelimit):
        cache=False
    else:
        prev_time=logs[temp][len(logs[temp])-1-cachelimit]["datetime"]#check if within cachetime
        cur_time=logs[temp][len(logs[temp])-1]["datetime"]
        if(time.mktime(cur_time)-time.mktime(prev_time)<cachetime):
            cache=True
        else:
            cache=False


    # Check if already cached or not
    cache_path=cachedir + "/" + temp.replace("/","__")
    if(os.path.isfile(cache_path)):
        last_mtime = time.strptime(time.ctime(os.path.getmtime(cache_path)), "%a %b %d %H:%M:%S %Y")
        # last_mtime=os.path.getmtime(cache_path)
    else:
        last_mtime=None #not in cache

    #unlocking
    removelock(parsed_details["total_url"])

    #appending details to parsed_details and returning
    parsed_details["docache"]=cache
    parsed_details["cache_path"]=cache_path
    parsed_details["last_mtime"]=last_mtime
    return parsed_details






def serve_get(client_socket, client_address, parsed_details):
    # Get handling function
    # written during trying to build basic proxy server
    # will later incorporate caching into it

    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((parsed_details["server_url"], parsed_details["server_port"]))
        server_socket.send(parsed_details["client_data"])


        response = server_socket.recv(buffsize)
        mod_check = "304 Not Modified"

        # extracting the client details individually
        last_mtime = parsed_details["last_mtime"]
        cache_path = parsed_details["cache_path"]
        total_url = parsed_details["total_url"]

        # client address converted to string
        adr = str(client_address)

        if mod_check in response and last_mtime :
            # the request exists in cache and file not modified since last cache
            
            print("returning cached file %s to %s" % (cache_path, adr))
            
            applylock(total_url)
            fil = open(cache_path, 'rb')
            
            while True :
                block = fil.read(buffsize)
                if block :
                    client_socket.send(block)
                else :
                    break
            
            fil.close()
            removelock(total_url)

        else :

            cache_flag = parsed_details["docache"]

            if cache_flag :
                # request not in cache and asked to cache

                print("caching file while serving %s to %s" % (cache_path, adr))
                
                get_cache_space()
                applylock(total_url)
                
                fil = open(cache_path, 'w+')
                
                while True:
                    if response :
                        client_socket.send(response)
                        fil.write(response)
                    else :
                        break
                    response = server_socket.recv(buffsize)
                    
                fil.close()
                removelock(total_url)

            else :

                while True:
                    if response :
                        client_socket.send(response)
                    else :
                        break
                    response = server_socket.recv(buffsize)

            client_socket.send("\r\n\r\n")

    except Exception as exc :
        print exc

    server_socket.close()
    client_socket.close()
    return




def serve_post(client_socket, client_address, parsed_details):
    """Post handling function"""
    
    try:
        
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((parsed_details["server_url"], parsed_details["server_port"]))
        server_socket.send(parsed_details["client_data"])

        while True:
            response = server_socket.recv(buffsize)
            if response :
                client_socket.send(response)
            else :
                break

    except Exception as exc :
        print exc
    
    server_socket.close()
    client_socket.close()
    return




def parser(client_address, client_data):
    """returns a dictionary consisting of 
    "server_port" , "server_url" , "total_url" 
    "client_data" , "protocol" , "method" , "auth_b64"
    Error Handling taken care of
    in case of exception a void dictionary sent -> here None"""

    try :
    
        # taking lines upto the indices with nonempty values
        lines = client_data.splitlines()
        while lines and lines[-1] == '':
            lines.pop()

        # check at the beginning for auth
        auth_lines = []
        st = "Authorization"
        for x in lines:
            if st in x :
                auth_lines.append(x)
        if not(auth_lines) :
            auth_b64 = None
        else :
            auth_b64 = auth_lines[0].split()[2]

        # using tokens of the first line
        tokens = lines[0].split()
        url = tokens[1]

        # getting starting index of IP
        prot_ind = url.find("://")
        if prot_ind == -1 :
            protocol = "http"
        else :
            protocol = url[:prot_ind]
            url = url[(prot_ind+3):]

        # getting url path
        path_ind = url.find("/")
        if path_ind == -1:
            path_ind = len(url) 

        # getting any present port in client_data
        port_ind = url.find(":")

        # getting the request path
        server_port = 0
        server_url = ""
        
        # case handling for missing ports : expected not to got into this
        if path_ind < port_ind :
            server_port = 105
            server_url = url[:path_ind]
        elif port_ind < 0 :
            server_port = 105
            server_url = url[:path_ind]
        else :
            tmp = url[(port_ind+1):path_ind]
            server_port = int(tmp,10)
            server_url = url[:port_ind]

        # request for server

        #changing token1
        tokens[1] = url[path_ind:]

        #space separating data
        lines[0] = ' '.join(tokens)
        
        #joining lines and getting into format
        client_data = "\r\n".join(lines) + '\r\n\r\n'

        return {
            "protocol" : protocol,
            "method" : tokens[0],
            "server_port" : server_port,
            "server_url" : server_url,
            "total_url" : url,
            "client_data" : client_data,
            "auth_b64" : auth_b64,
        }

    except Exception as exc :
        print(exc)
        print
        return None




def handle_request(client_socket, client_address, client_data):
    """thread function called which handles single request"""

    #parsing data
    parsed_details = parser(client_address, client_data)

    #if exception in parser
    if parsed_details==None :
        print "Error occured\n"
        print("Enough parsed_details not found")
        client_socket.close()
        return

    # checking for blocking
    block_flg = 0

    st = ""
    st += parsed_details["server_url"]
    st += ":"
    st += str(parsed_details["server_port"])

    if st in blockedIP :
        if not(parsed_details["auth_b64"]) :
            block_flg = 1
        elif not(parsed_details["auth_b64"] in userdetails) :
            block_flg = 1

    #info if blocked
    if block_flg == 1 :
        print("blocked")


    #if method=post
    elif parsed_details["method"] == "POST" :
        serve_post(client_socket, client_address, parsed_details)
    
    #if method=get
    elif parsed_details["method"] == "GET" :
        
        parsed_details = cache_preprocessing(client_address, parsed_details)
        

        #if there in cache then check last modified time
        if parsed_details["last_mtime"]:

            #remove blank lines at the end
            x=parsed_details["client_data"]
            lines = x.splitlines()
            while lines[len(lines)-1] == '':
                lines.remove('')

            #attach header

            #set time format
            header1 = time.strftime("%a %b %d %H:%M:%S %Y", parsed_details["last_mtime"])
            header2 = "If-Modified-Since: " + header1

            #add to client data
            lines.append(header2)

            #concatanate the lines
            parsed_details["client_data"] = "\r\n".join(lines) + "\r\n\r\n"

        #call get function
        serve_get(client_socket, client_address, parsed_details)

    client_socket.close()
    print client_address,"closed"
    print




def start():
    """
        Create socket connections
        Listen to clients
        New thread for every client
        Error handling
    """
    try:
        # Create a TCP socket
        prox_sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Re-use the socket
        prox_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # bind the socket to a public host, and a port   
        prox_sock.bind(('',proxy_port))
        # become a server socket
        prox_sock.listen(10)

        #printing parsed_details
        temp=prox_sock.getsockname()
        print "Serving proxy on " + str(temp[0]) + " " + str(temp[1]) + " ..."
    
    except Exception as e:
        print "Error in initialising proxy server"
        print e
        prox_sock.close()
        raise SystemExit

    #while loop for incoming clients
    while True:
        clientconnect=False#to check if connection established or not
        
        try:
            # Establish the connection
            client_socket, client_addr = prox_sock.accept()
            client_data = client_socket.recv(buffsize)
            clientconnect=True

            #printing format
            print
            print str(client_addr)
            print str(datetime.datetime.now())
            print client_data
            print

            #start new thread for each client
            thread.start_new_thread(handle_request,(client_socket, client_addr, client_data))

        except KeyboardInterrupt:
            if clientconnect:
                client_socket.close()
            prox_sock.close()
            print "\n\nProxy server shutting down ...\n"
            break   

#calling to start proxy server
start()