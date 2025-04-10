import usys
import ustruct as struct
import network
import time
import math
from machine import Pin, I2C, SPI
from ssd1306 import SSD1306_I2C
from nrf24l01 import NRF24L01
from micropython import const

WIDTH = 128
HEIGHT = 32
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=200000)
oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)

POWER = {"0 dBm": const(0x06), "-6 dBm": const(0x04), "-12 dBm": const(0x02), "-18 dBm": const(0x00)}
DATA_RATE = {"250 kbps": const(0x20), "1 Mbps": const(0x00), "2 Mbps": const(0x08),}
CH_FREQ = 121 # FRECUENCIA DEL CANAL 121: 2521 MHz
button = Pin(20, Pin.IN, Pin.PULL_UP)
ledAdvance = Pin(11, Pin.OUT)
ledMeasure = Pin(12, Pin.OUT)
ledDisc = Pin(13, Pin.OUT)
cfg = {"spi": 0, "miso": 16, "mosi": 19, "sck": 18, "csn": 5, "ce": 17}
csn = Pin(cfg["csn"], mode=Pin.OUT, value=1)
ce = Pin(cfg["ce"], mode=Pin.OUT, value=0)

nrf = NRF24L01(SPI(cfg["spi"]), csn, ce,channel = CH_FREQ, payload_size=32)

############################################
# CONFIGURACION DE POTENCIA Y TASA DE BITS #
############################################
potencia = POWER["0 dBm"] # 0 dBm, -6 dBm, -12 dBm, -18 dBm
tasaDeBits = DATA_RATE["1 Mbps"] # 250 kbps, 1 Mbps, 2 Mbps

nrf.set_power_speed(potencia, tasaDeBits)

pipes = (b"\xe1\xf0\xf0\xf0\xf0", b"\xd2\xf0\xf0\xf0\xf0")
nrf.open_tx_pipe(pipes[0])
nrf.open_rx_pipe(1, pipes[1])
nrf.start_listening()

linkStatus = True
j = 0
counter = -1
filename = "rssi_measurements.txt"
with open(filename, 'a') as file:
    file.write("Distance(m)\tAverageRSSI(dBm)\tStandard_deviation\n")

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
ssid = "Sergio"
password = "sergio123"

def buttonAnimation():
    ledAdvance.value(1)
    if not counter == -1:
        oled.invert(True)
        oled.fill(0)
        oled.text("PRESS BUTTON", 18, 8)
        oled.show()
    for x in range(6):
        oled.fill_rect(37, 19, 51, 12, 0)
        for i in range(3):
            oled.text("-", 40 + i, 26)
        for i in range(8 - x):
            oled.text(".", 46, 23 - i)    
        for i in range(18):
            oled.text("-", 49 + i, 18 + x)
        for i in range(8 - x):
            oled.text(".", 70, 23 - i)
        for i in range(3):
            oled.text("-", 73 + i, 26)
        oled.show()
    
    for i in range(3):
        oled.text(".", 35 + 3 * i, 17 + i)
        oled.text(".", 68 - 2 * i, 14 + i)
        oled.text(".", 49 + 2 * i, 14 + i)
        oled.text(".", 81 - 3 * i, 17 + i)
        oled.show()
    time.sleep(0.1)
    ledAdvance.value(0)
    time.sleep(0.2)
    oled.fill_rect(37, 19, 51, 12, 0)
    for i in range(3):
        oled.text("-", 40 + i, 26)
    for i in range(8):
        oled.text(".", 46, 23 - i)    
    for i in range(18):
        oled.text("-", 49 + i, 18)
    for i in range(8):
        oled.text(".", 70, 23 - i)
    for i in range(3):
            oled.text("-", 73 + i, 26)
    oled.show()
def standardDeviation(data):
    n = len(data)
    median = sum(data) / n
    variance = sum((x - median) ** 2 for x in data) / (n - 1)
    return math.sqrt(variance)

def wifiStatus():
    counter = 0
    while wifi.isconnected() == False:
        ledAdvance.value(0)
        ledMeasure.value(0)
        oled.invert(True)
        oled.fill(0)                
        oled.text("Connection Lost", 4, 12)
        oled.fill_rect(48, 20, 28, 4, 0)
        oled.show()
        ledDisc(1)
        for i in range(5):
            oled.text(".", 48 + 5 * i, 17)
            time.sleep(0.2)
            oled.show()
            if i == 4:
                ledDisc.value(0)
                time.sleep(0.2)
        time.sleep(0.8)
        counter += 1
        if counter == 3:
            wifi.connect(ssid, password)
    print("Conexión establecida!")
    print("Dirección IP:", wifi.ifconfig()[0])
    oled.invert(True)
    oled.fill(0)
    oled.text("Connection Up", 12, 10)
    oled.show()
    time.sleep(2)
    oled.fill(0)
    
wifi.connect(ssid, password)
wifiStatus()

