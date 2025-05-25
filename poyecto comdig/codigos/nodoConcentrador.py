import random
import sys
import struct
import utime
from machine import I2C, Pin
from machine import Pin, SPI, SoftSPI
from nrf24l01 import NRF24L01
from micropython import const

POWER = {"0 dBm": const(0x06), "-6 dBm": const(0x04), "-12 dBm": const(0x02), "-18 dBm": const(0x00)}
DATA_RATE = {"250 kbps": const(0x20), "1 Mbps": const(0x00), "2 Mbps": const(0x08),}

SSID = "Sergio"
PASSWORD = "sergio123"

i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)
spi = SPI(0, sck=Pin(2), mosi=Pin(3), miso=Pin(4))
cfg = {"spi": spi, "csn": 5, "ce": 6}

csn = Pin(cfg["csn"], mode=Pin.OUT, value=1)
ce = Pin(cfg["ce"], mode=Pin.OUT, value=0)
spi = cfg["spi"]

nrf = NRF24L01(spi, csn, ce, channel = 100, payload_size=16)
nrf.set_power_speed(POWER["-12 dBm"], DATA_RATE["2 Mbps"])

nrf.open_rx_pipe(1, b'1Node')
nrf.open_rx_pipe(2, b'2Node')
nrf.open_rx_pipe(3, b'3Node')
nrf.open_rx_pipe(4, b'4Node')

interval = 5
avg1 = []
avg2 = []
avg3 = []
avg4 = []

def leer_pipe():
    STATUS = 0x07
    status = nrf.reg_read(STATUS)
    pipe_num = (status >> 1) & 0x07
    return pipe_num

while True:
    nrf.start_listening()
    if nrf.any():
        pipe = leer_pipe()
        if pipe == 1:
            data = struct.unpack("i", nrf.recv())
            avg1.append(data[0])
            if(len(avg1) == interval):
                avg = sum(avg1) / len(avg1)
                avg1 = []
                print(str(pipe) + str(avg))
        if pipe == 2:
            data = struct.unpack("i", nrf.recv())
            avg2.append(data[0])
            if(len(avg2) == interval):
                avg = sum(avg2) / len(avg2)
                avg2 = []
                print(str(pipe) + str(avg))
        if pipe == 3:
            data = struct.unpack("i", nrf.recv())
            avg3.append(data[0])
            if(len(avg3) == interval):
                avg = sum(avg3) / len(avg3)
                avg3 = []
                print(str(pipe) + str(avg))
        if pipe == 4:
            gyro_x, gyro_y, gyro_z= struct.unpack('fff', nrf.recv())
            print(pipe, gyro_x, gyro_y, gyro_z)
