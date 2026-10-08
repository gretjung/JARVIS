# ============================================================
# JARVIS AI AGENT v3.0
# Identity + Voice + Visual Core + Auto ComfyUI
# ============================================================

import os
import re
import subprocess
import requests

from core.identity import (
    JARVIS_NAME,
    JARVIS_VERSION,
    get_system_prompt,
    get_response,
)

from core.visual_core import visual_core

from tools.comfyui import (
    generate_image,
    enable_image_mode,
    disable_image_mode,
    image_mode_status,
    is_comfyui_running,
)

try:
    import ollama
except ImportError:
    ollama = None


class Agent:

    def __init__(
        self,
        voice=None
    ):

        self.name = JARVIS_NAME
        self.version = JARVIS_VERSION

        self.model = "qwen3:8b"

        self.voice = voice

        self.conversation = []

        self.image_mode = False

        self.last_image_path = None

    # ========================================================
    # Helper
    # ========================================================

    def say(self, text):

        if self.voice:

            try:
                self.voice.speak(
                    text,
                    wait=False
                )

            except Exception as e:

                print(
                    f"[JARVIS VOICE] {e}"
                )

    # ========================================================
    # Ollama Status
    # ========================================================

    def ollama_status(self):

        try:

            response = requests.get(
                "http://127.0.0.1:11434/api/tags",
                timeout=3
            )

            if response.status_code == 200:

                return True

        except Exception:
            pass

        return False

    # ========================================================
    # ComfyUI Status
    # ========================================================

    def comfyui_status(self):

        try:

            return is_comfyui_running()

        except Exception:

            return False

    # ========================================================
    # System Status
    # ========================================================

    def system_status(self):

        ollama_online = self.ollama_status()

        comfy_online = self.comfyui_status()

        voice_online = (
            self.voice is not None
        )

        image_status = (
            "ON"
            if self.image_mode
            else "OFF"
        )

        return (
            "\n"
            "==================================================\n"
            "JARVIS SYSTEM STATUS\n"
            "==================================================\n"
            f"AI CORE       : "
            f"{'ONLINE' if ollama_online else 'OFFLINE'}\n"
            f"IDENTITY      : ONLINE\n"
            f"VOICE         : "
            f"{'ONLINE' if voice_online else 'OFFLINE'}\n"
            f"COMFYUI       : "
            f"{'ONLINE' if comfy_online else 'OFFLINE'}\n"
            f"IMAGE MODE    : {image_status}\n"
            f"VISUAL CORE   : ONLINE\n"
            "=================================================="
        )

    # ========================================================
    # Voice Commands
    # ========================================================

    def handle_voice_command(
        self,
        text
    ):

        lower = text.lower().strip()

        if lower in (
            "เปิดเสียง",
            "เปิดระบบเสียง",
            "เสียงเปิด",
            "เปิด voice",
            "enable voice",
        ):

            if self.voice:

                self.voice.enable()

                return "เปิดระบบเสียงแล้วครับ"

            return "ระบบเสียงยังไม่พร้อมครับ"

        if lower in (
            "ปิดเสียง",
            "ปิดระบบเสียง",
            "เสียงปิด",
            "ปิด voice",
            "disable voice",
        ):

            if self.voice:

                self.voice.disable()

                return "ปิดระบบเสียงแล้วครับ"

            return "ระบบเสียงยังไม่พร้อมครับ"

        if lower in (
            "หยุดเสียง",
            "หยุดพูด",
            "หยุดการพูด",
            "stop voice",
            "stop speaking",
        ):

            if self.voice:

                self.voice.stop()

                return "หยุดเสียงแล้วครับ"

            return "ระบบเสียงยังไม่พร้อมครับ"

        if lower in (
            "สถานะเสียง",
            "เช็คเสียง",
            "เช็กเสียง",
            "voice status",
        ):

            if self.voice:

                try:
                    return self.voice.status()

                except Exception:

                    return "ระบบเสียงออนไลน์ครับ"

            return "ระบบเสียงออฟไลน์ครับ"

        if lower in (
            "ทดสอบเสียง",
            "ทดสอบระบบเสียง",
            "test voice",
        ):

            if self.voice:

                self.voice.test_voice()

                return (
                    "กำลังทดสอบระบบเสียงครับ"
                )

            return "ระบบเสียงยังไม่พร้อมครับ"

        return None

    # ========================================================
    # Image Mode Commands
    # ========================================================

    def handle_image_mode_command(
        self,
        text
    ):

        lower = text.lower().strip()

        if lower in (
            "เปิดโหมดเจนภาพ",
            "เปิดโหมดสร้างภาพ",
            "เปิด image mode",
        ):

            result = enable_image_mode()

            self.image_mode = True

            return (
                "เปิดโหมดสร้างภาพแล้วครับ"
                if result
                else
                "ไม่สามารถเปิดโหมดสร้างภาพได้ครับ"
            )

        if lower in (
            "ปิดโหมดเจนภาพ",
            "ปิดโหมดสร้างภาพ",
            "ปิด image mode",
        ):

            result = disable_image_mode(
                close_comfyui=True
            )

            self.image_mode = False

            return (
                "ปิดโหมดสร้างภาพแล้วครับ"
                if result
                else
                "ปิดโหมดสร้างภาพไม่สำเร็จครับ"
            )

        if lower in (
            "สถานะโหมดเจนภาพ",
            "สถานะโหมดสร้างภาพ",
            "image mode status",
        ):

            try:

                status = image_mode_status()

                return str(status)

            except Exception:

                return (
                    "ไม่สามารถตรวจสอบสถานะได้ครับ"
                )

        return None

    # ========================================================
    # Automatic Image Generation
    # ========================================================

    def generate_image_auto(
        self,
        prompt
    ):
        """
        Automatic ComfyUI lifecycle.

        If ComfyUI is OFFLINE:
            JARVIS starts it.

        If ComfyUI is already ONLINE:
            JARVIS uses it and does NOT shut it down.

        If JARVIS started ComfyUI:
            JARVIS shuts it down after generation.
        """

        started_by_jarvis = False

        try:

            # ------------------------------------------------
            # Check current state
            # ------------------------------------------------

            online = self.comfyui_status()

            print(
                "[JARVIS IMAGE] "
                f"ComfyUI before generation: "
                f"{'ONLINE' if online else 'OFFLINE'}"
            )

            # ------------------------------------------------
            # Start automatically
            # ------------------------------------------------

            if not online:

                print(
                    "[JARVIS IMAGE] "
                    "Starting ComfyUI automatically..."
                )

                result = enable_image_mode()

                if not result:

                    return (
                        None,
                        False,
                        "ไม่สามารถเปิด ComfyUI ได้ครับ"
                    )

                started_by_jarvis = True

                print(
                    "[JARVIS IMAGE] "
                    "ComfyUI started by JARVIS."
                )

            # ------------------------------------------------
            # Generate
            # ------------------------------------------------

            print(
                "[JARVIS IMAGE] "
                "Generating image..."
            )

            image_path = generate_image(
                prompt
            )

            if not image_path:

                return (
                    None,
                    started_by_jarvis,
                    "ComfyUI ไม่ได้คืนไฟล์ภาพครับ"
                )

            print(
                "[JARVIS IMAGE] "
                f"Generation completed: {image_path}"
            )

            self.last_image_path = image_path

            return (
                image_path,
                started_by_jarvis,
                None
            )

        except Exception as e:

            print(
                "[JARVIS IMAGE] "
                f"Generation error: {e}"
            )

            return (
                None,
                started_by_jarvis,
                str(e)
            )

        finally:

            # ------------------------------------------------
            # AUTO SHUTDOWN
            # ------------------------------------------------

            if started_by_jarvis:

                print(
                    "[JARVIS IMAGE] "
                    "JARVIS started ComfyUI."
                )

                print(
                    "[JARVIS IMAGE] "
                    "Shutting down ComfyUI..."
                )

                try:

                    disable_image_mode(
                        close_comfyui=True
                    )

                    print(
                        "[JARVIS IMAGE] "
                        "ComfyUI shutdown complete."
                    )

                except Exception as e:

                    print(
                        "[JARVIS IMAGE] "
                        f"Shutdown error: {e}"
                    )

    # ========================================================
    # Image Generation Command
    # ========================================================

    def handle_image_command(
        self,
        text
    ):

        lower = text.lower().strip()

        commands = [
            "สร้างภาพ",
            "สร้างรูป",
            "เจนภาพ",
            "เจนรูป",
            "วาดภาพ",
            "สร้างรูปภาพ",
            "generate image",
            "generate picture",
            "create image",
        ]

        matched = None

        for command in commands:

            if lower.startswith(command):

                matched = command
                break

        if matched is None:

            return None

        # ----------------------------------------------------
        # Extract prompt
        # ----------------------------------------------------

        prompt = text[
            len(matched):
        ].strip()

        if not prompt:

            return (
                "กรุณาบอกสิ่งที่ต้องการให้สร้างภาพครับ"
            )

        print()
        print(
            "=================================================="
        )
        print(
            "[JARVIS IMAGE] IMAGE REQUEST"
        )
        print(
            "=================================================="
        )

        print(
            f"[JARVIS IMAGE] User prompt: {prompt}"
        )

        # ----------------------------------------------------
        # Visual Core
        # ----------------------------------------------------

        visual_result = visual_core.process(
            prompt
        )

        if not visual_result.get(
            "success"
        ):

            return (
                "ไม่สามารถวิเคราะห์คำสั่ง "
                "สร้างภาพได้ครับ"
            )

        visual_prompt = visual_result[
            "prompt"
        ]

        negative_prompt = visual_result[
            "negative_prompt"
        ]

        print()
        print(
            "[JARVIS IMAGE] "
            "VISUAL CORE READY"
        )

        print(
            f"[JARVIS IMAGE] "
            f"Subject: "
            f"{visual_result.get('subject')}"
        )

        print(
            f"[JARVIS IMAGE] "
            f"Prompt: {visual_prompt}"
        )

        print(
            f"[JARVIS IMAGE] "
            f"Negative: {negative_prompt}"
        )

        # ----------------------------------------------------
        # Auto ComfyUI
        # ----------------------------------------------------

        (
            path,
            started_by_jarvis,
            error
        ) = self.generate_image_auto(
            visual_prompt
        )

        if not path:

            if error:

                return (
                    f"สร้างภาพไม่สำเร็จครับ: "
                    f"{error}"
                )

            return (
                "สร้างภาพไม่สำเร็จครับ"
            )

        print(
            "=================================================="
        )
        print(
            "[JARVIS IMAGE] DONE"
        )
        print(
            "=================================================="
        )

        return (
            "สร้างภาพเสร็จเรียบร้อยแล้วครับ\n"
            f"IMAGE_PATH: {path}"
        )

    # ========================================================
    # Windows Commands
    # ========================================================

    def handle_windows_command(
        self,
        text
    ):

        lower = text.lower().strip()

        # Chrome
        if lower in (
            "เปิด chrome",
            "เปิด google chrome",
        ):

            try:

                subprocess.Popen(
                    [
                        "cmd",
                        "/c",
                        "start",
                        "",
                        "chrome",
                    ]
                )

                return (
                    "กำลังเปิด Chrome ครับ"
                )

            except Exception as e:

                return (
                    f"เปิด Chrome ไม่สำเร็จครับ: {e}"
                )

        # Notepad
        if lower in (
            "เปิด notepad",
            "เปิดโน้ตแพด",
            "เปิด โน้ตแพด",
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

        # Calculator
        if lower in (
            "เปิดเครื่องคิดเลข",
            "เปิด calculator",
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
    # Basic System Commands
    # ========================================================

    def handle_system_command(
        self,
        text
    ):

        lower = text.lower().strip()

        if lower in (
            "สถานะระบบ",
            "เช็คสถานะระบบ",
            "เช็กสถานะระบบ",
            "system status",
        ):

            return self.system_status()

        if lower in (
            "เวอร์ชัน",
            "version",
            "เวอร์ชั่น",
        ):

            return (
                f"{JARVIS_NAME} "
                f"Version {JARVIS_VERSION} "
                "ครับ"
            )

        if lower in (
            "คุณคือใคร",
            "นายคือใคร",
            "แกคือใคร",
            "who are you",
        ):

            return (
                "ผมคือ JARVIS "
                "ผู้ช่วยปัญญาประดิษฐ์ส่วนตัวของคุณครับ"
            )

        if lower in (
            "สวัสดี",
            "หวัดดี",
            "hello",
            "hi",
            "hey jarvis",
        ):

            return get_response(
                "greeting"
            )

        return None

    # ========================================================
    # AI
    # ========================================================

    def ask_ai(
        self,
        text
    ):

        if not self.ollama_status():

            return (
                "Ollama ไม่ออนไลน์ครับ"
            )

        messages = [
            {
                "role": "system",
                "content": get_system_prompt(),
            }
        ]

        messages.extend(
            self.conversation[-12:]
        )

        messages.append(
            {
                "role": "user",
                "content": text,
            }
        )

        payload = {
            "model": self.model,
            "stream": False,
            "messages": messages,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            },
        }

        try:

            response = requests.post(
                "http://127.0.0.1:11434/api/chat",
                json=payload,
                timeout=180
            )

            response.raise_for_status()

            data = response.json()

            answer = (
                data
                .get("message", {})
                .get("content", "")
            )

            # Remove Qwen thinking block
            answer = re.sub(
                r"<think>.*?</think>",
                "",
                answer,
                flags=re.I | re.S
            ).strip()

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

            self.conversation = (
                self.conversation[-20:]
            )

            return answer

        except Exception as e:

            print(
                f"[JARVIS AI] Error: {e}"
            )

            return (
                f"AI Core เกิดข้อผิดพลาดครับ: {e}"
            )

    # ========================================================
    # Main Router
    # ========================================================

    def handle(
        self,
        text
    ):

        if not text:

            return ""

        text = text.strip()

        if not text:

            return ""

        print()
        print(
            f"[JARVIS] USER: {text}"
        )

        # ----------------------------------------------------
        # Voice
        # ----------------------------------------------------

        result = self.handle_voice_command(
            text
        )

        if result is not None:

            return result

        # ----------------------------------------------------
        # Image Generation
        #
        # IMPORTANT:
        # This comes BEFORE Image Mode commands.
        # The user does not need to turn Image Mode ON.
        # ----------------------------------------------------

        result = self.handle_image_command(
            text
        )

        if result is not None:

            return result

        # ----------------------------------------------------
        # Image Mode
        # ----------------------------------------------------

        result = self.handle_image_mode_command(
            text
        )

        if result is not None:

            return result

        # ----------------------------------------------------
        # Windows
        # ----------------------------------------------------

        result = self.handle_windows_command(
            text
        )

        if result is not None:

            return result

        # ----------------------------------------------------
        # System
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


if __name__ == "__main__":

    print("=" * 60)
    print("JARVIS AI AGENT v3.0")
    print("=" * 60)

    agent = Agent()

    print(
        agent.system_status()
    )