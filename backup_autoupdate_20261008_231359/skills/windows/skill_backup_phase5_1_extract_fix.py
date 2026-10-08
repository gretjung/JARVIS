# JARVIS WINDOWS SKILL v3.2
# Robust application launcher

import os
from pathlib import Path
import subprocess
import difflib


class WindowsSkill:

    name = "Windows"
    enabled = True

    ALIASES = {
        "?????????????": "Visual Studio Code",
        "????????": "Steam",
        "?????????": "Paint",
        "????????????": "Spotify",
        "?????????? ????": "Google Chrome",
        "??????????????": "Google Chrome",
        "โครม": "Google Chrome",
        "กูเกิลโครม": "Google Chrome",
        "กูเกิล โครม": "Google Chrome",

        "ดิสคอร์ด": "Discord",
        "ดิสคอด": "Discord",
        "ดิสคอท": "Discord",

        "สตรีม": "Steam",
        "สตีม": "Steam",

        "วีเอสโค้ด": "Visual Studio Code",
        "วีเอสโค๊ด": "Visual Studio Code",
        "วีเอส โค้ด": "Visual Studio Code",

        "สปอติฟาย": "Spotify",
        "สปอติไฟ": "Spotify",

        "โอ บี เอส": "OBS",
        "โอเบส": "OBS",

        "โฟโต้ช็อป": "Photoshop",
        "โฟโตช็อป": "Photoshop",
        "โฟโต้ ช็อป": "Photoshop",

        "เอดจ์": "Microsoft Edge",
        "ไมโครซอฟท์เอดจ์": "Microsoft Edge",

        "เทเลแกรม": "Telegram",
        "ไลน์": "LINE",

        "โน้ตแพด": "Notepad",
        "โน๊ตแพด": "Notepad",

        "เครื่องคิดเลข": "Calculator",

        "เพนท์": "Paint",
        "เพนต์": "Paint",

        "ไฟล์เอ็กซ์พลอเรอร์": "File Explorer",
        "ไฟล์ เอ็กซ์พลอเรอร์": "File Explorer",
    }

    SPECIAL = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "paint": "mspaint.exe",
        "file explorer": "explorer.exe",
    }

    DIRECT_PATHS = {
        "google chrome": [
            os.path.expandvars(
                r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"
            ),
            os.path.expandvars(
                r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
            ),
            os.path.expandvars(
                r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
            ),
        ],

        "discord": [],

        "steam": [
            r"C:\Program Files (x86)\Steam\steam.exe",
            r"C:\Program Files\Steam\steam.exe",
        ],

        "visual studio code": [
            os.path.expandvars(
                r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"
            ),
            os.path.expandvars(
                r"%ProgramFiles%\Microsoft VS Code\Code.exe"
            ),
        ],

        "spotify": [
            os.path.expandvars(
                r"%APPDATA%\Spotify\Spotify.exe"
            ),
        ],

        "microsoft edge": [
            os.path.expandvars(
                r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
            ),
            os.path.expandvars(
                r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
            ),
        ],

        "photoshop": [
            os.path.expandvars(
                r"%ProgramFiles%\Adobe\Adobe Photoshop 2026\Photoshop.exe"
            ),
            os.path.expandvars(
                r"%ProgramFiles%\Adobe\Adobe Photoshop 2025\Photoshop.exe"
            ),
        ],
    }

    def normalize_command(self, text):

        if not text:
            return ""

        text = str(text).strip()

        # Natural Thai polite prefixes.
        prefixes = [
            "?????????",
            "??????",
            "????",
            "?????",
            "?????",
            "????",
        ]

        changed = True

        while changed:

            changed = False

            for prefix in prefixes:

                if text.startswith(prefix):

                    text = text[len(prefix):].strip()
                    changed = True
                    break

        # Natural Thai polite endings.
        endings = [
            "????????",
            "?????????",
            "????????",
            "??????",
            "?????",
            "????????",
            "???????",
            "????",
            "???",
            "??",
            "??????",
            "????",
        ]

        changed = True

        while changed:

            changed = False

            for ending in endings:

                if text.endswith(ending):

                    text = text[:-len(ending)].strip()
                    changed = True
                    break

        return text


    def can_handle(self, text):

        if not text:
            return False

        text = text.strip().lower()

        prefixes = (
            "เปิด ",
            "เปิด",
            "open ",
            "launch ",
            "start ",
        )

        return text.startswith(prefixes)

    def _extract_app_name(self, text):

        text = self.normalize_command(text)

        text = text.strip()

        prefixes = [
            "เปิด ",
            "เปิด",
            "open ",
            "launch ",
            "start ",
        ]

        lower = text.lower()

        for prefix in prefixes:
            if lower.startswith(prefix.lower()):
                return text[len(prefix):].strip()

        return text

    def _normalize_name(self, name):

        name = name.strip().lower()

        if name in self.ALIASES:
            return self.ALIASES[name]

        return name

    def get_start_apps(self):

        try:

            command = [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Get-StartApps | "
                "Select-Object Name,AppID | "
                "ConvertTo-Json -Compress"
            ]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return []

            import json

            data = json.loads(result.stdout)

            if isinstance(data, dict):
                data = [data]

            return data

        except Exception as e:

            print(
                "[JARVIS WINDOWS] "
                f"StartApps error: {e}"
            )

            return []

    def find_start_app(self, target):

        apps = self.get_start_apps()

        if not apps:
            return None

        target = target.lower().strip()

        # Exact
        for app in apps:

            name = str(
                app.get("Name", "")
            ).strip()

            if name.lower() == target:
                return app

        # Contains
        for app in apps:

            name = str(
                app.get("Name", "")
            ).strip()

            if target in name.lower():
                return app

        # Fuzzy
        best = None
        best_score = 0

        for app in apps:

            name = str(
                app.get("Name", "")
            ).strip()

            score = difflib.SequenceMatcher(
                None,
                target,
                name.lower()
            ).ratio()

            if score > best_score:

                best_score = score
                best = app

        if best and best_score >= 0.55:
            return best

        return None

    def launch_start_app(self, app):

        try:

            app_id = app.get("AppID", "")
            name = app.get("Name", "")

            if not app_id:
                return False

            subprocess.Popen(
                [
                    "explorer.exe",
                    f"shell:AppsFolder\\{app_id}"
                ]
            )

            print(
                "[JARVIS WINDOWS] "
                f"Start Menu App launched: {name}"
            )

            return True

        except Exception as e:

            print(
                "[JARVIS WINDOWS] "
                f"Start Menu launch error: {e}"
            )

            return False

    def launch_discord(self):

        discord_root = Path(
            os.path.expandvars(
                r"%LOCALAPPDATA%\Discord"
            )
        )

        if not discord_root.exists():

            print(
                "[JARVIS WINDOWS] "
                "Discord folder not found"
            )

            return False

        versions = sorted(
            discord_root.glob(
                "app-*/Discord.exe"
            ),
            reverse=True
        )

        if not versions:

            print(
                "[JARVIS WINDOWS] "
                "Discord.exe not found"
            )

            return False

        discord_exe = versions[0]

        try:

            subprocess.Popen(
                [str(discord_exe)],
                cwd=str(discord_exe.parent)
            )

            print(
                "[JARVIS WINDOWS] "
                f"Discord EXE launched: {discord_exe}"
            )

            return True

        except Exception as e:

            print(
                "[JARVIS WINDOWS] "
                f"Discord launch error: {e}"
            )

            return False


    def launch_direct(self, target):

        key = target.lower().strip()

        # Discord uses the real versioned Discord.exe.
        if key == "discord":

            return self.launch_discord()

        # Special Windows programs
        if key in self.SPECIAL:

            exe = self.SPECIAL[key]

            try:

                subprocess.Popen(
                    [exe],
                    shell=False
                )

                print(
                    "[JARVIS WINDOWS] "
                    f"Direct launched: {exe}"
                )

                return True

            except FileNotFoundError:
                pass

            except Exception as e:

                print(
                    "[JARVIS WINDOWS] "
                    f"Direct launch error: {e}"
                )

        # Known direct paths
        paths = self.DIRECT_PATHS.get(key, [])

        for path in paths:

            if os.path.isfile(path):

                try:

                    subprocess.Popen(
                        [path],
                        shell=False
                    )

                    print(
                        "[JARVIS WINDOWS] "
                        f"Direct path launched: {path}"
                    )

                    return True

                except Exception as e:

                    print(
                        "[JARVIS WINDOWS] "
                        f"Path launch error: {e}"
                    )

        # PATH lookup
        try:

            import shutil

            candidates = [
                target,
                target + ".exe",
            ]

            for candidate in candidates:

                found = shutil.which(candidate)

                if found:

                    subprocess.Popen(
                        [found],
                        shell=False
                    )

                    print(
                        "[JARVIS WINDOWS] "
                        f"PATH launched: {found}"
                    )

                    return True

        except Exception as e:

            print(
                "[JARVIS WINDOWS] "
                f"PATH error: {e}"
            )

        return False

    def execute(self, text):

        app_name = self._extract_app_name(text)

        target = self._normalize_name(app_name)

        print(
            "[JARVIS WINDOWS] "
            f"Target: {target}"
        )

        # Try direct executable first
        if self.launch_direct(target):
            return f"กำลังเปิด {target} ครับ"

        # Try Start Menu
        app = self.find_start_app(target)

        if app:

            if self.launch_start_app(app):
                return (
                    f"กำลังเปิด "
                    f"{app.get('Name', target)} ครับ"
                )

        print(
            "[JARVIS WINDOWS] "
            f"Application not found: {target}"
        )

        return (
            f"ไม่พบโปรแกรม {target} "
            "ในเครื่องครับ"
        )

