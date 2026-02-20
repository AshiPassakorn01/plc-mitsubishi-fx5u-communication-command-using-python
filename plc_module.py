from pymodbus.client import ModbusTcpClient

class PLCController:
    def __init__(self, config_print: bool = True):
        self.client = None
        self.config_print = config_print
        
        # ----------------------------------------------------
        # Modbus Address Offsets 
        # (แก้ไขให้ตรงกับ Modbus Device Assignment ใน GX Works3)
        # ----------------------------------------------------
        self.offset_y = 0      # สมมติ Y เริ่มที่ Modbus Address 0
        self.offset_m = 8192   # สมมติ M เริ่มที่ Modbus Address 8192
        self.offset_d = 0      # สมมติ D เริ่มที่ Holding Register 0
        self.offset_x = 0      # สมมติ X เริ่มที่ Input Register 0

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
        # บวก Offset ของ Y เข้าไป
        modbus_addr = address + self.offset_y
        return self._execute_write_coil(modbus_addr, status, f"Output Y{address}")

    def write_M(self, address: int, status: bool) -> bool:
        # บวก Offset ของ M เข้าไป
        modbus_addr = address + self.offset_m
        return self._execute_write_coil(modbus_addr, status, f"Relay M{address}")

    def _execute_write_coil(self, modbus_address: int, status: bool, label: str) -> bool:
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

    def write_holding(self, address: int, value: int) -> bool:
        if not self.client or not self.client.is_socket_open():
            self._display("Error: Not connected!")
            return False
            
        modbus_addr = address + self.offset_d
        try:
            result = self.client.write_register(modbus_addr, int(value))
            if not result.isError():
                self._display(f"Wrote Holding Reg D{address} (Addr: {modbus_addr}) -> {int(value)}")
                return True
            else:
                self._display(f"Write Holding Error at D{address}")
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
            
        modbus_addr = address + self.offset_d
        try:
            result = self.client.read_holding_registers(modbus_addr, count=1)
            if not result.isError():
                val = float(result.registers[0])
                self._display(f"Read Reg D{address} (Addr: {modbus_addr}) -> {val}")
                return val, True
            else:
                self._display(f"Read Error at D{address}")
                return 0.0, False
        except Exception as e:
            self._display(f"Read Exception: {e}")
            return 0.0, False

    # แยกฟังก์ชันอ่าน Y และ M ออกจากกันให้ชัดเจน
    def read_Y(self, address: int) -> tuple[bool, bool]:
        modbus_addr = address + self.offset_y
        return self._execute_read_coil(modbus_addr, f"Output Y{address}")

    def read_M(self, address: int) -> tuple[bool, bool]:
        modbus_addr = address + self.offset_m
        return self._execute_read_coil(modbus_addr, f"Relay M{address}")

    def _execute_read_coil(self, modbus_address: int, label: str) -> tuple[bool, bool]:
        if not self.client or not self.client.is_socket_open():
            self._display("Error: Not connected!")
            return False, False
            
        try:
            result = self.client.read_coils(modbus_address, count=1)
            if not result.isError():
                val = result.bits[0]
                self._display(f"Read {label} (Addr: {modbus_address}) -> {'ON' if val else 'OFF'}")
                return val, True
            else:
                self._display(f"Read Error at {label}")
                return False, False
        except Exception as e:
            self._display(f"Read Exception: {e}")
            return False, False

    def read_input(self, address: int) -> tuple[bool, bool]:
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
            else:
                self._display(f"Read Error at X{address}")
                return False, False
        except Exception as e:
            self._display(f"Read Exception: {e}")
            return False, False