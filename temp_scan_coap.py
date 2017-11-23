from CBOR import CBOR
from machine import  I2C
from BMP280 import BMP280
import time
from network import LoRa
import pycom
import socket
import binascii
import pycom
import CoAP


i2c = I2C(0, I2C.MASTER, baudrate=100000)
print(i2c.scan())

pycom.heartbeat(False)

lora = LoRa(mode=LoRa.LORAWAN)
for i in range (0,  255):
    led = i<< 16| i <<8  | i
    pycom.rgbled(led)
    time.sleep(0.01)

# join a network using OTAA (Over the Air Activation)
app_eui = binascii.unhexlify('00 00 00 00 00 00 00 00'.replace(' ',''))
app_key = binascii.unhexlify('11 22 33 44 55 66 77 88 11 22 33 44 55 66 77 88'.replace(' ',''))

lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key),  timeout=0)

# wait until the module has joined the network
while not lora.has_joined():
    time.sleep(2.5)
    print('Not yet joined...')


for i in range (0,  255):
    led = (255-i) << 16| (255-i)  <<8  | i
    pycom.rgbled(led)
    time.sleep(0.01)

s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)
s.setsockopt(socket.SOL_LORA,  socket.SO_CONFIRMED,  False)

bmp = BMP280(i2c)

(rp,  p,  t) = bmp.getValue(0)
oldT = int(t*100)
temp_record = CBOR([CBOR(oldT)])

MAX_FRAME = 20

while True:
    (rp,  p,  t) = bmp.getValue(0)
    t100 = int(t*100)

    deltaT =  t100 -oldT
    d = CBOR (deltaT)

    print (deltaT)
    if ((temp_record.length() + d.length()) < MAX_FRAME):
        temp_record.addList(d)
        temp_record.dump()
    else:
        print ("Sending CoAP")
        CoAPMsg = CoAP.Message()
        CoAPMsg.new_header(type=CoAP.CON,  code=CoAP.POST, midSize=4,  token=0x82)
        CoAPMsg.add_option_path('foo')
        CoAPMsg.add_option_content(60) #CBOR
        CoAPMsg.end_option()
        CoAPMsg.add_value(temp_record)


        s.setblocking(True)
        s.settimeout(10)

        try:
            s.send (CoAPMsg.buffer)
            print(CoAPMsg.buffer);
            temp_record = CBOR([CBOR(t100)])
        except:
            print("error in sending")

        try:
            data = s.recv(64)
            print ("received ", data)
            recvData = True
        except:
            print("no data")
            recvData = False

        if (recvData):
            rcv_type = (data[0] & 0x30) >> 4
            rcv_mid  = (data[2] << 8 + data[3])



    time.sleep(10)
    oldT = t100
