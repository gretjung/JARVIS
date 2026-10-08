import customtkinter as ctk
import tkinter as tk

import threading
import subprocess
import platform
import psutil
import ollama
import pyttsx3
import webbrowser
import os
import time
import re
import difflib
import json
import math


# =========================================================
# J.A.R.V.I.S CONFIG
# =========================================================

MODEL = "qwen3:8b"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_DIR = os.path.join(BASE_DIR, "memory")
SKILLS_FILE = os.path.join(MEMORY_DIR, "skills.json")

os.makedirs(MEMORY_DIR, exist_ok=True)


# =========================================================
# COLORS
# =========================================================

BG = "#03060B"
PANEL = "#07101A"
PANEL2 = "#091722"

CYAN = "#00E5FF"
BLUE = "#008CFF"
LIGHT_BLUE = "#8DEBFF"

WHITE = "#E8FBFF"
GRAY = "#718B9A"

GREEN = "#00FF9C"
RED = "#FF3155"
YELLOW = "#FFD43B"


# =========================================================
# WINDOWS APP PATHS
# =========================================================

START_MENU_PATHS = [
    os.path.expandvars(
        r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"
    ),
    os.path.expandvars(
        r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs"
    )
]


# =========================================================
# JARVIS ENGINE
# =========================================================

