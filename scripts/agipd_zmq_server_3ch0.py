from collections import deque
from functools import partial
import msgpack
import msgpack_numpy
msgpack_numpy.patch()
import numpy as np
from time import sleep, time
import sys
from threading import Thread
import zmq

_TRAINS = [i for i in range(1455918683, 1455918699)]
_PULSES = 64
_MODULES = 16
_MOD_X = 512
_MOD_Y = 128
#_SHAPE = (_PULSES, _MODULES, _MOD_X, _MOD_Y)
_SHAPE = (_MOD_X, _MOD_Y, 2, _PULSES)


def gen_combined_detector_data(source):
    gen = {source: {}}
    
    #metadata
    sec, frac = str(time()).split('.')
    frac = frac + "0"*(18-len(frac))
    print(sec, frac)
    tid = int(sec+frac[:1])
    gen[source]['metadata'] = {
        'source': source,
        'timestamp': {'tid': tid,
            'sec': int(sec), 'frac': int(frac)
    }}
    
    # detector random data
    rand_data = partial(np.random.uniform, low=1500, high=1600,
                        size=(_MOD_X, _MOD_Y))
    data = np.zeros(_SHAPE, dtype=np.uint16)  # np.float32)
    for pulse in range(_PULSES):
        if pulse < 2 or pulse%2 == 0:
            data[:, :, 0, pulse] = rand_data()
            data[:, :, 1, pulse] = rand_data()
            #data[:, :, 0, pulse] = pulse
            #data[:, :, 1, pulse] = 1
    cellId = np.array(range(_PULSES), dtype=np.uint64) // 2 + 1
    print(cellId)
    length = np.ones(_PULSES, dtype=np.uint32) * int(131072)
    pulseId = np.array([i for i in range(_PULSES)], dtype=np.uint64)
    #cellId[(pulseId >= 2) * ((pulseId % 2) == 0) * (pulseId < 62)] = np.asarray(range(30), dtype=np.uint16)[:]
    trainId = np.ones(_PULSES, dtype=np.uint64) * int(tid)
    status = np.zeros(_PULSES, dtype=np.uint16)
    
    gen[source]['image.data'] = data
    gen[source]['image.cellId'] = cellId
    gen[source]['image.length'] = length
    gen[source]['image.pulseId'] = pulseId
    gen[source]['image.trainId'] = trainId
    gen[source]['image.status'] = status
    
    checksum = np.ones(16, dtype=np.int8)
    magicNumberEnd = np.ones(8, dtype=np.int8)
    status = 0
    trainId = tid
    
    gen[source]['trailer.checksum'] = checksum
    gen[source]['trailer.magicNumberEnd'] = magicNumberEnd
    gen[source]['trailer.status'] = status
    gen[source]['trailer.trainId'] = trainId
    
    data = np.ones(416, dtype=np.uint8)
    trainId = tid
    
    gen[source]['detector.data'] = data
    gen[source]['detector.trainId'] = trainId
    
    dataId = 0
    linkId = np.iinfo(np.uint64).max
    magicNumberBegin = np.ones(8, dtype=np.int8)
    majorTrainFormatVersion = 2
    minorTrainFormatVersion = 1
    pulseCount = _PULSES
    reserved = np.ones(16, dtype=np.uint8)
    trainId = tid
    
    gen[source]['header.dataId'] = dataId
    gen[source]['header.kinkId'] = linkId
    gen[source]['header.magicNumberBegin'] = magicNumberBegin
    gen[source]['header.majorTrainFormatVersion'] = majorTrainFormatVersion
    gen[source]['header.minorTrainFormatVersion'] = minorTrainFormatVersion
    gen[source]['header.pulseCount'] = pulseCount
    gen[source]['header.reserved'] = reserved
    
    return gen
    
    
def generate(source, queue):
    while True:
        if len(queue) < queue.maxlen:
            data = gen_combined_detector_data(source)
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
    port = 4600
    main(source, port)
