import os
import sys
import random
import time

if len(sys.argv) < 4:
    print "Usage: python client.py <CLIENT_PORTS_RANGE> <PROXY_PORT> <END_SERVER_PORT>"
    print "Example: python client.py 19990-19999 20000 20010"
    raise SystemExit

CLIENT_PORTA = sys.argv[1]
PROXY_PORT = sys.argv[2]
SERVER_PORT = sys.argv[3]

D = {0: "GET", 1: "GET"}

while True:
    filename = "%d.data" % (int(random.random() * 1) + 1)
    METHOD = D[int(random.random() * len(D))]
    CLIENT_PORT = str(random.randint(int(CLIENT_PORTA), int(CLIENT_PORTA) + 10))

    print 'sending request - ', "curl --user pranav:qwerty --request %s --proxy 127.0.0.1:%s geeksforgeeks.org"\
                                % (METHOD, PROXY_PORT)

    os.system("curl --user pranav:qwerty --request %s --proxy 127.0.0.1:%s geeksforgeeks.org" % (
        METHOD, PROXY_PORT))

    time.sleep(5)

    print 'sending request - ', "curl --user pranav:qwerty --request %s --proxy 127.0.0.1:%s 127.0.0.1:%s/%s" % (
        METHOD, PROXY_PORT, SERVER_PORT, filename)

    os.system("curl --user pranav:qwerty --request %s  --proxy 127.0.0.1:%s 127.0.0.1:%s/%s" % (
        METHOD, PROXY_PORT, SERVER_PORT, filename))

    time.sleep(5)
