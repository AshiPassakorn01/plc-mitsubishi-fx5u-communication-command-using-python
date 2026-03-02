import os , sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import time
from tkinter import messagebox
from basic.plc_module import PLCController 
from position_monitor import ServoMonitorUI

import tkinter as tk

# Initialize PLC Connection
plc = PLCController(config_print=True)
IP_ADDRESS = "192.168.3.250"
PORT = 502
plc.plcConnect(IP_ADDRESS, port=PORT)
def ddrvi(ENO=True, MODE="pulse", TARGET=0, SPEED=0, PPR=10000, AXIS=1, REPORT=False):
    if not ENO:
        print(f">> [Axis {AXIS}] ENO is False. Command aborted.")
        return False

    def calculate_motion_params():
        if MODE.lower() == "pulse":
            pos = int(TARGET)
            spd = int(SPEED)
        elif MODE.lower() == "rev":
            pos = round(TARGET * PPR)
            spd = round((SPEED * PPR) / 60.0)
        elif MODE.lower() == "deg":
            pos = round((TARGET / 360.0) * PPR)
            spd = round((SPEED / 360.0) * PPR)
        else:
            raise ValueError(f"Unknown MODE: '{MODE}'. Use 'pulse', 'rev', or 'deg'.")
        return pos, spd

    def report_status(message, msgtype=None):
        if REPORT:
            if msgtype == -1:
                messagebox.showerror("DDRVI Status", message)
            elif msgtype == 0:
                messagebox.showinfo("DDRVI Status", message)

    try:
        final_position, final_speed = calculate_motion_params()
    except Exception as e:
        if REPORT:
            messagebox.showerror("DDRVI Error", str(e))
        print(f">> [Axis {AXIS}] Error: {str(e)}")
        return False

    if final_speed == 0:
        if REPORT:
            messagebox.showerror("DDRVI Error", f"Calculated speed cannot be zero on Axis {AXIS}!")
        return False

    timeout = (abs(final_position) / final_speed) * 2.0 + 5.0 
    
    trigger_addr = AXIS * 100        # M100, M200, M300, M400
    pos_addr = AXIS * 100            # D100, D200, D300, D400
    spd_addr = (AXIS * 100) + 2      # D102, D202, D302, D402
    axis_reg_addr = (AXIS * 100) + 4 # D104, D204, D304, D404
    sig_addr = (AXIS * 100) + 10     # M110, M210, M310, M410

    PLCDATA = {
        "position": pos_addr, 
        "speed": spd_addr,  
        "axis_reg": axis_reg_addr,
        "done": sig_addr,        
        "err": sig_addr + 1      
    }
    
    plc.write_M(address=PLCDATA["done"], status=False)
    plc.write_M(address=PLCDATA["err"], status=False)
    
    plc.write_holding_32bit(address=PLCDATA["position"], value=final_position)
    plc.write_holding_32bit(address=PLCDATA["speed"], value=final_speed)
    plc.write_holding_32bit(address=PLCDATA["axis_reg"], value=AXIS)
    
    print(f">> [Axis {AXIS}] Mode: {MODE.upper()} | Target: {TARGET}, Speed: {SPEED}")
    print(f">> [Axis {AXIS}] Sending Start Command (M{trigger_addr}): Pos(D{pos_addr})={final_position}, Speed(D{spd_addr})={final_speed}, AxisReg(D{axis_reg_addr})={AXIS}")
    
    plc.pulse_M(address=trigger_addr, duration=0.1, blocking=True)  
    
    start_time = time.time()
    while True:
        curr_speed = plc.read_holding_32bit(PLCDATA["speed"])[0]
        if (time.time() - start_time) > timeout:
            messagebox.showerror("Timeout Error", f"Axis {AXIS} operation timed out!")
            return False
            
        is_done, _ = plc.read_M(address=PLCDATA["done"])
        is_err, _ = plc.read_M(address=PLCDATA["err"])
        
        if is_err:
            report_status(f"Error occurred during servo operation on Axis {AXIS}!", msgtype=-1)
            return False
            
        if is_done:
            plc.write_M(address=PLCDATA["done"], status=False)
            report_status(f"Servo operation completed successfully on Axis {AXIS}!", msgtype=0)
            print(f">> [Axis {AXIS}] Movement Finished.\n")
            return True
            
        time.sleep(0.1)
        
import threading

