import os
import shutil
from typing import Optional, List

# --- KivyMD specyficzne (zamiast gołych Kivy widżetów)
from kivymd.app import MDApp
from kivymd.uix.fitimage import FitImage
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton

# --- Kivy podstawowe
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty, ListProperty, NumericProperty, BooleanProperty
from kivy.clock import Clock
from kivy.uix.image import AsyncImage  # tylko do asynchronicznych zdjęć, nie ekranów

# --- Twoje moduły
from services.api_client import APIClient
from utils.camera import CameraHelper
from utils.gps import GPSHelper



class LoginScreen(MDScreen):
    pass


class RegisterScreen(MDScreen):
    pass


class FeedScreen(MDScreen):
    posts = ListProperty([])  # [{user, photo, lat, lon, created_at}]

    def on_pre_enter(self):
        # Odśwież feed po wejściu
        MDApp.get_running_app().refresh_feed()

    def populate_grid(self):
        grid = self.ids.grid
        grid.clear_widgets()
        api = MDApp.get_running_app().api
        for item in self.posts:
            # Karta zdjęcia
            from kivymd.uix.card import MDCard
            from kivymd.uix.boxlayout import MDBoxLayout
            from kivymd.uix.label import MDLabel

            card = MDCard(
                radius=[12, 12, 12, 12],
                padding=dp(0),
                md_bg_color=MDApp.get_running_app().theme_cls.surfaceColor,
                style="elevated",
                ripple_behavior=True,
                size_hint_y=None,
                height=dp(220),
            )

            box = MDBoxLayout(orientation="vertical")
            img = AsyncImage(
                source=api.uploads_url(item["photo"]),
                allow_stretch=True,
                keep_ratio=True,
            )
            meta = MDBoxLayout(orientation="vertical", padding=dp(12), size_hint_y=None, height=dp(64))
            user = MDLabel(
                text=item.get("user", ""),
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1),
                bold=True,
            )
            sub = MDLabel(
                text=(item.get("created_at") or ""),
                theme_text_color="Custom",
                text_color=(1, 1, 1, 0.85),
                font_style="Label",
            )
            # półprzezroczysty overlay tła pod napisami
            from kivy.uix.widget import Widget
            overlay = Widget(size_hint_y=None, height=dp(64))
            with overlay.canvas.before:
                from kivy.graphics import Color, Rectangle
                Color(0, 0, 0, 0.35)
                overlay._rect = Rectangle(pos=overlay.pos, size=overlay.size)
            overlay.bind(pos=lambda w, v: setattr(overlay._rect, "pos", v))
            overlay.bind(size=lambda w, v: setattr(overlay._rect, "size", v))

            meta.add_widget(user)
            meta.add_widget(sub)
            box.add_widget(img)
            box.add_widget(overlay)
            box.add_widget(meta)
            card.add_widget(box)
            grid.add_widget(card)


class NewPostScreen(MDScreen):
    photo_path = StringProperty("")
    coords = StringProperty("")
    lat = NumericProperty(0.0)
    lon = NumericProperty(0.0)
    has_location = BooleanProperty(False)

    def open_camera(self):
        def ok(path):
            self.photo_path = path
            Snackbar(text="Zrobiono zdjęcie").open()

        def err(msg):
            Snackbar(text=f"Kamera: {msg}").open()

        CameraHelper.take_photo(ok, err)

    def get_location(self):
        def ok(lat, lon):
            self.lat = float(lat)
            self.lon = float(lon)
            self.coords = f"{self.lat:.6f}, {self.lon:.6f}"
            self.has_location = True
            Snackbar(text="Pobrano pozycję GPS").open()

        def err(msg):
            Snackbar(text=f"GPS: {msg}").open()

        GPSHelper.get_location(ok, err)

    def publish(self):
        app = MDApp.get_running_app()
        user_id = app.state_user_id
        if not user_id:
            Snackbar(text="Najpierw zaloguj się.").open()
            app.change_screen("login")
            return
        if not self.photo_path or not os.path.exists(self.photo_path):
            Snackbar(text="Brak zdjęcia do wysłania.").open()
            return
        try:
            resp = app.api.upload_photo(
                user_id=user_id,
                filepath=self.photo_path,
                lat=self.lat if self.has_location else None,
                lon=self.lon if self.has_location else None,
            )
            # przenieś plik do uploads (opcjonalnie, lokalny cache)
            try:
                uploads_dir = os.path.join(os.getcwd(), "uploads_cache")
                os.makedirs(uploads_dir, exist_ok=True)
                shutil.copy(self.photo_path, os.path.join(uploads_dir, os.path.basename(self.photo_path)))
            except Exception:
                pass
            self.photo_path = ""
            self.coords = ""
            self.has_location = False
            Snackbar(text="Opublikowano!").open()
            app.change_screen("feed")
            Clock.schedule_once(lambda *_: app.refresh_feed(), 0.2)
        except Exception as e:
            Snackbar(text=f"Upload: {e}").open()


class Root(MDScreenManager):
    pass


class TourismoApp(MDApp):
    api: APIClient
    state_user_id: Optional[int] = None
    state_email: Optional[str] = None

    def build(self):
        # Motyw: zieleń + biel, Material You (M3)
        self.theme_cls.material_style = "M3"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.primary_hue = "500"
        self.title = "Tourismo"

        # Kolory powierzchni dopasowane do białej estetyki
        # (opcjonalnie można dostroić: surfaceColor jest dostępny od nowszych kivymd)
        try:
            self.theme_cls.surfaceColor = self.theme_cls.bg_light  # delikatne białe tło
        except Exception:
            pass

        self.api = APIClient()
        return Builder.load_file(os.path.join(os.path.dirname(__file__), "tourismo.kv"))

    # --- nawigacja
    def change_screen(self, name: str):
        self.root.current = name

    # --- auth
    def do_login(self, email: str, password: str):
        if not email or not password:
            Snackbar(text="Podaj e-mail i hasło.").open()
            return
        try:
            data = self.api.login(email, password)
            self.state_user_id = int(data["user_id"])
            self.state_email = data["email"]
            Snackbar(text=f"Witaj, {self.state_email}!").open()
            self.change_screen("feed")
        except Exception as e:
            Snackbar(text=f"Logowanie: {e}").open()

    def do_register(self, email: str, password: str):
        if not email or not password:
            Snackbar(text="Podaj e-mail i hasło.").open()
            return
        try:
            self.api.register(email, password)
            Snackbar(text="Konto utworzone. Zaloguj się.").open()
            self.change_screen("login")
        except Exception as e:
            Snackbar(text=f"Rejestracja: {e}").open()

    # --- feed
    def refresh_feed(self):
        try:
            data = self.api.get_feed()
            feed: FeedScreen = self.root.get_screen("feed")
            feed.posts = data
            Clock.schedule_once(lambda *_: feed.populate_grid(), 0)
        except Exception as e:
            Snackbar(text=f"Feed: {e}").open()


if __name__ == "__main__":
    TourismoApp().run()
