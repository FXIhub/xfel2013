import numpy
import zmq
import msgpack
import time
import pickle
from threading import Thread

SOURCE = "tcp://10.253.0.52:4700"
OUTPUT_PORT = 4700

recv_context = zmq.Context()
recv_request = recv_context.socket(zmq.REQ)
recv_request.connect(SOURCE)
data_container = {'gmd':None,
                  'injposX':None,
                  'injposY':None,
                  'injposZ':None}

def fill_data_into_container(data):
    try:
        injposx = data['SPB_IRU_INJMOV/MOTOR/X']['actualPosition']
        data_container['injposX'] = injposx
    except:
        print("No injector motor X in the data")
    try:
        injposy = data['SPB_IRU_INJMOV/MOTOR/Y']['actualPosition']
        data_container['injposY'] = injposy
    except:
        print("No injector motor Y in the data")
    try:
        injposz = data['SPB_IRU_INJMOV/MOTOR/Z']['actualPosition']
        data_container['injposZ'] = injposz
    except:
        print("No injector motor Z in the data")
    # TODO: Add details for gmd

def recv_data(recv_request, data_container):
    while(True):
        recv_request.send(b"next")
        msg = recv_request.recv()
        data = msgpack.loads(msg)
        fill_data_into_container(data)
        time.sleep(0.1)

send_context = zmq.Context()
send_socket = send_context.socket(zmq.REP)
send_socket.bind('tcp://*:{}'.format(OUTPUT_PORT))

t = Thread(target=recv_data, args=(recv_request, data_container))
t.start()
    
while True:
    msg = send_socket.recv()
    if msg == b'next':
        send_socket.send(msgpack.dumps(data_container))
    else:
        print('wrong request')
        break
