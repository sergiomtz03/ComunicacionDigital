import network
import sys
import struct
import utime
from machine import Pin, SPI, I2C
from nrf24l01 import NRF24L01
from micropython import const
from ssd1306 import SSD1306_I2C

POWER = {"0 dBm": const(0x06), "-6 dBm": const(0x04), "-12 dBm": const(0x02), "-18 dBm": const(0x00)}
DATA_RATE = {"250 kbps": const(0x20), "1 Mbps": const(0x00), "2 Mbps": const(0x08),}
SSID = "Sergio"
PASSWORD = "sergio123"

WIDTH = 128
HEIGHT = 32

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=200000)
oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)

spi = SPI(0, sck=Pin(2), mosi=Pin(3), miso=Pin(4))
cfg = {"spi": spi, "csn": 5, "ce": 6}

csn = Pin(cfg["csn"], mode=Pin.OUT, value=1)
ce = Pin(cfg["ce"], mode=Pin.OUT, value=0)
spi = cfg["spi"]

nrf = NRF24L01(spi, csn, ce, channel = 100, payload_size=8)
nrf.set_power_speed(POWER["0 dBm"], DATA_RATE["2 Mbps"])

nrf.open_tx_pipe(b'3Node')

wifi = network.WLAN(network.STA_IF)
wifi.active(True)

def wifi_connect():
    while not wifi.isconnected():
        wifi.connect(SSID, PASSWORD)
        utime.sleep(3)
        oled.invert(True)
        oled.fill(0)
        oled.text("Connection Lost", 4, 12)
        oled.show()
    print("WiFi conectado! IP:", wifi.ifconfig()[0])

# Variables para control de tiempo
last_oled_update = utime.ticks_ms()
OLED_UPDATE_INTERVAL = 2000  # 2 segundos

wifi_connect()

while True:
    current_time = utime.ticks_ms()
    
    # Actualizar OLED cada 2 segundos (sin bloquear el loop)
    if utime.ticks_diff(current_time, last_oled_update) >= OLED_UPDATE_INTERVAL:
        oled.invert(True)
        oled.fill(0)
        oled.text("Node 2", 40, 2)
        oled.text("RSSI:", 10, 15)
        oled.text(f"{wifi.status('rssi')} dBm", 50, 15)
        oled.show()
        last_oled_update = current_time
    
    # Transmisión continua del NRF (sin delays)
    if wifi.isconnected():
        try:
            nrf.stop_listening()
            rssi = wifi.status('rssi')
            nrf.send(struct.pack("i", rssi))
            print("Enviado:", rssi)
        except OSError as e:
            print("Error NRF:", e)
    else:
        print("WiFi desconectado!")
        wifi_connect()
    
    utime.sleep_ms(10)  # Pausa mínima para evitar saturación
