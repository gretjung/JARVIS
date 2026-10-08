# -*- coding: utf-8 -*-

"""
JARVIS AI AGENT
Version 2.0.0

เชื่อม:
- JARVIS Identity
- Ollama / Qwen
- Voice
- Windows Tools
- Image Generation
"""

import os
import re
import subprocess
import requests

from core.identity import (
    JARVIS_NAME,
    JARVIS_VERSION,
    get_system_prompt,
    get_response,
    get_state,
)

try:
    from tools.comfyui import (
        enable_image_mode,
        disable_image_mode,
        image_mode_status,
        generate_image,
    )

from core.visual_core import visual_core
except Exception:
    enable_image_mode = None
    disable_image_mode = None
    image_mode_status = None
    generate_image = None


# ============================================================
# CONFIGURATION
# ============================================================

OLLAMA_URL = "http://127.0.0.1:11434"

MODEL = "qwen3:8b"

REQUEST_TIMEOUT = 180


# ============================================================
# JARVIS AGENT
# ============================================================

class Agent:

    def __init__(self, voice=None):

        self.voice = voice

        self.name = JARVIS_NAME

        self.version = JARVIS_VERSION

        self.model = MODEL

        self.conversation = []

        self.image_mode = False

        print(
            f"[JARVIS AGENT] {self.name} "
            f"v{self.version} initialized."
        )

        print(
            f"[JARVIS AGENT] Model: {self.model}"
        )


    # ========================================================
    # MAIN HANDLER
    # ========================================================

    def handle(self, text):

        text = str(text).strip()

        if not text:

            return get_response("unknown")

        print(
            f"[JARVIS] COMMAND: {text}"
        )

        # ----------------------------------------------------
        # VOICE
        # ----------------------------------------------------

        result = self.handle_voice_command(
            text
        )

        if result is not None:

            return result

        # ----------------------------------------------------
        # IMAGE MODE
        # ----------------------------------------------------

        result = self.handle_image_mode_command(
            text
        )

        if result is not None:

            return result

        # ----------------------------------------------------
        # IMAGE GENERATION
        # ----------------------------------------------------

        if self.is_image_command(text):

            return self.handle_image_generation(
                text
            )

        # ----------------------------------------------------
        # WINDOWS COMMANDS
        # ----------------------------------------------------

        result = self.handle_windows_command(
            text
        )

        if result is not None:

            return result

        # ----------------------------------------------------
        # SYSTEM STATUS
        # ----------------------------------------------------

        result = self.handle_system_command(
            text
        )

        if result is not None:

            return result

        # ----------------------------------------------------
        # AI
        # ----------------------------------------------------

        return self.ask_ai(
            text
        )


    # ========================================================
    # VOICE COMMANDS
    # ========================================================

    def handle_voice_command(self, text):

        lower = text.lower()

        # ----------------------------------------------------
        # ENABLE
        # ----------------------------------------------------

        enable_commands = [
            "เปิดเสียง",
            "เปิดระบบเสียง",
            "เสียงเปิด",
            "เปิด voice",
            "enable voice",
        ]

        if any(
            command in lower
            for command in enable_commands
        ):

            if self.voice is not None:

                try:

                    self.voice.enable()

                    return get_response(
                        "voice_enabled"
                    )

                except Exception as e:

                    return (
                        f"เปิดระบบเสียงไม่สำเร็จครับ: {e}"
                    )

            return "ระบบเสียงยังไม่พร้อมใช้งานครับ"

        # ----------------------------------------------------
        # DISABLE
        # ----------------------------------------------------

        disable_commands = [
            "ปิดเสียง",
            "ปิดระบบเสียง",
            "เสียงปิด",
            "ปิด voice",
            "disable voice",
        ]

        if any(
            command in lower
            for command in disable_commands
        ):

            if self.voice is not None:

                try:

                    self.voice.disable()

                    return get_response(
                        "voice_disabled"
                    )

                except Exception as e:

                    return (
                        f"ปิดระบบเสียงไม่สำเร็จครับ: {e}"
                    )

            return "ระบบเสียงยังไม่พร้อมใช้งานครับ"

        # ----------------------------------------------------
        # STOP
        # ----------------------------------------------------

        stop_commands = [
            "หยุดเสียง",
            "หยุดพูด",
            "หยุดการพูด",
            "stop voice",
            "stop speaking",
        ]

        if any(
            command in lower
            for command in stop_commands
        ):

            if self.voice is not None:

                try:

                    self.voice.stop()

                    return "หยุดเสียงแล้วครับ"

                except Exception as e:

                    return (
                        f"หยุดเสียงไม่สำเร็จครับ: {e}"
                    )

            return "ไม่มีระบบเสียงที่กำลังทำงานครับ"

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        status_commands = [
            "สถานะเสียง",
            "เช็คเสียง",
            "เช็กเสียง",
            "voice status",
        ]

        if any(
            command in lower
            for command in status_commands
        ):

            if self.voice is not None:

                try:

                    if hasattr(
                        self.voice,
                        "status"
                    ):

                        return self.voice.status()

                    if hasattr(
                        self.voice,
                        "voice_status"
                    ):

                        return self.voice.voice_status()

                except Exception:
                    pass

            return "VOICE: OFFLINE"

        # ----------------------------------------------------
        # TEST
        # ----------------------------------------------------

        test_commands = [
            "ทดสอบเสียง",
            "ทดสอบระบบเสียง",
            "test voice",
        ]

        if any(
            command in lower
            for command in test_commands
        ):

            if self.voice is not None:

                try:

                    self.voice.test_voice()

                    return (
                        "กำลังทดสอบระบบเสียงครับ"
                    )

                except Exception as e:

                    return (
                        f"ทดสอบเสียงไม่สำเร็จครับ: {e}"
                    )

            return "ระบบเสียงยังไม่พร้อมครับ"

        return None


    # ========================================================
    # IMAGE MODE
    # ========================================================

    def handle_image_mode_command(self, text):

        lower = text.lower()

        # ----------------------------------------------------
        # OPEN
        # ----------------------------------------------------

        open_commands = [
            "เปิดโหมดเจนภาพ",
            "เปิดโหมดสร้างภาพ",
            "เปิดโหมดสร้างรูป",
            "เปิด image mode",
            "enable image mode",
        ]

        if any(
            command in lower
            for command in open_commands
        ):

            if enable_image_mode is None:

                return (
                    "ระบบสร้างภาพยังไม่พร้อมครับ"
                )

            try:

                result = enable_image_mode()

                self.image_mode = True

                return str(result)

            except Exception as e:

                return (
                    f"เปิดโหมดสร้างภาพไม่สำเร็จครับ: {e}"
                )

        # ----------------------------------------------------
        # CLOSE
        # ----------------------------------------------------

        close_commands = [
            "ปิดโหมดเจนภาพ",
            "ปิดโหมดสร้างภาพ",
            "ปิดโหมดสร้างรูป",
            "ปิด image mode",
            "disable image mode",
        ]

        if any(
            command in lower
            for command in close_commands
        ):

            if disable_image_mode is None:

                return (
                    "ระบบสร้างภาพยังไม่พร้อมครับ"
                )

            try:

                result = disable_image_mode()

                self.image_mode = False

                return str(result)

            except Exception as e:

                return (
                    f"ปิดโหมดสร้างภาพไม่สำเร็จครับ: {e}"
                )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        status_commands = [
            "สถานะโหมดเจนภาพ",
            "สถานะโหมดสร้างภาพ",
            "เช็คโหมดเจนภาพ",
            "เช็กโหมดเจนภาพ",
            "image mode status",
        ]

        if any(
            command in lower
            for command in status_commands
        ):

            if image_mode_status is None:

                return (
                    "ระบบสร้างภาพยังไม่พร้อมครับ"
                )

            try:

                return str(
                    image_mode_status()
                )

            except Exception as e:

                return (
                    f"ตรวจสอบโหมดสร้างภาพไม่สำเร็จครับ: {e}"
                )

        return None


    # ========================================================
    # IMAGE COMMAND DETECTION
    # ========================================================

    def is_image_command(self, text):

        lower = text.lower()

        commands = [
            "สร้างรูป",
            "สร้างภาพ",
            "เจนภาพ",
            "เจนรูป",
            "วาดภาพ",
            "สร้างรูปภาพ",
            "generate image",
            "generate picture",
            "create image",
        ]

        return any(
            command in lower
            for command in commands
        )


    # ========================================================
    # IMAGE GENERATION
    # ========================================================

    def handle_image_generation(self, text):

        if generate_image is None:

            return (
                "ระบบสร้างภาพยังไม่พร้อมครับ"
            )

        # ----------------------------------------------------
        # REMOVE COMMAND
        # ----------------------------------------------------

        prompt = text

        remove_commands = [
            "สร้างรูป",
            "สร้างภาพ",
            "เจนภาพ",
            "เจนรูป",
            "วาดภาพ",
            "สร้างรูปภาพ",
            "generate image",
            "generate picture",
            "create image",
        ]

        for command in remove_commands:

            prompt = prompt.replace(
                command,
                "",
                1
            )

        prompt = prompt.strip()

        if not prompt:

            prompt = (
                "a futuristic artificial intelligence "
                "laboratory, cinematic lighting, "
                "highly detailed"
            )

        # ----------------------------------------------------
        # ENABLE IMAGE MODE
        # ----------------------------------------------------

        try:

            if not self.image_mode:

                enable_image_mode()

                self.image_mode = True

        except Exception as e:

            print(
                f"[JARVIS IMAGE] Enable error: {e}"
            )

        # ----------------------------------------------------
        # GENERATE
        # ----------------------------------------------------

        print(
            f"[JARVIS IMAGE] Prompt: {prompt}"
        )

        try:

            path = generate_image(
                prompt
            )

            if not path:

                return (
                    "สร้างภาพไม่สำเร็จครับ"
                )

            return (
                "สร้างภาพเสร็จเรียบร้อยแล้วครับ\n"
                f"IMAGE_PATH: {path}"
            )

        except Exception as e:

            print(
                f"[JARVIS IMAGE] ERROR: {e}"
            )

            return (
                f"สร้างภาพไม่สำเร็จครับ: {e}"
            )


    # ========================================================
    # WINDOWS COMMANDS
    # ========================================================

    def handle_windows_command(self, text):

        lower = text.lower()

        # ----------------------------------------------------
        # CHROME
        # ----------------------------------------------------

        if (
            "เปิด chrome" in lower
            or "open chrome" in lower
        ):

            try:

                subprocess.Popen(
                    [
                        "cmd",
                        "/c",
                        "start",
                        "",
                        "chrome"
                    ]
                )

                return (
                    "กำลังเปิด Chrome ครับ"
                )

            except Exception as e:

                return (
                    f"เปิด Chrome ไม่สำเร็จครับ: {e}"
                )

        # ----------------------------------------------------
        # NOTEPAD
        # ----------------------------------------------------

        if (
            "เปิด notepad" in lower
            or "เปิดโน้ตแพด" in lower
            or "open notepad" in lower
        ):

            try:

                subprocess.Popen(
                    [
                        "notepad.exe"
                    ]
                )

                return (
                    "กำลังเปิด Notepad ครับ"
                )

            except Exception as e:

                return (
                    f"เปิด Notepad ไม่สำเร็จครับ: {e}"
                )

        # ----------------------------------------------------
        # CALCULATOR
        # ----------------------------------------------------

        if (
            "เปิดเครื่องคิดเลข" in lower
            or "เปิด calculator" in lower
            or "open calculator" in lower
        ):

            try:

                subprocess.Popen(
                    [
                        "calc.exe"
                    ]
                )

                return (
                    "กำลังเปิดเครื่องคิดเลขครับ"
                )

            except Exception as e:

                return (
                    f"เปิดเครื่องคิดเลขไม่สำเร็จครับ: {e}"
                )

        return None


    # ========================================================
    # SYSTEM COMMANDS
    # ========================================================

    def handle_system_command(self, text):

        lower = text.lower()

        # ----------------------------------------------------
        # JARVIS STATUS
        # ----------------------------------------------------

        status_commands = [
            "สถานะระบบ",
            "เช็คสถานะระบบ",
            "เช็กสถานะระบบ",
            "system status",
            "jarvis status",
        ]

        if any(
            command in lower
            for command in status_commands
        ):

            return self.system_status()

        # ----------------------------------------------------
        # VERSION
        # ----------------------------------------------------

        version_commands = [
            "เวอร์ชัน",
            "version",
            "jarvis version",
        ]

        if any(
            command in lower
            for command in version_commands
        ):

            return (
                f"JARVIS เวอร์ชัน {JARVIS_VERSION} "
                "พร้อมทำงานครับ"
            )

        # ----------------------------------------------------
        # WHO ARE YOU
        # ----------------------------------------------------

        identity_commands = [
            "คุณคือใคร",
            "นายคือใคร",
            "แกคือใคร",
            "who are you",
            "what are you",
        ]

        if any(
            command in lower
            for command in identity_commands
        ):

            return (
                "ผมคือ JARVIS ผู้ช่วย AI ส่วนตัวครับ"
            )

        # ----------------------------------------------------
        # GREETING
        # ----------------------------------------------------

        greetings = [
            "สวัสดี",
            "หวัดดี",
            "hello",
            "hi",
        ]

        if any(
            command in lower
            for command in greetings
        ):

            return (
                "สวัสดีครับ ผม JARVIS "
                "พร้อมทำงานครับ"
            )

        return None


    # ========================================================
    # SYSTEM STATUS
    # ========================================================

    def system_status(self):

        ollama = "OFFLINE"

        comfy = "OFFLINE"

        voice = "OFFLINE"

        # ----------------------------------------------------
        # OLLAMA
        # ----------------------------------------------------

        try:

            response = requests.get(
                f"{OLLAMA_URL}/api/tags",
                timeout=3
            )

            if response.status_code == 200:

                ollama = "ONLINE"

        except Exception:
            pass

        # ----------------------------------------------------
        # COMFYUI
        # ----------------------------------------------------

        try:

            response = requests.get(
                "http://127.0.0.1:8188/system_stats",
                timeout=3
            )

            if response.status_code == 200:

                comfy = "ONLINE"

        except Exception:
            pass

        # ----------------------------------------------------
        # VOICE
        # ----------------------------------------------------

        if self.voice is not None:

            voice = "ONLINE"

        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        return (
            "JARVIS SYSTEM STATUS\n\n"
            f"AI CORE       : {ollama}\n"
            f"IDENTITY      : ONLINE\n"
            f"VOICE         : {voice}\n"
            f"VISUAL CORE   : {comfy}\n"
            f"IMAGE MODE    : "
            f"{'ON' if self.image_mode else 'OFF'}"
        )


    # ========================================================
    # AI / OLLAMA
    # ========================================================

    def ask_ai(self, text):

        # ----------------------------------------------------
        # BUILD PROMPT
        # ----------------------------------------------------

        messages = [

            {
                "role": "system",
                "content": get_system_prompt(),
            }

        ]

        # ----------------------------------------------------
        # CONVERSATION MEMORY
        # ----------------------------------------------------

        for message in self.conversation[-12:]:

            messages.append(
                message
            )

        messages.append(
            {
                "role": "user",
                "content": text,
            }
        )

        # ----------------------------------------------------
        # OLLAMA REQUEST
        # ----------------------------------------------------

        try:

            response = requests.post(
                f"{OLLAMA_URL}/api/chat",

                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                    },
                },

                timeout=REQUEST_TIMEOUT
            )

        except requests.exceptions.ConnectionError:

            return (
                "ไม่สามารถเชื่อมต่อ AI Core ได้ครับ "
                "กรุณาตรวจสอบว่า Ollama กำลังทำงานอยู่"
            )

        except requests.exceptions.Timeout:

            return (
                "AI Core ใช้เวลาประมวลผลนานเกินไปครับ"
            )

        except Exception as e:

            return (
                f"เชื่อมต่อ AI Core ไม่สำเร็จครับ: {e}"
            )

        # ----------------------------------------------------
        # HTTP ERROR
        # ----------------------------------------------------

        if response.status_code != 200:

            return (
                f"AI Core ตอบกลับด้วยสถานะ "
                f"{response.status_code} ครับ"
            )

        # ----------------------------------------------------
        # PARSE
        # ----------------------------------------------------

        try:

            data = response.json()

            answer = (
                data
                .get("message", {})
                .get("content", "")
                .strip()
            )

        except Exception as e:

            return (
                f"อ่านผลลัพธ์จาก AI Core ไม่สำเร็จครับ: {e}"
            )

        if not answer:

            return (
                "AI Core ไม่ได้ส่งคำตอบกลับมาครับ"
            )

        # ----------------------------------------------------
        # REMOVE QWEN THINKING TAGS
        # ----------------------------------------------------

        answer = re.sub(
            r"<think>.*?</think>",
            "",
            answer,
            flags=re.DOTALL
        ).strip()

        # ----------------------------------------------------
        # MEMORY
        # ----------------------------------------------------

        self.conversation.append(
            {
                "role": "user",
                "content": text,
            }
        )

        self.conversation.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        # ----------------------------------------------------
        # LIMIT MEMORY
        # ----------------------------------------------------

        if len(self.conversation) > 20:

            self.conversation = (
                self.conversation[-20:]
            )

        return answer


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("JARVIS AI AGENT TEST")
    print("=" * 60)
    print()

    agent = Agent()

    print(
        agent.system_status()
    )

    print()

    print(
        "Identity:",
        JARVIS_NAME
    )

    print(
        "Version:",
        JARVIS_VERSION
    )

    print()

    print("=" * 60)