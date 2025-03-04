% Cargar datos desde un archivo CSV
filename = '/MATLAB Drive/informe_fft/scripts/ADC/5ms.csv'; % Nombre del archivo
opts = detectImportOptions(filename); % Detectar opciones de importación
data = readmatrix(filename, opts); % Leer el archivo

% Suponiendo que la primera columna es el tiempo y la segunda es la señal
tiempo = data(:, 1); 
senal = data(:, 2);

% Graficar la señal
figure;
stem(tiempo, senal, 'r', 'LineWidth', 1.5);
hold
plot(tiempo, senal, 'b', 'LineWidth', 1.5);
grid on;
xlabel('Tiempo (ms)');
ylabel('Voltaje (V)');
title('Muestreo 5ms');
xlim([2400 2500]); % Ajustar escala horizontal