Here is a professional README file in English, keeping a standard and clean structure based on the module we just built. All emojis have been removed as requested.

```markdown
# Modbus TCP PLC Controller

A Python module designed to simplify communication with Programmable Logic Controllers (PLCs) using the Modbus TCP protocol. This controller acts as a wrapper around the `pymodbus` library, providing straightforward methods to read and write data to various PLC memory areas (Outputs, Internal Relays, Data Registers, and Inputs).

## Prerequisites

This module requires Python 3.x and the `pymodbus` library.

You can install the required dependency using pip:

```bash
pip install pymodbus

```

## Features

* **Standardized Return Values:** Write functions return a boolean indicating success. Read functions return a tuple containing the read value and a boolean success flag.
* **Configurable Logging:** Includes a `config_print` parameter to easily enable or disable console logs during execution.
* **Simplified Interface:** Dedicated functions for different PLC memory types (e.g., `write_Y`, `write_M`, `read_holding`) to make the code highly readable.
* **No Slave Parameter Issue:** Optimized for modern Modbus TCP implementations where the unit/slave ID is not required or strictly handled by the IP connection.

## Quick Start

### 1. Initialization and Connection

Import the class and initialize it. You can disable internal logging by setting `config_print=False`.

```python
from plc_module import PLCController

# Initialize the controller
plc = PLCController(config_print=True)

# Connect to the PLC
IP_ADDRESS = "192.168.3.250"
PORT = 502

if plc.plcConnect(ip=IP_ADDRESS, port=PORT):
    print("Ready to communicate.")
else:
    print("Connection failed.")

```

### 2. Writing to PLC

Write operations return a single boolean (`True` if successful, `False` otherwise).

```python
# Write to Output Coil (Y0 -> ON)
plc.write_Y(address=0, status=True)

# Write to Internal Relay (M100 -> OFF)
plc.write_M(address=100, status=False)

# Write to Holding Register (D10 -> 1234)
plc.write_holding(address=10, value=1234)

```

### 3. Reading from PLC

Read operations return a tuple: `(value, status)`.

```python
# Read Output/Relay Coil (M or Y)
value, success = plc.read_coil(address=0)
if success:
    print(f"Coil Status: {value}")

# Read Input (X)
value, success = plc.read_input(address=0)
if success:
    print(f"Input Status: {value}")

# Read Holding Register (D)
value, success = plc.read_holding(address=10)
if success:
    print(f"Register Value: {value}")

```

### 4. Disconnection

Always disconnect cleanly when operations are finished.

```python
plc.plcDisconnect()

```

## Handling Signed 16-bit Integers

Modbus Holding Registers hold unsigned 16-bit integers (0 to 65535). If you need to write or read negative numbers, you must handle the Two's Complement conversion in your main script:

**Writing negative values:**

```python
value_to_send = -5
plc.write_holding(address=10, value=value_to_send & 0xFFFF)

```

**Reading negative values:**

```python
val, ok = plc.read_holding(address=10)
if ok:
    int_val = int(val)
    if int_val > 32767:
        int_val -= 65536
    print(f"Signed Value: {int_val}")

```

## Methods Reference

| Method | Arguments | Returns | Description |
| --- | --- | --- | --- |
| `plcConnect` | `ip (str)`, `port (int)` | `bool` | Establishes a TCP connection to the PLC. |
| `plcDisconnect` | None | `bool` | Closes the active TCP connection. |
| `write_Y` | `address (int)`, `status (bool)` | `bool` | Writes a boolean value to an Output coil. |
| `write_M` | `address (int)`, `status (bool)` | `bool` | Writes a boolean value to an Internal Relay coil. |
| `write_holding` | `address (int)`, `value (int)` | `bool` | Writes a 16-bit integer to a Holding Register. |
| `read_coil` | `address (int)` | `tuple[bool, bool]` | Reads status from a Coil (Y or M). Returns `(value, success)`. |
| `read_input` | `address (int)` | `tuple[bool, bool]` | Reads status from a Discrete Input (X). Returns `(value, success)`. |
| `read_holding` | `address (int)` | `tuple[float, bool]` | Reads a numeric value from a Holding Register. Returns `(value, success)`. |

```

Would you like me to add a specific section detailing the `run_plc_test` script to the README as well?

```