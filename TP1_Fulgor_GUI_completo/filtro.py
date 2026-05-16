"""
filtro.py

Modulo de filtros para el TP1 de Python - Fundacion Fulgor.

Incluye filtros:
- Raised Cosine (RC)
- Root Raised Cosine (RRC)

La clase se usa desde main.py o desde app_gui.py.
"""

import numpy as np
import matplotlib.pyplot as plt


class RaisedCosineFilter:
    def __init__(self, alpha=0.25, span=6, sps=8, rrc=True):
        self.alpha = float(alpha)
        self.span = int(span)
        self.sps = int(sps)
        self.rrc = bool(rrc)
        self._validate()
        self.taps = self.generate_filter()

    def _validate(self):
        if not (0 <= self.alpha <= 1):
            raise ValueError("alpha debe estar entre 0 y 1")
        if self.span <= 0:
            raise ValueError("span debe ser positivo")
        if self.sps <= 0:
            raise ValueError("sps debe ser positivo")

    def generate_filter(self):
        alpha = self.alpha
        span = self.span
        sps = self.sps
        T = 1.0

        N = span * sps
        t = np.arange(-N // 2, N // 2 + 1, dtype=float) / sps
        h = np.zeros_like(t)

        if alpha == 0:
            return np.sinc(t / T)

        if self.rrc:
            for i, ti in enumerate(t):
                if np.isclose(ti, 0.0):
                    h[i] = 1.0 - alpha + (4.0 * alpha / np.pi)

                elif np.isclose(abs(ti), T / (4.0 * alpha)):
                    h[i] = (alpha / np.sqrt(2.0)) * (
                        (1.0 + 2.0 / np.pi) * np.sin(np.pi / (4.0 * alpha))
                        +
                        (1.0 - 2.0 / np.pi) * np.cos(np.pi / (4.0 * alpha))
                    )

                else:
                    numerator = (
                        np.sin(np.pi * ti * (1.0 - alpha) / T)
                        +
                        4.0 * alpha * ti / T
                        * np.cos(np.pi * ti * (1.0 + alpha) / T)
                    )

                    denominator = (
                        np.pi * ti
                        * (1.0 - (4.0 * alpha * ti / T) ** 2)
                    )

                    h[i] = numerator / denominator

        else:
            for i, ti in enumerate(t):
                if np.isclose(ti, 0.0):
                    h[i] = 1.0

                elif np.isclose(abs(ti), T / (2.0 * alpha)):
                    h[i] = (np.pi / 4.0) * np.sinc(1.0 / (2.0 * alpha))

                else:
                    h[i] = (
                        np.sinc(ti / T)
                        * np.cos(np.pi * alpha * ti / T)
                        / (1.0 - (2.0 * alpha * ti / T) ** 2)
                    )

        return h

    def get_coefficients(self):
        return self.taps

    def time_axis(self):
        N = self.span * self.sps
        return np.arange(-N // 2, N // 2 + 1, dtype=float) / self.sps

    def frequency_response(self, n_fft=4096):
        H = np.fft.fftshift(np.fft.fft(self.taps, n_fft))
        f = np.linspace(-0.5, 0.5, len(H), endpoint=False)
        mag_db = 20.0 * np.log10(np.abs(H) + 1e-12)
        return f, mag_db

    def export_coefficients(self, filename="coeficientes.txt"):
        with open(filename, "w", encoding="utf-8") as file:
            file.write("# Coeficientes del filtro\n")
            file.write(f"# alpha = {self.alpha}\n")
            file.write(f"# span  = {self.span}\n")
            file.write(f"# sps   = {self.sps}\n")
            file.write(f"# tipo  = {'RRC' if self.rrc else 'RC'}\n\n")
            for i, value in enumerate(self.taps):
                file.write(f"h[{i}] = {value:.12f}\n")

    # Metodos con matplotlib para cumplir tambien en modo consola
    def plot_time(self):
        t = self.time_axis()
        tipo = "RRC" if self.rrc else "RC"

        plt.figure(figsize=(9, 4))
        plt.stem(t, self.taps)
        plt.title(f"Respuesta temporal discreta - {tipo}")
        plt.xlabel("Tiempo [periodos de simbolo]")
        plt.ylabel("Amplitud")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def plot_frequency(self):
        f, mag_db = self.frequency_response()
        tipo = "RRC" if self.rrc else "RC"

        plt.figure(figsize=(9, 4))
        plt.plot(f, mag_db)
        plt.title(f"Respuesta en frecuencia - {tipo}")
        plt.xlabel("Frecuencia normalizada")
        plt.ylabel("Magnitud [dB]")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def plot_both(self):
        t = self.time_axis()
        f, mag_db = self.frequency_response()
        tipo = "RRC" if self.rrc else "RC"

        plt.figure(figsize=(12, 5))

        plt.subplot(1, 2, 1)
        plt.stem(t, self.taps)
        plt.title("Respuesta temporal discreta")
        plt.xlabel("Tiempo [periodos de simbolo]")
        plt.ylabel("Amplitud")
        plt.grid(True)

        plt.subplot(1, 2, 2)
        plt.plot(f, mag_db)
        plt.title("Respuesta en frecuencia")
        plt.xlabel("Frecuencia normalizada")
        plt.ylabel("Magnitud [dB]")
        plt.grid(True)

        plt.suptitle(
            f"Filtro {tipo} | alpha={self.alpha}, "
            f"span={self.span}, sps={self.sps}"
        )
        plt.tight_layout()
        plt.show()


def compare_filters(alpha_values, span=6, sps=8, rrc=True):
    plt.figure(figsize=(10, 5))
    for alpha in alpha_values:
        filt = RaisedCosineFilter(alpha=alpha, span=span, sps=sps, rrc=rrc)
        f, mag_db = filt.frequency_response()
        plt.plot(f, mag_db, label=f"alpha={alpha}")

    tipo = "RRC" if rrc else "RC"
    plt.title(f"Comparacion de varios filtros {tipo}")
    plt.xlabel("Frecuencia normalizada")
    plt.ylabel("Magnitud [dB]")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


def bpsk_filtered_signal(filtro, n_bits=32):
    bits = np.random.randint(0, 2, n_bits)
    symbols = 2 * bits - 1

    upsampled = np.zeros(n_bits * filtro.sps)
    upsampled[::filtro.sps] = symbols

    y = np.convolve(upsampled, filtro.get_coefficients())
    return y


def plot_filtered_bpsk(filtro, n_bits=32):
    y = bpsk_filtered_signal(filtro, n_bits=n_bits)

    plt.figure(figsize=(10, 5))
    plt.plot(y)
    plt.title("Senal BPSK filtrada")
    plt.xlabel("Muestras")
    plt.ylabel("Amplitud")
    plt.grid(True)
    plt.tight_layout()
    plt.show()
