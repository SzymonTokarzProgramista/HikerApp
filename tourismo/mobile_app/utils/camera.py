from plyer import camera
import os, tempfile, time

class CameraHelper:
    @staticmethod
    def take_photo(callback_ok, callback_err):
        try:
            path = os.path.join(tempfile.gettempdir(), f"tourismo_{int(time.time())}.jpg")
            camera.take_picture(filename=path, on_complete=lambda *_: callback_ok(path))
        except Exception as e:
            callback_err(str(e))
