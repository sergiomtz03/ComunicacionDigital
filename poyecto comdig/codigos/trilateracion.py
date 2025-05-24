import serial
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle

# Configuración
WINDOW_SIZE = 10  # Puntos mostrados en gráficas
MAX_HISTORY = 500  # Máximo puntos en memoria
CALIBRATION = {'rssi_0': -45.0, 'n': 2.2}  # Parámetros de calibración

# Configuración serial
port = 'COM3'
baudrate = 9600

# Variables globales para RSSI
rssi_values = [0, 0, 0, 0]

# Posiciones de los nodos fijos (beacons)
beacons = [
    {"x": -1, "y": 1, "name": "Nodo 1"},
    {"x": 50, "y": 0, "name": "Nodo 2"},
    {"x": 0, "y": 30, "name": "Nodo 3"},
    {"x": 50, "y": 30, "name": "Nodo 4"},
]

# Historial de datos
time_history = []
rssi_history = [[], [], [], []]  # RSSI por nodo
distance_history = [[], [], [], []]  # Distancias estimadas
position_history = {'x': [], 'y': []}  # Posiciones estimadas

# Configuración de la gráfica
fig = plt.figure(figsize=(15, 10))
gs = fig.add_gridspec(3, 2)
ax_main = fig.add_subplot(gs[0:2, 0:2])  # Mapa principal
ax_rssi = fig.add_subplot(gs[2, 0])     # Gráfica RSSI
ax_dist = fig.add_subplot(gs[2, 1])     # Gráfica distancias

# Configuración del mapa principal
ax_main.set_xlim(-5, 55)
ax_main.set_ylim(-5, 55)
ax_main.set_xlabel('Coordenada X (metros)')
ax_main.set_ylabel('Coordenada Y (metros)')
ax_main.set_title('Sistema de Localización en Tiempo Real')
ax_main.grid(True)

# Dibujar nodos fijos
for i, beacon in enumerate(beacons):
    color = 'red' if i == 0 else 'green'
    ax_main.scatter(beacon["x"], beacon["y"], color=color, s=100, 
                   label='Nodos Fijos' if i == 0 else "")
    ax_main.text(beacon["x"] + 0.3, beacon["y"] + 0.3, beacon["name"], fontsize=10)

# Elementos móviles
scatter = ax_main.scatter([], [], color='blue', s=100, label='Nodo Móvil')
lines = [ax_main.plot([], [], 'k--', alpha=0.3)[0] for _ in beacons]
circles = [ax_main.add_patch(Circle((0, 0), 0, fill=False, color='r', alpha=0.2)) 
           for _ in beacons]
ax_main.legend(loc='upper left')

# Configuración gráfica RSSI
ax_rssi.set_title('Valores RSSI en Tiempo Real')
ax_rssi.set_xlabel('Tiempo (iteraciones)')
ax_rssi.set_ylabel('RSSI (dBm)')
ax_rssi.grid(True)
rssi_lines = [ax_rssi.plot([], [], label=f'Nodo {i+1}')[0] for i in range(4)]
ax_rssi.legend(loc='upper right')

# Configuración gráfica distancias
ax_dist.set_title('Distancias Estimadas')
ax_dist.set_xlabel('Tiempo (iteraciones)')
ax_dist.set_ylabel('Distancia (metros)')
ax_dist.grid(True)
dist_lines = [ax_dist.plot([], [], label=f'Dist a Nodo {i+1}')[0] for i in range(4)]
ax_dist.legend(loc='upper right')

def rssi_to_distance(rssi, rssi_0=-45.0, n=2.0):
    """Convierte RSSI a distancia con manejo de errores"""
    try:
        distance = 10 ** ((rssi_0 - rssi) / (10 * n))
        return max(distance, 0.1)  # Distancia mínima de 0.1 metros
    except:
        return 1.0  # Valor por defecto si hay error

