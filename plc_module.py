from pymodbus.client import ModbusTcpClient

class PLCController:
    def __init__(self):
        self.client = None

    def plcConnect(self, ip: str, port: int = 502) -> bool:
        self.client = ModbusTcpClient(host=ip, port=port)
        if self.client.connect():
            #print(f"[PLC] Connected successfully to {ip}:{port}")
            return True
        else:
            #print(f"[PLC] Failed to connect to {ip}:{port}")
            return False

    def plcDisconnect(self) -> bool:
        if self.client:
            self.client.close()
            self.client = None
            #print("[PLC] Disconnected successfully.")
            return True
        return False

    def write_coil(self, address: int, value: bool) -> bool:
        if not self.client:
            #print("[PLC] Error: Not connected!")
            return False
            
        try:
            # ใช้คำสั่ง write_coil เพื่อสั่งงานเปิด/ปิด
            self.client.write_coil(address, value)
            state_str = "ON" if value else "OFF"
            #print(f"[PLC] Wrote Coil {address} -> {state_str}")
            return True
        except Exception as e:
            #rint(f"[PLC] Write Coil Error: {e}")
            return False

    def write_holding(self, address: int, value: int) -> bool:

        if not self.client:
            #print("[PLC] Error: Not connected!")
            return False
            
        try:
            self.client.write_register(address, int(value))
            #print(f"[PLC] Wrote Holding Register {address} -> {int(value)}")
            return True
        except Exception as e:
            #print(f"[PLC] Write Holding Error: {e}")
            return False
        
    def read_holding(self, address: int) -> tuple[float, bool]:
        if not self.client:
            #print("[PLC] Error: Not connected!")
            return 0.0, False
            
        try:
            result = self.client.read_holding_registers(address, count=1)
            
            if not result.isError():
                val = float(result.registers[0])
                #print(f"[PLC] Read Register {address} -> {val}")
                return val, True
            else:
                #print(f"[PLC] Read Error at Address {address}")
                return 0.0, False
                
        except Exception as e:
            #print(f"[PLC] Read Exception: {e}")
            return 0.0, False
        
    def read_coil(self, address: int) -> tuple[bool, bool]:

        if not self.client:
            #print("[PLC] Error: Not connected!")
            return False, False
            
        try:
            result = self.client.read_coils(address, count=1)
            
            if not result.isError():
                val = result.bits[0]
                #print(f"[PLC] Read M/Y Address {address} -> {'ON' if val else 'OFF'}")
                return val, True
            else:
                #print(f"[PLC] Read Error at M/Y Address {address}")
                return False, False
        except Exception as e:
            #print(f"[PLC] Read Exception: {e}")
            return False, False

    def read_input(self, address: int) -> tuple[bool, bool]:
        if not self.client:
            #print("[PLC] Error: Not connected!")
            return False, False
            
        try:
            result = self.client.read_discrete_inputs(address, count=1)
            
            if not result.isError():
                val = result.bits[0]
                #print(f"[PLC] Read X Address {address} -> {'ON' if val else 'OFF'}")
                return val, True
            else:
                #print(f"[PLC] Read Error at X Address {address}")
                return False, False
        except Exception as e:
            #print(f"[PLC] Read Exception: {e}")
            return False, False