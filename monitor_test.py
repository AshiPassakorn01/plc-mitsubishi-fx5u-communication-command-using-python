import tkinter as tk
from tkinter import messagebox
from plc_module import PLCController

class PLCMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PLC Modbus Monitor")
        self.root.geometry("850x650")
        
        # Initialize PLC with config_print=False to avoid flooding the console
        self.plc = PLCController(config_print=False)
        self.is_connected = False
        
        self.x_labels = []
        self.y_labels = []
        self.m_labels = {}
        self.d_labels = {}
        
        self.blink_state = False
        
        self.create_widgets()
        self.update_data()

    def create_widgets(self):
        # --- 1. Connection & Refresh Rate ---
        conn_frame = tk.Frame(self.root, pady=10)
        conn_frame.pack(fill=tk.X, padx=10)
        
        tk.Label(conn_frame, text="IP Address:").pack(side=tk.LEFT, padx=5)
        self.ip_entry = tk.Entry(conn_frame, width=15)
        self.ip_entry.insert(0, "192.168.3.250")
        self.ip_entry.pack(side=tk.LEFT, padx=5)
        
        self.btn_connect = tk.Button(conn_frame, text="Connect", command=self.toggle_connect, bg="lightgray", width=10)
        self.btn_connect.pack(side=tk.LEFT, padx=5)

        tk.Label(conn_frame, text=" | ").pack(side=tk.LEFT)

        tk.Label(conn_frame, text="Refresh (ms):").pack(side=tk.LEFT, padx=5)
        self.refresh_entry = tk.Entry(conn_frame, width=6)
        self.refresh_entry.insert(0, "500")
        self.refresh_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(conn_frame, text="Status:").pack(side=tk.LEFT, padx=5)
        self.status_led = tk.Label(conn_frame, width=2, bg="gray", relief=tk.SUNKEN)
        self.status_led.pack(side=tk.LEFT, padx=5)

        # --- 2. Address Settings M and D ---
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

        # --- 3. Display Grids ---
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
            
            # Loop for M labels
            for i in range(a, b + 1):
                lbl = tk.Label(self.m_frame, text=f"M{i}", width=6, bg="gray", fg="white", relief=tk.RAISED)
                lbl.pack(side=tk.LEFT, padx=2)
                self.m_labels[i] = lbl
                
            # Loop for D labels
            for i in range(c, d + 1):
                lbl = tk.Label(self.d_frame, text=f"D{i}\n0", width=8, bg="white", fg="black", relief=tk.SUNKEN)
                lbl.pack(side=tk.LEFT, padx=2)
                self.d_labels[i] = lbl
                
        except ValueError:
            messagebox.showerror("Error", "Please enter valid integers for start and end ranges.")

    def toggle_connect(self):
        if not self.is_connected:
            ip = self.ip_entry.get()
            if self.plc.plcConnect(ip):
                self.is_connected = True
                self.btn_connect.config(text="Disconnect", bg="green", fg="white")
            else:
                messagebox.showerror("Connection Error", "Failed to connect to PLC.")
        else:
            self.plc.plcDisconnect()
            self.is_connected = False
            self.btn_connect.config(text="Connect", bg="lightgray", fg="black")
            self.status_led.config(bg="gray")
            self.reset_colors()

    def reset_colors(self):
        for lbl in self.x_labels + self.y_labels + list(self.m_labels.values()):
            lbl.config(bg="gray")
        for i, lbl in self.d_labels.items():
            lbl.config(text=f"D{i}\n0")

    def update_data(self):
        try:
            refresh_rate = int(self.refresh_entry.get())
            if refresh_rate < 50: refresh_rate = 50 
        except ValueError:
            refresh_rate = 500

        if self.is_connected:
            # 1. Read X0-X15
            for i in range(16):
                val, ok = self.plc.read_input(i)
                if ok: self.x_labels[i].config(bg="green" if val else "gray")
                
            # 2. Read Y0-Y15 (Using read_Y)
            for i in range(16):
                val, ok = self.plc.read_Y(i)
                if ok: self.y_labels[i].config(bg="red" if val else "gray")
                
            # 3. Read M (Using read_M)
            for addr, lbl in self.m_labels.items():
                val, ok = self.plc.read_M(addr) 
                if ok: lbl.config(bg="orange" if val else "gray")
                
            # 4. Read D (Handling Signed 16-bit)
            for addr, lbl in self.d_labels.items():
                val, ok = self.plc.read_holding(addr)
                if ok:
                    int_val = int(val)
                    if int_val > 32767:
                        int_val -= 65536
                    lbl.config(text=f"D{addr}\n{int_val}")

            self.blink_state = not self.blink_state
            self.status_led.config(bg="yellow" if self.blink_state else "gray")

        # Re-schedule the update
        self.root.after(refresh_rate, self.update_data)
            
if __name__ == "__main__":
    root = tk.Tk()
    app = PLCMonitorGUI(root)
    root.mainloop()