"""
main.py

Version por consola del TP1.

Usa:
- filtro.py
- com_serie.py
- puerto serie virtual loop://
"""

from filtro import RaisedCosineFilter, compare_filters, plot_filtered_bpsk
from com_serie import ComunicacionSerie


class ControladorFiltro:
    def __init__(self):
        self.alpha = 0.25
        self.span = 6
        self.sps = 8
        self.rrc = True
        self.generar_filtro()

    def generar_filtro(self):
        self.filtro = RaisedCosineFilter(
            alpha=self.alpha,
            span=self.span,
            sps=self.sps,
            rrc=self.rrc
        )

    def estado(self):
        tipo = "rrc" if self.rrc else "rc"
        return f"alpha={self.alpha}, span={self.span}, sps={self.sps}, type={tipo}"

    def procesar_comando(self, comando):
        partes = comando.lower().split()

        if len(partes) == 0:
            return "ERROR: comando vacio"

        if partes[0] == "help":
            return (
                "\nCOMANDOS:\n"
                "  status\n"
                "  set alpha 0.5\n"
                "  set span 10\n"
                "  set sps 8\n"
                "  set type rrc\n"
                "  set type rc\n"
                "  gen\n"
                "  coef\n"
                "  plot time\n"
                "  plot freq\n"
                "  plot both\n"
                "  compare\n"
                "  signal\n"
                "  export\n"
                "  exit\n"
            )

        if partes[0] == "status":
            return "CONFIG -> " + self.estado()

        if partes[0] == "set":
            if len(partes) != 3:
                return "ERROR: usar set parametro valor"

            parametro = partes[1]
            valor = partes[2]

            try:
                if parametro == "alpha":
                    alpha = float(valor)
                    if not (0 <= alpha <= 1):
                        return "ERROR: alpha debe estar entre 0 y 1"
                    self.alpha = alpha

                elif parametro == "span":
                    span = int(valor)
                    if span <= 0:
                        return "ERROR: span debe ser positivo"
                    self.span = span

                elif parametro == "sps":
                    sps = int(valor)
                    if sps <= 0:
                        return "ERROR: sps debe ser positivo"
                    self.sps = sps

                elif parametro == "type":
                    if valor == "rrc":
                        self.rrc = True
                    elif valor == "rc":
                        self.rrc = False
                    else:
                        return "ERROR: type debe ser rrc o rc"
                else:
                    return "ERROR: parametro desconocido"

                self.generar_filtro()
                return "OK -> " + self.estado()

            except ValueError:
                return "ERROR: valor invalido"

        if partes[0] == "gen":
            self.generar_filtro()
            return "OK: filtro generado -> " + self.estado()

        if partes[0] == "coef":
            texto = "\nCOEFICIENTES:\n"
            for i, value in enumerate(self.filtro.get_coefficients()):
                texto += f"h[{i}] = {value:.8f}\n"
            return texto

        if partes[0] == "plot":
            if len(partes) != 2:
                return "ERROR: usar plot time, plot freq o plot both"

            if partes[1] == "time":
                self.filtro.plot_time()
                return "OK: grafica temporal discreta generada"
            if partes[1] == "freq":
                self.filtro.plot_frequency()
                return "OK: grafica en frecuencia generada"
            if partes[1] == "both":
                self.filtro.plot_both()
                return "OK: grafica temporal + frecuencia generada"
            return "ERROR: usar plot time, plot freq o plot both"

        if partes[0] == "compare":
            compare_filters([0.0, 0.25, 0.5, 1.0], self.span, self.sps, self.rrc)
            return "OK: comparacion generada"

        if partes[0] == "signal":
            plot_filtered_bpsk(self.filtro)
            return "OK: senal BPSK filtrada generada"

        if partes[0] == "export":
            self.filtro.export_coefficients("coeficientes.txt")
            return "OK: coeficientes exportados en coeficientes.txt"

        if partes[0] == "exit":
            return "EXIT"

        return "ERROR: comando no reconocido. Escribi help"


def main():
    controlador = ControladorFiltro()
    serie = ComunicacionSerie(port="loop://", baudrate=9600, timeout=1, virtual=True)
    serie.open()

    print("==================================================")
    print(" TP1 Python - Filtros controlados por puerto serie")
    print("==================================================")
    print("Modo: puerto serie virtual loop://")
    print("Escribi help para ver comandos.")
    print("Escribi exit para terminar.")
    print("CONFIG INICIAL ->", controlador.estado())
    print()

    while True:
        comando_usuario = input("ToSent: ")

        serie.send_command(comando_usuario)
        comando_recibido = serie.read_line()

        print("RX serie:", comando_recibido)
        respuesta = controlador.procesar_comando(comando_recibido)

        if respuesta == "EXIT":
            break

        print(">>", respuesta)
        print()

    serie.close()
    print("Programa finalizado.")


if __name__ == "__main__":
    main()
