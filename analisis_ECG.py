import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as signal
import pywt
import pandas as pd

# 1. Cargar los datos desde un archivo .txt con dos columnas
file_path = 'juanitados.txt'  # Reemplaza con la ruta de tu archivo
datos = np.loadtxt(file_path, delimiter=',')  # Cargar datos
tiempo = datos[:, 0]  # Primera columna: tiempo
voltaje = datos[:, 1]  # Segunda columna: voltaje (señal ECG)
fs = 100  # Frecuencia de muestreo en Hz

# Calcular el tiempo total de la señal y recortar a 5 minutos
total_time = len(voltaje) / fs  # Tiempo total en segundos
print(f"Tiempo total de la señal: {total_time:.2f} segundos")
print(f"Frecuencia de muestreo: {fs} Hz")


# 2. Filtrado de la señal ECG (pasabanda: 1-40 Hz)
lowcut = 1.0
highcut = 40.0
nyq = 0.5 * fs
low = lowcut / nyq
high = highcut / nyq

b, a = signal.butter(4, [low, high], btype='band')
ecg_filtered = signal.filtfilt(b, a, voltaje)

# 3. Filtro pasabajas (40 Hz)
cutoff_low = 40.0
low = cutoff_low / nyq
b_low, a_low = signal.butter(4, low, btype='low')
ecg_filtered = signal.filtfilt(b_low, a_low, ecg_filtered)

# 4. Filtro mediana
ecg_filtered = signal.medfilt(ecg_filtered, kernel_size=5)

# 5. Detección de picos R
peaks, _ = signal.find_peaks(ecg_filtered, height=np.mean(ecg_filtered) * 1.5, distance=fs * 0.6)
rpeaks_times = peaks / fs  # Tiempo de los picos en segundos

# 6. Calcular intervalos R-R
rr_intervals = np.diff(rpeaks_times)  # Intervalos R-R en segundos
mean_rr = np.mean(rr_intervals)  # Promedio de R-R
std_rr = np.std(rr_intervals)  # Desviación estándar de R-R

# Crear un DataFrame para mostrar los intervalos R-R
df_rr_intervals = pd.DataFrame({
    'Índice Pico R': np.arange(1, len(rr_intervals) + 1),
    'Intervalo R-R (s)': rr_intervals,
})

# Mostrar resultados organizados en la consola
print("\nIntervalos R-R (s):")
print(df_rr_intervals)

# Mostrar resumen de intervalos R-R
print(f"\nPromedio de intervalos R-R: {mean_rr:.2f} s")
print(f"Desviación estándar de intervalos R-R: {std_rr:.2f} s")

# 7. Gráfica de la señal original y filtrada
plt.figure(figsize=(14, 10))

# Señal original
plt.subplot(2, 1, 1)
plt.plot(tiempo, voltaje, label='Señal ECG Original', color='#800080', linewidth=1.5)
plt.title('Señal ECG Original', fontsize=16, fontweight='bold', color='#333333')
plt.xlabel('Tiempo (s)', fontsize=14)
plt.ylabel('Amplitud (mV)', fontsize=14)
plt.legend(loc='upper right', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.6)

# Señal filtrada y picos R
plt.subplot(2, 1, 2)
plt.plot(tiempo, ecg_filtered, label='Señal ECG Filtrada', color='#007acc', linewidth=1.5)
plt.plot(tiempo[peaks], ecg_filtered[peaks], 'ro', label='Picos R', markersize=5, alpha=0.7)
plt.title('Señal ECG Filtrada con Picos R', fontsize=16, fontweight='bold', color='#333333')
plt.xlabel('Tiempo (s)', fontsize=14)
plt.ylabel('Amplitud (mV)', fontsize=14)
plt.legend(loc='upper right', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.show()


# 8. Transformada Wavelet Continua (CWT)
scales = np.arange(1.0, 64.0, 1.0)  # Rango de escalas ajustado
wavelet = 'cmor1.5-1.0'  # Wavelet de Morlet con B=1.5 y C=1.0

# Aplicar CWT a la señal de 5 minutos
try:
    print("Aplicando CWT...")
    coefficients, frequencies = pywt.cwt(ecg_filtered, scales, wavelet, sampling_period=1/fs)
    print("CWT aplicada correctamente.")
except ValueError as e:
    print("Error al aplicar CWT:", str(e))  # Captura el error específico
    coefficients, frequencies = None, None  # Asignar None para evitar fallos posteriores

# 9. Espectrograma de la señal
if coefficients is not None:
    plt.figure(figsize=(10, 6))
    plt.imshow(np.abs(coefficients), extent=[0, tiempo[-1], frequencies[-1], frequencies[0]], cmap='jet', aspect='auto')
    plt.colorbar(label='Amplitud')
    plt.ylabel('Frecuencia (Hz)')
    plt.xlabel('Tiempo (s)')
    plt.title('Espectrograma Wavelet de la señal ECG (5 minutos)')
    plt.show()
else:
    print("No se puede mostrar el espectrograma debido a un error en la CWT.")

# 10. Calcular potencias en bandas de interés
freqs = fs / (2 * scales)  # Convertir escalas a frecuencias

# Verificar las frecuencias asociadas a las escalas
print("Frecuencias asociadas a las escalas:", freqs)

# Definir bandas de frecuencia ajustadas
lf_band = np.logical_and(freqs >= 0.5, freqs <= 2.0)  # Banda LF ajustada (0.5 - 2.0 Hz)
hf_band = np.logical_and(freqs >= 2.0, freqs <= 5.0)  # Banda HF ajustada (2.0 - 5.0 Hz)

# Verificar selección de bandas
print("Índices de LF seleccionados:", np.where(lf_band))
print("Índices de HF seleccionados:", np.where(hf_band))

# Calcular potencia en bandas
lf_power = np.trapz(np.abs(coefficients[lf_band, :]), axis=0)
hf_power = np.trapz(np.abs(coefficients[hf_band, :]), axis=0)

# 11. Mostrar potencias en consola
print(f"\nPotencia promedio en banda LF: {np.mean(lf_power):.4f}")
print(f"Potencia promedio en banda HF: {np.mean(hf_power):.4f}")

# Evitar división por cero en caso de que la potencia HF sea cero
if np.sum(hf_power) > 0:
    lf_hf_ratio = np.mean(lf_power) / np.mean(hf_power)
else:
    lf_hf_ratio = np.nan  # Asignar 'nan' si no se puede calcular la relación

print(f"Relación LF/HF: {lf_hf_ratio:.4f}")

# 12. Visualización de potencias en bandas
plt.figure(figsize=(12, 6))
time_axis = np.arange(0, len(lf_power)) * (5 * 60 / len(lf_power))  # Tiempo en segundos
plt.plot(time_axis, lf_power, label='Potencia LF', color='blue')
plt.plot(time_axis, hf_power, label='Potencia HF', color='red')
plt.title('Potencia en Bandas LF y HF a lo largo del tiempo (5 minutos)')
plt.xlabel('Tiempo (s)')
plt.ylabel('Potencia')
plt.legend()
plt.grid()
plt.show()
