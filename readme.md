
---

# PLC Modbus TCP Controller

A lightweight Python wrapper for controlling PLCs (specifically tested with Mitsubishi FX5U) via Modbus TCP. It acts as a wrapper around the `pymodbus` library, providing straightforward methods to read and write data to various PLC memory areas (Outputs, Internal Relays, Data Registers, and Inputs).

## Installation

This module requires Python 3.x and the `pymodbus` library.

```bash
pip install pymodbus

```

## Project Structure

* **`plc_module.py`**: The core library containing the `PLCController` class.
* **`monitor_test.py`**: A real-time GUI monitoring tool built with Tkinter.
* **`plc_sample.py`**: Basic script for testing Mitsubishi FX5U communication.
* **`test_group_rw.py`**: The automated testing script for group reading/writing with random values and verification.

## Features

* **Standardized Return Values:** Write functions return a boolean indicating success. Read functions return a tuple containing the read value and a boolean success flag.
* **Configurable Logging:** Includes a `config_print` parameter to easily enable or disable console logs during execution.
* **Simplified Interface:** Dedicated functions for different PLC memory types (e.g., `write_Y`, `write_M`) to make the code highly readable.
* **Streamlined Modbus Parameters:** Optimized for modern Modbus TCP implementations where the unit/slave ID is handled strictly by the IP connection.

---

## API Quick Reference

### 1. Connection

* **`plcConnect(ip: str, port: int = 502) -> bool`**
Connects to the PLC. Returns `True` if successful.
* **`plcDisconnect() -> bool`**
Closes the connection safely. Returns `True` if disconnected successfully.

### 2. Write Data

* **`write_Y(address: int, status: bool) -> bool`**
Turns ON (`True`) or OFF (`False`) a Physical Output Coil (**Y**).
* **`write_M(address: int, status: bool) -> bool`**
Turns ON (`True`) or OFF (`False`) an Internal Relay Coil (**M**).
* **`write_holding(address: int, value: int) -> bool`**
Writes a 16-bit integer to a Data Register (**D**).

### 3. Read Data

> **Note:** All read methods return a tuple containing two variables: `(value, success_status)`.

* **`read_coil(address: int) -> tuple[bool, bool]`**
Reads the state of a Coil (**M** or **Y**).
* **`read_input(address: int) -> tuple[bool, bool]`**
Reads the state of a Discrete Input (**X**).
* **`read_holding(address: int) -> tuple[float, bool]`**
Reads a number from a Data Register (**D**).

---

## Quick Start Example

```python
from plc_module import PLCController

# Initialize the controller (set config_print=False to disable console logs)
plc = PLCController(config_print=True)

# Connect to the PLC
if plc.plcConnect("192.168.3.250"):
    
    # Write: Set target speed (D0) and trigger start command (M10)
    plc.write_holding(address=0, value=4500)  
    plc.write_M(address=10, status=True)    
    
    # Read: Check current speed from D0
    speed, status = plc.read_holding(address=0)
    
    if status:
        print(f"Current Speed: {speed} RPM")
    
    # Disconnect
    plc.plcDisconnect()

```

---

## Handling Signed 16-bit Integers

Modbus Holding Registers natively hold unsigned 16-bit integers (0 to 65535). If you need to write or read negative numbers, you must handle the Two's Complement conversion in your main script:

**Writing negative values:**

```python
value_to_send = -5
# Use bitwise AND to convert to unsigned 16-bit before sending
plc.write_holding(address=10, value=value_to_send & 0xFFFF)

```

**Reading negative values:**

```python
val, ok = plc.read_holding(address=10)
if ok:
    int_val = int(val)
    # If the value exceeds the signed 16-bit positive limit, convert it back to negative
    if int_val > 32767:
        int_val -= 65536
    print(f"Signed Value: {int_val}")

```

---

## Command Summary Table

| Method | Parameters | Return Type | Description |
| --- | --- | --- | --- |
| `plcConnect` | `ip` (str), `port` (int, default: 502) | `bool` | Establishes a TCP connection to the PLC. Returns True on success. |
| `plcDisconnect` | None | `bool` | Closes the active TCP connection. |
| `write_Y` | `address` (int), `status` (bool) | `bool` | Writes a boolean state (ON/OFF) to a physical output coil (Y). |
| `write_M` | `address` (int), `status` (bool) | `bool` | Writes a boolean state (ON/OFF) to an internal relay coil (M). |
| `write_holding` | `address` (int), `value` (int) | `bool` | Writes a 16-bit integer to a holding register (D). |
| `read_coil` | `address` (int) | `tuple[bool, bool]` | Reads the boolean state of a coil (Y or M). Returns `(value, success)`. |
| `read_input` | `address` (int) | `tuple[bool, bool]` | Reads the boolean state of a discrete input (X). Returns `(value, success)`. |
| `read_holding` | `address` (int) | `tuple[float, bool]` | Reads a numeric value from a holding register (D). Returns `(value, success)`. |

---