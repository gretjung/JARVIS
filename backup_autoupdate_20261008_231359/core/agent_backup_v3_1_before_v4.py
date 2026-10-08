# ============================================================
# JARVIS AI AGENT v3.1
# Identity + Voice + Visual Core + Auto ComfyUI
# ============================================================

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


class Agent:

    # ========================================================
    # INIT
    # ========================================================

    def __init__(self, voice=None):

        self.name = JARVIS_NAME
        self.version = JARVIS_VERSION

        self.model = "qwen3:8b"

        self.voice = voice

        self.conversation = []

        self.image_mode = False

        self.last_image_path = None

    # ========================================================
    # VOICE
    # ========================================================

    def say(self, text):

        if not self.voice:
            return

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
    # OLLAMA STATUS
    # ========================================================

    def ollama_status(self):

        try:

            response = requests.get(
                "http://127.0.0.1:11434/api/tags",
                timeout=3
            )

            return response.status_code == 200

        except Exception:

            return False

    # ========================================================
    # COMFYUI STATUS
    # ========================================================

    def comfyui_status(self):

        try:

            return is_comfyui_running()

        except Exception:

            return False

    # ========================================================
    # SYSTEM STATUS
    # ========================================================

    def system_status(self):

        ollama_online = self.ollama_status()

        comfy_online = self.comfyui_status()

        voice_online = self.voice is not None

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
    # VOICE COMMANDS
    # ========================================================

    def handle_voice_command(self, text):

        lower = text.lower().strip()

        # ----------------------------------------------------
        # ENABLE
        # ----------------------------------------------------

        if lower in (
            "เปิดเสียง",
            "เปิดระบบเสียง",
            "เสียงเปิด",
            "เปิด voice",
            "enable voice",
        ):

            if self.voice:

                self.voice.enable()

                return (
                    "เปิดระบบเสียงแล้วครับ"
                )

            return (
                "ระบบเสียงยังไม่พร้อมครับ"
            )

        # ----------------------------------------------------
        # DISABLE
        # ----------------------------------------------------

        if lower in (
            "ปิดเสียง",
            "ปิดระบบเสียง",
            "เสียงปิด",
            "ปิด voice",
            "disable voice",
        ):

            if self.voice:

                self.voice.disable()

                return (
                    "ปิดระบบเสียงแล้วครับ"
                )

            return (
                "ระบบเสียงยังไม่พร้อมครับ"
            )

        # ----------------------------------------------------
        # STOP
        # ----------------------------------------------------

        if lower in (
            "หยุดเสียง",
            "หยุดพูด",
            "หยุดการพูด",
            "stop voice",
            "stop speaking",
        ):

            if self.voice:

                self.voice.stop()

                return (
                    "หยุดเสียงแล้วครับ"
                )

            return (
                "ระบบเสียงยังไม่พร้อมครับ"
            )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

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

                    return (
                        "ระบบเสียงออนไลน์ครับ"
                    )

            return (
                "ระบบเสียงออฟไลน์ครับ"
            )

        # ----------------------------------------------------
        # TEST
        # ----------------------------------------------------

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

            return (
                "ระบบเสียงยังไม่พร้อมครับ"
            )

        return None

    # ========================================================
    # IMAGE MODE COMMANDS
    # ========================================================

    def handle_image_mode_command(self, text):

        lower = text.lower().strip()

        # ----------------------------------------------------
        # OPEN MANUALLY
        # ----------------------------------------------------

        if lower in (
            "เปิดโหมดเจนภาพ",
            "เปิดโหมดสร้างภาพ",
            "เปิด image mode",
        ):

            result = enable_image_mode()

            if result:

                self.image_mode = True

                return (
                    "เปิดโหมดสร้างภาพแล้วครับ"
                )

            return (
                "ไม่สามารถเปิดโหมดสร้างภาพได้ครับ"
            )

        # ----------------------------------------------------
        # CLOSE MANUALLY
        # ----------------------------------------------------

        if lower in (
            "ปิดโหมดเจนภาพ",
            "ปิดโหมดสร้างภาพ",
            "ปิด image mode",
        ):

            try:

                result = disable_image_mode(
                    close_comfyui=True
                )

                self.image_mode = False

                if result:

                    return (
                        "ปิดโหมดสร้างภาพแล้วครับ"
                    )

                return (
                    "ปิดโหมดสร้างภาพไม่สำเร็จครับ"
                )

            except Exception as e:

                self.image_mode = False

                return (
                    f"ปิดโหมดสร้างภาพไม่สำเร็จครับ: {e}"
                )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        if lower in (
            "สถานะโหมดเจนภาพ",
            "สถานะโหมดสร้างภาพ",
            "image mode status",
        ):

            try:

                return str(
                    image_mode_status()
                )

            except Exception:

                return (
                    "ไม่สามารถตรวจสอบสถานะได้ครับ"
                )

        return None

    # ========================================================
    # AUTOMATIC COMFYUI IMAGE GENERATION
    # ========================================================

    def generate_image_auto(self, prompt):

        """
        JARVIS Automatic Image Generation Lifecycle

        CASE A
        ------------------------------------------------------
        ComfyUI OFFLINE
            ↓
        Start ComfyUI
            ↓
        Enable Image Mode
            ↓
        Generate
            ↓
        Disable Image Mode
            ↓
        Shutdown ComfyUI


        CASE B
        ------------------------------------------------------
        ComfyUI ONLINE
            ↓
        Enable Image Mode
            ↓
        Generate
            ↓
        Disable Image Mode
            ↓
        KEEP ComfyUI ONLINE
        """

        started_by_jarvis = False

        image_mode_enabled_by_jarvis = False

        image_path = None

        error_message = None

        try:

            # =================================================
            # STEP 1
            # CHECK COMFYUI
            # =================================================

            comfy_online = self.comfyui_status()

            print()
            print(
                "[JARVIS IMAGE] "
                "=========================================="
            )

            print(
                "[JARVIS IMAGE] "
                f"ComfyUI before generation: "
                f"{'ONLINE' if comfy_online else 'OFFLINE'}"
            )

            # =================================================
            # STEP 2
            # START COMFYUI IF NEEDED
            # =================================================

            if not comfy_online:

                print(
                    "[JARVIS IMAGE] "
                    "ComfyUI is OFFLINE."
                )

                print(
                    "[JARVIS IMAGE] "
                    "Starting ComfyUI automatically..."
                )

                start_result = enable_image_mode()

                if not start_result:

                    error_message = (
                        "ไม่สามารถเปิด ComfyUI ได้ครับ"
                    )

                    return (
                        None,
                        False,
                        error_message
                    )

                started_by_jarvis = True

                image_mode_enabled_by_jarvis = True

                self.image_mode = True

                print(
                    "[JARVIS IMAGE] "
                    "ComfyUI started by JARVIS."
                )

                print(
                    "[JARVIS IMAGE] "
                    "IMAGE GENERATION MODE: ON"
                )

            # =================================================
            # STEP 3
            # COMFYUI ALREADY ONLINE
            #
            # IMPORTANT:
            # generate_image() requires IMAGE MODE ON.
            # =================================================

            else:

                print(
                    "[JARVIS IMAGE] "
                    "ComfyUI already ONLINE."
                )

                print(
                    "[JARVIS IMAGE] "
                    "Enabling IMAGE GENERATION MODE..."
                )

                enable_result = enable_image_mode()

                if not enable_result:

                    error_message = (
                        "ไม่สามารถเปิด "
                        "IMAGE GENERATION MODE ได้ครับ"
                    )

                    return (
                        None,
                        False,
                        error_message
                    )

                image_mode_enabled_by_jarvis = True

                self.image_mode = True

                print(
                    "[JARVIS IMAGE] "
                    "IMAGE GENERATION MODE: ON"
                )

            # =================================================
            # STEP 4
            # GENERATE IMAGE
            # =================================================

            print(
                "[JARVIS IMAGE] "
                "Generating image..."
            )

            image_path = generate_image(
                prompt
            )

            # =================================================
            # STEP 5
            # VALIDATE IMAGE
            # =================================================

            if not image_path:

                error_message = (
                    "ComfyUI ไม่ได้คืนไฟล์ภาพครับ"
                )

                return (
                    None,
                    started_by_jarvis,
                    error_message
                )

            self.last_image_path = image_path

            print(
                "[JARVIS IMAGE] "
                f"Generation completed: "
                f"{image_path}"
            )

            return (
                image_path,
                started_by_jarvis,
                None
            )

        except Exception as e:

            error_message = str(e)

            print(
                "[JARVIS IMAGE] "
                f"Generation error: {e}"
            )

            return (
                None,
                started_by_jarvis,
                error_message
            )

        finally:

            # =================================================
            # STEP 6
            # TURN IMAGE MODE OFF
            # =================================================

            if image_mode_enabled_by_jarvis:

                print(
                    "[JARVIS IMAGE] "
                    "Disabling IMAGE GENERATION MODE..."
                )

                try:

                    disable_image_mode(
                        close_comfyui=False
                    )

                    self.image_mode = False

                    print(
                        "[JARVIS IMAGE] "
                        "IMAGE GENERATION MODE: OFF"
                    )

                except Exception as e:

                    print(
                        "[JARVIS IMAGE] "
                        f"Image mode shutdown error: {e}"
                    )

            # =================================================
            # STEP 7
            # CLOSE COMFYUI ONLY IF JARVIS STARTED IT
            # =================================================

            if started_by_jarvis:

                print(
                    "[JARVIS IMAGE] "
                    "JARVIS started ComfyUI."
                )

                print(
                    "[JARVIS IMAGE] "
                    "Shutting down ComfyUI automatically..."
                )

                try:

                    disable_image_mode(
                        close_comfyui=True
                    )

                    self.image_mode = False

                    print(
                        "[JARVIS IMAGE] "
                        "ComfyUI shutdown complete."
                    )

                except Exception as e:

                    print(
                        "[JARVIS IMAGE] "
                        f"ComfyUI shutdown error: {e}"
                    )

            print(
                "[JARVIS IMAGE] "
                "=========================================="
            )

    # ========================================================
    # IMAGE COMMAND
    # ========================================================

    def handle_image_command(self, text):

        lower = text.lower().strip()

        commands = (
            "สร้างภาพ",
            "สร้างรูป",
            "เจนภาพ",
            "เจนรูป",
            "วาดภาพ",
            "สร้างรูปภาพ",
            "generate image",
            "generate picture",
            "create image",
        )

        matched_command = None

        for command in commands:

            if lower.startswith(command):

                matched_command = command

                break

        if matched_command is None:

            return None

        # ====================================================
        # EXTRACT USER PROMPT
        # ====================================================

        prompt = text[
            len(matched_command):
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
            f"[JARVIS IMAGE] "
            f"User prompt: {prompt}"
        )

        # ====================================================
        # VISUAL CORE
        # ====================================================

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

        visual_prompt = (
            visual_result["prompt"]
        )

        negative_prompt = (
            visual_result["negative_prompt"]
        )

        subject = (
            visual_result.get("subject")
        )

        print()
        print(
            "[JARVIS IMAGE] "
            "VISUAL CORE READY"
        )

        print(
            f"[JARVIS IMAGE] "
            f"Subject: {subject}"
        )

        print(
            f"[JARVIS IMAGE] "
            f"Prompt: {visual_prompt}"
        )

        print(
            f"[JARVIS IMAGE] "
            f"Negative: {negative_prompt}"
        )

        # ====================================================
        # AUTOMATIC COMFYUI
        # ====================================================

        (
            image_path,
            started_by_jarvis,
            error
        ) = self.generate_image_auto(
            visual_prompt
        )

        # ====================================================
        # ERROR
        # ====================================================

        if not image_path:

            if error:

                return (
                    f"สร้างภาพไม่สำเร็จครับ: "
                    f"{error}"
                )

            return (
                "สร้างภาพไม่สำเร็จครับ"
            )

        # ====================================================
        # SUCCESS
        # ====================================================

        print()
        print(
            "=================================================="
        )

        print(
            "[JARVIS IMAGE] IMAGE GENERATION COMPLETE"
        )

        print(
            "=================================================="
        )

        print(
            f"[JARVIS IMAGE] "
            f"Saved: {image_path}"
        )

        return (
            "สร้างภาพเสร็จเรียบร้อยแล้วครับ\n"
            f"IMAGE_PATH: {image_path}"
        )

    # ========================================================
    # WINDOWS COMMANDS
    # ========================================================

    def handle_windows_command(self, text):

        lower = text.lower().strip()

        # ----------------------------------------------------
        # CHROME
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # NOTEPAD
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # CALCULATOR
        # ----------------------------------------------------

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
    # SYSTEM COMMANDS
    # ========================================================

    def handle_system_command(self, text):

        lower = text.lower().strip()

        # ----------------------------------------------------
        # SYSTEM STATUS
        # ----------------------------------------------------

        if lower in (
            "สถานะระบบ",
            "เช็คสถานะระบบ",
            "เช็กสถานะระบบ",
            "system status",
        ):

            return self.system_status()

        # ----------------------------------------------------
        # VERSION
        # ----------------------------------------------------

        if lower in (
            "เวอร์ชัน",
            "เวอร์ชั่น",
            "version",
        ):

            return (
                f"{JARVIS_NAME} "
                f"Version {JARVIS_VERSION} "
                "ครับ"
            )

        # ----------------------------------------------------
        # IDENTITY
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # GREETING
        # ----------------------------------------------------

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
    # AI CORE
    # ========================================================

    def ask_ai(self, text):

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
    # MAIN ROUTER
    # ========================================================

    def handle(self, text):

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
        # VOICE
        # ----------------------------------------------------

        result = self.handle_voice_command(
            text
        )

        if result is not None:

            return result

        # ----------------------------------------------------
        # IMAGE GENERATION
        #
        # MUST BE BEFORE IMAGE MODE COMMANDS
        # ----------------------------------------------------

        result = self.handle_image_command(
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
        # WINDOWS
        # ----------------------------------------------------

        result = self.handle_windows_command(
            text
        )

        if result is not None:

            return result

        # ----------------------------------------------------
        # SYSTEM
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


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("JARVIS AI AGENT v3.1")
    print("=" * 60)

    agent = Agent()

    print()
    print(
        agent.system_status()
    )

    print()
    print(
        "Agent initialized successfully."
    )