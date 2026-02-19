
---

# 🤖 PLC Modbus TCP Controller

A lightweight Python wrapper for controlling PLCs (specifically tested with Mitsubishi FX5U) via Modbus TCP. It supports Coils, Discrete Inputs, and Holding Registers.

## 📦 Installation

```bash
pip install pymodbus

```

## 📂 Project Structure

* **`plc_module.py`**: The core library containing the `PLCController` class.
* **`monitor_test.py`**: A real-time GUI monitoring tool built with Tkinter.
* **`plc_sample.py`**: Basic script for testing Mitsubishi FX5U communication.

---

## 📖 API Quick Reference

### 1. Connection 🛜

* **`plcConnect(ip: str, port: int = 502) -> bool`**
* Connects to the PLC. Returns `True` if successful.


* **`plcDisconnect() -> bool`**
* Closes the connection safely.



### 2. Write Data ✍️

* **`write_coil(address: int, value: bool) -> bool`**
* Turns ON (`True`) or OFF (`False`) a Coil (mapped to **M** or **Y**).


* **`write_holding(address: int, value: int) -> bool`**
* Writes an integer to a Data Register (mapped to **D**).



### 3. Read Data 🔍

> **Note:** All read methods return two variables: `(value, success_status)`.

* **`read_coil(address: int) -> tuple[bool, bool]`**
* Reads the state of a Coil (**M** or **Y**).


* **`read_input(address: int) -> tuple[bool, bool]`**
* Reads the state of a Discrete Input (**X**).


* **`read_holding(address: int) -> tuple[float, bool]`**
* Reads a number from a Data Register (**D**).



---

## 🚀 Quick Start Example

```python
from plc_module import PLCController

# Initialize the controller
plc = PLCController()

# Connect to the PLC
if plc.plcConnect("192.168.3.250"):
    
    # Write: Set target speed (D0) and trigger start command (M10)
    plc.write_holding(0, 4500)  
    plc.write_coil(10, True)    
    
    # Read: Check current speed from D0
    speed, status = plc.read_holding(0)
    
    if status:
        print(f"Current Speed: {speed} RPM")
    
    # Disconnect
    plc.plcDisconnect()

```

---

### **Next Steps for your GitHub:**

1. **Create `requirements.txt**`: Run `pip freeze > requirements.txt` in your terminal.
2. **Add a License**: Consider adding an MIT License so others can use your code.