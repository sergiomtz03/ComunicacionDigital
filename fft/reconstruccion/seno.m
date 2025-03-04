% Cargar datos desde un archivo CSV
data = readmatrix('/MATLAB Drive/informe_fft/armonicos/señal_1.csv'); % Asegúrate de cambiar el nombre del archivo si es diferente

frecuencias = data(:,1); % Columna de frecuencias
amplitudes = data(:,2);  % Columna de amplitudes

% Definir parámetros de la señal
fs = max(frecuencias) * 10; % Frecuencia de muestreo (suficientemente alta)
T = 1 / min(frecuencias);   % Período de la señal fundamental
t = linspace(0, 2*T, 1000); % Vector de tiempo para dos períodos

% Reconstrucción de la señal senoidal
senal = zeros(size(t));
for i = 1:length(frecuencias)
    senal = senal + amplitudes(i) * cos(2 * pi * frecuencias(i) * t);
end

% Graficar la señal reconstruida
figure;
plot(t, senal + 5, 'r', 'LineWidth', 1.5);
xlabel('Tiempo (s)');
ylabel('Amplitud');
ylim([2.5, 7.5])
grid on;
