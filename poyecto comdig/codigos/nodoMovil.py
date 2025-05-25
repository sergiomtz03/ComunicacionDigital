import sys
import struct
import utime
from machine import Pin, SPI, I2C
from nrf24l01 import NRF24L01
from micropython import const
from ssd1306 import SSD1306_I2C
from mpu6050 import MPU6050

POWER = {"0 dBm": const(0x06), "-6 dBm": const(0x04), "-12 dBm": const(0x02), "-18 dBm": const(0x00)}
DATA_RATE = {"250 kbps": const(0x20), "1 Mbps": const(0x00), "2 Mbps": const(0x08),}
SAMPLE_INTERVAL = 1000

i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=200000)
mpu = MPU6050(i2c)

spi = SPI(0, sck=Pin(2), mosi=Pin(3), miso=Pin(4))
cfg = {"spi": spi, "csn": 5, "ce": 6}

csn = Pin(cfg["csn"], mode=Pin.OUT, value=1)
ce = Pin(cfg["ce"], mode=Pin.OUT, value=0)
spi = cfg["spi"]

nrf = NRF24L01(spi, csn, ce, channel = 100, payload_size=16)
nrf.set_power_speed(POWER["0 dBm"], DATA_RATE["2 Mbps"])

nrf.open_tx_pipe(b'4Node')

last_sample_time = utime.ticks_ms()
current_data = {'accel': {'x': 0, 'y': 0, 'z': 0}, 
                'gyro': {'x': 0, 'y': 0, 'z': 0}}
def get_sensor_data():
    """Lee y retorna los datos actuales de los sensores"""
    return {
        'accel': mpu.get_accel_data(),
        'gyro': mpu.get_gyro_data()
    }
while True:
    current_time = utime.ticks_ms()
    # Tomar nueva muestra cada 2 segundos
    if utime.ticks_diff(current_time, last_sample_time) >= SAMPLE_INTERVAL:
        current_data = get_sensor_data()
        last_sample_time = current_time
        print("\n--- Nueva muestra tomada ---")
        print(f"Aceleración: X={current_data['accel']['x']:.2f}, Y={current_data['accel']['y']:.2f}, Z={current_data['accel']['z']:.2f}")
        print(f"Giroscopio: X={current_data['gyro']['x']:.2f}, Y={current_data['gyro']['y']:.2f}, Z={current_data['gyro']['z']:.2f}")
    try:
        nrf.stop_listening()
        nrf.send(struct.pack("fff", round(current_data['gyro']['x'], 2), round(current_data['gyro']['y'], 2), round(current_data['gyro']['z'], 2)))
    except OSError as e:
        pass

