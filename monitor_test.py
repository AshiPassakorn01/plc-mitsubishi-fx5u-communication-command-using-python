import tkinter as tk
from tkinter import messagebox
from plc_module import PLCController

class PLCMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PLC Modbus Monitor")
        self.root.geometry("850x650")
        
        self.plc = PLCController()
        self.is_connected = False
        
        self.x_labels = []
        self.y_labels = []
        self.m_labels = {}
        self.d_labels = {}
        
        # ตัวแปรสถานะไฟกะพริบ
        self.blink_state = False
        
        self.create_widgets()
        self.update_data()

    def create_widgets(self):
        # --- 1. แถบเชื่อมต่อ และ Refresh Rate ---
        conn_frame = tk.Frame(self.root, pady=10)
        conn_frame.pack(fill=tk.X, padx=10)
        
        tk.Label(conn_frame, text="IP Address:").pack(side=tk.LEFT, padx=5)
        self.ip_entry = tk.Entry(conn_frame, width=15)
        self.ip_entry.insert(0, "192.168.3.250")
        self.ip_entry.pack(side=tk.LEFT, padx=5)
        
        self.btn_connect = tk.Button(conn_frame, text="Connect", command=self.toggle_connect, bg="lightgray", width=10)
        self.btn_connect.pack(side=tk.LEFT, padx=5)

        # ขีดเส้นคั่น
        tk.Label(conn_frame, text=" | ").pack(side=tk.LEFT)

        # ช่องปรับ Refresh Rate
        tk.Label(conn_frame, text="Refresh (ms):").pack(side=tk.LEFT, padx=5)
        self.refresh_entry = tk.Entry(conn_frame, width=6)
        self.refresh_entry.insert(0, "500")
        self.refresh_entry.pack(side=tk.LEFT, padx=5)

        # ไฟกะพริบแสดงสถานะการอ่าน (Tx/Rx)
        tk.Label(conn_frame, text="Status:").pack(side=tk.LEFT, padx=5)
        self.status_led = tk.Label(conn_frame, width=2, bg="gray", relief=tk.SUNKEN)
        self.status_led.pack(side=tk.LEFT, padx=5)

        # --- 2. แถบตั้งค่า Address M และ D ---
        setting_frame = tk.Frame(self.root, pady=10)
        setting_frame.pack(fill=tk.X, padx=10)
        
        tk.Label(setting_frame, text="M [START]:").pack(side=tk.LEFT)
        self.m_start = tk.Entry(setting_frame, width=5)
        self.m_start.insert(0, "0")
        self.m_start.pack(side=tk.LEFT, padx=2)
        
        tk.Label(setting_frame, text="to [END]:").pack(side=tk.LEFT)
        self.m_end = tk.Entry(setting_frame, width=5)
        self.m_end.insert(0, "5")
        self.m_end.pack(side=tk.LEFT, padx=2)
        
        tk.Label(setting_frame, text=" | D [START]:").pack(side=tk.LEFT)
        self.d_start = tk.Entry(setting_frame, width=5)
        self.d_start.insert(0, "0")
        self.d_start.pack(side=tk.LEFT, padx=2)
        
        tk.Label(setting_frame, text="to [END]:").pack(side=tk.LEFT)
        self.d_end = tk.Entry(setting_frame, width=5)
        self.d_end.insert(0, "5")
        self.d_end.pack(side=tk.LEFT, padx=2)
        
        tk.Button(setting_frame, text="Update M, D", command=self.build_dynamic_grids).pack(side=tk.LEFT, padx=10)

        # --- 3. ส่วนแสดงผลตาราง ---
        x_frame = tk.LabelFrame(self.root, text="Input (X0 - X15)", padx=10, pady=10)
        x_frame.pack(fill=tk.X, padx=10, pady=5)
        for i in range(16):
            lbl = tk.Label(x_frame, text=f"X{i}", width=6, bg="gray", fg="white", relief=tk.RAISED)
            lbl.grid(row=i//8, column=i%8, padx=2, pady=2)
            self.x_labels.append(lbl)

        y_frame = tk.LabelFrame(self.root, text="Output (Y0 - Y15)", padx=10, pady=10)
        y_frame.pack(fill=tk.X, padx=10, pady=5)
        for i in range(16):
            lbl = tk.Label(y_frame, text=f"Y{i}", width=6, bg="gray", fg="white", relief=tk.RAISED)
            lbl.grid(row=i//8, column=i%8, padx=2, pady=2)
            self.y_labels.append(lbl)

        self.m_frame = tk.LabelFrame(self.root, text="Relay (M)", padx=10, pady=10)
        self.m_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.d_frame = tk.LabelFrame(self.root, text="Data Register (D)", padx=10, pady=10)
        self.d_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.build_dynamic_grids()

    def build_dynamic_grids(self):
        for widget in self.m_frame.winfo_children(): widget.destroy()
        for widget in self.d_frame.winfo_children(): widget.destroy()
        self.m_labels.clear()
        self.d_labels.clear()
        
        try:
            a, b = int(self.m_start.get()), int(self.m_end.get())
            c, d = int(self.d_start.get()), int(self.d_end.get())
            
            for i in range(a, b + 1):
                lbl = tk.Label(self.m_frame, text=f"M{i}", width=6, bg="gray", fg="white", relief=tk.RAISED)
                lbl.pack(side=tk.LEFT, padx=2)
                self.m_labels[i] = lbl
                
            for i in range(c, d + 1):
                lbl = tk.Label(self.d_frame, text=f"D{i}\n0", width=8, bg="white", fg="black", relief=tk.SUNKEN)
                lbl.pack(side=tk.LEFT, padx=2)
                self.d_labels[i] = lbl
                
        except ValueError:
            messagebox.showerror("Error", "กรุณาใส่ตัวเลข a, b, c, d ให้ถูกต้อง")

    def toggle_connect(self):
        if not self.is_connected:
            ip = self.ip_entry.get()
            if self.plc.plcConnect(ip):
                self.is_connected = True
                self.btn_connect.config(text="Disconnect", bg="green", fg="white")
            else:
                messagebox.showerror("Connection Error", "ไม่สามารถเชื่อมต่อ PLC ได้")
        else:
            self.plc.plcDisconnect()
            self.is_connected = False
            self.btn_connect.config(text="Connect", bg="lightgray", fg="black")
            self.status_led.config(bg="gray") # ปิดไฟสถานะเมื่อตัดการเชื่อมต่อ
            self.reset_colors()

    def reset_colors(self):
        for lbl in self.x_labels + self.y_labels + list(self.m_labels.values()):
            lbl.config(bg="gray")
        for i, lbl in self.d_labels.items():
            lbl.config(text=f"D{i}\n0")

    def update_data(self):
        # ดึงค่า Refresh Rate จากช่องกรอก (ถ้าผู้ใช้พิมพ์ผิดให้ใช้ 500ms เป็นค่าพื้นฐาน)
        try:
            refresh_rate = int(self.refresh_entry.get())
            if refresh_rate < 50: refresh_rate = 50 # ป้องกันการใส่ค่าน้อยเกินไปจนโปรแกรมค้าง
        except ValueError:
            refresh_rate = 500

        if self.is_connected:
            # 1. อ่านค่า X0-X15
            for i in range(16):
                val, ok = self.plc.read_input(i)
                if ok: self.x_labels[i].config(bg="green" if val else "gray")
                
            # 2. อ่านค่า Y0-Y15
            for i in range(16):
                val, ok = self.plc.read_coil(i)
                if ok: self.y_labels[i].config(bg="red" if val else "gray")
                
            # 3. อ่านค่า M
            for addr, lbl in self.m_labels.items():
                val, ok = self.plc.read_coil(addr) 
                if ok: lbl.config(bg="orange" if val else "gray")
                
            # 4. อ่านค่า D
            for addr, lbl in self.d_labels.items():
                val, ok = self.plc.read_holding(addr)
                if ok: lbl.config(text=f"D{addr}\n{int(val)}")

            # สลับสถานะไฟกะพริบ (Blink) เพื่อแสดงว่ามีการส่ง-รับข้อมูลอยู่จริง
            self.blink_state = not self.blink_state
            self.status_led.config(bg="yellow" if self.blink_state else "gray")

        # วนลูปรันตัวเองตาม Refresh Rate ที่ตั้งไว้
        self.root.after(refresh_rate, self.update_data)
            
if __name__ == "__main__":
    root = tk.Tk()
    app = PLCMonitorGUI(root)
    root.mainloop()