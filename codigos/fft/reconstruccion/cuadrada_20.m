% Cargar datos desde un archivo CSV
data = readmatrix('/MATLAB Drive/informe_fft/armonicos/señal_3.csv'); % Cambia el nombre del archivo si es diferente
frecuencias = data(:,1); % Columna de frecuencias
amplitudes = data(:,2);  % Columna de amplitudes

% Parámetros de la señal
fs = max(frecuencias) * 10; % Frecuencia de muestreo (suficientemente alta)
T = 1 / min(frecuencias);   % Período de la señal fundamental
t = linspace(0, 4*T, 1000); % Vector de tiempo para dos períodos

% Constantes del ciclo útil
tau = 0.2 * T; % Ciclo útil del 20%
x = pi * tau / T;

% Calcular amplitudes ajustadas según el ciclo útil del 20%
for i = 1:length(frecuencias)
    n = frecuencias(i) / (1/T); % Determinar el índice del armónico
    amplitudes(i) = (2 / (n * pi)) * sin(n * x); % Fórmula ajustada
end

% Reconstrucción de la señal en el dominio del tiempo
v_t = zeros(size(t)); % Inicializar señal
for i = 1:length(frecuencias)
    % Sumar cada armónico con frecuencia y amplitud especificadas
    v_t = v_t + amplitudes(i) * cos(2 * pi * frecuencias(i) * t);
end

% Graficar la señal reconstruida
figure;
plot(t, v_t, 'b', 'LineWidth', 1.5);
xlabel('Tiempo (s)');
ylabel('Amplitud');
grid on;