def ddrvi_sync(commands):

    threads = []
    
    for cmd in commands:
        t = threading.Thread(target=ddrvi, kwargs=cmd)
        threads.append(t)
        
    for t in threads:
        t.start()
        
    for t in threads:
        t.join()
        
    print(">> [SYNC] All synchronized axes have completed their movements.\n")

def ddrvi_sync_intp(commands):
    def get_pulse(mode, target, ppr):
        if mode == "pulse": return int(target)
        if mode == "rev": return round(target * ppr)
        if mode == "deg": return round((target / 360.0) * ppr)
        raise ValueError(f"Unknown MODE: '{mode}'")

    def get_pps(mode, speed, ppr):
        if mode == "pulse": return int(speed)
        if mode == "rev": return round((speed * ppr) / 60.0)
        if mode == "deg": return round((speed / 360.0) * ppr)
        raise ValueError(f"Unknown MODE: '{mode}'")

    ref_cmd = None
    speed_count = 0
    
    for cmd in commands:
        speed_val = cmd.get("SPEED", 0)
        if speed_val is not None and speed_val > 0:
            speed_count += 1
            ref_cmd = cmd
            
    if speed_count != 1:
        raise ValueError(f"Interpolation Error: Only 1 Reference speed is allowed (found {speed_count} axes with SPEED set)")

    ref_mode = ref_cmd.get("MODE", "pulse").lower()
    ref_target = ref_cmd["TARGET"]
    ref_speed = ref_cmd["SPEED"]
    ref_ppr = ref_cmd.get("PPR", 10000)
    
    ref_pulse = get_pulse(ref_mode, ref_target, ref_ppr)
    ref_pps = get_pps(ref_mode, ref_speed, ref_ppr)
    
    if ref_pulse == 0:
        raise ValueError("Interpolation Error: Reference Axis Position (TARGET) must not be 0")
        
    time_required = abs(ref_pulse) / ref_pps
    
    print("\n" + "="*50)
    print(f"INTERPOLATION DRIVE (Est. Time: {time_required:.3f} sec)")
    print("="*50)

    threads = []
    
    for cmd in commands:
        axis = cmd["AXIS"]
        mode = cmd.get("MODE", "pulse").lower()
        target = cmd["TARGET"]
        ppr = cmd.get("PPR", 10000)
        report = cmd.get("REPORT", False)
        
        target_pulse = get_pulse(mode, target, ppr)
        
        if cmd == ref_cmd:
            speed_pps = ref_pps
        else:
            if target_pulse == 0:
                speed_pps = 0
            else:
                speed_pps = round(abs(target_pulse) / time_required)
                if speed_pps == 0: speed_pps = 1 # ป้องกันความเร็วเป็น 0 ถ้าระยะสั้นมาก
                
        print(f"   ┣ [Axis {axis}] Target: {target_pulse} pulses, Sync Speed: {speed_pps} pps")
        
        sync_kwargs = {
            "MODE": "pulse",
            "TARGET": target_pulse,
            "SPEED": speed_pps,
            "PPR": ppr,
            "AXIS": axis,
            "REPORT": report
        }
        
        t = threading.Thread(target=ddrvi, kwargs=sync_kwargs)
        threads.append(t)

    print(">> Triggering All Axes Simultaneously...\n")
    
    for t in threads:
        t.start()
        
    for t in threads:
        t.join()
        
    print(">> [SYNC INTP] Interpolation movement completed.\n")

def monitoring():
    def launch_monitor():
        monitor_window = tk.Tk()
        app = ServoMonitorUI(monitor_window, plc)
        monitor_window.mainloop()
    
    ui_thread = threading.Thread(target=launch_monitor, daemon=True)
    ui_thread.start()
    
