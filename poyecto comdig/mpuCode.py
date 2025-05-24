from machine import I2C, Pin
import time
from mpu6050 import MPU6050

# Configuración I2C (pines por defecto en Raspberry Pi Pico)
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)

# Inicialización de sensores
mpu = MPU6050(i2c)

# Bucle principal
while True:
    # Lectura MPU6050
    accel = mpu.get_accel_data()
    gyro = mpu.get_gyro_data()
    temp_mpu = mpu.get_temp()

    # Mostrar datos
    print("\n--- MPU6050 ---")
    print(f"Aceleración (g): X={accel['x']:.2f}, Y={accel['y']:.2f}, Z={accel['z']:.2f}")
    print(f"Giroscopio (°/s): X={gyro['x']:.2f}, Y={gyro['y']:.2f}, Z={gyro['z']:.2f}")
    print(f"Temperatura MPU: {temp_mpu:.2f} °C")
    
    time.sleep(1)
