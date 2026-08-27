import unittest

from dev_blakeblair_FireTVADB.actions.specs import BUTTONS


class InputSpecTests(unittest.TestCase):
    def test_general_input_select(self):
        self.assertEqual(BUTTONS["InputSelect"]["keycode"], "KEYCODE_TV_INPUT")

    def test_hdmi_inputs(self):
        for number in range(1, 5):
            self.assertEqual(
                BUTTONS[f"InputHDMI{number}"]["keycode"],
                f"KEYCODE_TV_INPUT_HDMI_{number}",
            )

    def test_other_tv_inputs(self):
        expected = {
            "InputAntennaCable": "KEYCODE_TV_ANTENNA_CABLE",
            "InputComposite1": "KEYCODE_TV_INPUT_COMPOSITE_1",
            "InputComposite2": "KEYCODE_TV_INPUT_COMPOSITE_2",
            "InputComponent1": "KEYCODE_TV_INPUT_COMPONENT_1",
            "InputComponent2": "KEYCODE_TV_INPUT_COMPONENT_2",
            "InputVGA1": "KEYCODE_TV_INPUT_VGA_1",
        }
        for action, keycode in expected.items():
            self.assertEqual(BUTTONS[action]["keycode"], keycode)

    def test_live_tv_compatibility_uses_guide(self):
        self.assertEqual(BUTTONS["Guide"]["keycode"], "KEYCODE_GUIDE")
        self.assertEqual(BUTTONS["LiveTV"]["keycode"], "KEYCODE_GUIDE")


if __name__ == "__main__":
    unittest.main()