def test_servo(axis=1, ppr=3600):
    def test_low_speed(test_axis, test_ppr, DIRECTION="forward"):
        for i in range(1, 4):
            if DIRECTION == "forward":
                target = 1
            else:
                target = -1
                
            ddrvi(MODE="rev", TARGET=target, SPEED=50*i, PPR=test_ppr, AXIS=test_axis, REPORT=False)
            time.sleep(0.5)
            
    def test_high_speed(test_axis, test_ppr, DIRECTION="forward"):
        for i in range(3):
            if DIRECTION == "forward":
                target = 2
            else:
                target = -2
            
            ddrvi(MODE="rev", TARGET=target, SPEED=300+100*i, PPR=test_ppr, AXIS=test_axis, REPORT=False)
            time.sleep(0.5)
            
    def struggle_test1(test_axis, test_ppr, SECTIONS=4, DIRECTION="forward"):
        for i in range(SECTIONS):
            if DIRECTION == "forward":
                target = 1.0/SECTIONS
            else:
                target = -1.0/SECTIONS
            ddrvi(MODE="rev", TARGET=target, SPEED=500, PPR=test_ppr, AXIS=test_axis, REPORT=False)
            time.sleep(0.1)
    
    def struggle_test2(test_axis, test_ppr):
        for i in range(10):
            ddrvi(MODE="rev", TARGET=0.25, SPEED=150, PPR=test_ppr, AXIS=test_axis, REPORT=False)
            time.sleep(0.1)
            
            ddrvi(MODE="rev", TARGET=-0.15, SPEED=1000, PPR=test_ppr, AXIS=test_axis, REPORT=False)
            time.sleep(0.1)
    
    # basic forward and reverse tests
    print(f">> Running Basic Tests on Axis {axis}...")
    ddrvi(MODE="rev", TARGET=1, SPEED=20, PPR=ppr*2, AXIS=axis, REPORT=False)
    time.sleep(1)
    ddrvi(MODE="rev", TARGET=-1, SPEED=20, PPR=ppr*2, AXIS=axis, REPORT=False)
    time.sleep(1)
    
    # speed tests
    print(f">> Running Speed Tests on Axis {axis}...")
    test_low_speed(axis, ppr, DIRECTION="forward")
    time.sleep(1)
    test_low_speed(axis, ppr, DIRECTION="reverse")
    time.sleep(1)
    test_high_speed(axis, ppr, DIRECTION="forward")
    time.sleep(1)
    test_high_speed(axis, ppr, DIRECTION="reverse")
    time.sleep(1)
    
    # sectional struggle tests
    print(f">> Running Sectional Struggle Tests on Axis {axis}...")
    struggle_test1(axis, ppr, DIRECTION="forward", SECTIONS=8)
    time.sleep(0.5)
    struggle_test1(axis, ppr, DIRECTION="forward", SECTIONS=16)
    time.sleep(0.5)
    struggle_test1(axis, ppr, DIRECTION="reverse", SECTIONS=8)
    time.sleep(0.5)
    struggle_test1(axis, ppr, DIRECTION="reverse", SECTIONS=16)
    time.sleep(0.5)
    
    # rapid direction change test
    print(f">> Running Rapid Direction Change Test on Axis {axis}...")
    struggle_test2(axis, ppr)
    
    messagebox.showinfo("Test Completed", f"All servo motion tests on Axis {axis} have been completed successfully!")
    
    print("\n" + "="*50)
    print(f"TEST SEQUENCE ON AXIS {axis} COMPLETED SUCCESSFULLY")
    print("="*50)
    
if __name__ == "__main__":        
    monitoring()
    MOTOR_PPR1 = 36000
    MOTOR_PPR2 = 360000
    """sync_tasks1 = [
        {"AXIS": 1, "MODE": "pulse", "TARGET": MOTOR_PPR1,  "SPEED": 3600, "PPR": MOTOR_PPR1 },
        {"AXIS": 2, "MODE": "pulse", "TARGET": MOTOR_PPR2,                "PPR": MOTOR_PPR2},
        {"AXIS": 3, "MODE": "pulse", "TARGET": MOTOR_PPR1,               "PPR": MOTOR_PPR2}
    ]
    
    ddrvi_sync_intp(sync_tasks1)"""
    
    """ddrvi(MODE="rev", TARGET=1, SPEED=100, PPR=MOTOR_PPR1, AXIS=1, REPORT=False)
    ddrvi(MODE="rev", TARGET=1, SPEED=50, PPR=MOTOR_PPR1, AXIS=2, REPORT=False)
    ddrvi(MODE="rev", TARGET=1, SPEED=50, PPR=MOTOR_PPR1, AXIS=3, REPORT=False)

    time.sleep(2)
    
    ddrvi_sync_intp([{"AXIS": 1, "MODE": "rev", "TARGET": 10, "SPEED": 100, "PPR": MOTOR_PPR1},
                      {"AXIS": 2, "MODE": "rev", "TARGET": 5, "PPR": MOTOR_PPR1},
                      {"AXIS": 3, "MODE": "rev", "TARGET": 1, "PPR": MOTOR_PPR1}])"""
                      
    test_servo(ppr=MOTOR_PPR1, axis=1)

    print("--- Finished ---")