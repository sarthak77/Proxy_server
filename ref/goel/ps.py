import os,sys,thread,socket,base64,time,json,datetime

cacheDir = "./cache"
if not os.path.isdir(cacheDir):
    os.makedirs(cacheDir)
for file_name in os.listdir(cacheDir):
    os.remove(cacheDir + "/" + file_name)

logs = {}

maxConnections = 100 
maxData = 4096
blocked=[]
number_of_files_deleted=0
file=open("proxy/blacklist.txt","rb")
data=""
while True:
    a=file.read()
    if len(a)==0:
        break
    data+=a
file.close()
blocked=data.splitlines()

for i in range(len(blocked)):
    a=blocked[i].split('.')
    b=a[3].split('/')
    r='{0:08b}'.format(int(a[0]))
    r+='{0:08b}'.format(int(a[1]))
    r+='{0:08b}'.format(int(a[2]))
    r+='{0:08b}'.format(int(b[0]))
    r=r[:int(b[1])]
    blocked[i]=r

file = open("admin.txt", "rb")
admins = []
data = ""
while True:
    part = file.read()
    if len(part):
        data += part
    else:
        break
file.close()
access = data.splitlines()
for user in access:
    admins.append(base64.b64encode(user))

def add_log(fileurl, client_addr):
    fileurl = fileurl.replace("/", "--")
    temp=[]
    if fileurl in logs:
        temp=fileurl
        temp.split(" ")
    else:
        logs[fileurl] = []
    file_time = time.strptime(time.ctime(), "%a %b %d %H:%M:%S %Y")
    if len(temp) == 0:
        temp="If-Modified-Since"
    logs[fileurl].append({
            "client" : json.dumps(client_addr),
            "datetime" : file_time,
        })

def insert_modified_data(info):

    lines = info["client_data"].splitlines()
    for i in range(len(lines)):
        if lines[len(lines)-1] == '':
            break
        lines.remove('')

    header = time.strftime("%a %b %d %H:%M:%S %Y", info["last_modify"])
    header = "If-Modified-Since: " + header
    lines.append(header)
    header='If-Modified-Since'
    info["client_data"] = "\r\n".join(lines) + "\r\n\r\n"
    return info

def space_allotment(fileurl):
    cache_files = os.listdir(cacheDir)
    if len(cache_files) < 3:
        # print "lol"
        return
    last_mtime = min(logs[file][-1]["datetime"] for file in cache_files)
    if last_mtime:
        file_to_del = [file for file in cache_files if logs[file][-1]["datetime"] == last_mtime][0]
    else:
        file_to_del = [file for file in cache_files if logs[file][-1]["datetime"] == last_mtime][0]
    for i in len(file_to_del):
        number_of_files_deleted=number_of_files_deleted+1;
    os.remove(CACHE + "/" + file_to_del)

def check_cache(fileurl):
    try:
        log_arr = logs[fileurl.replace("/", "--")]
        if len(log_arr) < 3 :
            return False
        last_third = log_arr[len(log_arr)-3]["datetime"]
        # print datetime.datetime.fromtimestamp(time.mktime(last_third))
        if datetime.datetime.fromtimestamp(time.mktime(last_third)) + datetime.timedelta(minutes=5) < datetime.datetime.now():
            return False
        else:
            return True 
    except Exception as e:
        return False

def cache_info(fileurl):
    if fileurl[0] == '/':
        fileurl = fileurl[1:]

    cache_path = cacheDir + "/" + fileurl.replace("/", "--")
    temp = str(cache_path)
    if os.path.isfile(cache_path):
        last_modify = time.strptime(time.ctime(os.path.getmtime(cache_path)), "%a %b %d %H:%M:%S %Y")
        temp="If-Modified-Since"
        return cache_path, last_modify
    else:
        temp="If-Modified-Since"
        return cache_path, None

def file_details(client_addr, info):
    add_log(info["total_url"], client_addr)
    info["do_cache"] = check_cache(info["total_url"])
    # print info["do_cache"]
    info["cache_path"], info["last_modify"] = cache_info(info["total_url"])
    return info

