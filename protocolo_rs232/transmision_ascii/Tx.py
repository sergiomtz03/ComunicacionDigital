from machine import Pin, UART
import utime

# Configuración del LED
led = Pin(2, Pin.OUT)  # LED integrado en la Raspberry Pi Pico (GPIO 25)

# Configuración de UART
uart = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))  # UART0, TX=GP0, RX=GP1

while True:
    uart.write('A')
    utime.sleep(0.1)
    if uart.any():
        received_data = uart.read(1)
        print(f"Carácter recibido: {received_data.decode()}")
        for i in range(3):
                led.on()
                utime.sleep(0.5)
                led.off()
                utime.sleep(0.5)
                if i == 1:
                    uart.write('A')
                if i == 2:
                    utime.sleep(1)
