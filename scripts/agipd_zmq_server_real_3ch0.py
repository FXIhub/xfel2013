from collections import deque
from functools import partial
import msgpack
import msgpack_numpy
msgpack_numpy.patch()
import numpy as np
from time import sleep, time
import sys, os
from threading import Thread
import zmq
import pickle

_TRAINS = [i for i in range(1455918683, 1455918699)]
_PULSES = 64
_SAVED_PULSES = int((64-2)/2)
_MODULES = 16
_MOD_X = 512
_MOD_Y = 128
_SHAPE = (_SAVED_PULSES, _MODULES, _MOD_X, _MOD_Y)
#_SHAPE = (_MOD_X, _MOD_Y, 2, _PULSES)

data_file = "/gpfs/exfel/exp/SPB/201701/p002013/usr/ekeberg/data_simulation_template/dump_3ch0.p"

if not os.path.exists(data_file):
    this_dir = os.path.dirname(os.path.realpath(__file__))
    data_file = "%s/../data/dump_3ch0.p" % this_dir

if not os.path.exists(data_file):
    print("ERROR: Cannot find data file!")
    
with open(data_file, "rb") as file_handle:
    data_dict = pickle.load(file_handle)
    
def generate(source, queue):
    while True:
        if len(queue) < queue.maxlen:
            data = data_dict
            queue.append(data)
            print(data[source]['metadata']['timestamp']['tid'])
        else:
            sleep(0.1)


def main(source, port):
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind('tcp://*:{}'.format(port))

    queue = deque(maxlen=10)

    t = Thread(target=generate, args=(source, queue,))
    t.start()
    
    while True:
        msg = socket.recv()
        if msg == b'next':
            while len(queue) <= 0:
                sleep(0.1)
            socket.send(msgpack.dumps(queue.popleft()))
        else:
            print('wrong request')
            break
    else:
        socket.close()
        context.destroy()


if __name__ == '__main__':
    source = 'SPB_DET_AGIPD1M-1/DET/3CH0:xtdf'
    #source = 'SPB_DET_AGIPD1M-1/DET'
    port = 4600
    main(source, port)