class JarvisEngine:

    def __init__(self, gui=None):

        self.gui = gui

        # ---------------------------------------------
        # TTS
        # ---------------------------------------------

        self.tts = None

        try:
            self.tts = pyttsx3.init()

            self.tts.setProperty("rate", 175)
            self.tts.setProperty("volume", 1.0)

        except Exception as e:
            print("TTS ERROR:", e)

        # ---------------------------------------------
        # Conversation
        # ---------------------------------------------

        self.messages = [
            {
                "role": "system",
                "content": """
คุณคือ J.A.R.V.I.S ผู้ช่วย AI ประจำเครื่อง Windows

หน้าที่:
- ตอบคำถาม
- ช่วยควบคุมคอมพิวเตอร์ผ่านความสามารถที่ Python อนุญาต
- ตอบภาษาเดียวกับผู้ใช้
- ถ้าผู้ใช้พูดภาษาไทย ให้ตอบภาษาไทย
- ตอบกระชับ
- บุคลิกสุภาพ ฉลาด และมีอารมณ์ขันเล็กน้อย

สำคัญ:
คุณไม่มีสิทธิ์รัน shell, PowerShell หรือ Python code โดยตรง
การควบคุม Windows จะถูกจัดการโดย Python
"""
            }
        ]

        # ---------------------------------------------
        # Learned Skills
        # ---------------------------------------------

        self.skills = self.load_skills()

        # Skill ที่กำลังรอการยืนยัน
        self.pending_skill = None


    # =====================================================
    # SKILL STORAGE
    # =====================================================

    def load_skills(self):

        if not os.path.exists(SKILLS_FILE):

            default = {}

            self.save_skills(default)

            return default

        try:

            with open(
                SKILLS_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

                if isinstance(data, dict):
                    return data

        except Exception as e:

            print("LOAD SKILLS ERROR:", e)

        return {}


    def save_skills(self, skills=None):

        if skills is None:
            skills = self.skills

        try:

            with open(
                SKILLS_FILE,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    skills,
                    f,
                    ensure_ascii=False,
                    indent=2
                )

            return True

        except Exception as e:

            print("SAVE SKILLS ERROR:", e)

            return False


    # =====================================================
    # TTS
    # =====================================================

    def speak(self, text):

        if not self.tts:
            return

        try:

            self.tts.say(text)
            self.tts.runAndWait()

        except Exception as e:

            print("TTS ERROR:", e)


    # =====================================================
    # CLEAN COMMAND
    # =====================================================

    def clean_command(self, text):

        text = text.strip()

        replacements = [
            "hello jarvis",
            "hey jarvis",
            "hi jarvis",
            "ok jarvis",
            "okay jarvis",
            "jarvis",
            "จาวิส",
            "เจวิส",
            "จาร์วิส"
        ]

        lower = text.lower()

        for word in replacements:

            lower = lower.replace(word.lower(), "")

        return lower.strip()


    # =====================================================
    # EXTRACT APP NAME
    # =====================================================

    def extract_app_name(self, text):

        text = self.clean_command(text)

        patterns = [
            r"^เปิด\s*",
            r"^open\s*",
            r"^launch\s*",
            r"^start\s*",
            r"^run\s*",
            r"^โปรแกรม\s*",
            r"^แอป\s*",
            r"^แอพ\s*"
        ]

        result = text

        changed = True

        while changed:

            changed = False

            for pattern in patterns:

                new_result = re.sub(
                    pattern,
                    "",
                    result,
                    flags=re.IGNORECASE
                )

                if new_result != result:

                    result = new_result
                    changed = True

        # remove ending polite words
        result = re.sub(
            r"(ให้หน่อย|หน่อย|ที|ด้วย|please|for me)$",
            "",
            result,
            flags=re.IGNORECASE
        )

        return result.strip()


    # =====================================================
    # START MENU SEARCH
    # =====================================================

    def get_start_menu_apps(self):

        apps = []

        for base in START_MENU_PATHS:

            if not os.path.exists(base):
                continue

            try:

                for root, dirs, files in os.walk(base):

                    for file in files:

                        if not file.lower().endswith(".lnk"):
                            continue

                        full_path = os.path.join(root, file)

                        name = os.path.splitext(file)[0]

                        apps.append({
                            "name": name,
                            "path": full_path,
                            "type": "lnk"
                        })

            except Exception:
                pass

        return apps


    # =====================================================
    # WINDOWS APPS
    # =====================================================

    def get_windows_apps(self):

        apps = []

        try:

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Get-StartApps | ConvertTo-Json -Compress"
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return apps

            data = json.loads(result.stdout)

            if isinstance(data, dict):
                data = [data]

            for item in data:

                name = item.get("Name")
                app_id = item.get("AppID")

                if name and app_id:

                    apps.append({
                        "name": name,
                        "path": app_id,
                        "type": "uwp"
                    })

        except Exception as e:

            print("WINDOWS APP SEARCH ERROR:", e)

        return apps


    # =====================================================
    # ALL APPS
    # =====================================================

    def get_all_apps(self):

        apps = []

        apps.extend(
            self.get_start_menu_apps()
        )

        apps.extend(
            self.get_windows_apps()
        )

        # remove duplicates
        result = {}

        for app in apps:

            key = (
                app["name"].lower(),
                app["path"].lower()
            )

            result[key] = app

        return list(result.values())


    # =====================================================
    # FIND APPLICATION
    # =====================================================

    def find_application(self, query):

        query = query.strip().lower()

        if not query:
            return None

        apps = self.get_all_apps()

        if not apps:
            return None

        # ---------------------------------------------
        # Exact
        # ---------------------------------------------

        for app in apps:

            if app["name"].lower() == query:

                return app

        # ---------------------------------------------
        # Normalized exact
        # ---------------------------------------------

        def normalize(s):

            return re.sub(
                r"[^a-zA-Z0-9ก-๙]+",
                "",
                s.lower()
            )

        nq = normalize(query)

        for app in apps:

            if normalize(app["name"]) == nq:

                return app

        # ---------------------------------------------
        # Query inside app name
        # ---------------------------------------------

        for app in apps:

            name = app["name"].lower()

            if query in name:

                return app

        # ---------------------------------------------
        # App name inside query
        # ---------------------------------------------

        for app in apps:

            name = app["name"].lower()

            if name and name in query:

                return app

        # ---------------------------------------------
        # Fuzzy search
        # ---------------------------------------------

        names = [
            app["name"]
            for app in apps
        ]

        matches = difflib.get_close_matches(
            query,
            names,
            n=1,
            cutoff=0.45
        )

        if matches:

            target = matches[0].lower()

            for app in apps:

                if app["name"].lower() == target:

                    return app

        return None


    # =====================================================
    # OPEN APPLICATION
    # =====================================================

    def open_application(self, query):

        query = query.strip()

        if not query:

            return False, "ผมไม่พบชื่อโปรแกรมครับ"


        # ---------------------------------------------
        # ROBLOX SPECIAL CASE
        # ---------------------------------------------

        if query.lower() == "roblox":

            try:

                os.startfile("roblox-player:")

                return True, "กำลังเปิด Roblox ให้ครับ 🎮"

            except Exception:
                pass

            search_roots = [
                os.path.expandvars(
                    r"%LOCALAPPDATA%\Roblox"
                ),
                os.path.expandvars(
                    r"%PROGRAMFILES%\Roblox"
                ),
                os.path.expandvars(
                    r"%PROGRAMFILES(X86)%\Roblox"
                )
            ]

            for base in search_roots:

                if not os.path.exists(base):
                    continue

                try:

                    for root, dirs, files in os.walk(base):

                        for file in files:

                            if file.lower() == "robloxplayerbeta.exe":

                                path = os.path.join(
                                    root,
                                    file
                                )

                                subprocess.Popen(
                                    [path],
                                    shell=False
                                )

                                return True, "กำลังเปิด Roblox ให้ครับ 🎮"

                except Exception:
                    pass


        # ---------------------------------------------
        # NORMAL WINDOWS APP
        # ---------------------------------------------

        app = self.find_application(query)

        if app:

            try:

                if app["type"] == "lnk":

                    os.startfile(app["path"])

                elif app["type"] == "uwp":

                    subprocess.Popen(
                        [
                            "explorer.exe",
                            "shell:AppsFolder\\" + app["path"]
                        ]
                    )

                return True, (
                    f"กำลังเปิด {app['name']} ให้ครับ"
                )

            except Exception as e:

                print("OPEN APP ERROR:", e)

                return False, (
                    f"พบ {app['name']} แล้ว แต่เปิดไม่ได้ครับ"
                )

        return False, (
            f"ผมหาโปรแกรม '{query}' ไม่พบครับ"
        )


    # =====================================================
    # GOOGLE
    # =====================================================

    def open_google(self):

        webbrowser.open(
            "https://www.google.com"
        )

        return "กำลังเปิด Google ให้ครับ 🌐"


    # =====================================================
    # YOUTUBE
    # =====================================================

    def open_youtube(self):

        webbrowser.open(
            "https://www.youtube.com"
        )

        return "กำลังเปิด YouTube ให้ครับ 🎬"


    # =====================================================
    # SYSTEM SPECS
    # =====================================================

    def get_specs(self):

        cpu = platform.processor()

        ram = psutil.virtual_memory()

        ram_gb = ram.total / (
            1024 ** 3
        )

        ram_percent = ram.percent

        return (
            f"CPU: {cpu}\n"
            f"RAM: {ram_gb:.1f} GB "
            f"ใช้งาน {ram_percent}%\n"
            f"GPU: RTX 4060 8GB"
        )


    # =====================================================
    # CREATE SKILL WITH QWEN
    # =====================================================

    def generate_skill(self, user_text):

        prompt = f"""
คุณคือ Skill Builder ของ J.A.R.V.I.S

ผู้ใช้ต้องการสร้างคำสั่งใหม่:

"{user_text}"

สร้าง JSON เท่านั้น ห้ามมี markdown
ห้ามมีคำอธิบายเพิ่มเติม

รูปแบบ:

{{
  "name": "ชื่อ skill ภาษาอังกฤษสั้นๆ",
  "description": "คำอธิบาย",
  "triggers": [
    "คำสั่งที่ผู้ใช้อาจพูด",
    "อีกคำสั่งหนึ่ง"
  ],
  "actions": [
    {{
      "type": "open_app",
      "value": "ชื่อโปรแกรม"
    }}
  ]
}}

ประเภท action ที่อนุญาตเท่านั้น:

1. open_app
เปิดโปรแกรม Windows

2. open_url
เปิดเว็บไซต์ โดย value ต้องเป็น URL http หรือ https

3. say
ให้ JARVIS พูดข้อความ

4. wait
รอเป็นจำนวนวินาที โดย value ต้องไม่เกิน 10

ห้ามสร้าง action อื่น
ห้ามสร้าง shell
ห้ามสร้าง powershell
ห้ามสร้าง cmd
ห้ามสร้าง python
ห้ามสร้าง execute
ห้ามสร้าง code

ถ้าผู้ใช้ขอสิ่งที่ไม่สามารถสร้างเป็น Skill ได้
ให้ตอบ:

{{
  "error": "ไม่สามารถสร้าง Skill นี้ได้"
}}
"""

        try:

            response = ollama.chat(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": prompt
                    },
                    {
                        "role": "user",
                        "content": user_text
                    }
                ],
                options={
                    "temperature": 0.1
                }
            )

            content = response["message"]["content"].strip()

            # -----------------------------------------
            # Remove markdown fences
            # -----------------------------------------

            content = re.sub(
                r"^```json",
                "",
                content,
                flags=re.IGNORECASE
            )

            content = re.sub(
                r"^```",
                "",
                content
            )

            content = re.sub(
                r"```$",
                "",
                content
            )

            content = content.strip()

            # -----------------------------------------
            # Extract JSON
            # -----------------------------------------

            start = content.find("{")
            end = content.rfind("}")

            if start == -1 or end == -1:

                return None, "Qwen ไม่ได้ส่ง JSON ที่ถูกต้อง"

            content = content[start:end + 1]

            data = json.loads(content)

            # -----------------------------------------
            # Validate
            # -----------------------------------------

            valid, error = self.validate_skill(data)

            if not valid:

                return None, error

            return data, None

        except Exception as e:

            print("SKILL GENERATION ERROR:", e)

            return None, (
                f"สร้าง Skill ไม่สำเร็จ: {e}"
            )


    # =====================================================
    # VALIDATE SKILL
    # =====================================================

    def validate_skill(self, skill):

        if not isinstance(skill, dict):

            return False, "Skill ต้องเป็น JSON object"

        if "error" in skill:

            return False, skill["error"]

        required = [
            "name",
            "description",
            "triggers",
            "actions"
        ]

        for key in required:

            if key not in skill:

                return False, (
                    f"Skill ขาดข้อมูล: {key}"
                )

        if not isinstance(
            skill["triggers"],
            list
        ):

            return False, "triggers ต้องเป็น list"

        if not isinstance(
            skill["actions"],
            list
        ):

            return False, "actions ต้องเป็น list"

        if not skill["actions"]:

            return False, "Skill ต้องมี action อย่างน้อย 1 รายการ"

        allowed = {
            "open_app",
            "open_url",
            "say",
            "wait"
        }

        for action in skill["actions"]:

            if not isinstance(action, dict):

                return False, "รูปแบบ action ไม่ถูกต้อง"

            action_type = action.get("type")

            if action_type not in allowed:

                return False, (
                    f"Action '{action_type}' ไม่ได้รับอนุญาต"
                )

            value = action.get("value")

            if value is None:

                return False, "Action ไม่มี value"

            if action_type == "open_url":

                if not (
                    str(value).startswith("http://")
                    or
                    str(value).startswith("https://")
                ):

                    return False, (
                        "open_url อนุญาตเฉพาะ http/https"
                    )

            if action_type == "wait":

                try:

                    seconds = float(value)

                    if seconds < 0 or seconds > 10:

                        return False, (
                            "wait อนุญาตสูงสุด 10 วินาที"
                        )

                except Exception:

                    return False, (
                        "wait ต้องเป็นตัวเลข"
                    )

        return True, None


    # =====================================================
    # SAVE NEW SKILL
    # =====================================================

    def save_new_skill(self, skill):

        name = skill["name"].strip().lower()

        safe_name = re.sub(
            r"[^a-z0-9ก-๙_-]+",
            "_",
            name
        )

        skill["id"] = safe_name

        self.skills[safe_name] = skill

        return self.save_skills()


    # =====================================================
    # FIND LEARNED SKILL
    # =====================================================

    def find_learned_skill(self, command):

        command_clean = self.clean_command(
            command
        ).lower().strip()

        if not command_clean:
            return None

        # Exact trigger
        for skill in self.skills.values():

            for trigger in skill.get(
                "triggers",
                []
            ):

                trigger_clean = self.clean_command(
                    str(trigger)
                ).lower().strip()

                if command_clean == trigger_clean:

                    return skill

        # Contains trigger
        for skill in self.skills.values():

            for trigger in skill.get(
                "triggers",
                []
            ):

                trigger_clean = self.clean_command(
                    str(trigger)
                ).lower().strip()

                if (
                    trigger_clean
                    and trigger_clean in command_clean
                ):

                    return skill

        return None


    # =====================================================
    # EXECUTE SKILL
    # =====================================================

    def execute_skill(self, skill):

        name = skill.get(
            "name",
            "Skill"
        )

        actions = skill.get(
            "actions",
            []
        )

        self.gui_add_message(
            "JARVIS",
            f"กำลังใช้ Skill: {name}"
        )

        for action in actions:

            action_type = action.get("type")
            value = action.get("value")

            # -----------------------------------------
            # OPEN APP
            # -----------------------------------------

            if action_type == "open_app":

                success, message = self.open_application(
                    str(value)
                )

                self.gui_add_message(
                    "JARVIS",
                    message
                )

                if not success:

                    return message

            # -----------------------------------------
            # OPEN URL
            # -----------------------------------------

            elif action_type == "open_url":

                url = str(value)

                if (
                    url.startswith("http://")
                    or
                    url.startswith("https://")
                ):

                    webbrowser.open(url)

                    self.gui_add_message(
                        "JARVIS",
                        f"กำลังเปิด {url}"
                    )

            # -----------------------------------------
            # SAY
            # -----------------------------------------

            elif action_type == "say":

                text = str(value)

                self.gui_add_message(
                    "JARVIS",
                    text
                )

                threading.Thread(
                    target=self.speak,
                    args=(text,),
                    daemon=True
                ).start()

            # -----------------------------------------
            # WAIT
            # -----------------------------------------

            elif action_type == "wait":

                try:

                    seconds = min(
                        float(value),
                        10
                    )

                    time.sleep(seconds)

                except Exception:
                    pass

        return (
            f"ทำตาม Skill '{name}' เรียบร้อยแล้วครับ"
        )


    # =====================================================
    # SHOW SKILLS
    # =====================================================

    def list_skills(self):

        if not self.skills:

            return "ตอนนี้ยังไม่มี Skill ที่เรียนรู้เพิ่มเติมครับ"

        lines = [
            "Skill ที่ผมเรียนรู้ไว้:"
        ]

        for skill in self.skills.values():

            name = skill.get(
                "name",
                "Unknown"
            )

            desc = skill.get(
                "description",
                ""
            )

            lines.append(
                f"• {name} — {desc}"
            )

        return "\n".join(lines)


    # =====================================================
    # DELETE SKILL
    # =====================================================

    def delete_skill(self, text):

        query = text.strip().lower()

        # remove command words
        query = re.sub(
            r"^(ลบ|delete|remove)\s*(คำสั่ง|skill)?\s*",
            "",
            query,
            flags=re.IGNORECASE
        )

        if not query:

            return "บอกชื่อ Skill ที่ต้องการลบด้วยครับ"

        for key, skill in list(
            self.skills.items()
        ):

            name = skill.get(
                "name",
                ""
            ).lower()

            if (
                query == key.lower()
                or query in name
                or name in query
            ):

                del self.skills[key]

                self.save_skills()

                return (
                    f"ลบ Skill '{name}' เรียบร้อยแล้วครับ"
                )

        return (
            f"ผมหา Skill '{query}' ไม่พบครับ"
        )


    # =====================================================
    # HANDLE SKILL CREATION
    # =====================================================

    def handle_learning(self, command):

        # ---------------------------------------------
        # Confirm
        # ---------------------------------------------

        if self.pending_skill:

            lower = command.lower().strip()

            yes_words = [
                "yes",
                "y",
                "ใช่",
                "ยืนยัน",
                "ตกลง",
                "เอาเลย",
                "บันทึก",
                "สร้างเลย"
            ]

            no_words = [
                "no",
                "n",
                "ไม่",
                "ยกเลิก",
                "cancel"
            ]

            if lower in yes_words:

                skill = self.pending_skill

                if self.save_new_skill(skill):

                    self.pending_skill = None

                    return (
                        f"สร้าง Skill '{skill['name']}' "
                        f"และบันทึกเรียบร้อยแล้วครับ"
                    )

                return "ผมบันทึก Skill ไม่สำเร็จครับ"

            if lower in no_words:

                self.pending_skill = None

                return (
                    "ยกเลิกการสร้าง Skill เรียบร้อยแล้วครับ"
                )

            return (
                "ผมกำลังรอการยืนยันครับ\n"
                "พิมพ์ 'ยืนยัน' เพื่อสร้าง "
                "หรือ 'ยกเลิก' เพื่อยกเลิก"
            )

        # ---------------------------------------------
        # List skills
        # ---------------------------------------------

        lower = command.lower().strip()

        if (
            "ทำอะไรได้บ้าง" in lower
            or
            "มีคำสั่งอะไร" in lower
            or
            "skill มีอะไร" in lower
            or
            "รายการ skill" in lower
            or
            "list skill" in lower
        ):

            return self.list_skills()

        # ---------------------------------------------
        # Delete
        # ---------------------------------------------

        if (
            lower.startswith("ลบคำสั่ง")
            or
            lower.startswith("ลบ skill")
            or
            lower.startswith("delete skill")
            or
            lower.startswith("remove skill")
        ):

            return self.delete_skill(
                command
            )

        # ---------------------------------------------
        # Create
        # ---------------------------------------------

        learning_patterns = [
            "เพิ่มคำสั่ง",
            "สร้างคำสั่ง",
            "เรียนรู้คำสั่ง",
            "จำคำสั่ง",
            "สอนคำสั่ง",
            "เพิ่ม skill",
            "สร้าง skill",
            "learn command",
            "create command"
        ]

        is_learning = any(
            p in lower
            for p in learning_patterns
        )

        if not is_learning:

            return None

        self.gui_add_message(
            "JARVIS",
            "กำลังให้ Qwen ออกแบบ Skill ให้ครับ..."
        )

        skill, error = self.generate_skill(
            command
        )

        if error:

            return error

        self.pending_skill = skill

        # ---------------------------------------------
        # Display preview
        # ---------------------------------------------

        preview = (
            "ผมสร้าง Skill นี้ให้แล้วครับ\n\n"
            f"ชื่อ: {skill['name']}\n"
            f"รายละเอียด: {skill['description']}\n\n"
            "คำสั่งที่ใช้เรียก:\n"
        )

        for trigger in skill["triggers"]:

            preview += (
                f"• {trigger}\n"
            )

        preview += "\nสิ่งที่จะทำ:\n"

        for action in skill["actions"]:

            action_type = action["type"]
            value = action["value"]

            preview += (
                f"• {action_type}: {value}\n"
            )

        preview += (
            "\nต้องการบันทึก Skill นี้ไหม?\n"
            "พิมพ์ 'ยืนยัน' หรือ 'ยกเลิก'"
        )

        return preview


    # =====================================================
    # GUI MESSAGE
    # =====================================================

    def gui_add_message(
        self,
        sender,
        text
    ):

        if self.gui:

            self.gui.after(
                0,
                lambda: self.gui.add_message(
                    sender,
                    text
                )
            )


    # =====================================================
    # PROCESS COMMAND
    # =====================================================

    def process_command(self, original):

        command = self.clean_command(
            original
        )

        if not command:

            return "มีอะไรให้ผมช่วยครับ?"


        # =================================================
        # LEARNING SYSTEM
        # =================================================

        learning_result = self.handle_learning(
            command
        )

        if learning_result is not None:

            return learning_result


        # =================================================
        # RUN LEARNED SKILL
        # =================================================

        skill = self.find_learned_skill(
            command
        )

        if skill:

            return self.execute_skill(
                skill
            )


        # =================================================
        # GOOGLE
        # =================================================

        if (
            "google" in command.lower()
            and
            (
                "เปิด" in command.lower()
                or
                "open" in command.lower()
            )
        ):

            return self.open_google()


        # =================================================
        # YOUTUBE
        # =================================================

        if (
            "youtube" in command.lower()
            and
            (
                "เปิด" in command.lower()
                or
                "open" in command.lower()
            )
        ):

            return self.open_youtube()


        # =================================================
        # SYSTEM SPECS
        # =================================================

        if (
            "สเปค" in command.lower()
            or
            "spec" in command.lower()
            or
            "สเปก" in command.lower()
        ):

            return self.get_specs()


        # =================================================
        # TIME
        # =================================================

        if (
            "เวลา" in command.lower()
            or
            "กี่โมง" in command.lower()
            or
            "time" in command.lower()
        ):

            return (
                "ตอนนี้เวลา "
                + time.strftime("%H:%M:%S")
                + " ครับ"
            )


        # =================================================
        # OPEN APP
        # =================================================

        open_words = [
            "เปิด",
            "open",
            "launch",
            "start",
            "run"
        ]

        if any(
            word in command.lower()
            for word in open_words
        ):

            app_name = self.extract_app_name(
                command
            )

            if app_name:

                success, message = (
                    self.open_application(
                        app_name
                    )
                )

                # IMPORTANT:
                # Never send failed app command
                # to Qwen.

                return message


        # =================================================
        # QWEN GENERAL CHAT
        # =================================================

        try:

            self.messages.append({
                "role": "user",
                "content": original
            })

            response = ollama.chat(
                model=MODEL,
                messages=self.messages
            )

            answer = response[
                "message"
            ][
                "content"
            ].strip()

            self.messages.append({
                "role": "assistant",
                "content": answer
            })

            # keep conversation small
            if len(self.messages) > 12:

                self.messages = (
                    [self.messages[0]]
                    + self.messages[-10:]
                )

            return answer

        except Exception as e:

            print("QWEN ERROR:", e)

            return (
                "ขออภัยครับ ไม่สามารถเชื่อมต่อ "
                "Qwen ได้ในขณะนี้"
            )


