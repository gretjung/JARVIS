# ============================================================
# JARVIS IMAGE GENERATION SKILL v1.0
# ============================================================

from core.visual_core import visual_core

from tools.comfyui import (
    generate_image,
    enable_image_mode,
    disable_image_mode,
    is_comfyui_running,
)


class ImageGenerationSkill:

    name = "IMAGE_GENERATION"

    enabled = True

    def __init__(self):

        self.image_mode = False

        self.last_image_path = None

    # ========================================================
    # CAN HANDLE
    # ========================================================

    def can_handle(self, text):

        if not self.enabled:
            return False

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

        for command in commands:

            if lower.startswith(command):

                return True

        return False

    # ========================================================
    # EXTRACT PROMPT
    # ========================================================

    def extract_prompt(self, text):

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

        for command in commands:

            if lower.startswith(command):

                return text[
                    len(command):
                ].strip()

        return ""

    # ========================================================
    # GENERATE
    # ========================================================

    def execute(self, text):

        prompt = self.extract_prompt(
            text
        )

        if not prompt:

            return (
                "กรุณาบอกสิ่งที่ต้องการให้สร้างภาพครับ"
            )

        print()
        print(
            "[JARVIS IMAGE SKILL]"
        )

        print(
            f"[JARVIS IMAGE SKILL] "
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

        print(
            "[JARVIS IMAGE SKILL] "
            "Visual Core ready."
        )

        print(
            f"[JARVIS IMAGE SKILL] "
            f"Subject: "
            f"{visual_result.get('subject')}"
        )

        # ====================================================
        # COMFYUI CHECK
        # ====================================================

        comfy_online = is_comfyui_running()

        print(
            "[JARVIS IMAGE SKILL] "
            f"ComfyUI: "
            f"{'ONLINE' if comfy_online else 'OFFLINE'}"
        )

        started_by_skill = False

        try:

            # ------------------------------------------------
            # START / ENABLE
            # ------------------------------------------------

            if not comfy_online:

                print(
                    "[JARVIS IMAGE SKILL] "
                    "Starting ComfyUI..."
                )

                if not enable_image_mode():

                    return (
                        "ไม่สามารถเปิด ComfyUI ได้ครับ"
                    )

                started_by_skill = True

                self.image_mode = True

            else:

                print(
                    "[JARVIS IMAGE SKILL] "
                    "Enabling Image Mode..."
                )

                if not enable_image_mode():

                    return (
                        "ไม่สามารถเปิดโหมดสร้างภาพได้ครับ"
                    )

                self.image_mode = True

            # ------------------------------------------------
            # GENERATE
            # ------------------------------------------------

            print(
                "[JARVIS IMAGE SKILL] "
                "Generating..."
            )

            image_path = generate_image(
                visual_prompt
            )

            if not image_path:

                return (
                    "ComfyUI ไม่ได้คืนไฟล์ภาพครับ"
                )

            self.last_image_path = image_path

            return (
                "สร้างภาพเสร็จเรียบร้อยแล้วครับ\n"
                f"IMAGE_PATH: {image_path}"
            )

        except Exception as e:

            print(
                "[JARVIS IMAGE SKILL] "
                f"Error: {e}"
            )

            return (
                f"สร้างภาพไม่สำเร็จครับ: {e}"
            )

        finally:

            # ------------------------------------------------
            # DISABLE IMAGE MODE
            # ------------------------------------------------

            if self.image_mode:

                try:

                    disable_image_mode(
                        close_comfyui=False
                    )

                except Exception as e:

                    print(
                        "[JARVIS IMAGE SKILL] "
                        f"Mode shutdown error: {e}"
                    )

                self.image_mode = False

            # ------------------------------------------------
            # CLOSE ONLY IF WE STARTED IT
            # ------------------------------------------------

            if started_by_skill:

                try:

                    disable_image_mode(
                        close_comfyui=True
                    )

                except Exception as e:

                    print(
                        "[JARVIS IMAGE SKILL] "
                        f"ComfyUI shutdown error: {e}"
                    )