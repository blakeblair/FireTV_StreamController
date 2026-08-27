import os

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk

from src.backend.DeckManagement.InputIdentifier import Input
from src.backend.PluginManager.ActionHolder import ActionHolder
from src.backend.PluginManager.ActionInputSupport import ActionInputSupport
from src.backend.PluginManager.PluginBase import PluginBase

from .actions.LaunchApp import LaunchApp
from .actions.RawKey import RawKey
from .actions.RemoteButton import RemoteButton
from .actions.SendText import SendText
from .actions.specs import BUTTONS
from .controller import FireTVController


class FireTVADB(PluginBase):
    def __init__(self):
        super().__init__()
        self.has_plugin_settings = True
        self.controller = FireTVController(self)

        support = {
            Input.Key: ActionInputSupport.SUPPORTED,
            Input.Dial: ActionInputSupport.SUPPORTED,
            Input.Touchscreen: ActionInputSupport.UNSUPPORTED,
        }

        for suffix, spec in BUTTONS.items():
            self.add_action_holder(
                ActionHolder(
                    plugin_base=self,
                    action_core=RemoteButton,
                    action_id_suffix=suffix,
                    action_name=spec["name"],
                    action_support=support,
                    icon=Gtk.Image.new_from_file(os.path.join(self.PATH, "assets", spec["icon"])),
                )
            )

        self.add_action_holder(
            ActionHolder(
                plugin_base=self,
                action_core=LaunchApp,
                action_id_suffix="LaunchApp",
                action_name="App Shortcut",
                action_support=support,
                icon=Gtk.Image.new_from_file(os.path.join(self.PATH, "assets", "apps.svg")),
            )
        )

        self.add_action_holder(
            ActionHolder(
                plugin_base=self,
                action_core=RawKey,
                action_id_suffix="RawKey",
                action_name="Custom Key Event",
                action_support=support,
                icon=Gtk.Image.new_from_file(os.path.join(self.PATH, "assets", "key.svg")),
            )
        )

        self.add_action_holder(
            ActionHolder(
                plugin_base=self,
                action_core=SendText,
                action_id_suffix="SendText",
                action_name="Send Text",
                action_support=support,
                icon=Gtk.Image.new_from_file(os.path.join(self.PATH, "assets", "text.svg")),
            )
        )

        self.register(
            plugin_name="Fire TV ADB",
            github_repo="https://github.com/blakeblair/FireTV_StreamController",
            plugin_version="0.1.2",
            app_version="1.5.0-beta.14",
        )

    def get_settings_area(self):
        group = Adw.PreferencesGroup()
        group.set_title("Fire TV ADB connection")
        group.set_description("Configure the Fire TV target used by every action in this plugin.")

        settings = self.get_settings()

        self.target_row = Adw.EntryRow(title="ADB target")
        self.target_row.set_text(settings.get("target", ""))
        group.add(self.target_row)

        self.adb_row = Adw.EntryRow(title="ADB executable")
        self.adb_row.set_text(settings.get("adb_path", "adb"))
        group.add(self.adb_row)

        action_row = Adw.ActionRow(title="Connection")
        action_row.set_subtitle("Save the target, then connect and verify that ADB reports device state.")
        save_button = Gtk.Button(label="Save")
        save_button.set_valign(Gtk.Align.CENTER)
        save_button.connect("clicked", self.on_save_clicked)
        test_button = Gtk.Button(label="Test")
        test_button.set_valign(Gtk.Align.CENTER)
        test_button.connect("clicked", self.on_test_clicked)
        action_row.add_suffix(save_button)
        action_row.add_suffix(test_button)
        group.add(action_row)

        self.status_row = Adw.ActionRow(title="Status")
        self.status_row.set_subtitle("Not tested")
        group.add(self.status_row)

        return group

    def save_connection_settings(self):
        settings = self.get_settings()
        settings["target"] = self.target_row.get_text().strip()
        settings["adb_path"] = self.adb_row.get_text().strip() or "adb"
        self.set_settings(settings)
        self.controller.last_verified = 0.0

    def on_save_clicked(self, button):
        self.save_connection_settings()
        self.status_row.set_subtitle("Saved")

    def on_test_clicked(self, button):
        self.save_connection_settings()
        self.status_row.set_subtitle("Testing…")
        button.set_sensitive(False)
        future = self.controller.submit_test()
        future.add_done_callback(lambda f: GLib.idle_add(self.finish_test, f, button))

    def finish_test(self, future, button):
        button.set_sensitive(True)
        error = future.exception()
        if error is None:
            _, target = future.result()
            self.status_row.set_subtitle(f"Connected: {target}")
        else:
            self.status_row.set_subtitle(str(error))
        return False

    def on_uninstall(self):
        self.controller.shutdown()
        super().on_uninstall()
