import numpy
import zmq
import msgpack
import msgpack_numpy
msgpack_numpy.patch()
import time
import pickle
from threading import Thread

loud = False

SOURCE = "tcp://10.253.0.52:4700"
OUTPUT_PORT = 4700
# exflonc09: 10.253.0.67
# exflonc11: 10.253.0.69
OUTPUT = "tcp://10.253.0.69:%i" % OUTPUT_PORT
#OUTPUT = 'tcp://*:{}'.format(OUTPUT_PORT)

print("Source socket: %s" % SOURCE)
print("Output socket: %s" % OUTPUT)

recv_context = zmq.Context()
recv_request = recv_context.socket(zmq.REQ)
recv_request.connect(SOURCE)
data_container = {
    'injposX': None,
    'injposY': None,
    'injposZ': None,
    'xgm_xtd2': None,
    'xgm_xtd9': None,
    'cam_ehc_scr': None,
    'cam_inline': None,
    'cam_ehd_ibs': None,
}

_counter = 0
def fill_data_into_container(data):
    global _counter
    print("(%i)" % _counter)
    _counter += 1
    #print(data.keys())
    # Injector motors
    #data_key = 'encoderPosition'
    data_key = 'actualPosition'
    try:
        injposx = data['SPB_IRU_INJMOV/MOTOR/X'][data_key]
        data_container['injposX'] = injposx
        if loud: print("x=%f" % injposx)
    except:
        print("No injector motor X in the data")
    try:
        injposy = data['SPB_IRU_INJMOV/MOTOR/Y'][data_key]
        data_container['injposY'] = injposy
        if loud: print("y=%f" % injposy)
    except:
        print("No injector motor Y in the data")
    try:
        injposz = data['SPB_IRU_INJMOV/MOTOR/Z'][data_key]
        data_container['injposZ'] = injposz
        if loud: print("z=%f" % injposz)
    except:
        print("No injector motor Z in the data")
    # GMD
    try:
        xgm_xtd2 = data['SA1_XTD2_XGM/XGM/DOOCS']['pulseEnergy.pulseEnergy'] # in uJ
        data_container['xgm_xtd2'] = xgm_xtd2
        if loud: print("XGM_XTD2 = %f uJ" % xgm_xtd2)
    except:
        print("No XGM_XTD2 in the data.")
    try:
        xgm_xtd9 = data['SPB_XTD9_XGM/XGM/DOOCS']['pulseEnergy.pulseEnergy'] # in uJ
        data_container['xgm_xtd9'] = xgm_xtd9
        if loud: print("XGM_XTD9 = %f uJ" % xgm_xtd9)
    except:
        print("No XGM_XTD9 in the data.")
    # Cameras
    try:
        im = data['SPB_IRU_INLINEMIC_CAM:daqOutput']['data.image']['Data']
        data_container['cam_inline'] = im
    except:
        print("No inline microscope data.")
    try:
        im = data['SPB_EHC_SCR:daqOutput']['data.image']['Data']
        data_container['cam_ehc_scr'] = im
    except:
        print("No EHC_SCR camera data.")
    try:
        im = data['SPB_EHD_IBS:daqOutput']['data.image']['Data']
        data_container['cam_ehd_ibs'] = im
    except:
        print("No EHD_IBS camera data.")

def recv_data(recv_request, data_container):
    while(True):
        if loud: print("recv", data_container.keys())
        recv_request.send(b"next")
        msg = recv_request.recv()
        data = msgpack.loads(msg)
        fill_data_into_container(data)
        time.sleep(0.1)

send_context = zmq.Context()
send_socket = send_context.socket(zmq.REP)
send_socket.bind(OUTPUT)

t = Thread(target=recv_data, args=(recv_request, data_container))
t.start()

while True:
    msg = send_socket.recv()
    if msg == b'next':
        if loud: print("send", data_container.keys())
        send_socket.send(msgpack.dumps(data_container))
    else:
        print('WARNING: wrong request')
        break
