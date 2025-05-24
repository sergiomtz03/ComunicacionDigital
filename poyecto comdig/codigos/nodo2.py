import network
import sys
import struct
import utime
from machine import Pin, SPI, SoftSPI
from nrf24l01 import NRF24L01
from micropython import const

POWER = {"0 dBm": const(0x06), "-6 dBm": const(0x04), "-12 dBm": const(0x02), "-18 dBm": const(0x00)}
DATA_RATE = {"250 kbps": const(0x20), "1 Mbps": const(0x00), "2 Mbps": const(0x08),}
SSID = "Sergio"
PASSWORD = "sergio123"

spi = SPI(0, sck=Pin(2), mosi=Pin(3), miso=Pin(4))
cfg = {"spi": spi, "csn": 5, "ce": 6}

csn = Pin(cfg["csn"], mode=Pin.OUT, value=1)
ce = Pin(cfg["ce"], mode=Pin.OUT, value=0)
spi = cfg["spi"]

nrf = NRF24L01(spi, csn, ce, channel = 100, payload_size=8)
nrf.set_power_speed(POWER["0 dBm"], DATA_RATE["2 Mbps"])

nrf.open_tx_pipe(b'2Node')

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
def wifiStatus():
    while wifi.isconnected() == False:
        wifi.connect(SSID, PASSWORD)
        utime.sleep(3)
    print("Conexión establecida!")
    print("Dirección IP:", wifi.ifconfig()[0])
    
while True:
    if wifi.isconnected() == False:
        print("Conexión perdida!")
        wifiStatus()
    nrf.stop_listening()
    print(wifi.status('rssi'))
    try:
        nrf.send(struct.pack("i", wifi.status('rssi')))
    except OSError:
        pass
