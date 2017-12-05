import socket
import os

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('localhost',19999))
s.listen(5)

while True:
    (cs, addr) = s.accept()
    while True:
	msg = cs.recv(1000)
	if msg == '':
	   raise RuntimeError
	else:
	   #print("SOUND")
	   #os.system("aplay %s" %('glass.wav'))
	   os.system("aplay %s" %('beamline.wav'))
	
