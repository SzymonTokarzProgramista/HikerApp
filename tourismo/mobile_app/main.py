import os
import shutil
from typing import Optional, List

# --- KivyMD
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton

# --- Kivy
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty, ListProperty, NumericProperty, BooleanProperty
from kivy.clock import Clock
from kivy.uix.image import AsyncImage  # tylko do asynchronicznych zdjęć

# --- Twoje moduły
from services.api_client import APIClient
from utils.camera import CameraHelper
from utils.gps import GPSHelper


# === PROSTY ZAMIENNIK SNACKBARA ============================================

_current_dialog: Optional[MDDialog] = None


def show_snackbar(message: str, title: str = "Info"):
    """
    Zamiennik Snackbar -> prosty MDDialog z tekstem.
    UWAGA: MUSI być wołane z głównego wątku Kivy -> wymuszamy przez Clock.
    """
    def _open_dialog(dt):
        global _current_dialog

        # zamknij poprzedni dialog, jeśli jeszcze jest otwarty
        if _current_dialog:
            try:
                _current_dialog.dismiss()
            except Exception:
                pass
            _current_dialog = None

        _current_dialog = MDDialog(
            title=title,
            text=str(message),
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda *_: _current_dialog.dismiss()
                )
            ],
        )
        _current_dialog.open()

    Clock.schedule_once(_open_dialog, 0)


# === EKRANY =================================================================


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

        from kivymd.uix.card import MDCard
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.label import MDLabel
        from kivy.uix.widget import Widget
        from kivy.graphics import Color, Rectangle

        for item in self.posts:
            card = MDCard(
                radius=[12, 12, 12, 12],
                padding=dp(0),
                md_bg_color=(
                    MDApp.get_running_app().theme_cls.surfaceColor
                    if hasattr(MDApp.get_running_app().theme_cls, "surfaceColor")
                    else MDApp.get_running_app().theme_cls.bg_light
                ),
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

            meta = MDBoxLayout(
                orientation="vertical",
                padding=dp(12),
                size_hint_y=None,
                height=dp(64),
            )

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

            # półprzezroczysty overlay pod napisami
            overlay = Widget(size_hint_y=None, height=dp(64))
            with overlay.canvas.before:
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
    photo_path = StringProperty("")  # NIE może być None
    coords = StringProperty("")
    lat = NumericProperty(0.0)
    lon = NumericProperty(0.0)
    has_location = BooleanProperty(False)

    def open_camera(self):
        def ok(path):
            # callback może przyjść spoza UI thread -> przerzuć na Clock
            def _set(dt):
                if not path:
                    show_snackbar("Nie wybrano zdjęcia.")
                    return
                self.photo_path = str(path)
                show_snackbar("Wybrano zdjęcie")
            Clock.schedule_once(_set, 0)

        def err(msg):
            Clock.schedule_once(lambda dt, m=str(msg): show_snackbar(f"Kamera: {m}"), 0)

        CameraHelper.take_photo(ok, err)

    def get_location(self):
        def ok(lat, lon):
            def _set(dt):
                self.lat = float(lat)
                self.lon = float(lon)
                self.coords = f"{self.lat:.6f}, {self.lon:.6f}"
                self.has_location = True
                show_snackbar("Pobrano pozycję GPS")
            Clock.schedule_once(_set, 0)

        def err(msg):
            Clock.schedule_once(lambda dt, m=str(msg): show_snackbar(f"GPS: {m}"), 0)

        GPSHelper.get_location(ok, err)

    def publish(self):
        app = MDApp.get_running_app()
        user_id = app.state_user_id

        if not user_id:
            show_snackbar("Najpierw zaloguj się.")
            app.change_screen("login")
            return

        # photo_path musi być stringiem + istnieć
        if not self.photo_path or not os.path.exists(self.photo_path):
            show_snackbar("Brak zdjęcia do wysłania.")
            return

        try:
            app.api.upload_photo(
                user_id=user_id,
                filepath=self.photo_path,
                lat=self.lat if self.has_location else None,
                lon=self.lon if self.has_location else None,
            )

            # opcjonalny lokalny cache zdjęć
            try:
                uploads_dir = os.path.join(os.getcwd(), "uploads_cache")
                os.makedirs(uploads_dir, exist_ok=True)
                shutil.copy(
                    self.photo_path,
                    os.path.join(uploads_dir, os.path.basename(self.photo_path)),
                )
            except Exception:
                pass

            self.photo_path = ""
            self.coords = ""
            self.has_location = False

            show_snackbar("Opublikowano!")
            app.change_screen("feed")
            Clock.schedule_once(lambda *_: app.refresh_feed(), 0.2)

        except Exception as e:
            show_snackbar(f"Upload: {e}")


class Root(MDScreenManager):
    pass


# === GŁÓWNA APLIKACJA =======================================================


class TourismoApp(MDApp):
    api: APIClient
    state_user_id: Optional[int] = None
    state_email: Optional[str] = None

    def build(self):
        # Motyw
        self.theme_cls.material_style = "M3"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.primary_hue = "500"
        self.title = "Tourismo"

        # Kolor powierzchni (jeśli dostępny)
        try:
            self.theme_cls.surfaceColor = self.theme_cls.bg_light
        except Exception:
            pass

        self.api = APIClient()
        kv_path = os.path.join(os.path.dirname(__file__), "tourismo.kv")
        return Builder.load_file(kv_path)

    # --- nawigacja
    def change_screen(self, name: str):
        self.root.current = name

    # --- auth
    def do_login(self, email: str, password: str):
        if not email or not password:
            show_snackbar("Podaj e-mail i hasło.")
            return
        try:
            data = self.api.login(email, password)
            self.state_user_id = int(data["user_id"])
            self.state_email = data["email"]
            show_snackbar(f"Witaj, {self.state_email}!")
            self.change_screen("feed")
        except Exception as e:
            show_snackbar(f"Logowanie: {e}")

    def do_register(self, email: str, password: str):
        if not email or not password:
            show_snackbar("Podaj e-mail i hasło.")
            return
        try:
            self.api.register(email, password)
            show_snackbar("Konto utworzone. Zaloguj się.")
            self.change_screen("login")
        except Exception as e:
            show_snackbar(f"Rejestracja: {e}")

    # --- feed
    def refresh_feed(self):
        try:
            data = self.api.get_feed()
            feed: FeedScreen = self.root.get_screen("feed")
            feed.posts = data
            Clock.schedule_once(lambda *_: feed.populate_grid(), 0)
        except Exception as e:
            show_snackbar(f"Feed: {e}")


if __name__ == "__main__":
    TourismoApp().run()
