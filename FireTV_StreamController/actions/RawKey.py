from gi.repository import Adw, GLib

from src.backend.DeckManagement.InputIdentifier import Input
from src.backend.PluginManager.ActionCore import ActionCore
from src.backend.PluginManager.EventAssigner import EventAssigner


class RawKey(ActionCore):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_configuration = True
        self.add_event_assigner(
            EventAssigner(
                id="Send",
                ui_label="Send",
                default_events=[Input.Key.Events.DOWN, Input.Dial.Events.DOWN],
                callback=self.on_send,
            )
        )

    def on_ready(self):
        self.set_media(media_path=self.get_asset_path("key.svg"), size=0.75)
        label = self.get_settings().get("label", "Key")
        self.set_bottom_label(label)

    def on_send(self, data=None):
        settings = self.get_settings()
        keycode = settings.get("keycode", "").strip()
        if not keycode:
            self.show_error(1)
            return
        future = self.plugin_base.controller.submit_key(keycode, settings.get("longpress", False))
        future.add_done_callback(self._finished)

    def _finished(self, future):
        error = future.exception()
        if error is not None:
            if self.plugin_base.logger:
                self.plugin_base.logger.error(f"Fire TV ADB: {error}")
            GLib.idle_add(self.show_error, 1)

    def get_config_rows(self):
        settings = self.get_settings()

        keycode = Adw.EntryRow(title="Android keycode")
        keycode.set_text(settings.get("keycode", "KEYCODE_HOME"))
        keycode.connect("notify::text", self.on_keycode_changed)

        longpress = Adw.SwitchRow(title="Long press")
        longpress.set_active(settings.get("longpress", False))
        longpress.connect("notify::active", self.on_longpress_changed)

        label = Adw.EntryRow(title="Deck label")
        label.set_text(settings.get("label", "Key"))
        label.connect("notify::text", self.on_label_changed)

        return [keycode, longpress, label]

    def on_keycode_changed(self, row, _):
        settings = self.get_settings()
        settings["keycode"] = row.get_text().strip()
        self.set_settings(settings)

    def on_longpress_changed(self, row, _):
        settings = self.get_settings()
        settings["longpress"] = row.get_active()
        self.set_settings(settings)

    def on_label_changed(self, row, _):
        settings = self.get_settings()
        settings["label"] = row.get_text()
        self.set_settings(settings)
        self.on_ready()
