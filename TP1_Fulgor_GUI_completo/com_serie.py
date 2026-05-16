"""
com_serie.py

Modulo de comunicacion serie para el TP1.

Por defecto usa loop:// como puerto serie virtual.
Asi se puede probar sin FPGA, ESP32 ni hardware real.
"""

import time
import serial


class ComunicacionSerie:
    def __init__(self, port="loop://", baudrate=9600, timeout=1, virtual=True):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.virtual = virtual
        self.ser = None

    def open(self):
        if self.virtual:
            self.ser = serial.serial_for_url(
                self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
        else:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=self.timeout
            )

        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

    def close(self):
        if self.ser is not None and self.ser.is_open:
            self.ser.close()

    def is_open(self):
        return self.ser is not None and self.ser.is_open

    def send_command(self, command):
        if not self.is_open():
            raise RuntimeError("El puerto serie no esta abierto")

        if not command.endswith("\n"):
            command += "\n"

        self.ser.write(command.encode("utf-8"))

    def read_line(self):
        if not self.is_open():
            raise RuntimeError("El puerto serie no esta abierto")

        line = self.ser.readline()
        return line.decode("utf-8", errors="ignore").strip()

    def send_and_receive(self, command, wait_time=0.05):
        self.send_command(command)
        time.sleep(wait_time)
        return self.read_line()