while True:
    ledDisc.value(0)
    ledMeasure.value(0)
    if counter == -1:
        oled.fill(0)
        oled.text("Connection Up", 12, 10)
        oled.show()
    buttonAnimation()
    if wifi.isconnected() == False:
        print("Conexión perdida!")
        wifi.connect(ssid, password)
        wifiStatus()
    if button.value() == 1:
        counter += 1
        oled.fill(0)
        oled.text("MEASURE", 36, 11)
        oled.text("#" + str(counter + 1), 58, 20)
        oled.show()
        while button.value() == 1:
            time.sleep(0.1)
        time.sleep(0.1)
        print(counter)
        if counter >= 0:
            ledMeasure.value(1)
            oled.invert(True)
            oled.fill(0)
            rssiMeasureArray = []
            for i in range(200):
                rssiMeasure = wifi.status('rssi')
                rssiMeasureArray.append(rssiMeasure)
                oled.text("ON", 5, 2)
                time.sleep(0.1)
                oled.text("MEASURING", 28, 11)
                oled.fill_rect(100, -5, 20, 15, 0)
                if rssiMeasure >= -60:
                    for b in range(7):
                        oled.text(".", 115, -5 + b)
                if rssiMeasure > -80:
                    for b in range(5):
                        oled.text(".", 112, -3 + b)
                if rssiMeasure >= -95:
                    for b in range(3):
                        oled.text(".", 109, -1 + b)
                if rssiMeasure >= -105:
                    for b in range(1):
                        oled.text(".", 106, 1 + b)
                if rssiMeasure <= -115 or rssiMeasure == 0.0:
                    oled.fill_rect(100, -5, 20, 15, 0)
                    for b in range(5):
                        oled.text(".", 110 + 2 * b, -3 + b)
                    for b in range(5):
                        oled.text(".", 118 - 2 * b, -3 + b)
                for x in range(99):
                    oled.text("-", 10 + x, 17)
                    oled.text("-", 10 + x, 19)
                if i % 2 == 0:
                    nrf.stop_listening()
                    print("sending:", rssiMeasure)
                    try:
                        nrf.send(struct.pack("f", rssiMeasure))
                    except OSError:
                        pass
                    nrf.start_listening()
                    j += 1
                    oled.text(".", 8 + j, 16)
                    oled.fill_rect(36, 2, 55, 7, 0)
                    oled.text(str(rssiMeasure) + " dBm", 35, 2)
                    oled.show()
                for x in range(j):
                    oled.text(".", 8 + x, 16)
                if i % 5 == 0:
                    oled.fill_rect(50, 25, 80, 7, 0)
                    oled.text(str(i) + "/200", 60, 25)
                if i % 10 == 0:
                    oled.fill_rect(5, 25, 40, 7, 0)
                    oled.text(str(i / 10) + "s", 5, 25)
                    oled.show()
                if i == 199:
                    oled.fill_rect(5, 25, 40, 7, 0)
                    oled.fill_rect(50, 25, 80, 7, 0)
                    oled.text(".", 109, 16)
                    oled.text("200/200", 60, 25)
                    oled.text("20.0s", 5, 25)
                    oled.show()
                    j = 0
                    time.sleep(2)
                    ledMeasure(0)
                if rssiMeasure == 0.0:
                    linkStatus = False
                    print("Conexión perdida!")
                    oled.fill_rect(5, 2, 20, 7, 0)
                    oled.fill_rect(36, 2, 55, 7, 0)
                    oled.text(str(rssiMeasure) + " dBm", 45, 2)
                    oled.text("OFF", 5, 2)
                    oled.show()
                    time.sleep(2)
                    oled.fill(0)
                    wifi.connect(ssid, password)
                    wifiStatus()
            rssiAverage = sum(rssiMeasureArray) / len(rssiMeasureArray)
            deviation = standardDeviation(rssiMeasureArray)
            if linkStatus == True:
                oled.invert(True)
                oled.fill(0)
                oled.text("Dist: " + str(counter) + " m", 4, 20)
                oled.text("Dev: " + str(round(deviation, 3)), 4, 11)
                oled.text("Avg: " + str(round(rssiAverage,2)) + " dBm", 4, 2)
                oled.text("#" + str(counter + 1), 105, 25)
                oled.show()
                time.sleep(4)
                oled.fill(0)
                oled.text("SAVING DATA", 20, 11)
                for i in range(24):
                    oled.text(".", 14 + 4 * i, 3)
                    oled.show()
                    time.sleep(0.02)
                for i in range(4):
                    oled.text(".", 107, 3 + 3 * i)
                    oled.show()
                    time.sleep(0.02)
                for i in range(24):
                    oled.text(".", 107 - 4 * i, 15)
                    oled.show()
                    time.sleep(0.02)
                for i in range(4):
                    oled.text(".", 14, 15 - 3 * i)
                    oled.show()
                    time.sleep(0.02)
                with open(filename, "a") as file:
                    file.write("{}\t{:.3f}\t{:.2f}\n".format(counter, rssiAverage, deviation))
                time.sleep(0.2)
                oled.fill(0)
                oled.text("PRESS BUTTON", 18, 8)
                oled.show()
            else:
                oled.invert(True)
                oled.fill(0)
                oled.text("DISCARDING", 24, 11)
                for i in range(24):
                    oled.text(".", 14 + 4 * i, 3)
                    oled.show()
                    time.sleep(0.02)
                for i in range(4):
                    oled.text(".", 107, 3 + 3 * i)
                    oled.show()
                    time.sleep(0.02)
                for i in range(24):
                    oled.text(".", 107 - 4 * i, 15)
                    oled.show()
                    time.sleep(0.02)
                for i in range(4):
                    oled.text(".", 14, 15 - 3 * i)
                    oled.show()
                    time.sleep(0.02)
                counter -= 1
                linkStatus = True
                time.sleep(0.2)
                oled.invert(True)
                oled.fill(0)
                oled.text("PRESS BUTTON", 18, 8)
                oled.show()
