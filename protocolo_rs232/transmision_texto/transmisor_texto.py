from machine import UART, Pin
import time
start = time.ticks_ms()
uart = UART(0, baudrate=3000000, tx=Pin(0), rx=Pin(1))

filename = "data.txt"
with open(filename, "r") as file:
    print(f"Enviando archivo: {filename}")
    for line in file:
        uart.write(line)
        print(f"Enviado: {line.strip()}")
print("Archivo enviado con éxito.")

stop = time.ticks_ms()
execution_time = time.ticks_diff(stop, start)

print(f"Data transmitted in {execution_time:.3f} miliseconds.")