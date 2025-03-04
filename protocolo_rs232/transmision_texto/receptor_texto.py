from machine import UART, Pin
import time
uart = UART(0, baudrate=3000000, tx=Pin(16), rx=Pin(17))

filename = "dataR.txt"

with open(filename, "w") as file:
    print("Esperando datos...")
    while True:
        if uart.any():
            data = uart.read()
            file.write(data)
            print(f"Recibido: {data.strip()}")