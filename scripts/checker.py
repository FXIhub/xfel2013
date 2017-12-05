import socket
import zmq
import time

sound_port = 19999
timeout = 20000
#timeout = 1000

zmq_context = zmq.Context()
zmq_request = zmq_context.socket(zmq.REQ)
zmq_request.RCVTIMEO = timeout
zmq_request.connect('tcp://10.253.0.52:4600')

try:
    sound_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sound_socket.connect(('localhost', sound_port))
    print('Connect to sound socket on port %d' %sound_port)
except ConnectionRefusedError as e:
    sound_socket = None
    print('Could not connect sound socket')
    print(e)

current = time.time()

while(True):
    print("Asked for data...")
    zmq_request.send(b'next')
    while(True):
        try:
            msg = zmq_request.recv()
            print("Received data, t = %.2f" %(time.time()-current))
            break
        except zmq.error.Again:        
            if sound_socket is not None:
                try:
                    print("No data in %d seconds, lets scream..."  %(timeout/1000))
                    sound_socket.send(b'scream\n')
                except:
                    pass
            current = time.time()


