from utils.gallery_picker import GalleryPicker

class CameraHelper:
    @staticmethod
    def take_photo(callback_ok, callback_err):
        # Teraz „take_photo” = wybierz z galerii
        GalleryPicker.pick_image(callback_ok, callback_err)
