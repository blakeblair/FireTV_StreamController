from concurrent.futures import ThreadPoolExecutor
import os
import shutil
import subprocess
import threading
import time


class ADBError(RuntimeError):
    pass


class FireTVController:
    def __init__(self, plugin_base):
        self.plugin_base = plugin_base
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="firetv-adb")
        self.lock = threading.Lock()
        self.last_verified = 0.0
        self.verify_ttl = 8.0

    def shutdown(self):
        self.executor.shutdown(wait=False, cancel_futures=True)

    def get_settings(self):
        settings = self.plugin_base.get_settings()
        return {
            "target": settings.get("target", "").strip(),
            "adb_path": settings.get("adb_path", "adb").strip() or "adb",
        }

    def resolve_adb(self):
        configured = self.get_settings()["adb_path"]
        if os.path.isabs(configured):
            if os.path.isfile(configured) and os.access(configured, os.X_OK):
                return configured
            raise ADBError(f"ADB executable is not usable: {configured}")

        resolved = shutil.which(configured)
        if resolved:
            return resolved

        raise ADBError(
            f"ADB executable '{configured}' was not found in PATH. Install android-tools or set an absolute ADB path."
        )

    def get_target(self):
        target = self.get_settings()["target"]
        if not target:
            raise ADBError("No Fire TV ADB target is configured.")
        return target

    def _run(self, args, timeout=3.0):
        try:
            return subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ADBError(f"ADB command timed out: {' '.join(args)}") from exc
        except OSError as exc:
            raise ADBError(str(exc)) from exc

    def _state_is_device(self, adb, target):
        result = self._run([adb, "-s", target, "get-state"], timeout=1.5)
        return result.returncode == 0 and result.stdout.strip() == "device"

    def ensure_connected(self, force=False):
        with self.lock:
            adb = self.resolve_adb()
            target = self.get_target()
            now = time.monotonic()

            if not force and now - self.last_verified < self.verify_ttl:
                return adb, target

            if self._state_is_device(adb, target):
                self.last_verified = now
                return adb, target

            self._run([adb, "connect", target], timeout=4.0)

            if not self._state_is_device(adb, target):
                raise ADBError(f"Could not connect to Fire TV at {target}.")

            self.last_verified = time.monotonic()
            return adb, target

    def _shell(self, shell_args):
        adb, target = self.ensure_connected()
        result = self._run([adb, "-s", target, "shell", *shell_args], timeout=3.0)

        if result.returncode == 0:
            return result.stdout.strip()

        self.last_verified = 0.0
        adb, target = self.ensure_connected(force=True)
        result = self._run([adb, "-s", target, "shell", *shell_args], timeout=3.0)

        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip() or "ADB shell command failed."
            raise ADBError(message)

        return result.stdout.strip()

    def send_key(self, keycode, longpress=False):
        args = ["input", "keyevent"]
        if longpress:
            args.append("--longpress")
        args.append(keycode)
        return self._shell(args)

    def start_component(self, component):
        component = component.strip()
        if not component or "/" not in component:
            raise ADBError("App component must look like package.name/.ActivityName")
        return self._shell(["am", "start", "-n", component])

    def send_text(self, text):
        encoded = text.replace(" ", "%s")
        return self._shell(["input", "text", encoded])

    def submit_key(self, keycode, longpress=False):
        return self.executor.submit(self.send_key, keycode, longpress)

    def submit_component(self, component):
        return self.executor.submit(self.start_component, component)

    def submit_text(self, text):
        return self.executor.submit(self.send_text, text)

    def submit_test(self):
        return self.executor.submit(self.ensure_connected, True)
