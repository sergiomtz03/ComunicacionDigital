from machine import Pin, UART
import utime

# Configuración del LED
led = Pin(2, Pin.OUT)  # LED integrado en la Raspberry Pi Pico (GPIO 25)
# Configuración de UART
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))  # UART0, TX=GP0, RX=GP1
i = 1
while True:
    if uart.any():
        received_data = uart.read(1)
        print(f"Carácter recibido: {received_data.decode()}")
        uart.write('B')
        led.on()
        utime.sleep(4)
        led.off()
        utime.sleep(1)
        i += 1
        with open('recibidos.txt', 'a') as archivo:
            archivo.write(f"{i}\n")
        