from kivy.lang import Builder
from kivy.properties import StringProperty, ListProperty, NumericProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.snackbar import Snackbar
from kivy.uix.image import AsyncImage
from kivy.metrics import dp

from services.api_client import APIClient
from utils.camera import CameraHelper
from utils.gps import GPSHelper


class LoginScreen(Screen):
    pass


class RegisterScreen(Screen):
    pass


class FeedScreen(Screen):
    posts = ListProperty([])  # [{user, photo, lat, lon, created_at}]

    def on_pre_enter(self):
        app = MDApp.get_running_app()
        try:
            data = app.api.get_feed()
            self.posts = data
            # odśwież miniatury po zbudowaniu widoku
            Clock.schedule_once(lambda *_: self.populate_grid(), 0)
        except Exception as e:
            Snackbar(text=f"Błąd feedu: {e}").open()

    def populate_grid(self):
        grid = self.ids.get("grid")
        if not grid:
            return
        grid.clear_widgets()
        app = MDApp.get_running_app()
        for item in self.posts:
            src = app.api.uploads_url(item["photo"])
            img = AsyncImage(source=src, size_hint_y=None, height=dp(160), allow_stretch=True, keep_ratio=True)
            grid.add_widget(img)


class NewPostScreen(Screen):
    selected_path = StringProperty("")
    coords = StringProperty("")
    user_id = NumericProperty(0)

    def on_pre_enter(self):
        self.user_id = MDApp.get_running_app().user_id or 0

    def take_photo(self):
        CameraHelper.take_photo(
            callback_ok=lambda path: (setattr(self, "selected_path", path), Snackbar(text="Zrobiono zdjęcie").open()),
            callback_err=lambda err: Snackbar(text=f"Błąd aparatu: {err}").open()
        )

    def get_location(self):
        GPSHelper.get_location(
            cb_ok=lambda lat, lon: (setattr(self, "coords", f"{lat:.5f},{lon:.5f}"),
                                    Snackbar(text=f"GPS: {lat:.5f},{lon:.5f}").open()),
            cb_err=lambda err: Snackbar(text=f"Błąd GPS: {err}").open()
        )

    def publish(self):
        app = MDApp.get_running_app()
        if not self.selected_path:
            Snackbar(text="Najpierw zrób zdjęcie").open()
            return
        lat = lon = None
        if self.coords and "," in self.coords:
            lat, lon = self.coords.split(",", 1)
        try:
            app.api.upload_post(app.user_id, self.selected_path,
                                float(lat) if lat else None,
                                float(lon) if lon else None)
            Snackbar(text="Opublikowano!").open()
            self.selected_path, self.coords = "", ""
            app.change_screen("feed")
        except Exception as e:
            Snackbar(text=f"Błąd publikacji: {e}").open()


class Root(ScreenManager):
    pass


class TourismoApp(MDApp):
    api: APIClient
    user_id = None
    email = None

    def build(self):
        self.title = "Tourismo"
        self.theme_cls.primary_palette = "Blue"
        self.api = APIClient()
        Builder.load_file("tourismo.kv")
        return Root()

    def change_screen(self, name):
        self.root.current = name

    # Auth
    def do_login(self, email, password):
        try:
            res = self.api.login(email, password)
            if res.get("ok"):
                self.user_id = res["user_id"]
                self.email = res["email"]
                self.change_screen("feed")
            else:
                Snackbar(text=res.get("error", "Błąd logowania")).open()
        except Exception as e:
            Snackbar(text=f"Logowanie nieudane: {e}").open()

    def do_register(self, email, password):
        try:
            res = self.api.register(email, password)
            if res.get("ok"):
                Snackbar(text="Konto utworzone — zaloguj się.").open()
                self.change_screen("login")
            else:
                Snackbar(text=res.get("error", "Rejestracja nieudana")).open()
        except Exception as e:
            Snackbar(text=f"Rejestracja nieudana: {e}").open()


if __name__ == "__main__":
    TourismoApp().run()
