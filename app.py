from flask import Flask,send_from_directory
from modbus_initializer import ModbusClientSingleton
import threading
from cameras_initializar import CameraManager

app = Flask(__name__)

# Initialize Modbus client singleton with IP and port
modbus_client = ModbusClientSingleton('localhost', 502)

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        directory=app.root_path,
        path='static/favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )



def start_flask():
    app.run()

def initialize_modbus():
    if modbus_client.connect():
        print("Modbus client initialized")
    else:
        print("Failed to connect to Modbus server, starting recovery thread")
        recovery_thread = threading.Thread(target=modbus_client.recover_connection)
        recovery_thread.start()

if __name__ == '__main__':
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.start()

    # # Initialize Modbus in the main thread or another thread
    # modbus_thread = threading.Thread(target=initialize_modbus())
    # modbus_thread.start()

       # Example usage of CameraManager
    camera_serials = ["BF10849AAK00008"]
    websocket_address = "localhost"
    websocket_port = 5000

    manager = CameraManager(camera_serials, websocket_address, websocket_port)
    try:
        manager.enumCameras()
        if set(camera_serials) == set(manager.cameras.keys()):
            print("All cameras discovered successfully")
            pass
        else:
            print("Failed to discover all cameras")
 
       
        manager.start_camera_threads()
        manager.monitor_cameras()
    except KeyboardInterrupt:
        print("Shutdown requested by user.")
    finally:
        manager.stop_camera_threads()
        manager.cleanup()

    # print(flask_thread,modbus_thread)                                                                                                                                           