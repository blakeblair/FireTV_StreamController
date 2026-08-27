import threading

from gi.repository import GLib

from src.backend.DeckManagement.InputIdentifier import Input
from src.backend.PluginManager.ActionCore import ActionCore
from src.backend.PluginManager.EventAssigner import EventAssigner

from .specs import BUTTONS


class RemoteButton(ActionCore):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repeat_stop = threading.Event()
        self.repeat_thread = None
        self.add_event_assigner(
            EventAssigner(
                id="Press",
                ui_label="Press",
                default_events=[Input.Key.Events.DOWN, Input.Dial.Events.DOWN],
                callback=self.on_press,
            )
        )
        self.add_event_assigner(
            EventAssigner(
                id="Release",
                ui_label="Release",
                default_events=[Input.Key.Events.UP, Input.Dial.Events.UP],
                callback=self.on_release,
            )
        )

    def get_spec(self):
        suffix = self.action_id.split("::", 1)[-1]
        return BUTTONS[suffix]

    def on_ready(self):
        spec = self.get_spec()
        self.set_media(media_path=self.get_asset_path(spec["icon"]), size=0.78)

    def on_press(self, data=None):
        spec = self.get_spec()
        self._submit(spec["keycode"])
        if spec["repeat"]:
            self._start_repeat(spec["keycode"])

    def on_release(self, data=None):
        self._stop_repeat()

    def _submit(self, keycode):
        future = self.plugin_base.controller.submit_key(keycode)
        future.add_done_callback(self._finished)

    def _finished(self, future):
        error = future.exception()
        if error is not None:
            if self.plugin_base.logger:
                self.plugin_base.logger.error(f"Fire TV ADB: {error}")
            GLib.idle_add(self.show_error, 1)

    def _start_repeat(self, keycode):
        self._stop_repeat()
        self.repeat_stop.clear()

        def worker():
            if self.repeat_stop.wait(0.45):
                return
            while not self.repeat_stop.wait(0.14):
                self._submit(keycode)

        self.repeat_thread = threading.Thread(target=worker, daemon=True)
        self.repeat_thread.start()

    def _stop_repeat(self):
        self.repeat_stop.set()

    def on_remove(self):
        self._stop_repeat()

    def on_removed_from_cache(self):
        self._stop_repeat()
