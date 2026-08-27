from gi.repository import Adw, GLib

from src.backend.DeckManagement.InputIdentifier import Input
from src.backend.PluginManager.ActionCore import ActionCore
from src.backend.PluginManager.EventAssigner import EventAssigner


class LaunchApp(ActionCore):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_configuration = True
        self.add_event_assigner(
            EventAssigner(
                id="Launch",
                ui_label="Launch",
                default_events=[Input.Key.Events.DOWN, Input.Dial.Events.DOWN],
                callback=self.on_launch,
            )
        )

    def on_ready(self):
        self.set_media(media_path=self.get_asset_path("apps.svg"), size=0.75)
        label = self.get_settings().get("label", "App")
        self.set_bottom_label(label)

    def on_launch(self, data=None):
        component = self.get_settings().get("component", "").strip()
        if not component:
            self.show_error(1)
            return
        future = self.plugin_base.controller.submit_component(component)
        future.add_done_callback(self._finished)

    def _finished(self, future):
        error = future.exception()
        if error is not None:
            if self.plugin_base.logger:
                self.plugin_base.logger.error(f"Fire TV ADB: {error}")
            GLib.idle_add(self.show_error, 1)

    def get_config_rows(self):
        settings = self.get_settings()

        component = Adw.EntryRow(title="Android component")
        component.set_text(settings.get("component", ""))
        component.connect("notify::text", self.on_component_changed)

        label = Adw.EntryRow(title="Deck label")
        label.set_text(settings.get("label", "App"))
        label.connect("notify::text", self.on_label_changed)

        return [component, label]

    def on_component_changed(self, row, _):
        settings = self.get_settings()
        settings["component"] = row.get_text().strip()
        self.set_settings(settings)

    def on_label_changed(self, row, _):
        settings = self.get_settings()
        settings["label"] = row.get_text()
        self.set_settings(settings)
        self.on_ready()
