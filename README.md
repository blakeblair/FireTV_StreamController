# StreamController Fire TV ADB

A StreamController plugin that exposes Fire TV remote controls as Stream Deck actions over Android Debug Bridge.

## Target

This source targets the Nixpkgs StreamController package version `1.5.0-beta.14`.

## Included actions

- Up
- Down
- Left
- Right
- Select
- Back
- Home
- Menu
- Rewind
- Play / Pause
- Fast Forward
- Mute
- Volume Up
- Volume Down
- Guide
- Power
- Alexa / Voice Assist
- Live TV / Guide
- Info
- Input Select
- Input: HDMI 1
- Input: HDMI 2
- Input: HDMI 3
- Input: HDMI 4
- Input: Antenna / Cable
- Input: Composite 1
- Input: Composite 2
- Input: Component 1
- Input: Component 2
- Input: VGA 1
- App Shortcut
- Custom Key Event
- Send Text

The directional and volume actions repeat while the Stream Deck control is held. `Input Select` reproduces Android's TV input key, while the `Input:` actions request a specific source directly.

`App Shortcut` can be placed multiple times to reproduce the four preset app buttons on current Alexa Voice Remotes. Each instance takes an Android component in `package.name/.ActivityName` form.

`Custom Key Event` accepts an Android `KEYCODE_*` name and can optionally send it as a long press.

`Send Text` opens a text-entry dialog each time the Stream Deck action is pressed. Text is not predetermined or stored in the action. Enter the text on the NixOS host and press Send to type it into the currently focused Fire TV text field.

`Live TV / Guide` is retained as a compatibility action for layouts created with version 0.1.1. It now sends the same `KEYCODE_GUIDE` event as `Guide`, matching the Fire TV remote behavior documented by Amazon instead of the unsupported `KEYCODE_TV` mapping previously used.

## NixOS dependency

StreamController does not bundle ADB. Add Android platform tools to your NixOS configuration:

```nix
environment.systemPackages = with pkgs; [
  android-tools
];
```

Then rebuild your system.

## Enable ADB on Fire TV

On Fire TV, enable ADB debugging under the device developer options. Find the Fire TV IP address under the device's About > Network screen.

Connect once from the NixOS host:

```bash
adb connect FIRE_TV_IP:5555
adb devices
```

Accept the authorization prompt on the Fire TV and select the option to always allow the computer if you want persistent control.

## Install the plugin locally

The Nix package uses StreamController's normal data directory unless you changed the data path manually.

```bash
mkdir -p ~/.var/app/com.core447.StreamController/data/plugins
cp -r FireTV_StreamController ~/.var/app/com.core447.StreamController/data/plugins/
```

Restart StreamController.

Open StreamController settings, open the Fire TV ADB plugin settings, and set:

- `ADB target`: `FIRE_TV_IP:5555`
- `ADB executable`: `adb`

Press `Test`. The status should change to `Connected: FIRE_TV_IP:5555`.

## Remote parity limits

The plugin exposes an ADB equivalent for the Fire TV remote controls, including TV input selection, plus direct Android TV source-selection actions for HDMI 1-4, antenna/cable, composite, component, and VGA when the Fire TV device supports those inputs. Long-press behavior can be created with `Custom Key Event`.

There are hardware limits that ADB cannot erase:

1. The physical Alexa Voice Remote contains a microphone. Sending `KEYCODE_VOICE_ASSIST` can invoke Android's global voice-assist activity, but a Stream Deck does not send microphone audio to the Fire TV.
2. Some Fire TV remotes control a television, receiver, or soundbar through equipment control, HDMI-CEC, or IR. ADB injects a key event into Fire OS; it does not transmit the physical remote's IR signal. Whether power, volume, and mute reach external equipment therefore depends on the Fire TV and equipment-control setup.
3. A network ADB command cannot be relied on to wake a Fire TV after the device has suspended networking or stopped accepting ADB. The `Power` action is available whenever ADB is reachable, but it is not a guaranteed replacement for the physical remote's wake path.

## App shortcut components

Amazon documents launching a Fire TV app by Android component with:

```bash
adb shell am start -n package.name/.MainActivity
```

The plugin intentionally asks for the component instead of guessing application activities.

## Source layout

```text
FireTV_StreamController/
├── actions/
├── assets/
├── controller.py
├── main.py
├── manifest.json
├── about.json
└── attribution.json
```

## Official references

- StreamController plugin API: https://streamcontroller.github.io/docs/latest/plugin_dev/bases/ActionCore_py/
- StreamController plugin registration: https://streamcontroller.github.io/docs/latest/plugin_dev/plugin_template/main_py/
- Amazon Fire TV ADB setup: https://developer.amazon.com/docs/fire-tv/connecting-adb-to-device.html
- Amazon Alexa Voice Remote button layout: https://www.amazon.com/gp/help/customer/display.html?nodeId=THKXBX5oZWzl3GmLzQ
- Amazon Fire TV controller behavior: https://developer.amazon.com/docs/fire-tv/controller-behavior-guidelines.html
- Android `KeyEvent` constants: https://developer.android.com/reference/android/view/KeyEvent
- Android Open Source Project `input` command implementation: https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/cmds/input/src/com/android/commands/input/Input.java
