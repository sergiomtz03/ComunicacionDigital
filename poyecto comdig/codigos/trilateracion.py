import serial
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque
import math

# Configuración de visualización
WINDOW_SIZE = 20  # Muestra últimos 60 puntos (~6 segundos con interval=100)
MAX_HISTORY = 50  # Máximo de puntos en memoria

# Configuración del puerto serial
port = 'COM8'
baudrate = 9600

# Variables globales para almacenar los valores RSSI
node1 = 0
node2 = 0
node3 = 0
gyro_x = 0
gyro_y = 0
gyro_z = 0

# Posiciones de los 3 nodos fijos (beacons) en metros - Triángulo equilátero recomendado
beacons = [
    {"x": 0, "y": 0, "name": "Nodo 1"},
    {"x": 50, "y": 0, "name": "Nodo 2"},
    {"x": 25, "y": 4, "name": "Nodo 3"}  # Altura triángulo equilátero: √3/2 * lado
]

freq_mhz = 2400
# Historial de datos
time_history = deque(maxlen=MAX_HISTORY)
rssi_history = [deque(maxlen=MAX_HISTORY) for _ in range(3)]
distance_history = [deque(maxlen=MAX_HISTORY) for _ in range(3)]
position_history = {'x': deque(maxlen=MAX_HISTORY), 'y': deque(maxlen=MAX_HISTORY)}
gyro_history = [deque(maxlen=MAX_HISTORY) for _ in range(3)]

# Configuración de la gráfica principal
plt.style.use('default')
fig = plt.figure(figsize=(15, 10))
gs = fig.add_gridspec(4, 2)
ax_main = fig.add_subplot(gs[0:2, 0:2])  # Gráfica principal
ax_rssi = fig.add_subplot(gs[2, 0])     # Subgráfica RSSI
ax_dist = fig.add_subplot(gs[2, 1])     # Subgráfica distancias
ax_gyro = fig.add_subplot(gs[3, 0])
ax_rssi_node1 = fig.add_subplot(gs[3, 1])
# Configuración de la gráfica principal
ax_main.set_xlim(-2, 52)
ax_main.set_ylim(-2, 6)
ax_main.set_xlabel('Coordenada X (metros)')
ax_main.set_ylabel('Coordenada Y (metros)')
ax_main.set_title('Sistema de Localización con 3 Nodos (Espacio Libre)')
ax_main.grid(True)

# Elementos gráficos
scatter = ax_main.scatter([], [], color='blue', s=100, label='Nodo Móvil')
lines = [ax_main.plot([], [], 'k--', alpha=0.5)[0] for _ in beacons]

# Dibujar nodos fijos (solo una etiqueta en la leyenda)
for i, beacon in enumerate(beacons):
    if i == 0:
        ax_main.scatter(beacon["x"], beacon["y"], color='red', s=100, label='Nodos Fijos')
    else:
        ax_main.scatter(beacon["x"], beacon["y"], color='red', s=100)
    ax_main.text(beacon["x"] + 0.3, beacon["y"] + 0.3, beacon["name"], fontsize=10)

# Configurar leyenda principal
ax_main.legend(loc='upper left', bbox_to_anchor=(0, 1), frameon=True, fancybox=True)

# Configuración de subgráficas
ax_rssi.set_title('Valores RSSI en Tiempo Real')
ax_rssi.set_ylabel('RSSI (dBm)')
ax_rssi.grid(True)
rssi_lines = [ax_rssi.plot([], [], label=f'Nodo {i+1}')[0] for i in range(3)]
ax_rssi.legend(loc='upper right', bbox_to_anchor=(1, 1), ncol=1, frameon=True)

ax_gyro.set_title('Datos del Giroscopio (X, Y, Z)')
ax_gyro.set_xlabel('Tiempo')
ax_gyro.set_ylabel('Velocidad angular (°/s)')
ax_gyro.grid(True)
gyro_lines = [
    ax_gyro.plot([], [], label='Eje X')[0],
    ax_gyro.plot([], [], label='Eje Y')[0],
    ax_gyro.plot([], [], label='Eje Z')[0]
]
ax_gyro.legend(loc='upper right')

ax_rssi_node1.set_title('RSSI Nodo 1')
ax_rssi_node1.set_xlabel('Tiempo')
ax_rssi_node1.set_ylabel('RSSI (dBm)')
ax_rssi_node1.grid(True)
rssi_node1_line = ax_rssi_node1.plot([], [], 'r-', label='RSSI Nodo 1')[0]
ax_rssi_node1.legend(loc='upper right')

ax_dist.set_title('Distancias Estimadas')
ax_dist.set_ylabel('Distancia')
ax_dist.grid(True)
dist_lines = [ax_dist.plot([], [], label=f'Dist a Nodo {i+1}')[0] for i in range(3)]
ax_dist.legend(loc='upper right', bbox_to_anchor=(1, 1), ncol=1, frameon=True)

def fspl_to_distance(rssi, tx_power=0):
    """
    Convierte RSSI a distancia usando el modelo FSPL
    """
    d = 10 ** ((-6 + tx_power-rssi+27.56-20*math.log10(freq_mhz))/20)
    return d

