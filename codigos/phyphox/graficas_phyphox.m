% Cargar los datos del archivo CSV
data = readtable('aceleracion_vs_tiempo.csv');  % Asegúrate de reemplazar 'archivo.csv' con el nombre de tu archivo

% Asumimos que las columnas del CSV son 'Tiempo' y 'Presión'
% Si las columnas tienen otros nombres, ajusta los nombres de las variables
tiempo = data.Tiempo;  % Cambia 'Tiempo' si el encabezado de la columna es otro
presion = data.Aceleracion;  % Cambia 'Presion' si el encabezado de la columna es otro

% Crear el gráfico
figure;
plot(tiempo, presion, '-o', 'LineWidth', 1, 'MarkerSize', 1);
xlabel('Tiempo');  % Etiqueta del eje X
ylabel('Aceleración (m/s²)');  % Etiqueta del eje Y
grid on;  % Mostrar la cuadrícula en el gráfico
%xlim([325 330]);
%ylim([751 754]);