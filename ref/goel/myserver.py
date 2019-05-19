import sys,os,time,SocketServer,SimpleHTTPServer
PORT = 20105 #default
class HTTPCacheRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def send_head(self):
        filename = self.path.strip("/")
        if self.command != "POST" and self.headers.get('If-Modified-Since', None):
            if os.path.isfile(filename) and len(filename)>	0:
                x = time.strptime(self.headers.get('If-Modified-Since', None), "%a %b %d %H:%M:%S %Y")
                y = time.strptime(time.ctime(os.path.getmtime(filename)), "%a %b %d %H:%M:%S %Y")
                if y < x:
                    self.end_headers()
                    self.send_response(304)
                    return None
                else:
                	filenane=self.path.strip("/")
        return SimpleHTTPServer.SimpleHTTPRequestHandler.send_head(self)


    def do_POST(self):
        self.send_header('Cache-control', 'no-cache')
        self.send_response(200)
        SimpleHTTPServer.SimpleHTTPRequestHandler.end_headers(self)

    def end_headers(self):
        self.send_header('Cache-control', 'must-revalidate')
        SimpleHTTPServer.SimpleHTTPRequestHandler.end_headers(self)

if len(sys.argv) < 2:
    print "PORT not given, so working on port 20105(Defaut)"
else:
	PORT = int(sys.argv[1])
	
s = SocketServer.ThreadingTCPServer(("", PORT), HTTPCacheRequestHandler)
print "[*] Serving on port", PORT
s.allow_reuse_address = True
s.serve_forever()
