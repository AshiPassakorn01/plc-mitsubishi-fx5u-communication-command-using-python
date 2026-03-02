import os , sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import tkinter as tk
from tkinter import ttk

class ServoMonitorUI:
    def __init__(self, master, plc_controller):
        """
        GUI สำหรับมอนิเตอร์สถานะ แกน 1-4 (Fixed Unit: Pulse, PPS)
        """
        self.master = master
        self.plc = plc_controller
        
        if isinstance(self.master, tk.Tk) or isinstance(self.master, tk.Toplevel):
            self.master.title("Servo Multi-Axis Monitor")
            self.master.geometry("350x300")
            self.master.attributes("-topmost", True) # ให้อยู่บนสุดเสมอจะได้ดูง่ายๆ
        
        self.axis_data = {}
        
        self.setup_ui()
        self.update_monitor()

    def setup_ui(self):
        main_frame = ttk.Frame(self.master, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="Real-Time Position & Speed", font=("Arial", 12, "bold")).pack(pady=(0, 10))

        for axis in range(1, 5):
            frame = ttk.LabelFrame(main_frame, text=f"Axis {axis} Status")
            frame.pack(fill="x", pady=2, padx=5)
            
            pos_var = tk.StringVar(value="0 pulse")
            spd_var = tk.StringVar(value="0 pps")
            
            self.axis_data[axis] = {"pos": pos_var, "spd": spd_var}
            
            row = ttk.Frame(frame)
            row.pack(fill="x", padx=5, pady=2)
            
            ttk.Label(row, text="Position:", width=10).pack(side="left")
            ttk.Label(row, textvariable=pos_var, width=15, foreground="blue").pack(side="left")
            
            ttk.Label(row, text="Speed:", width=8).pack(side="left")
            ttk.Label(row, textvariable=spd_var, width=15, foreground="green").pack(side="left")

    def update_monitor(self):
        """
        ฟังก์ชันอ่านค่าจาก PLC และอัปเดต UI (วนลูปตัวเองทุกๆ 500ms)
        """
        if self.plc and self.plc.client and self.plc.client.is_socket_open():
            for axis in range(1, 5):

                offset = (axis - 1) * 40
                pos_addr = 5500 + offset
                spd_addr = 5504 + offset
                
                pos_val, pos_ok = self.plc.read_holding_32bit(pos_addr)
                spd_val, spd_ok = self.plc.read_holding_32bit(spd_addr)
                
                if pos_ok:
                    self.axis_data[axis]["pos"].set(f"{pos_val} pulse")
                if spd_ok:
                    self.axis_data[axis]["spd"].set(f"{spd_val} pps")
        else:
            for axis in range(1, 5):
                self.axis_data[axis]["pos"].set("Offline")
                self.axis_data[axis]["spd"].set("Offline")

        self.master.after(500, self.update_monitor)


if __name__ == "__main__":
    from basic.plc_module import PLCController
    
    test_plc = PLCController(config_print=False)
    test_plc.plcConnect("192.168.3.250", 502)
    
    root = tk.Tk()
    app = ServoMonitorUI(root, test_plc)
    root.mainloop()