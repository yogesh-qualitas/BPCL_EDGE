from pymodbus.client.tcp import ModbusTcpClient
import threading
import time

class ModbusClientSingleton:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, ip, port, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(ModbusClientSingleton, cls).__new__(cls)
                    cls._instance._client = ModbusTcpClient(ip, port=port)
                    cls._instance._connected = False
        return cls._instance

    def connect(self):
        if not self._connected:
            self._connected = self._client.connect()
        return self._connected

    def close(self):
        if self._connected:
            self._client.close()
            self._connected = False

    def is_connected(self):
        return self._connected

    def recover_connection(self):
        while not self._connected:
            print("Attempting to reconnect to Modbus server...")
            self._connected = self._client.connect()
            if self._connected:
                print("Reconnected to Modbus server.")
            else:
                time.sleep(5)  # Wait before retrying
