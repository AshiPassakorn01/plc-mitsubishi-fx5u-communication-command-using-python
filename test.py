from plc_module import PLCController

my_plc = PLCController()
connected = my_plc.plcConnect("192.168.3.250", 502)

if connected:
    # Test Write
    my_plc.write(0, True)     # Coil
    my_plc.write(3, 1500)     # Register
    
    # Test Read
    value, status = my_plc.read(3)
    
    # Test Disconnect
    my_plc.plcDisconnect()