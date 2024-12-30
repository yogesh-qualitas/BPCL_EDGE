import os
import logging
import threading
from datetime import datetime
from MVSDK import *
from dahua_camera import DahuaCameras                                                

class CameraManager:
    def __init__(self, camera_serials, websocket_address, websocket_port):
        """
        Initialize the CameraManager with a list of camera serials and WebSocket details.
        """
        self.camera_serials = camera_serials  # List of camera serial numbers
        
        self.websocket_address = websocket_address
        self.websocket_port = websocket_port
        self.cameras = {}  # Dictionary to store camera objects
        self.threads = {}  # Dictionary to store camera handling threads
        self.stop_threads = threading.Event()  # Event to signal thread termination
        self.setup_logging()

   
   
    def setup_logging(self):
        """
        Setup logging for the application.
        """
        # Create the directory structure for the log file if it doesn't exist
        log_dir = os.path.join("log", "cameraManager")
        os.makedirs(log_dir, exist_ok=True)

        # Generate the log file name based on the current date
        log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")

        # Configure the logging settings
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file, mode='a'),
                logging.StreamHandler()  # Optional: Log to console as well
            ]
        )

        logging.info("Logging setup complete. Logs will be saved to: %s", log_file)

    def enumCameras(self):
        """
        Discover cameras using GENICAM API.
        """
        system = pointer(GENICAM_System())
        nRet = GENICAM_getSystemInstance(byref(system))
        if nRet != 0:
            logging.error("Failed to get GENICAM system instance.")
            return None, None

        camera_list = pointer(GENICAM_Camera())
        camera_count = c_uint()
        nRet = system.contents.discovery(system, byref(camera_list), byref(camera_count), c_int(GENICAM_EProtocolType.typeAll))
        if nRet != 0:
            logging.error("Camera discovery failed.")
            return None, None
        elif camera_count.value < 1:
            logging.info("No cameras discovered.")
            return None, None
        else:
            logging.info("Discovered %d cameras.", camera_count.value)

            for i in range(0,camera_count.value):

                sr_no = str(camera_list[i].getSerialNumber(camera_list[i]).decode('utf-8'))
                print(sr_no)
                if sr_no in self.camera_serials:
                    self.cameras[sr_no]=DahuaCameras(camera_list[i].getSerialNumber(camera_list[i]),camera_list[i])

    def initialize_camera(self, serial):
        """
        Initialize a specific camera by its serial number.
        """
        logging.info("Initializing camera with serial: %s", serial)
        # Placeholder for camera initialization logic

    def handle_camera(self, serial):
        """
        Handle the camera stream and process frames in a separate thread.
        """
        logging.info("Handling camera with serial: %s", serial)
        # Placeholder for camera handling logic in a thread

    def start_camera_threads(self):
        """
        Start threads for handling all cameras.
        """
        logging.info("Starting threads for all cameras...")
        # Placeholder for starting camera threads

    def stop_camera_threads(self):
        """
        Signal all threads to stop and perform cleanup.
        """
        logging.info("Stopping all camera threads...")
        self.stop_threads.set()  # Signal threads to stop
        # Placeholder for stopping threads

    def reconnect_camera(self, serial):
        """
        Attempt to reconnect a disconnected camera.
        """
        logging.info("Attempting to reconnect camera with serial: %s", serial)
        # Placeholder for camera reconnection logic

    def monitor_cameras(self):
        """
        Continuously monitor cameras for disconnections and handle reconnections.
        """
        logging.info("Monitoring cameras...")
        # Placeholder for camera monitoring logic

    def cleanup(self):
        """
        Perform cleanup operations, such as closing connections and releasing resources.
        """
        logging.info("Performing cleanup operations...")
        # Placeholder for cleanup logic


