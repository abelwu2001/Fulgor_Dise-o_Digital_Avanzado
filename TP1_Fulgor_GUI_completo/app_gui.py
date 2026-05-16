import sys
import numpy as np
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg

from filtro import RaisedCosineFilter, bpsk_filtered_signal
from com_serie import ComunicacionSerie


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("TP1 Fulgor - Filtros por puerto serie virtual")
        self.resize(1280, 820)

        self.serie = None

        self.alpha = 0.25
        self.span = 6
        self.sps = 8
        self.rrc = True
        self.filtro = None
        self.generar_filtro()

        pg.setConfigOptions(antialias=True)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        # ================== Controles superiores ==================
        self.btn_connect = QtWidgets.QPushButton("Conectar puerto virtual")
        self.btn_connect.clicked.connect(self.toggle_serial)

        self.status_serial = QtWidgets.QLabel("Serie: desconectado")
        self.status_serial.setStyleSheet("font-weight: bold;")

        self.alpha_box = QtWidgets.QDoubleSpinBox()
        self.alpha_box.setRange(0.0, 1.0)
        self.alpha_box.setSingleStep(0.05)
        self.alpha_box.setValue(self.alpha)

        self.span_box = QtWidgets.QSpinBox()
        self.span_box.setRange(1, 50)
        self.span_box.setValue(self.span)

        self.sps_box = QtWidgets.QSpinBox()
        self.sps_box.setRange(1, 100)
        self.sps_box.setValue(self.sps)

        self.type_box = QtWidgets.QComboBox()
        self.type_box.addItems(["rrc", "rc"])

        self.btn_apply = QtWidgets.QPushButton("Aplicar config por serie")
        self.btn_apply.clicked.connect(self.apply_config_by_serial)

        form = QtWidgets.QGridLayout()
        form.addWidget(QtWidgets.QLabel("alpha"), 0, 0)
        form.addWidget(self.alpha_box, 0, 1)
        form.addWidget(QtWidgets.QLabel("span"), 0, 2)
        form.addWidget(self.span_box, 0, 3)
        form.addWidget(QtWidgets.QLabel("sps"), 0, 4)
        form.addWidget(self.sps_box, 0, 5)
        form.addWidget(QtWidgets.QLabel("tipo"), 0, 6)
        form.addWidget(self.type_box, 0, 7)
        form.addWidget(self.btn_apply, 0, 8)

        top = QtWidgets.QHBoxLayout()
        top.addWidget(self.btn_connect)
        top.addWidget(self.status_serial)
        top.addStretch(1)

        # ================== Botones de acciones ==================
        self.btn_gen = QtWidgets.QPushButton("Generar")
        self.btn_plot = QtWidgets.QPushButton("Actualizar gráficos")
        self.btn_compare = QtWidgets.QPushButton("Comparar filtros")
        self.btn_signal = QtWidgets.QPushButton("Señal BPSK filtrada")
        self.btn_export = QtWidgets.QPushButton("Exportar coeficientes")

        self.btn_gen.clicked.connect(lambda: self.send_serial_command("gen"))
        self.btn_plot.clicked.connect(self.update_all_plots)
        self.btn_compare.clicked.connect(self.plot_compare)
        self.btn_signal.clicked.connect(self.plot_signal)
        self.btn_export.clicked.connect(lambda: self.send_serial_command("export"))

        actions = QtWidgets.QHBoxLayout()
        actions.addWidget(self.btn_gen)
        actions.addWidget(self.btn_plot)
        actions.addWidget(self.btn_compare)
        actions.addWidget(self.btn_signal)
        actions.addWidget(self.btn_export)
        actions.addStretch(1)

        # ================== Entrada de comandos serie ==================
        self.command_line = QtWidgets.QLineEdit()
        self.command_line.setPlaceholderText("Escribí un comando: set alpha 0.5 | plot both | compare | coef | export")
        self.command_line.returnPressed.connect(self.send_command_from_line)

        self.btn_send = QtWidgets.QPushButton("Enviar por serie")
        self.btn_send.clicked.connect(self.send_command_from_line)

        command_row = QtWidgets.QHBoxLayout()
        command_row.addWidget(QtWidgets.QLabel("TX:"))
        command_row.addWidget(self.command_line, 1)
        command_row.addWidget(self.btn_send)

        # ================== Gráficos ==================
        self.plot_time = pg.PlotWidget(title="Respuesta temporal discreta")
        self.plot_time.setLabel("bottom", "Tiempo", units="símbolos")
        self.plot_time.setLabel("left", "Amplitud")
        self.plot_time.showGrid(x=True, y=True)

        self.plot_freq = pg.PlotWidget(title="Respuesta en frecuencia")
        self.plot_freq.setLabel("bottom", "Frecuencia normalizada")
        self.plot_freq.setLabel("left", "Magnitud", units="dB")
        self.plot_freq.showGrid(x=True, y=True)

        self.plot_compare_widget = pg.PlotWidget(title="Varios filtros en un mismo ploteo")
        self.plot_compare_widget.setLabel("bottom", "Frecuencia normalizada")
        self.plot_compare_widget.setLabel("left", "Magnitud", units="dB")
        self.plot_compare_widget.showGrid(x=True, y=True)
        self.plot_compare_widget.addLegend()

        self.plot_signal_widget = pg.PlotWidget(title="Señal BPSK filtrada")
        self.plot_signal_widget.setLabel("bottom", "Muestras")
        self.plot_signal_widget.setLabel("left", "Amplitud")
        self.plot_signal_widget.showGrid(x=True, y=True)

        plots = QtWidgets.QGridLayout()
        plots.addWidget(self.plot_time, 0, 0)
        plots.addWidget(self.plot_freq, 0, 1)
        plots.addWidget(self.plot_compare_widget, 1, 0)
        plots.addWidget(self.plot_signal_widget, 1, 1)

        # ================== Log ==================
        self.log = QtWidgets.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(150)

        # ================== Layout principal ==================
        layout = QtWidgets.QVBoxLayout(central)
        layout.addLayout(top)
        layout.addLayout(form)
        layout.addLayout(actions)
        layout.addLayout(command_row)
        layout.addLayout(plots, 1)
        layout.addWidget(QtWidgets.QLabel("Registro serie / respuestas"))
        layout.addWidget(self.log)

        self.update_all_plots()
        self.log_message("Listo. Conectá el puerto virtual y probá comandos como: help, status, set alpha 0.5, plot both.")

    # ================== Filtro ==================
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

    # ================== Serie ==================
    def toggle_serial(self):
        if self.serie is not None and self.serie.is_open():
            self.serie.close()
            self.status_serial.setText("Serie: desconectado")
            self.btn_connect.setText("Conectar puerto virtual")
            self.log_message("Puerto serie virtual cerrado.")
            return

        try:
            self.serie = ComunicacionSerie(port="loop://", baudrate=9600, timeout=1, virtual=True)
            self.serie.open()
            self.status_serial.setText("Serie: conectado en loop://")
            self.btn_connect.setText("Desconectar")
            self.log_message("Puerto serie virtual loop:// conectado.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"No se pudo abrir el puerto virtual:\n{e}")

    def ensure_serial(self):
        if self.serie is None or not self.serie.is_open():
            self.toggle_serial()
        return self.serie is not None and self.serie.is_open()

    def send_command_from_line(self):
        cmd = self.command_line.text().strip()
        if not cmd:
            return
        self.send_serial_command(cmd)
        self.command_line.clear()

    def send_serial_command(self, cmd):
        if not self.ensure_serial():
            return

        try:
            self.serie.send_command(cmd)
            rx = self.serie.read_line()

            self.log_message(f"TX -> {cmd}")
            self.log_message(f"RX serie -> {rx}")

            response = self.process_command(rx)
            self.log_message(f">> {response}")

            if rx.lower().startswith(("set", "gen")):
                self.sync_form()
                self.update_all_plots()

            if rx.lower() in ["plot both", "plot time", "plot freq"]:
                self.update_all_plots()

            if rx.lower() == "compare":
                self.plot_compare()

            if rx.lower() == "signal":
                self.plot_signal()

        except Exception as e:
            self.log_message(f"ERROR serie: {e}")

    def apply_config_by_serial(self):
        tipo = self.type_box.currentText()
        cmds = [
            f"set alpha {self.alpha_box.value()}",
            f"set span {self.span_box.value()}",
            f"set sps {self.sps_box.value()}",
            f"set type {tipo}",
            "gen"
        ]

        for cmd in cmds:
            self.send_serial_command(cmd)

    # ================== Procesador de comandos ==================
    def process_command(self, comando):
        partes = comando.lower().split()

        if len(partes) == 0:
            return "ERROR: comando vacio"

        if partes[0] == "help":
            return (
                "COMANDOS: status | set alpha 0.5 | set span 10 | "
                "set sps 8 | set type rrc | set type rc | gen | coef | "
                "plot time | plot freq | plot both | compare | signal | export"
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
                    value = float(valor)
                    if not (0 <= value <= 1):
                        return "ERROR: alpha debe estar entre 0 y 1"
                    self.alpha = value

                elif parametro == "span":
                    value = int(valor)
                    if value <= 0:
                        return "ERROR: span debe ser positivo"
                    self.span = value

                elif parametro == "sps":
                    value = int(valor)
                    if value <= 0:
                        return "ERROR: sps debe ser positivo"
                    self.sps = value

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
            coef = self.filtro.get_coefficients()
            texto = "COEFICIENTES:\n"
            for i, value in enumerate(coef[:20]):
                texto += f"h[{i}] = {value:.8f}\n"
            if len(coef) > 20:
                texto += f"... total de coeficientes: {len(coef)}"
            return texto

        if partes[0] == "plot":
            if len(partes) != 2:
                return "ERROR: usar plot time, plot freq o plot both"
            if partes[1] in ["time", "freq", "both"]:
                return f"OK: grafico {partes[1]} actualizado en interfaz"
            return "ERROR: usar plot time, plot freq o plot both"

        if partes[0] == "compare":
            return "OK: comparacion actualizada en interfaz"

        if partes[0] == "signal":
            return "OK: senal filtrada actualizada en interfaz"

        if partes[0] == "export":
            self.filtro.export_coefficients("coeficientes.txt")
            return "OK: coeficientes exportados en coeficientes.txt"

        return "ERROR: comando no reconocido. Escribi help"

    # ================== Graficos ==================
    def update_all_plots(self):
        self.plot_time.clear()
        self.plot_freq.clear()

        t = self.filtro.time_axis()
        h = self.filtro.get_coefficients()

        # Discreto: línea + puntos
        self.plot_time.plot(t, h, pen=pg.mkPen(width=1))
        self.plot_time.plot(t, h, pen=None, symbol="o", symbolSize=6)
        self.plot_time.addLine(y=0, pen=pg.mkPen(style=QtCore.Qt.DashLine))

        f, mag_db = self.filtro.frequency_response()
        self.plot_freq.plot(f, mag_db, pen=pg.mkPen(width=2))
        self.plot_freq.setYRange(max(-120, float(np.min(mag_db))), max(10, float(np.max(mag_db))), padding=0.05)

        self.plot_compare()
        self.plot_signal()

    def plot_compare(self):
        self.plot_compare_widget.clear()
        self.plot_compare_widget.addLegend()

        pens = [
            pg.mkPen(width=2),
            pg.mkPen(width=2, style=QtCore.Qt.DashLine),
            pg.mkPen(width=2, style=QtCore.Qt.DotLine),
            pg.mkPen(width=2, style=QtCore.Qt.DashDotLine)
        ]

        for idx, alpha in enumerate([0.0, 0.25, 0.5, 1.0]):
            filt = RaisedCosineFilter(
                alpha=alpha,
                span=self.span,
                sps=self.sps,
                rrc=self.rrc
            )
            f, mag_db = filt.frequency_response()
            self.plot_compare_widget.plot(
                f,
                mag_db,
                pen=pens[idx % len(pens)],
                name=f"alpha={alpha}"
            )

    def plot_signal(self):
        self.plot_signal_widget.clear()
        y = bpsk_filtered_signal(self.filtro, n_bits=32)
        self.plot_signal_widget.plot(np.arange(len(y)), y, pen=pg.mkPen(width=2))

    # ================== Utilidades ==================
    def sync_form(self):
        self.alpha_box.setValue(self.alpha)
        self.span_box.setValue(self.span)
        self.sps_box.setValue(self.sps)
        self.type_box.setCurrentText("rrc" if self.rrc else "rc")

    def log_message(self, text):
        self.log.appendPlainText(text)


def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