def trilaterate(rssi_values, beacons, tx_power=0):
    """
    Trilateración usando las ecuaciones del diagrama
    rssi_values: [RSSI_P1, RSSI_P2, RSSI_P3]
    beacons: Lista con las posiciones de los nodos
    """
    # Obtener distancias usando FSPL
    r1 = fspl_to_distance(rssi_values[0], tx_power)
    r2 = fspl_to_distance(rssi_values[1], tx_power)
    r3 = fspl_to_distance(rssi_values[2], tx_power)
    # Parámetros geométricos
    d = math.sqrt((beacons[1]["x"] - beacons[0]["x"])**2 + 
                 (beacons[1]["y"] - beacons[0]["y"])**2)
    i = beacons[2]["x"]
    j = beacons[2]["y"]
    
    # Calcular posición (X,Y) según las ecuaciones
    X = (r1**2 - r2**2 + d**2) / (2 * d)
    Y_numerator = r1**2 - r3**2 - X**2 + (X - i)**2 + j**2
    Y = Y_numerator / (2 * j)
    print(r1, r2, r3)
    print(X,Y)
    return X, Y, [r1, r2, r3]

def update(frame):
    global node1, node2, node3, gyro_x, gyro_y, gyro_z
    
    try:
        if ser.in_waiting > 0:
            data = ser.readline().decode('utf-8', errors='ignore').strip()
            if len(data) > 0:
                pipe = data[0]
                if pipe == '1':
                    node1 = float(data[1:])
                elif pipe == '2':
                    node2 = float(data[1:])
                elif pipe == '3':
                    node3 = float(data[1:])
                elif pipe == '4':
                    parts = data.split()
                    if len(parts) >= 4:
                        gyro_x = float(parts[1])
                        gyro_y = float(parts[2])
                        gyro_z = float(parts[3])
                        gyro_history[0].append(gyro_x)
                        gyro_history[1].append(gyro_y)
                        gyro_history[2].append(gyro_z)
                
                # Solo procesar si tenemos datos de los 3 nodos
                if node1 and node2 and node3:
                    x, y, distances = trilaterate([node1, node2, node3], beacons)
                    
                    # Actualizar historiales
                    time_history.append(frame)
                    position_history['x'].append(x)
                    position_history['y'].append(y)
                    
                    for i in range(3):
                        rssi_history[i].append([node1, node2, node3][i])
                        distance_history[i].append(distances[i])
                    
                    # Obtener el tamaño mínimo común
                    min_len = min(len(time_history), 
                                len(rssi_history[0]), 
                                len(distance_history[0]), 
                                len(gyro_history[0]))
                    
                    # Obtener datos recientes sincronizados
                    recent_time = list(time_history)[-min_len:][-WINDOW_SIZE:]
                    recent_rssi = [list(h)[-min_len:][-WINDOW_SIZE:] for h in rssi_history]
                    recent_dist = [list(h)[-min_len:][-WINDOW_SIZE:] for h in distance_history]
                    recent_gyro = [list(h)[-min_len:][-WINDOW_SIZE:] for h in gyro_history]
                    
                    # Actualizar gráficas solo si tenemos datos
                    if len(recent_time) > 0:
                        # Gráfica principal
                        scatter.set_offsets(np.c_[x, y])
                        for i, line in enumerate(lines):
                            line.set_data([beacons[i]["x"], x], [beacons[i]["y"], y])
                        
                        # Subgráfica de RSSI
                        for i, line in enumerate(rssi_lines):
                            line.set_data(recent_time, recent_rssi[i])
                        ax_rssi.relim()
                        ax_rssi.set_xlim(min(recent_time), max(recent_time))
                        ax_rssi.autoscale_view(scaley=True)
                        
                        # Subgráfica de distancias
                        for i, line in enumerate(dist_lines):
                            line.set_data(recent_time, recent_dist[i])
                        ax_dist.relim()
                        ax_dist.set_xlim(min(recent_time), max(recent_time))
                        ax_dist.autoscale_view(scaley=True)
                        
                        # Gráfica del giroscopio
                        for i, line in enumerate(gyro_lines):
                            line.set_data(recent_time, recent_gyro[i])
                        ax_gyro.relim()
                        ax_gyro.set_xlim(min(recent_time), max(recent_time))
                        ax_gyro.autoscale_view(scaley=True)
                        
                        # Gráfica de RSSI del Nodo 1
                        rssi_node1_line.set_data(recent_time, recent_rssi[0])
                        ax_rssi_node1.relim()
                        ax_rssi_node1.set_xlim(min(recent_time), max(recent_time))
                        ax_rssi_node1.autoscale_view(scaley=True)
                        
#                         print(f"Posición: ({x:.2f}, {y:.2f}) m | RSSI: {node1:.1f}, {node2:.1f}, {node3:.1f} dBm")
#                         print(f"Giroscopio: X={gyro_x:.2f}°/s, Y={gyro_y:.2f}°/s, Z={gyro_z:.2f}°/s")
    
    except Exception as e:
        print(f"Error en la lectura: {e}")
    
    return [scatter] + lines + rssi_lines + dist_lines + gyro_lines + [rssi_node1_line]

# Ajustar el tamaño de la figura para acomodar las nuevas gráficas
fig.set_size_inches(15, 14)  # Aumentar la altura

try:
    # Iniciar conexión serial
    ser = serial.Serial(port, baudrate, timeout=1)
    print(f"Conexión exitosa a {port}. Iniciando visualización...")
    
    # Configurar animación
    ani = FuncAnimation(fig, update, interval=100, blit=False, cache_frame_data=False)
    plt.tight_layout()
    plt.show()

except serial.SerialException as e:
    print(f"Error al abrir {port}: {e}")
    print("Posibles soluciones:")
    print("- Verifica que el puerto sea correcto")
    print("- Asegúrate que no hay otros programas usando el puerto")
    print("- Prueba ejecutando como administrador")

except KeyboardInterrupt:
    print("\nCerrando programa...")
    if 'ser' in locals() and ser.is_open:
        ser.close()
    plt.close()
