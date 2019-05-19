# Proxy Server
An HTTP proxy server implemented via python socket programming with caching, blacklisting, authentication functionality

## AUTHORS 
	- Himanshu Maheshwari(20171033)
	- Aayush Goel(20171188)

## Description
- ps.py is the proxy server
- myserver.py is the server
- Proxy works as middleman between the server and client and it does caching, authentication and blacklisting
- GET and POST requests are handled

## Features
- Threaded proxy server and thus handles many requests simultaneously.
- Caching is there.
- Authentication is there.
- Blacklisting is there(In CIDR format).
- All the features of pdf ae there.

## How to run

### Proxy  
`python proxy.py`  
It will run proxy on port 20100

### Server
- `python server.py 20103` to run server on port 20103  
- `python server.py` to run server on port 20105(Default)