from pymodbus.client import ModbusTcpClient

class PLCController:
    def __init__(self, config_print: bool = True):
        self.client = None
        self.config_print = config_print

    def _display(self, message: str):
        if self.config_print:
            print(f"[PLC] {message}")
            
    # ----------------------------------------------------
    # Connection Methods
    # ----------------------------------------------------
    def plcConnect(self, ip: str, port: int = 502) -> bool:
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
        if self.client:
            self.client.close()
            self.client = None
            self._display("Disconnected successfully.")
            return True
        return False
    
    # ----------------------------------------------------
    # Write Methods (Returns True / False)
    # ----------------------------------------------------
    
    def write_Y(self, address: int, status: bool) -> bool:
        return self._execute_write_coil(address, status, "Output Y")

    def write_M(self, address: int, status: bool) -> bool:
        return self._execute_write_coil(address, status, "Relay M")

    def _execute_write_coil(self, address: int, status: bool, label: str) -> bool:
        if not self.client or not self.client.is_socket_open():
            self._display("Error: Not connected!")
            return False
        
        try:
            result = self.client.write_coil(address, status)
            if not result.isError():
                state_str = "ON" if status else "OFF"
                self._display(f"Wrote {label} {address} -> {state_str}")
                return True
            else:
                self._display(f"Modbus Error writing {label} {address}")
                return False
        except Exception as e:
            self._display(f"Exception writing {label} {address}: {e}")
            return False

    def write_holding(self, address: int, value: int) -> bool:
        if not self.client or not self.client.is_socket_open():
            self._display("Error: Not connected!")
            return False
            
        try:
            result = self.client.write_register(address, int(value))
            if not result.isError():
                self._display(f"Wrote Holding Register {address} -> {int(value)}")
                return True
            else:
                self._display(f"Write Holding Error at Address {address}")
                return False
        except Exception as e:
            self._display(f"Write Holding Exception: {e}")
            return False
        
    # ----------------------------------------------------
    # Read Methods (Returns Tuple: Value, Success Status)
    # ----------------------------------------------------
    
    def read_holding(self, address: int) -> tuple[float, bool]:
        if not self.client or not self.client.is_socket_open():
            self._display("Error: Not connected!")
            return 0.0, False
            
        try:
            result = self.client.read_holding_registers(address, count=1)
            if not result.isError():
                val = float(result.registers[0])
                self._display(f"Read Register {address} -> {val}")
                return val, True
            else:
                self._display(f"Read Error at Address {address}")
                return 0.0, False
        except Exception as e:
            self._display(f"Read Exception: {e}")
            return 0.0, False
        
    def read_coil(self, address: int) -> tuple[bool, bool]:
        if not self.client or not self.client.is_socket_open():
            self._display("Error: Not connected!")
            return False, False
            
        try:
            result = self.client.read_coils(address, count=1)
            if not result.isError():
                val = result.bits[0]
                self._display(f"Read M/Y Address {address} -> {'ON' if val else 'OFF'}")
                return val, True
            else:
                self._display(f"Read Error at M/Y Address {address}")
                return False, False
        except Exception as e:
            self._display(f"Read Exception: {e}")
            return False, False

    def read_input(self, address: int) -> tuple[bool, bool]:
        if not self.client or not self.client.is_socket_open():
            self._display("Error: Not connected!")
            return False, False
            
        try:
            result = self.client.read_discrete_inputs(address, count=1)
            if not result.isError():
                val = result.bits[0]
                self._display(f"Read X Address {address} -> {'ON' if val else 'OFF'}")
                return val, True
            else:
                self._display(f"Read Error at X Address {address}")
                return False, False
        except Exception as e:
            self._display(f"Read Exception: {e}")
            return False, False