# ============================================================
# JARVIS VOICE SKILL v1.2
# ============================================================

class VoiceSkill:

    name = "VOICE"
    enabled = True

    def __init__(self, voice=None):
        self.voice = voice

    # ========================================================
    # CAN HANDLE
    # ========================================================

    def can_handle(self, text):

        if not self.enabled or not text:
            return False

        lower = text.strip().lower()

        commands = (
            # ENABLE
            "เปิดเสียง",
            "เปิดระบบเสียง",
            "เสียงเปิด",
            "เปิด voice",
            "enable voice",

            # DISABLE
            "ปิดเสียง",
            "ปิดระบบเสียง",
            "เสียงปิด",
            "ปิด voice",
            "disable voice",

            # STOP
            "หยุดเสียง",
            "หยุดพูด",
            "หยุดการพูด",
            "stop voice",
            "stop speaking",

            # STATUS
            "สถานะเสียง",
            "เช็คเสียง",
            "เช็กเสียง",
            "voice status",

            # TEST
            "ทดสอบเสียง",
            "ทดสอบระบบเสียง",
            "test voice",
        )

        return lower in commands

    # ========================================================
    # EXECUTE
    # ========================================================

    def execute(self, text):

        if not self.voice:
            return "ระบบเสียงยังไม่พร้อมครับ"

        lower = text.strip().lower()

        # ====================================================
        # ENABLE
        # ====================================================

        if lower in (
            "เปิดเสียง",
            "เปิดระบบเสียง",
            "เสียงเปิด",
            "เปิด voice",
            "enable voice",
        ):

            try:
                self.voice.enable()

                return "เปิดระบบเสียงแล้วครับ"

            except Exception as e:

                return (
                    f"ไม่สามารถเปิดระบบเสียงได้ครับ: {e}"
                )

        # ====================================================
        # DISABLE
        # ====================================================

        if lower in (
            "ปิดเสียง",
            "ปิดระบบเสียง",
            "เสียงปิด",
            "ปิด voice",
            "disable voice",
        ):

            try:
                self.voice.disable()

                return "ปิดระบบเสียงแล้วครับ"

            except Exception as e:

                return (
                    f"ไม่สามารถปิดระบบเสียงได้ครับ: {e}"
                )

        # ====================================================
        # STOP
        # ====================================================

        if lower in (
            "หยุดเสียง",
            "หยุดพูด",
            "หยุดการพูด",
            "stop voice",
            "stop speaking",
        ):

            try:
                self.voice.stop()

                return "หยุดเสียงแล้วครับ"

            except Exception as e:

                return (
                    f"ไม่สามารถหยุดเสียงได้ครับ: {e}"
                )

        # ====================================================
        # STATUS
        # ====================================================

        if lower in (
            "สถานะเสียง",
            "เช็คเสียง",
            "เช็กเสียง",
            "voice status",
        ):

            try:
                return self.voice.status()

            except Exception as e:

                return (
                    f"ไม่สามารถตรวจสอบระบบเสียงได้ครับ: {e}"
                )

        # ====================================================
        # TEST
        # ====================================================

        if lower in (
            "ทดสอบเสียง",
            "ทดสอบระบบเสียง",
            "test voice",
        ):

            try:

                # สำคัญ:
                # ไม่เรียก test_voice() ที่นี่
                #
                # เพราะ Agent จะเป็นผู้พูดผลลัพธ์
                # เพื่อป้องกันเสียงพูด 2 รอบ

                return "ระบบเสียงพร้อมทำงานครับ"

            except Exception as e:

                return (
                    f"ระบบเสียงมีปัญหาครับ: {e}"
                )

        return None