import tkinter as tk
from tkinter import ttk, messagebox
import threading

# Import the ddrvi function from your main control file
try:
    from mj4r_servo import ddrvi
except ImportError:
    print("Warning: Could not import 'ddrvi' from mj4r_servo_controll. Make sure the file exists.")
    # Dummy function for testing UI without the real file
    def ddrvi(*args, **kwargs):
        print(f"[DUMMY] Executing DDRVI: {kwargs}")
        return True

class ServoJogUI:
    def __init__(self, master, ppr=3600, axis=1, sig_addr=110):
        self.master = master
        self.ppr = ppr
        self.axis = axis
        self.sig_addr = sig_addr
        
        # Frame container
        self.frame = ttk.LabelFrame(master, text=f"Axis {self.axis} Jog Control", padding=10)
        self.frame.pack(padx=10, pady=10, fill="x")

        # Variables
        self.current_unit = tk.StringVar(value="pulse")
        
        # StringVars for Entries to track their values
        self.step_var = tk.StringVar(value="3600.0")
        self.speed1_var = tk.StringVar(value="36000.0")
        self.speed2_var = tk.StringVar(value="180000.0")
        self.speed3_var = tk.StringVar(value="360000.0")

        self.setup_ui()

    def setup_ui(self):
        # --- Unit Selection ---
        unit_frame = ttk.Frame(self.frame)
        unit_frame.pack(fill="x", pady=5)
        ttk.Label(unit_frame, text="Unit Config:").pack(side="left", padx=5)
        
        unit_cb = ttk.Combobox(unit_frame, textvariable=self.current_unit, values=["pulse", "rev", "deg"], state="readonly", width=10)
        unit_cb.pack(side="left", padx=5)
        unit_cb.bind("<<ComboboxSelected>>", self.on_unit_change)

        # Labels for unit display
        self.lbl_step_unit = ttk.Label(unit_frame, text="[Step: pulse | Speed: pps]")
        self.lbl_step_unit.pack(side="left", padx=10)

        # --- Jog Step Distance ---
        step_frame = ttk.Frame(self.frame)
        step_frame.pack(fill="x", pady=5)
        ttk.Label(step_frame, text="Jog Step Dist:").pack(side="left", padx=5)
        ttk.Entry(step_frame, textvariable=self.step_var, width=15).pack(side="left", padx=5)

        # --- Jog Speeds Rows ---
        self.create_jog_row("Jog Speed 1:", self.speed1_var)
        self.create_jog_row("Jog Speed 2:", self.speed2_var)
        self.create_jog_row("Jog Speed 3:", self.speed3_var)

    def create_jog_row(self, label_text, speed_var):
        row = ttk.Frame(self.frame)
        row.pack(fill="x", pady=5)
        
        ttk.Label(row, text=label_text, width=12).pack(side="left", padx=5)
        ttk.Entry(row, textvariable=speed_var, width=15).pack(side="left", padx=5)
        
        btn_neg = ttk.Button(row, text="Jog -", command=lambda: self.execute_jog(speed_var.get(), direction=-1))
        btn_neg.pack(side="left", padx=5)
        
        btn_pos = ttk.Button(row, text="Jog +", command=lambda: self.execute_jog(speed_var.get(), direction=1))
        btn_pos.pack(side="left", padx=5)

    def on_unit_change(self, event):
        new_unit = self.current_unit.get()
        # Derive old unit from label to know what we are converting from
        old_unit_str = self.lbl_step_unit.cget("text")
        if "pulse" in old_unit_str: old_unit = "pulse"
        elif "rev" in old_unit_str: old_unit = "rev"
        else: old_unit = "deg"

        if old_unit == new_unit:
            return

        # Update labels
        unit_map = {"pulse": "pps", "rev": "rpm", "deg": "deg/s"}
        self.lbl_step_unit.config(text=f"[Step: {new_unit} | Speed: {unit_map[new_unit]}]")

        # Convert Values
        self.convert_entry_var(self.step_var, old_unit, new_unit, is_speed=False)
        self.convert_entry_var(self.speed1_var, old_unit, new_unit, is_speed=True)
        self.convert_entry_var(self.speed2_var, old_unit, new_unit, is_speed=True)
        self.convert_entry_var(self.speed3_var, old_unit, new_unit, is_speed=True)

    def convert_entry_var(self, var, old_unit, new_unit, is_speed=False):
        try:
            val = float(var.get())
        except ValueError:
            var.set("0.0")
            return

        # 1. Convert everything to Base (Pulse or PPS)
        base_val = 0.0
        if old_unit == "pulse":
            base_val = val
        elif old_unit == "rev":
            if is_speed: base_val = (val * self.ppr) / 60.0 # RPM to PPS
            else: base_val = val * self.ppr # Rev to Pulse
        elif old_unit == "deg":
            if is_speed: base_val = (val / 360.0) * self.ppr # Deg/s to PPS
            else: base_val = (val / 360.0) * self.ppr # Deg to Pulse

        # 2. Convert Base to New Unit
        new_val = 0.0
        if new_unit == "pulse":
            new_val = base_val
        elif new_unit == "rev":
            if is_speed: new_val = (base_val * 60.0) / self.ppr # PPS to RPM
            else: new_val = base_val / self.ppr # Pulse to Rev
        elif new_unit == "deg":
            if is_speed: new_val = (base_val * 360.0) / self.ppr # PPS to Deg/s
            else: new_val = (base_val / self.ppr) * 360.0 # Pulse to Deg

        # Format to 2 decimal places to avoid float mess (or 0 for pulse)
        if new_unit == "pulse":
            var.set(f"{int(new_val)}")
        else:
            var.set(f"{new_val:.2f}")

    def execute_jog(self, speed_str, direction):
        try:
            speed_val = float(speed_str)
            step_val = float(self.step_var.get())
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numeric values for Speed and Step.")
            return

        mode = self.current_unit.get()
        target = step_val * direction

        print(f"\n[UI JOG] Triggered | Mode: {mode}, Target: {target}, Speed: {speed_val}")

        # Run DDRVI in a separate thread so UI doesn't freeze
        threading.Thread(
            target=ddrvi, 
            kwargs={
                "ENO": True, 
                "MODE": mode, 
                "TARGET": target, 
                "SPEED": speed_val, 
                "PPR": self.ppr, 
                "AXIS": self.axis, 
                "SIG": self.sig_addr, 
                "REPORT": False
            }, 
            daemon=True
        ).start()

# ========================================================
# Example of how to run this file standalone for testing
# ========================================================
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Servo Control Station")
    
    # Instance the UI inside the main window
    jog_ui = ServoJogUI(root, ppr=3600, axis=3)
    
    root.mainloop()