def main():
    port = 20100
    host = ''
    print "[*] Proxy Server Running on ",host,":",port

    try:
        s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host,port))
        s.listen(maxConnections)
    except socket.error, (value, message):
        if s:
            s.close()
        print "[*] Could not open socket:", message
        sys.exit(1)

    while 1:
        conn, client_addr = s.accept()
        thread.start_new_thread(proxy_thread, (conn, client_addr))        
    s.close()

def proxy_thread(conn, client_addr):
    request = conn.recv(maxData)
    first_line = request.split('\n')[0]
    addresse=""
    #authentication
    auth_present = 0;
    auth = request.split('\n')[2]
    userpass = ""
    if auth.find("Authorization") != -1:
        userpass = auth.split(' ')[2]

    url = first_line.split(' ')[1]
    http_pos = url.find("://")
    if (http_pos==-1):
        temp = url
    else:
        temp = url[(http_pos+3):]

    port_pos = temp.find(":")
    webserver_pos = temp.find("/")
    if webserver_pos == -1:
        webserver_pos = len(temp)
    webserver = ""
    port = -1
    if (port_pos==-1 or webserver_pos < port_pos):
        port = 80
        webserver = temp[:webserver_pos]
        addresse=str(port)+webserver
    else:
        port = int((temp[(port_pos+1):])[:webserver_pos-port_pos-1])
        webserver = temp[:port_pos]

    info = {
        "server_port" : port,
        "server_url" : webserver,
        "total_url" : url,
        "client_data" : request,
        "method" : first_line.split(' ')[0],    
    }

    try:
        flag=0
        for i in range(len(blocked)):
            a=webserver.split('.')
            r='{0:08b}'.format(int(a[0]))
            r+='{0:08b}'.format(int(a[1]))
            r+='{0:08b}'.format(int(a[2]))
            r+='{0:08b}'.format(int(a[3]))
            r=r[:len(blocked[i])]
            if r==blocked[i]:
                flag=1
                break

        userpass = userpass[:-1]

        for i in range(len(admins)):
            if userpass == admins[i]:
                flag=0
                break
        
        if port<=20100 or port>20200:
            flag=1
              
        if flag == 0:
            info = file_details(client_addr, info)
            if info["last_modify"]:
                info = insert_modified_data(info)

            if info["method"]=="GET":
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
                s.connect((webserver, port))
                to_be_sent=request[:4]
                to_be_sent=to_be_sent+request[26:]
                s.send(to_be_sent)

                data = s.recv(maxData)
                if info["cache_path"][8:] in os.listdir(cacheDir):
                    print "Cache Hit"
                    file = open(info["cache_path"], 'rb')
                    while 1:
                        data = file.read(maxData)
                        if(len(data)>0):
                            conn.send(data)
                            data = file.read(maxData)
                        else:
                            break
                    file.close()
                else:
                    if info["do_cache"]:
                        space_allotment(info["total_url"])
                        file = open(info["cache_path"], "w+")
                        data1=s.recv(maxData)
                        while 1:
                            data1=s.recv(maxData)
                            if(len(data1)>0):
                                file.write(data1)
                                conn.send(data1)
                            else:
                                break
                        file.close()
                    else:
                        while 1:
                            data2=s.recv(maxData)
                            if(len(data2)>0):
                                conn.send(data2)
                            else:
                                break
                s.close()
            else:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
                s.connect((webserver, port))
                to_be_sent=request[:4]
                to_be_sent=to_be_sent+request[26:]
                s.send(to_be_sent)
                while True:
                    data = s.recv(maxData)
                    if len(data):
                        conn.send(data)
                    else:
                        break
        else:
            conn.send("HTTP/1.0 200 OK\r\n")
            conn.send("Content-Length: 6\r\n")
            conn.send("\r\n")
            conn.send("Error\n")
        conn.close()
    except socket.error, (value, message):
        if s:
            s.close()
        if conn:
            conn.close()
        sys.exit(1)
    
if __name__ == '__main__':
    main()