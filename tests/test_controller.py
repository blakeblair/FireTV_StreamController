import os
from pathlib import Path
import tempfile
import unittest

from FireTV_StreamController.controller import FireTVController


class PluginStub:
    def __init__(self, settings):
        self.settings = settings

    def get_settings(self):
        return dict(self.settings)


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.log = self.root / "adb.log"
        self.adb = self.root / "adb"
        self.adb.write_text(
            "#!/usr/bin/env bash\n"
            "set -eu\n"
            f"printf '%s\\n' \"$*\" >> {self.log!s}\n"
            "if [[ \"${1:-}\" == connect ]]; then echo connected; exit 0; fi\n"
            "if [[ \"${3:-}\" == get-state ]]; then echo device; exit 0; fi\n"
            "exit 0\n"
        )
        self.adb.chmod(0o755)
        self.plugin = PluginStub({"target": "192.0.2.10:5555", "adb_path": str(self.adb)})
        self.controller = FireTVController(self.plugin)

    def tearDown(self):
        self.controller.shutdown()
        self.tmp.cleanup()

    def test_key_event(self):
        self.controller.send_key("KEYCODE_HOME")
        text = self.log.read_text()
        self.assertIn("-s 192.0.2.10:5555 get-state", text)
        self.assertIn("-s 192.0.2.10:5555 shell input keyevent KEYCODE_HOME", text)

    def test_long_key_event(self):
        self.controller.send_key("KEYCODE_HOME", True)
        self.assertIn("shell input keyevent --longpress KEYCODE_HOME", self.log.read_text())

    def test_component(self):
        self.controller.start_component("com.example/.MainActivity")
        self.assertIn("shell am start -n com.example/.MainActivity", self.log.read_text())

    def test_text(self):
        self.controller.send_text("hello world")
        self.assertIn("shell input text hello%sworld", self.log.read_text())


if __name__ == "__main__":
    unittest.main()
