from machine import Pin, UART
import utime

led_received = Pin(2, Pin.OUT)
led_send = Pin(18, Pin.OUT) 

uart = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
 
while True:
    uart.write('A')
    led_send.on()
    if uart.any():
        data_received = uart.read(1)
        print(f"Caracter recibido: {data_received.decode()}")
        led_received.on()
    utime.sleep(0.1)
    led_send.off()
    led_received.off()
    utime.sleep(0.1)