import os
import time
import tempfile
from kivy.clock import Clock
from kivy.utils import platform


class GalleryPicker:
    REQUEST_CODE = 4242

    @staticmethod
    def pick_image(callback_ok, callback_err):
        if platform != "android":
            Clock.schedule_once(lambda dt: callback_err("Picker działa tylko na Androidzie."), 0)
            return

        try:
            from jnius import autoclass
            from android import activity

            Intent = autoclass("android.content.Intent")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Activity = autoclass("android.app.Activity")

            intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType("image/*")
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)

            def on_activity_result(request_code, result_code, data):
                # ważne: odpinamy handler
                activity.unbind(on_activity_result=on_activity_result)

                if request_code != GalleryPicker.REQUEST_CODE:
                    return

                if result_code != Activity.RESULT_OK or data is None:
                    Clock.schedule_once(lambda dt: callback_err("Anulowano wybór zdjęcia."), 0)
                    return

                uri = data.getData()
                if uri is None:
                    Clock.schedule_once(lambda dt: callback_err("Nie udało się pobrać URI zdjęcia."), 0)
                    return

                try:
                    dest_path = GalleryPicker._copy_uri_to_cache(uri)
                    Clock.schedule_once(lambda dt: callback_ok(dest_path), 0)
                except Exception as ex:
                    msg = str(ex)
                    Clock.schedule_once(lambda dt, m=msg: callback_err(m), 0)

            activity.bind(on_activity_result=on_activity_result)

            current_activity = PythonActivity.mActivity
            current_activity.startActivityForResult(intent, GalleryPicker.REQUEST_CODE)

        except Exception as ex:
            msg = str(ex)
            Clock.schedule_once(lambda dt, m=msg: callback_err(m), 0)

    @staticmethod
    def _copy_uri_to_cache(uri):
        from jnius import autoclass, jarray

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        context = PythonActivity.mActivity
        resolver = context.getContentResolver()

        input_stream = resolver.openInputStream(uri)
        if input_stream is None:
            raise RuntimeError("Nie można otworzyć strumienia wybranego zdjęcia.")

        filename = f"tourismo_{int(time.time())}.jpg"
        dest_path = os.path.join(tempfile.gettempdir(), filename)

        buf = jarray("b", 1024 * 64)

        with open(dest_path, "wb") as f:
            while True:
                n = input_stream.read(buf)
                if n <= 0:
                    break
                f.write(bytes(buf[:n]))

        input_stream.close()

        if not os.path.exists(dest_path) or os.path.getsize(dest_path) == 0:
            raise RuntimeError("Skopiowany plik jest pusty.")

        return dest_path
