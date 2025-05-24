import serial
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

WINDOW_SIZE = 10  # Número de puntos a mostrar (ajusta según necesidad)
MAX_HISTORY = 500  # Máximo de puntos a mantener en memoria

# Configuración del puerto serial
port = 'COM3'
baudrate = 9600

# Variables globales para almacenar los valores RSSI
node1 = 0
node2 = 0
node3 = 0
node4 = 0

# Posiciones de los nodos fijos (beacons) en metros
beacons = [
    {"x": 0, "y": 0, "name": "Nodo 1"},
    {"x": 10, "y": 0, "name": "Nodo 2"},
    {"x": 0, "y": 10, "name": "Nodo 3"},
    {"x": 10, "y": 10, "name": "Nodo 4"},
]

# Historial de datos
time_history = []
rssi_history = [[], [], [], []]  # Para RSSI de cada nodo
distance_history = [[], [], [], []]  # Para distancias de cada nodo
position_history = {'x': [], 'y': []}  # Para posición del nodo móvil

# Configuración de la gráfica principal
plt.style.use('default')
fig = plt.figure(figsize=(15, 10))
gs = fig.add_gridspec(3, 2)
ax_main = fig.add_subplot(gs[0:2, 0:2])  # Gráfica principal más grande
ax_rssi = fig.add_subplot(gs[2, 0])     # Subgráfica RSSI
ax_dist = fig.add_subplot(gs[2, 1])     # Subgráfica distancias

# Configuración de la gráfica principal
ax_main.set_xlim(-2, 12)
ax_main.set_ylim(-2, 12)
ax_main.set_xlabel('Coordenada X (metros)')
ax_main.set_ylabel('Coordenada Y (metros)')
ax_main.set_title('Sistema de Localización en Tiempo Real')
ax_main.grid(True)

# Primero crea los elementos de la gráfica (scatter y lines)
scatter = ax_main.scatter([], [], color='blue', s=100, label='Nodo Móvil')
lines = [ax_main.plot([], [], 'k--', alpha=0.5)[0] for _ in beacons]

# Luego dibuja los nodos fijos
for i, beacon in enumerate(beacons):
    if i == 0:
        ax_main.scatter(beacon["x"], beacon["y"], color='red', s=100, label='Nodos Fijos')
    else:
        ax_main.scatter(beacon["x"], beacon["y"], color='red', s=100)
    ax_main.text(beacon["x"] + 0.3, beacon["y"] + 0.3, beacon["name"], fontsize=10)

# Finalmente configura la leyenda
ax_main.legend(loc='upper left', bbox_to_anchor=(0, 1),
              frameon=True, fancybox=True)

# Configuración de la subgráfica de RSSI
ax_rssi.set_title('Valores RSSI en Tiempo Real')
ax_rssi.set_xlabel('Tiempo (iteraciones)')
ax_rssi.set_ylabel('RSSI (dBm)')
ax_rssi.grid(True)
rssi_lines = [ax_rssi.plot([], [], label=f'Nodo {i+1}')[0] for i in range(4)]
ax_rssi.legend(loc='upper right', bbox_to_anchor=(1, 1), 
              ncol=1, frameon=True, fancybox=True)

# Configuración de la subgráfica de distancias
ax_dist.set_title('Distancias Estimadas en Tiempo Real')
ax_dist.set_xlabel('Tiempo (iteraciones)')
ax_dist.set_ylabel('Distancia (metros)')
ax_dist.grid(True)
dist_lines = [ax_dist.plot([], [], label=f'Dist a Nodo {i+1}')[0] for i in range(4)]
ax_dist.legend(loc='upper right', bbox_to_anchor=(1, 1), 
              ncol=1, frameon=True, fancybox=True)

def trilaterate(rssi_values, beacons, rssi_0=-60, n=2):
    """Función de trilateración basada en RSSI"""
    distances = [10 ** ((rssi_0 - rssi) / (10 * n)) for rssi in rssi_values]
    
    x1, y1 = beacons[0]["x"], beacons[0]["y"]
    x2, y2 = beacons[1]["x"], beacons[1]["y"]
    x3, y3 = beacons[2]["x"], beacons[2]["y"]
    x4, y4 = beacons[3]["x"], beacons[3]["y"]
    
    d1, d2, d3, d4 = distances
    
    A = np.array([
        [2 * (x2 - x1), 2 * (y2 - y1)],
        [2 * (x3 - x1), 2 * (y3 - y1)],
        [2 * (x4 - x1), 2 * (y4 - y1)]
    ])
    
    b = np.array([
        x2**2 + y2**2 - x1**2 - y1**2 + d1**2 - d2**2,
        x3**2 + y3**2 - x1**2 - y1**2 + d1**2 - d3**2,
        x4**2 + y4**2 - x1**2 - y1**2 + d1**2 - d4**2
    ])
    
    x, y = np.linalg.lstsq(A, b, rcond=None)[0]
    return x, y, distances

def update(frame):
    """Función para actualizar la gráfica en tiempo real"""
    global node1, node2, node3, node4, time_history
    
    try:
        if ser.in_waiting > 0:
            data = ser.readline().decode('utf-8').strip()
            if len(data) > 0:
                pipe = data[0]
                if pipe == '1':
                    node1 = float(data[1:])
                elif pipe == '2':
                    node2 = float(data[1:])
                elif pipe == '3':
                    node3 = float(data[1:])
                elif pipe == '4':
                    node4 = float(data[1:])
                
                # Calcular nueva posición y distancias
                x, y, distances = trilaterate([node1, node2, node3, node4], beacons)
                
                # Actualizar historiales
                time_history.append(frame)
                position_history['x'].append(x)
                position_history['y'].append(y)
                
                for i in range(4):
                    rssi_history[i].append([node1, node2, node3, node4][i])
                    distance_history[i].append(distances[i])
                
                # Limitar el tamaño de los historiales
                if len(time_history) > WINDOW_SIZE:
                    time_history.pop(0)
                    position_history['x'].pop(0)
                    position_history['y'].pop(0)
                    for i in range(4):
                        rssi_history[i].pop(0)
                        distance_history[i].pop(0)
                
                # Actualizar gráfica principal
                scatter.set_offsets(np.c_[x, y])
                for i, line in enumerate(lines):
                    line.set_data([beacons[i]["x"], x], [beacons[i]["y"], y])
                
                # Obtener solo los últimos WINDOW_SIZE puntos
                recent_time = time_history[-WINDOW_SIZE:]
                recent_rssi = [history[-WINDOW_SIZE:] for history in rssi_history]
                recent_dist = [history[-WINDOW_SIZE:] for history in distance_history]
                
                # Actualizar subgráfica de RSSI
                for i, line in enumerate(rssi_lines):
                    line.set_data(recent_time, recent_rssi[i])
                ax_rssi.relim()
                ax_rssi.set_xlim(min(recent_time), max(recent_time))
                ax_rssi.autoscale_view(scaley=True)  # Modificación aquí
                
                # Actualizar subgráfica de distancias
                for i, line in enumerate(dist_lines):
                    line.set_data(recent_time, recent_dist[i])
                ax_dist.relim()
                ax_dist.set_xlim(min(recent_time), max(recent_time))
                ax_dist.autoscale_view(scaley=True)  # Modificación aquí
                
                print(f"Posición: ({x:.2f}, {y:.2f}) m | RSSI: {node1:.1f}, {node2:.1f}, {node3:.1f}, {node4:.1f} dBm")
    
    except Exception as e:
        print(f"Error en la lectura: {e}")
    
    return [scatter] + lines + rssi_lines + dist_lines

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
