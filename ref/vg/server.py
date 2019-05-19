import sys
import os
import time
import SocketServer
import SimpleHTTPServer

if len(sys.argv) < 2:
    print "Needs one argument: server port"
    raise SystemExit

PORT = int(sys.argv[1])


class HTTPCacheRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def send_head(self):
        # print 'in f1'
        # print self.command,'\n', self.headers
        if self.command != "POST" and self.headers.get('If-Modified-Since', None):
            # print 'in if of f1'
            filename = self.path.strip("/")
            if os.path.isfile(filename):
                a = time.strptime(time.ctime(os.path.getmtime(filename)), "%a %b %d %H:%M:%S %Y")
                b = time.strptime(self.headers.get('If-Modified-Since', None), "%a %b  %d %H:%M:%S %Z %Y")
                if a < b:
                    self.send_response(304)
                    self.end_headers()
                    return None
        # print 'going out of f1'
        return SimpleHTTPServer.SimpleHTTPRequestHandler.send_head(self)

    def end_headers(self):
        # print 'in f2'
        self.send_header('Cache-control', 'must-revalidate')
        SimpleHTTPServer.SimpleHTTPRequestHandler.end_headers(self)
        # print 'going out of f2'

    def do_POST(self):
        # print 'in f3'
        self.send_response(200)
        self.send_header('Cache-control', 'no-cache')
        SimpleHTTPServer.SimpleHTTPRequestHandler.end_headers(self)
        # print 'going out of f3'

    # def do_GET(self):
    #     print 'in f4'
    #     self.send_response(200)
    #     self.send_header("Content-type", 'text/html')
    #     SimpleHTTPServer.SimpleHTTPRequestHandler.end_headers(self)
    #     self.wfile.write("<html><head><title>Test</title></head></html>")
    #     print 'going out of f4'

s = SocketServer.ThreadingTCPServer(("127.0.0.1", PORT), HTTPCacheRequestHandler)
s.allow_reuse_address = True
print "Serving on port", PORT
# print 'going to serve_forever()'
s.serve_forever()
