#################                SLAVE                 ###################
import usys
import ustruct as struct
import time
import math
import utime
from sh1106 import SH1106_I2C  
from machine import Pin, I2C, SPI
from nrf24l01 import NRF24L01
from micropython import const

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
ANCHO = 128
ALTO = 64

oled = SH1106_I2C(ANCHO, ALTO, i2c, addr=0x3C, rotate=180)
oled.contrast(255)
oled.fill(1)
POWER = {"0 dBm": const(0x06), "-6 dBm": const(0x04), "-12 dBm": const(0x02), "-18 dBm": const(0x00)}
DATA_RATE = {"250 kbps": const(0x20), "1 Mbps": const(0x00), "2 Mbps": const(0x08),}
CH_FREQ = 121 # FRECUENCIA DEL CANAL 121: 2521 MHz

cfg = {"spi": 0, "miso": 16, "mosi": 19, "sck": 18, "csn": 5, "ce": 17}
csn = Pin(cfg["csn"], mode=Pin.OUT, value=1)
ce = Pin(cfg["ce"], mode=Pin.OUT, value=0)

nrf = NRF24L01(SPI(cfg["spi"]), csn, ce, channel = CH_FREQ, payload_size=32)

############################################
# CONFIGURACION DE POTENCIA Y TASA DE BITS #
############################################

potencia = POWER["0 dBm"] # 0 dBm, -6 dBm, -12 dBm, -18 dBm
tasaDeBits = DATA_RATE["2 Mbps"] # 250 kbps, 1 Mbps, 2 Mbps

nrf.set_power_speed(potencia, tasaDeBits)

pipes = (b"\xe1\xf0\xf0\xf0\xf0", b"\xd2\xf0\xf0\xf0\xf0")
nrf.open_tx_pipe(pipes[1])
nrf.open_rx_pipe(1, pipes[0])
nrf.start_listening()


