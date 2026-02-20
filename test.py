import time
import random
import tkinter as tk
from tkinter import messagebox
from plc_module import PLCController

def run_plc_test():
    # Set config_print=False to keep the console output clean during loops
    plc = PLCController(config_print=False)
    
    IP_ADDRESS = "192.168.3.250"
    PORT = 502
    
    print("="*70)
    print("Starting Group Read/Write PLC Test with Random Values (Offset Version)")
    print("="*70)
    
    if plc.plcConnect(IP_ADDRESS, port=PORT):
        print("Connection successful. Proceeding...\n")

        # --------------------------------------------------
        # Step 1: Generate random values, store in list, and write to PLC
        # --------------------------------------------------
        print("[1] Generating random values for M0-M20 (ON/OFF) and D0-D20 (Signed 16-bit)...")
        
        sent_m_list = []
        sent_d_list = []
        
        for i in range(21):
            random_m = bool(random.getrandbits(1))
            sent_m_list.append(random_m)
            plc.write_M(address=i, status=random_m)
            
            random_d = random.randint(-32768, 32767)
            sent_d_list.append(random_d)
            plc.write_holding(address=i, value=random_d & 0xFFFF)
            
        print(f"   Sent random M0-M20 : {sent_m_list}")
        print(f"   Sent random D0-D20 : {sent_d_list}")
        
        time.sleep(1)

        # --------------------------------------------------
        # Step 2: Read all values into lists and print for comparison
        # --------------------------------------------------
        print("\n[2] Current values read from PLC:")
        
        list_x = [plc.read_input(address=i)[0] for i in range(18)]
        print(f"   Read X0-X17  : {list_x}")
        
        # Updated to use read_Y instead of read_coil
        list_y = [plc.read_Y(address=i)[0] for i in range(18)]
        print(f"   Read Y0-Y17  : {list_y}")
        
        # Updated to use read_M instead of read_coil
        list_m = [plc.read_M(address=i)[0] for i in range(21)]
        print(f"   Read M0-M20  : {list_m}")
        
        list_d = []
        for i in range(21):
            val, ok = plc.read_holding(address=i)
            int_val = int(val)
            if int_val > 32767:
                int_val -= 65536
            list_d.append(int_val)
        print(f"   Read D0-D20  : {list_d}")

        # --------------------------------------------------
        # Verification Step: Check if sent values match read values
        # --------------------------------------------------
        print("\n[ Verification ]")
        is_m_match = (sent_m_list == list_m)
        is_d_match = (sent_d_list == list_d)
        test_passed = (is_m_match and is_d_match)
        
        print(f"   M values match: {is_m_match}")
        print(f"   D values match: {is_d_match}")

        # You can visually verify if Y values stayed OFF (or in their original state)
        # while M values changed randomly.

        # --------------------------------------------------
        # Step 3: Reset M and D values to 0 / OFF
        # --------------------------------------------------
        print("\n[3] Clearing M0-M20 and D0-D20 to 0 (OFF)...")
        for i in range(21):
            plc.write_M(address=i, status=False)
            plc.write_holding(address=i, value=0)
        
        time.sleep(1)

        # --------------------------------------------------
        # Step 4: Read M and D again to confirm reset
        # --------------------------------------------------
        print("\n[4] Values after reset:")
        list_m_reset = [plc.read_M(address=i)[0] for i in range(21)]
        print(f"   Reset M0-M20 : {list_m_reset}")
        
        list_d_reset = [int(plc.read_holding(address=i)[0]) for i in range(21)]
        print(f"   Reset D0-D20 : {list_d_reset}")

        print("\n" + "="*70)
        plc.plcDisconnect()
        print("End of test.")
        print("="*70)
        
        # --------------------------------------------------
        # Show Pop-up Result
        # --------------------------------------------------
        root = tk.Tk()
        root.withdraw() 
        root.attributes('-topmost', True) 
        
        if test_passed:
            messagebox.showinfo("Test Result", "Success!\nAll read values perfectly match the sent random values.\nCheck console to verify Y state did not overlap with M.")
        else:
            messagebox.showerror("Test Result", "Error!\nMismatch detected between sent values and read values. Please check the console log.")
            
        root.destroy()
        
    else:
        print("\nConnection failed. Please check IP address or LAN cable.")

if __name__ == "__main__":
    run_plc_test()