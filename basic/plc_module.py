import time
import threading
from pymodbus.client import ModbusTcpClient

class PLCController:
    def __init__(self, config_print: bool = False):
        self.client = None
        self.config_print = config_print
        
        self.lock = threading.Lock() 
        
        self.offset_y = 0
        self.offset_m = 8192
        self.offset_d = 0
        self.offset_x = 0

    def _display(self, message: str):
        if self.config_print:
            print(f"[PLC] {message}")
            
    def plcConnect(self, ip: str, port: int = 502) -> bool:
        with self.lock:
            try:
                self.client = ModbusTcpClient(host=ip, port=port, timeout=3)
                if self.client.connect():
                    self._display(f"Connected to {ip}:{port}")
                    return True
                self._display(f"Failed to connect to {ip}:{port}")
                return False
            except Exception as e:
                self._display(f"Connect Exception: {e}")
                return False
        
    def plcDisconnect(self) -> bool:
        with self.lock:
            if self.client:
                self.client.close()
                self.client = None
                self._display("Disconnected successfully.")
                return True
            return False
    
    def write_Y(self, address: int, status: bool) -> bool:
        modbus_addr = address + self.offset_y
        return self._execute_write_coil(modbus_addr, status, f"Output Y{address}")

    def write_M(self, address: int, status: bool) -> bool:
        modbus_addr = address + self.offset_m
        return self._execute_write_coil(modbus_addr, status, f"Relay M{address}")

    # --- OPTIMIZE: write many M at once (Batch) ---
    def write_M_batch(self, address: int, values: list) -> bool:
        with self.lock:
            if not self.client or not self.client.is_socket_open():
                return False
            modbus_addr = address + self.offset_m
            try:
                result = self.client.write_coils(modbus_addr, values)
                if not result.isError():
                    self._display(f"Wrote Batch M{address} to M{address+len(values)-1} -> {values}")
                    return True
                return False
            except Exception as e:
                self._display(f"Write Batch M Exception: {e}")
                return False

    def _execute_write_coil(self, modbus_address: int, status: bool, label: str) -> bool:
        with self.lock:
            if not self.client or not self.client.is_socket_open():
                self._display("Error: Not connected!")
                return False
            try:
                result = self.client.write_coil(modbus_address, status)
                if not result.isError():
                    state_str = "ON" if status else "OFF"
                    self._display(f"Wrote {label} (Addr: {modbus_address}) -> {state_str}")
                    return True
                else:
                    self._display(f"Modbus Error writing {label}")
                    return False
            except Exception as e:
                self._display(f"Exception writing {label}: {e}")
                return False

    def pulse_Y(self, address: int, duration: float = 0.5, blocking: bool = True) -> bool:
        if blocking:
            return self._execute_pulse(self.write_Y, address, duration)
        else:
            threading.Thread(target=self._execute_pulse, args=(self.write_Y, address, duration), daemon=True).start()
            return True

    def pulse_M(self, address: int, duration: float = 0.5, blocking: bool = True) -> bool:
        if blocking:
            return self._execute_pulse(self.write_M, address, duration)
        else:
            threading.Thread(target=self._execute_pulse, args=(self.write_M, address, duration), daemon=True).start()
            return True

    def _execute_pulse(self, write_func, address: int, duration: float) -> bool:
        if write_func(address, True):
            time.sleep(duration)
            return write_func(address, False)
        return False

    def write_holding(self, address: int, value: int) -> bool:
        with self.lock:
            if not self.client or not self.client.is_socket_open():
                self._display("Error: Not connected!")
                return False
            modbus_addr = address + self.offset_d
            try:
                result = self.client.write_register(modbus_addr, int(value))
                if not result.isError():
                    self._display(f"Wrote Holding Reg D{address} (Addr: {modbus_addr}) -> {int(value)}")
                    return True
                return False
            except Exception as e:
                self._display(f"Write Holding Exception: {e}")
                return False
            
    def write_holding_32bit(self, address: int, value: int) -> bool:
        with self.lock:
            if not self.client or not self.client.is_socket_open():
                self._display("Error: Not connected!")
                return False
            modbus_addr = address + self.offset_d
            try:
                val_32 = int(value) & 0xFFFFFFFF
                low_word = val_32 & 0xFFFF
                high_word = (val_32 >> 16) & 0xFFFF
                result = self.client.write_registers(modbus_addr, [low_word, high_word])
                if not result.isError():
                    self._display(f"Wrote 32-bit Reg D{address} (Addr: {modbus_addr}) -> {int(value)}")
                    return True
                return False
            except Exception as e:
                self._display(f"Write 32-bit Exception: {e}")
                return False

    # --- OPTIMIZE: write many 32-bit registers at once (Batch) ---
    def write_holding_32bit_batch(self, address: int, values: list) -> bool:
        with self.lock:
            if not self.client or not self.client.is_socket_open():
                return False
            modbus_addr = address + self.offset_d
            try:
                registers = []
                for val in values:
                    val_32 = int(val) & 0xFFFFFFFF
                    registers.extend([val_32 & 0xFFFF, (val_32 >> 16) & 0xFFFF])
                result = self.client.write_registers(modbus_addr, registers)
                if not result.isError():
                    self._display(f"Wrote 32-bit Batch D{address} -> {values}")
                    return True
                return False
            except Exception as e:
                self._display(f"Write 32-bit Batch Exception: {e}")
                return False

    def read_holding(self, address: int) -> tuple[float, bool]:
        with self.lock:
            if not self.client or not self.client.is_socket_open():
                self._display("Error: Not connected!")
                return 0.0, False
            modbus_addr = address + self.offset_d
            try:
                result = self.client.read_holding_registers(modbus_addr, count=1)
                if not result.isError():
                    val = float(result.registers[0])
                    self._display(f"Read Reg D{address} (Addr: {modbus_addr}) -> {val}")
                    return val, True
                return 0.0, False
            except Exception as e:
                self._display(f"Read Exception: {e}")
                return 0.0, False

    def read_holding_32bit(self, address: int) -> tuple[int, bool]:
        with self.lock:
            if not self.client or not self.client.is_socket_open():
                self._display("Error: Not connected!")
                return 0, False
            modbus_addr = address + self.offset_d
            try:
                result = self.client.read_holding_registers(modbus_addr, count=2)
                if not result.isError():
                    val_32 = (result.registers[1] << 16) | result.registers[0]
                    if val_32 > 0x7FFFFFFF:
                        val_32 -= 0x100000000
                    self._display(f"Read 32-bit Reg D{address} (Addr: {modbus_addr}) -> {val_32}")
                    return val_32, True
                return 0, False
            except Exception as e:
                self._display(f"Read 32-bit Exception: {e}")
                return 0, False

    # --- OPTIMIZE: read many M at once (Batch) ---
    def read_M_batch(self, address: int, count: int) -> tuple[list, bool]:
        with self.lock:
            if not self.client or not self.client.is_socket_open():
                return [False]*count, False
            modbus_addr = address + self.offset_m
            try:
                result = self.client.read_coils(modbus_addr, count=count)
                if not result.isError():
                    vals = result.bits[:count]
                    return vals, True
                return [False]*count, False
            except Exception as e:
                return [False]*count, False

    def read_Y(self, address: int) -> tuple[bool, bool]:
        return self._execute_read_coil(address + self.offset_y, f"Output Y{address}")

    def read_M(self, address: int) -> tuple[bool, bool]:
        return self._execute_read_coil(address + self.offset_m, f"Relay M{address}")

    def _execute_read_coil(self, modbus_address: int, label: str) -> tuple[bool, bool]:
        with self.lock:
            if not self.client or not self.client.is_socket_open():
                self._display("Error: Not connected!")
                return False, False
            try:
                result = self.client.read_coils(modbus_address, count=1)
                if not result.isError():
                    val = result.bits[0]
                    self._display(f"Read {label} (Addr: {modbus_address}) -> {'ON' if val else 'OFF'}")
                    return val, True
                return False, False
            except Exception as e:
                self._display(f"Read Exception: {e}")
                return False, False

    def read_input(self, address: int) -> tuple[bool, bool]:
        with self.lock:
            if not self.client or not self.client.is_socket_open():
                self._display("Error: Not connected!")
                return False, False
            modbus_addr = address + self.offset_x
            try:
                result = self.client.read_discrete_inputs(modbus_addr, count=1)
                if not result.isError():
                    val = result.bits[0]
                    self._display(f"Read Input X{address} (Addr: {modbus_addr}) -> {'ON' if val else 'OFF'}")
                    return val, True
                return False, False
            except Exception as e:
                self._display(f"Read Exception: {e}")
                return False, False