def weighted_trilateration(rssi_values, beacons, calib):
    """Trilateración con mínimos cuadrados ponderados"""
    # Calcular distancias
    distances = [rssi_to_distance(rssi, calib['rssi_0'], calib['n']) 
                for rssi in rssi_values]
    
    # Extraer coordenadas de los beacons
    x = [b["x"] for b in beacons]
    y = [b["y"] for b in beacons]
    
    # Construir sistema de ecuaciones
    A = []
    b = []
    for i in range(1, len(beacons)):
        A.append([2*(x[i] - x[0]), 2*(y[i] - y[0])])
        b.append(x[i]**2 + y[i]**2 - x[0]**2 - y[0]**2 + 
                distances[0]**2 - distances[i]**2)
    
    A = np.array(A)
    b = np.array(b)
    
    # Ponderación por calidad de señal (inversa al cuadrado de la distancia)
    weights = [1/(d**2 + 1e-6) for d in distances[1:]]  # +1e-6 para evitar división por cero
    W = np.diag(weights)
    
    try:
        pos = np.linalg.lstsq(W @ A, W @ b, rcond=None)[0]
        x_est, y_est = pos[0], pos[1]
        
        # Validar que la posición es razonable
        x_est = np.clip(x_est, -5, 55)
        y_est = np.clip(y_est, -5, 55)
        
        return x_est, y_est, distances
    except:
        # Fallback: posición promedio si falla el cálculo
        avg_x = np.mean([b["x"] for b in beacons])
        avg_y = np.mean([b["y"] for b in beacons])
        return avg_x, avg_y, distances

def update(frame):
    """Actualiza la visualización con nuevos datos"""
    global rssi_values
    
    try:
        if ser.in_waiting > 0:
            data = ser.readline().decode('utf-8').strip()
            if len(data) > 0 and data[0] in ['1', '2', '3', '4']:
                node_idx = int(data[0]) - 1
                rssi_values[node_idx] = float(data[1:])
                
                # Calcular posición
                x, y, distances = weighted_trilateration(rssi_values, beacons, CALIBRATION)
                
                # Actualizar historiales
                time_history.append(frame)
                position_history['x'].append(x)
                position_history['y'].append(y)
                
                for i in range(4):
                    rssi_history[i].append(rssi_values[i])
                    distance_history[i].append(distances[i])
                
                # Limitar tamaño de historiales
                if len(time_history) > MAX_HISTORY:
                    time_history.pop(0)
                    position_history['x'].pop(0)
                    position_history['y'].pop(0)
                    for i in range(4):
                        rssi_history[i].pop(0)
                        distance_history[i].pop(0)
                
                # Actualizar visualización principal
                scatter.set_offsets(np.c_[x, y])
                
                # Líneas de conexión y círculos de error
                for i, (line, circle) in enumerate(zip(lines, circles)):
                    line.set_data([beacons[i]["x"], x], [beacons[i]["y"], y])
                    circle.center = (beacons[i]["x"], beacons[i]["y"])
                    circle.radius = distances[i]
                
                # Actualizar subgráficas (últimos WINDOW_SIZE puntos)
                recent_time = time_history[-WINDOW_SIZE:]
                
                # Gráfica RSSI
                for i, line in enumerate(rssi_lines):
                    line.set_data(recent_time, rssi_history[i][-WINDOW_SIZE:])
                ax_rssi.relim()
                ax_rssi.set_xlim(min(recent_time), max(recent_time))
                ax_rssi.autoscale_view(scaley=True)
                
                # Gráfica distancias
                for i, line in enumerate(dist_lines):
                    line.set_data(recent_time, distance_history[i][-WINDOW_SIZE:])
                ax_dist.relim()
                ax_dist.set_xlim(min(recent_time), max(recent_time))
                ax_dist.autoscale_view(scaley=True)
                
                print(f"Posición: ({x:.2f}, {y:.2f}) m | RSSI: {rssi_values} | Distancias: {[f'{d:.2f}' for d in distances]}")
    
    except Exception as e:
        print(f"Error: {e}")
    
    return [scatter] + lines + circles + rssi_lines + dist_lines

# Inicialización
try:
    ser = serial.Serial(port, baudrate, timeout=1)
    print(f"Conexión establecida en {port}. Iniciando...")
    
    ani = FuncAnimation(fig, update, interval=100, blit=False, cache_frame_data=False)
    plt.tight_layout()
    plt.show()

except serial.SerialException as e:
    print(f"Error al abrir {port}: {e}")
    print("Sugerencias:")
    print("1. Verifica el puerto COM correcto")
    print("2. Asegúrate que el dispositivo está conectado")
    print("3. Prueba reiniciando el IDE/consola")

except KeyboardInterrupt:
    print("\nCerrando programa...")
    if 'ser' in locals() and ser.is_open:
        ser.close()
    plt.close()