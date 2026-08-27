import globals as gl
from gi.repository import Adw, GLib, Gtk

from src.backend.DeckManagement.InputIdentifier import Input
from src.backend.PluginManager.ActionCore import ActionCore
from src.backend.PluginManager.EventAssigner import EventAssigner


class SendText(ActionCore):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_configuration = True
        self.dialog = None
        self.add_event_assigner(
            EventAssigner(
                id="Send",
                ui_label="Send",
                default_events=[Input.Key.Events.DOWN, Input.Dial.Events.DOWN],
                callback=self.on_send,
            )
        )

    def on_ready(self):
        self.set_media(media_path=self.get_asset_path("text.svg"), size=0.75)
        self.set_bottom_label(self.get_settings().get("label", "Text"))

    def on_send(self, data=None):
        GLib.idle_add(self._show_text_dialog)

    def _show_text_dialog(self):
        if self.dialog is not None:
            self.dialog.present()
            return False

        window = gl.app.get_active_window() if gl.app is not None else None
        if window is None and gl.app is not None:
            window = getattr(gl.app, "main_win", None)

        dialog = Adw.MessageDialog()
        if window is not None:
            dialog.set_transient_for(window)
        dialog.set_modal(True)
        dialog.set_heading("Send text to Fire TV")
        dialog.set_body("Type the text to send to the currently focused text field on the Fire TV.")
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("send", "Send")
        dialog.set_close_response("cancel")
        dialog.set_default_response("send")
        dialog.set_response_appearance("send", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_response_enabled("send", False)

        entry = Gtk.Entry()
        entry.set_placeholder_text("Text to send")
        entry.set_hexpand(True)
        entry.set_activates_default(True)
        entry.connect("notify::text", self._on_entry_changed, dialog)
        dialog.set_extra_child(entry)
        dialog.connect("response", self._on_dialog_response, entry)

        self.dialog = dialog
        dialog.present()
        GLib.idle_add(entry.grab_focus)
        return False

    def _on_entry_changed(self, entry, _param, dialog):
        dialog.set_response_enabled("send", bool(entry.get_text()))

    def _on_dialog_response(self, dialog, response, entry):
        text = entry.get_text()
        self.dialog = None
        dialog.destroy()

        if response != "send" or not text:
            return

        future = self.plugin_base.controller.submit_text(text)
        future.add_done_callback(self._finished)

    def _finished(self, future):
        error = future.exception()
        if error is not None:
            if self.plugin_base.logger:
                self.plugin_base.logger.error(f"Fire TV ADB: {error}")
            GLib.idle_add(self.show_error, 1)

    def get_config_rows(self):
        settings = self.get_settings()

        label = Adw.EntryRow(title="Deck label")
        label.set_text(settings.get("label", "Text"))
        label.connect("notify::text", self.on_label_changed)

        return [label]

    def on_label_changed(self, row, _):
        settings = self.get_settings()
        settings["label"] = row.get_text()
        self.set_settings(settings)
        self.on_ready()

    def on_remove(self):
        self._close_dialog()

    def on_removed_from_cache(self):
        self._close_dialog()

    def _close_dialog(self):
        if self.dialog is not None:
            dialog = self.dialog
            self.dialog = None
            GLib.idle_add(dialog.destroy)
