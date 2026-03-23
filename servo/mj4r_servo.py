import os, sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import time
import threading  
import keyboard
from tkinter import messagebox
import tkinter as tk

from basic.plc_module import PLCController 
  
class ServoController:
    def __init__(self, ip="192.168.3.250", port=502):
        self.plc = PLCController(config_print=True)
        self.ip = ip
        self.port = port
        self.e_stop_active = False  # Flag Emergency Stop

    def start(self):
        #START Triggered when the program starts. Connect to PLC and set up Emergency Stop hotkey.
        print(">> Initializing Servo System...")       
        self.plc.plcConnect(self.ip, port=self.port)
        
        self.e_stop_active = False
        try:
            self.plc.write_M(address=899, status=False)
        except Exception as e:
            print(f">> [Warning] Cannot reset M899 on PLC: {e}")

        # Spacebar add to key of Emergency Stop
        keyboard.add_hotkey('space', self.trigger_estop)
        
        print(">> Servo System STARTED. [Press 'SPACEBAR' anywhere for EMERGENCY STOP]")

    def trigger_estop(self):
        # call when spacebar is pressed
        if not self.e_stop_active:
            self.e_stop_active = True
            print("\n" + "!"*50)
            print("!!! EMERGENCY STOP TRIGGERED (SPACEBAR PRESSED) !!!")
            print("!"*50)

            try:
                self.plc.write_M(address=899, status=True)
                print(">> Sent M899 = ON to PLC successfully.")
            except Exception as e:
                print(f">> Failed to send E-Stop to PLC: {e}")

    def ddrvi(self, ENO=True, MODE="pulse", TARGET=0, SPEED=0, PPR=10000, AXIS=1, REPORT=False):
        if self.e_stop_active:
            print(f">> [Axis {AXIS}] Blocked: Emergency Stop is active.")
            return False

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
            if REPORT: messagebox.showerror("DDRVI Error", str(e))
            print(f">> [Axis {AXIS}] Error: {str(e)}")
            return False

        if final_speed == 0:
            if REPORT: messagebox.showerror("DDRVI Error", f"Calculated speed cannot be zero on Axis {AXIS}!")
            return False

        timeout = (abs(final_position) / final_speed) * 2.0 + 5.0 
        
        trigger_addr = AXIS * 100        
        pos_addr = AXIS * 100            
        spd_addr = (AXIS * 100) + 2      
        axis_reg_addr = (AXIS * 100) + 4 
        sig_addr = (AXIS * 100) + 10     

        PLCDATA = {
            "position": pos_addr, 
            "speed": spd_addr,  
            "axis_reg": axis_reg_addr,
            "done": sig_addr,        
            "err": sig_addr + 1      
        }
        
        self.plc.write_M_batch(address=PLCDATA["done"], values=[False, False])
        self.plc.write_holding_32bit_batch(address=PLCDATA["position"], values=[final_position, final_speed, AXIS])
        
        print(f">> [Axis {AXIS}] Mode: {MODE.upper()} | Target: {TARGET}, Speed: {SPEED}")
        print(f">> [Axis {AXIS}] Sending Start Command (M{trigger_addr}): Pos={final_position}, Speed={final_speed}")
        
        self.plc.pulse_M(address=trigger_addr, duration=0.1, blocking=False)  
        
        start_time = time.time()
        while True:
            # --- E-STOP CHECK --- 
            #  Spacebar pressed = break Break 
            if self.e_stop_active:
                print(f">> [Axis {AXIS}] Sequence aborted due to E-Stop!")
                return False

            if (time.time() - start_time) > timeout:
                messagebox.showerror("Timeout Error", f"Axis {AXIS} operation timed out!")
                return False
                
            bits, success = self.plc.read_M_batch(address=PLCDATA["done"], count=2)
            if success:
                is_done, is_err = bits[0], bits[1]
            else:
                is_done, is_err = False, False
            
            if is_err:
                report_status(f"Error occurred during servo operation on Axis {AXIS}!", msgtype=-1)
                return False
                
            if is_done:
                self.plc.write_M(address=PLCDATA["done"], status=False)
                report_status(f"Servo operation completed successfully on Axis {AXIS}!", msgtype=0)
                print(f">> [Axis {AXIS}] Movement Finished.\n")
                return True
                
            time.sleep(0.01)

    def ddrvi_sync(self, commands):
        if self.e_stop_active: return
        threads = []
        for cmd in commands:
            t = threading.Thread(target=self.ddrvi, kwargs=cmd)
            threads.append(t)
        for t in threads: t.start()
        for t in threads: t.join()
        if not self.e_stop_active:
            print(">> [SYNC] All synchronized axes have completed their movements.\n")
            
    def ddrva(self, ENO=True, MODE="pulse", TARGET=0, SPEED=0, PPR=10000, AXIS=1, REPORT=False):
    # DDRVA (Direct Distance Relative Move) - Move a relative distance based on current position
        if self.e_stop_active:
            print(f">> [Axis {AXIS}] Blocked: Emergency Stop is active.")
            return False

        if not ENO:
            print(f">> [Axis {AXIS}] ENO is False. Command aborted.")
            return False

        # read current position in pulses   
        current_pulse = self.current_position(axis=AXIS)
        
        if current_pulse is None:
            print(f">> [Axis {AXIS}] Error: failed to read current position for DDRVA ")
            if REPORT: messagebox.showerror("DDRVA Error", f"Failed to read current position on Axis {AXIS}")
            return False

        # Transform current position to the same unit as TARGET based on MODE
        try:
            if MODE.lower() == "pulse":
                current_pos = current_pulse
            elif MODE.lower() == "rev":
                current_pos = current_pulse / float(PPR)
            elif MODE.lower() == "deg":
                current_pos = (current_pulse / float(PPR)) * 360.0
            else:
                raise ValueError(f"Unknown MODE: '{MODE}'. Use 'pulse', 'rev', or 'deg'.")
        except ZeroDivisionError:
            print(f">> [Axis {AXIS}] Error: PPR cannot be zero.")
            return False

        # calculate (Relative Distance)
        relative_target = TARGET - current_pos

        print(f">> [DDRVA Axis {AXIS}] Current Pos: {current_pos:.2f} {MODE} | Absolute Target: {TARGET} {MODE}")
        print(f">> [DDRVA Axis {AXIS}] Calculated Relative Move: {relative_target:.2f} {MODE}")

        if abs(relative_target) < 0.0001:
            print(f">> [Axis {AXIS}] Already at the target position. No movement needed.\n")
            return True

        # call ddrvi with the calculated relative target and original parameters
        return self.ddrvi(
            ENO=ENO, 
            MODE=MODE, 
            TARGET=relative_target, 
            SPEED=SPEED, 
            PPR=PPR, 
            AXIS=AXIS, 
            REPORT=REPORT
        )
        
    def ddrva_sync(self, commands):
        if self.e_stop_active: return
        threads = []
        for cmd in commands:
            t = threading.Thread(target=self.ddrva, kwargs=cmd)
            threads.append(t)
        for t in threads: t.start()
        for t in threads: t.join()
        if not self.e_stop_active:
            print(">> [SYNC] All absolute synchronized axes have completed their movements.\n")
            
    def linear_interpolation_abs(self, commands, ref_axis=1):
        if self.e_stop_active:
            print(">> [Interpolation ABS] Blocked: Emergency Stop is active.")
            return False

        print(f"\n>> [Interpolation ABS Start call Reference axis: {ref_axis}...")
        
        # 1. read current positions and calculate distances for all axes, while identifying the reference axis command
        ref_distance = 0
        ref_speed = 0
        ref_found = False

        for cmd in commands:
            axis = cmd.get("AXIS")
            target = cmd.get("TARGET", 0)
            mode = cmd.get("MODE", "pulse").lower()
            ppr = cmd.get("PPR", 10000)

            # read current position in pulses for this axis
            current_pulse = self.current_position(axis=axis)
            if current_pulse is None:
                print(f">> [Interpolation ABS] Error: Cannot read current position of axis {axis}")
                return False

            # transform current position to the same unit as TARGET based on MODE
            if mode == "pulse":
                current_pos = current_pulse
            elif mode == "rev":
                current_pos = current_pulse / float(ppr)
            elif mode == "deg":
                current_pos = (current_pulse / float(ppr)) * 360.0
            else:
                print(f">> [Interpolation ABS] Error: Mode {mode} INVALID for axis {axis} - use 'pulse', 'rev', or 'deg'.")
                return False

            # calculate movement distance to target
            distance = target - current_pos
            cmd["_distance"] = distance

            # if this is the reference axis, store its distance and speed for interpolation
            if axis == ref_axis:
                ref_distance = abs(distance)
                ref_speed = cmd.get("SPEED", 0)
                ref_found = True

        if not ref_found:
            print(f">> [Interpolation ABS] Error: No reference axis (Axis {ref_axis}) found in commands")
            return False

        if ref_distance < 0.0001:
            print(f">> [Interpolation ABS] Error: Reference axis is already at the target position. Cannot synchronize speeds.")
            return False

        # calculate speeds for Slave axes based on the reference axis
        for cmd in commands:
            axis = cmd.get("AXIS")
            distance = cmd.pop("_distance")  # extract and remove temporary distance value
            
            if axis != ref_axis:
                if abs(distance) < 0.0001:
                    cmd["SPEED"] = 0  # if the slave axis is already at target, set speed to 0 to avoid unnecessary movement
                else:
                    # สมการ: Speed_slave = (|Distance_slave| * Speed_ref) / |Distance_ref|
                    new_speed = (abs(distance) * ref_speed) / ref_distance
                    cmd["SPEED"] = new_speed
                    
                print(f"   - Update axis {axis} (Slave)  | Target(ABS): {cmd.get('TARGET'):<6} | Run Distance: {distance:+.2f} | New Speed: {cmd.get('SPEED'):.2f}")
            else:
                print(f"   - Reference axis {axis} (Master) | Target(ABS): {cmd.get('TARGET'):<6} | Run Distance: {distance:+.2f} | Base Speed: {cmd.get('SPEED'):.2f}")

        # call ddrva_sync after updating speeds
        self.ddrva_sync(commands)
        
        return True

    def test_servo(self, axis=1, ppr=3600):
        #  E-Stop Check
        def check_estop():
            return self.e_stop_active

        def test_low_speed(test_axis, test_ppr, DIRECTION="forward"):
            for i in range(1, 4):
                if check_estop(): return
                target = 1 if DIRECTION == "forward" else -1
                self.ddrvi(MODE="rev", TARGET=target, SPEED=50*i, PPR=test_ppr, AXIS=test_axis, REPORT=False)
                time.sleep(0.5)
                
        def test_high_speed(test_axis, test_ppr, DIRECTION="forward"):
            for i in range(3):
                if check_estop(): return
                target = 2 if DIRECTION == "forward" else -2
                self.ddrvi(MODE="rev", TARGET=target, SPEED=300+100*i, PPR=test_ppr, AXIS=test_axis, REPORT=False)
                time.sleep(0.5)
                
        def struggle_test1(test_axis, test_ppr, SECTIONS=4, DIRECTION="forward"):
            for i in range(SECTIONS):
                if check_estop(): return
                target = 1.0/SECTIONS if DIRECTION == "forward" else -1.0/SECTIONS
                self.ddrvi(MODE="rev", TARGET=target, SPEED=500, PPR=test_ppr, AXIS=test_axis, REPORT=False)
                time.sleep(0.1)
        
        def struggle_test2(test_axis, test_ppr):
            for i in range(10):
                if check_estop(): return
                self.ddrvi(MODE="rev", TARGET=0.25, SPEED=150, PPR=test_ppr, AXIS=test_axis, REPORT=False)
                time.sleep(0.1)
                if check_estop(): return
                self.ddrvi(MODE="rev", TARGET=-0.15, SPEED=1000, PPR=test_ppr, AXIS=test_axis, REPORT=False)
                time.sleep(0.1)
        
        if check_estop(): return
        print(f">> Running Basic Tests on Axis {axis}...")
        self.ddrvi(MODE="rev", TARGET=1, SPEED=20, PPR=ppr*2, AXIS=axis, REPORT=False)
        time.sleep(1)
        
        if check_estop(): return
        self.ddrvi(MODE="rev", TARGET=-1, SPEED=20, PPR=ppr*2, AXIS=axis, REPORT=False)
        time.sleep(1)
        
        print(f">> Running Speed Tests on Axis {axis}...")
        test_low_speed(axis, ppr, DIRECTION="forward")
        if check_estop(): return
        test_low_speed(axis, ppr, DIRECTION="reverse")
        if check_estop(): return
        test_high_speed(axis, ppr, DIRECTION="forward")
        if check_estop(): return
        test_high_speed(axis, ppr, DIRECTION="reverse")
        if check_estop(): return
        
        print(f">> Running Sectional Struggle Tests on Axis {axis}...")
        struggle_test1(axis, ppr, DIRECTION="forward", SECTIONS=8)
        if check_estop(): return
        struggle_test1(axis, ppr, DIRECTION="reverse", SECTIONS=8)
        if check_estop(): return
        
        print(f">> Running Rapid Direction Change Test on Axis {axis}...")
        struggle_test2(axis, ppr)
        if check_estop(): return
       
        self.ddrvi(MODE="rev", TARGET=-1, SPEED=100, PPR=ppr, AXIS=axis, REPORT=False)  
        
        if not self.e_stop_active:
            messagebox.showinfo("Test Completed", f"All servo motion tests on Axis {axis} have been completed successfully!")
            print("\n" + "="*50)
            print(f"TEST SEQUENCE ON AXIS {axis} COMPLETED SUCCESSFULLY")
            print("="*50)
        else:
            print("\n>> TEST ABORTED DUE TO EMERGENCY STOP.")
    
    
    def current_position(self, axis):
        data_pos_addr = {1: 5500, 2: 5540, 3: 5580, 4: 5620}
        
        if not axis:
            print(">> Missing axis number. __int__")
            return None
        if axis < 1 or axis > 4:
            print(f">> Invalid axis number [1,2,3,4]. Given: {axis}")
            return None 
        
        value, success = self.plc.read_holding_32bit(address=data_pos_addr[axis])
        if success:
            return value
        else:
            print(f">> Failed to read. Axis {axis}.")
            return None
        
if __name__ == "__main__":
    servo = ServoController()
    servo.start()
    
    servo.test_servo(axis=1, ppr=3600)