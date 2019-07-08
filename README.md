## Proxy_server
A multithreaded HTTP proxy server, which can handle and serve many requests, using sockets.

### Features
- Threaded Proxy server
- The proxy must keep count of the requests that are made. If a URL is
requested more than 3 times in 5 minutes, the response from the server
must be cached. In case of any further requests for the same, the proxy
must utilise the “If Modified Since” header to check if any updates have
been made, and if not, then serve the response from the cache. The cache
has a memory limit of 3 responses.
- The proxy must support blacklisting of certain outside domains. These
addresses will be stored in “proxy/blacklist.txt” in CIDR format. If the
request wants a page that belongs to one of these, then, return an error
page.
- Handle proxy authentication using Basic Access Authentication and
appropriate headers to allow access to blacklisted sites as well. The
authentication will be username/password based, and can be assumed to
be stored on the proxy server.
