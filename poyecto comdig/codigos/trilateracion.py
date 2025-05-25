import serial
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Configuración de visualización
WINDOW_SIZE = 25  # Muestra últimos 60 puntos (~6 segundos con interval=100)
MAX_HISTORY = 300  # Máximo de puntos en memoria

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
    {"x": 10, "y": 0, "name": "Nodo 2"},
    {"x": 5, "y": 8.66, "name": "Nodo 3"}  # Altura triángulo equilátero: √3/2 * lado
]

# Historial de datos
time_history = []
rssi_history = [[], [], []]  # Para RSSI de cada nodo
distance_history = [[], [], []]  # Para distancias de cada nodo
position_history = {'x': [], 'y': []}  # Para posición del nodo móvil

# Configuración de la gráfica principal
plt.style.use('default')
fig = plt.figure(figsize=(15, 10))
gs = fig.add_gridspec(3, 2)
ax_main = fig.add_subplot(gs[0:2, 0:2])  # Gráfica principal
ax_rssi = fig.add_subplot(gs[2, 0])     # Subgráfica RSSI
ax_dist = fig.add_subplot(gs[2, 1])     # Subgráfica distancias

# Configuración de la gráfica principal
ax_main.set_xlim(-2, 12)
ax_main.set_ylim(-2, 12)
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
ax_rssi.set_xlabel('Tiempo (iteraciones)')
ax_rssi.set_ylabel('RSSI (dBm)')
ax_rssi.grid(True)
rssi_lines = [ax_rssi.plot([], [], label=f'Nodo {i+1}')[0] for i in range(3)]
ax_rssi.legend(loc='upper right', bbox_to_anchor=(1, 1), ncol=1, frameon=True)

ax_dist.set_title('Distancias Estimadas')
ax_dist.set_xlabel('Tiempo (iteraciones)')
ax_dist.set_ylabel('Distancia (metros)')
ax_dist.grid(True)
dist_lines = [ax_dist.plot([], [], label=f'Dist a Nodo {i+1}')[0] for i in range(3)]
ax_dist.legend(loc='upper right', bbox_to_anchor=(1, 1), ncol=1, frameon=True)

def rssi_to_distance(rssi, rssi_0=-60, n=2):
    """Modelo de propagación en espacio libre (log-distance path loss)"""
    # Fórmula: d = 10^((rssi_0 - rssi)/(10*n))
    return 10 ** ((rssi_0 - rssi) / (10 * n))

def trilaterate(rssi_values, beacons, rssi_0=-60, n=2):
    """Función de trilateración con 3 nodos usando mínimos cuadrados"""
    # Convertir RSSI a distancias
    distances = [rssi_to_distance(rssi, rssi_0, n) for rssi in rssi_values]
    
    # Coordenadas de los beacons
    x1, y1 = beacons[0]["x"], beacons[0]["y"]
    x2, y2 = beacons[1]["x"], beacons[1]["y"]
    x3, y3 = beacons[2]["x"], beacons[2]["y"]
    
    d1, d2, d3 = distances
    
    # Matriz A y vector b para el sistema de ecuaciones
    A = np.array([
        [2 * (x2 - x1), 2 * (y2 - y1)],
        [2 * (x3 - x1), 2 * (y3 - y1)]
    ])
    
    b = np.array([
        x2**2 + y2**2 - x1**2 - y1**2 + d1**2 - d2**2,
        x3**2 + y3**2 - x1**2 - y1**2 + d1**2 - d3**2
    ])
    
    # Resolver el sistema usando mínimos cuadrados
    x, y = np.linalg.lstsq(A, b, rcond=None)[0]
    return x, y, distances

def update(frame):
    """Función para actualizar la gráfica en tiempo real"""
    global node1, node2, node3, gyro_x, gyro_y, gyro_z, time_history
    
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
                    parts = data.split()
                    if len(parts) >= 4:
                        gyro_x = float(parts[1])  # Primer valor después del identificador
                        gyro_y = float(parts[2])
                        gyro_z = float(parts[3])
                
                # Calcular posición con 3 nodos
                x, y, distances = trilaterate([node1, node2, node3], beacons)
                
                # Actualizar historiales
                time_history.append(frame)
                position_history['x'].append(x)
                position_history['y'].append(y)
                
                for i in range(3):
                    rssi_history[i].append([node1, node2, node3][i])
                    distance_history[i].append(distances[i])
                
                # Limitar tamaño de historiales
                if len(time_history) > MAX_HISTORY:
                    time_history.pop(0)
                    position_history['x'].pop(0)
                    position_history['y'].pop(0)
                    for i in range(3):
                        rssi_history[i].pop(0)
                        distance_history[i].pop(0)
                
                # Actualizar gráfica principal
                scatter.set_offsets(np.c_[x, y])
                for i, line in enumerate(lines):
                    line.set_data([beacons[i]["x"], x], [beacons[i]["y"], y])
                
                # Mostrar últimos WINDOW_SIZE puntos
                recent_time = time_history[-WINDOW_SIZE:]
                recent_rssi = [history[-WINDOW_SIZE:] for history in rssi_history]
                recent_dist = [history[-WINDOW_SIZE:] for history in distance_history]
                
                # Actualizar subgráfica de RSSI
                for i, line in enumerate(rssi_lines):
                    line.set_data(recent_time, recent_rssi[i])
                ax_rssi.relim()
                ax_rssi.set_xlim(min(recent_time), max(recent_time))
                ax_rssi.autoscale_view(scaley=True)
                
                # Actualizar subgráfica de distancias
                for i, line in enumerate(dist_lines):
                    line.set_data(recent_time, recent_dist[i])
                ax_dist.relim()
                ax_dist.set_xlim(min(recent_time), max(recent_time))
                ax_dist.autoscale_view(scaley=True)
                
                print(f"Posición: ({x:.2f}, {y:.2f}) m | RSSI: {node1:.1f}, {node2:.1f}, {node3:.1f} dBm | Distancias: {distances[0]:.2f}, {distances[1]:.2f}, {distances[2]:.2f} m")
    
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