# =========================================================
# JARVIS HUD
# =========================================================

class JarvisHUD(ctk.CTk):

    def __init__(self):

        super().__init__()

        self.title(
            "J.A.R.V.I.S — AI COMMAND SYSTEM"
        )

        self.geometry(
            "1400x850"
        )

        self.minsize(
            1100,
            700
        )

        self.configure(
            fg_color=BG
        )

        self.engine = JarvisEngine(
            self
        )

        self.ring_angle = 0

        self.build_ui()

        self.animate_hud()

        self.update_stats()


    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):

        # ---------------------------------------------
        # HEADER
        # ---------------------------------------------

        header = ctk.CTkFrame(
            self,
            fg_color=BG
        )

        header.pack(
            fill="x",
            padx=30,
            pady=(20, 5)
        )

        title = ctk.CTkLabel(
            header,
            text="J.A.R.V.I.S",
            font=(
                "Consolas",
                28,
                "bold"
            ),
            text_color=CYAN
        )

        title.pack(
            side="left"
        )

        self.status_label = ctk.CTkLabel(
            header,
            text="● SYSTEM ONLINE",
            font=(
                "Consolas",
                14,
                "bold"
            ),
            text_color=GREEN
        )

        self.status_label.pack(
            side="right"
        )


        # ---------------------------------------------
        # MAIN
        # ---------------------------------------------

        main = ctk.CTkFrame(
            self,
            fg_color=BG
        )

        main.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=15
        )


        # =============================================
        # LEFT HUD
        # =============================================

        left = ctk.CTkFrame(
            main,
            width=410,
            fg_color=PANEL,
            corner_radius=18,
            border_width=1,
            border_color="#10384A"
        )

        left.pack(
            side="left",
            fill="y",
            padx=(0, 15)
        )

        left.pack_propagate(
            False
        )


        self.canvas = tk.Canvas(
            left,
            width=380,
            height=430,
            bg=PANEL,
            highlightthickness=0
        )

        self.canvas.pack(
            pady=20
        )


        # =============================================
        # SYSTEM INFO
        # =============================================

        self.cpu_label = ctk.CTkLabel(
            left,
            text="CPU: --",
            font=(
                "Consolas",
                13
            ),
            text_color=LIGHT_BLUE
        )

        self.cpu_label.pack(
            anchor="w",
            padx=25,
            pady=4
        )


        self.ram_label = ctk.CTkLabel(
            left,
            text="RAM: --",
            font=(
                "Consolas",
                13
            ),
            text_color=LIGHT_BLUE
        )

        self.ram_label.pack(
            anchor="w",
            padx=25,
            pady=4
        )


        self.gpu_label = ctk.CTkLabel(
            left,
            text="GPU: RTX 4060 8GB",
            font=(
                "Consolas",
                13
            ),
            text_color=LIGHT_BLUE
        )

        self.gpu_label.pack(
            anchor="w",
            padx=25,
            pady=4
        )


        self.model_label = ctk.CTkLabel(
            left,
            text="AI MODEL: QWEN3 8B",
            font=(
                "Consolas",
                13,
                "bold"
            ),
            text_color=CYAN
        )

        self.model_label.pack(
            anchor="w",
            padx=25,
            pady=4
        )


        self.skill_label = ctk.CTkLabel(
            left,
            text="LEARNED SKILLS: 0",
            font=(
                "Consolas",
                13,
                "bold"
            ),
            text_color=GREEN
        )

        self.skill_label.pack(
            anchor="w",
            padx=25,
            pady=4
        )


        # =============================================
        # RIGHT
        # =============================================

        right = ctk.CTkFrame(
            main,
            fg_color=PANEL,
            corner_radius=18,
            border_width=1,
            border_color="#10384A"
        )

        right.pack(
            side="left",
            fill="both",
            expand=True
        )


        # ---------------------------------------------
        # CHAT HEADER
        # ---------------------------------------------

        chat_header = ctk.CTkLabel(
            right,
            text="COMMUNICATION CHANNEL",
            font=(
                "Consolas",
                14,
                "bold"
            ),
            text_color=CYAN
        )

        chat_header.pack(
            anchor="w",
            padx=20,
            pady=(15, 5)
        )


        # ---------------------------------------------
        # CHAT
        # ---------------------------------------------

        self.chat = ctk.CTkTextbox(
            right,
            fg_color="#040A10",
            text_color=WHITE,
            font=(
                "Consolas",
                13
            ),
            corner_radius=12
        )

        self.chat.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=10
        )

        self.chat.configure(
            state="disabled"
        )


        # ---------------------------------------------
        # INPUT
        # ---------------------------------------------

        input_frame = ctk.CTkFrame(
            right,
            fg_color="transparent"
        )

        input_frame.pack(
            fill="x",
            padx=15,
            pady=(0, 15)
        )


        self.entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="พิมพ์คำสั่งให้ JARVIS...",
            height=45,
            font=(
                "Consolas",
                13
            ),
            fg_color="#040A10",
            border_color="#15546A"
        )

        self.entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 10)
        )

        self.entry.bind(
            "<Return>",
            lambda e: self.send_command()
        )


        self.send_button = ctk.CTkButton(
            input_frame,
            text="SEND",
            width=90,
            height=45,
            fg_color="#06394B",
            hover_color="#075A75",
            border_width=1,
            border_color=CYAN,
            text_color=WHITE,
            command=self.send_command
        )

        self.send_button.pack(
            side="right"
        )


        # ---------------------------------------------
        # VOICE
        # ---------------------------------------------

        voice = ctk.CTkButton(
            right,
            text="🎙  VOICE",
            height=38,
            fg_color="#071E29",
            hover_color="#0A3444",
            border_width=1,
            border_color="#15546A",
            text_color=LIGHT_BLUE,
            command=self.voice_placeholder
        )

        voice.pack(
            padx=15,
            pady=(0, 15)
        )


        self.add_message(
            "JARVIS",
            "ระบบพร้อมใช้งานครับ\n"
            "ผมสามารถเรียนรู้ Skill ใหม่จากคุณได้แล้ว"
        )


    # =====================================================
    # CHAT MESSAGE
    # =====================================================

    def add_message(
        self,
        sender,
        text
    ):

        self.chat.configure(
            state="normal"
        )

        self.chat.insert(
            "end",
            f"\n{sender}\n",
            "sender"
        )

        self.chat.insert(
            "end",
            f"{text}\n"
        )

        self.chat.see(
            "end"
        )

        self.chat.configure(
            state="disabled"
        )


    # =====================================================
    # SEND
    # =====================================================

    def send_command(self):

        command = self.entry.get().strip()

        if not command:
            return

        self.entry.delete(
            0,
            "end"
        )

        self.add_message(
            "YOU",
            command
        )

        self.status_label.configure(
            text="● THINKING",
            text_color=YELLOW
        )

        self.send_button.configure(
            state="disabled"
        )

        threading.Thread(
            target=self.process_background,
            args=(command,),
            daemon=True
        ).start()


    # =====================================================
    # BACKGROUND
    # =====================================================

    def process_background(
        self,
        command
    ):

        answer = self.engine.process_command(
            command
        )

        self.after(
            0,
            lambda: self.finish_response(
                answer
            )
        )


    # =====================================================
    # RESPONSE
    # =====================================================

    def finish_response(
        self,
        answer
    ):

        self.add_message(
            "JARVIS",
            answer
        )

        self.status_label.configure(
            text="● SPEAKING",
            text_color=CYAN
        )

        threading.Thread(
            target=self.speak_background,
            args=(answer,),
            daemon=True
        ).start()


    # =====================================================
    # SPEAK
    # =====================================================

    def speak_background(
        self,
        text
    ):

        self.engine.speak(
            text
        )

        self.after(
            0,
            lambda: self.status_label.configure(
                text="● SYSTEM ONLINE",
                text_color=GREEN
            )
        )

        self.after(
            0,
            lambda: self.send_button.configure(
                state="normal"
            )
        )


    # =====================================================
    # VOICE PLACEHOLDER
    # =====================================================

    def voice_placeholder(self):

        self.add_message(
            "JARVIS",
            "ระบบ Voice ยังรอ PyAudio ครับ\n"
            "ตอนนี้ใช้การพิมพ์คำสั่งได้ก่อน"
        )


    # =====================================================
    # HUD ANIMATION
    # =====================================================

    def animate_hud(self):

        self.canvas.delete(
            "all"
        )

        cx = 190
        cy = 210

        # ---------------------------------------------
        # Outer circles
        # ---------------------------------------------

        self.canvas.create_oval(
            40,
            60,
            340,
            360,
            outline="#07384B",
            width=2
        )

        self.canvas.create_oval(
            65,
            85,
            315,
            335,
            outline="#07526B",
            width=2
        )

        self.canvas.create_oval(
            95,
            115,
            285,
            305,
            outline="#0A6C89",
            width=2
        )

        # ---------------------------------------------
        # Rotating arc
        # ---------------------------------------------

        self.ring_angle = (
            self.ring_angle + 4
        ) % 360

        self.canvas.create_arc(
            45,
            65,
            335,
            355,
            start=self.ring_angle,
            extent=90,
            outline=CYAN,
            width=4
        )

        self.canvas.create_arc(
            70,
            90,
            310,
            330,
            start=-self.ring_angle,
            extent=75,
            outline=BLUE,
            width=3
        )

        self.canvas.create_arc(
            100,
            120,
            280,
            300,
            start=self.ring_angle * 2,
            extent=50,
            outline=LIGHT_BLUE,
            width=2
        )

        # ---------------------------------------------
        # Tick marks
        # ---------------------------------------------

        for i in range(0, 360, 15):

            angle = math.radians(
                i + self.ring_angle
            )

            x1 = cx + 145 * math.cos(angle)
            y1 = cy + 145 * math.sin(angle)

            x2 = cx + 155 * math.cos(angle)
            y2 = cy + 155 * math.sin(angle)

            self.canvas.create_line(
                x1,
                y1,
                x2,
                y2,
                fill="#11617A",
                width=2
            )

        # ---------------------------------------------
        # Core
        # ---------------------------------------------

        pulse = (
            math.sin(
                time.time() * 4
            ) + 1
        ) / 2

        radius = (
            50
            + pulse * 5
        )

        self.canvas.create_oval(
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
            outline=CYAN,
            width=3
        )

        self.canvas.create_oval(
            cx - 35,
            cy - 35,
            cx + 35,
            cy + 35,
            fill="#031923",
            outline=LIGHT_BLUE,
            width=2
        )

        self.canvas.create_oval(
            cx - 18,
            cy - 18,
            cx + 18,
            cy + 18,
            fill=CYAN,
            outline=WHITE,
            width=2
        )

        self.canvas.create_text(
            cx,
            cy + 80,
            text="J.A.R.V.I.S",
            fill=CYAN,
            font=(
                "Consolas",
                15,
                "bold"
            )
        )

        self.canvas.create_text(
            cx,
            cy + 105,
            text="AI COMMAND CORE",
            fill=GRAY,
            font=(
                "Consolas",
                9
            )
        )

        self.after(
            40,
            self.animate_hud
        )


    # =====================================================
    # SYSTEM STATS
    # =====================================================

    def update_stats(self):

        try:

            cpu = psutil.cpu_percent(
                interval=None
            )

            ram = psutil.virtual_memory()

            self.cpu_label.configure(
                text=f"CPU LOAD: {cpu:.0f}%"
            )

            self.ram_label.configure(
                text=(
                    f"RAM LOAD: "
                    f"{ram.percent:.0f}%"
                )
            )

            self.skill_label.configure(
                text=(
                    f"LEARNED SKILLS: "
                    f"{len(self.engine.skills)}"
                )
            )

        except Exception:
            pass

        self.after(
            1500,
            self.update_stats
        )


# =========================================================
# START JARVIS
# =========================================================

if __name__ == "__main__":

    ctk.set_appearance_mode(
        "dark"
    )

    ctk.set_default_color_theme(
        "blue"
    )

    app = JarvisHUD()

    app.mainloop()