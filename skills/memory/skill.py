# ============================================================
# JARVIS MEMORY SKILL v1.2
# ============================================================

class MemorySkill:

    name = "MEMORY"
    enabled = True

    def __init__(self, memory):
        self.memory = memory

    # ========================================================
    # CAN HANDLE
    # ========================================================

    def can_handle(self, text):

        if not text:
            return False

        lower = text.strip().lower()

        patterns = [

            # Remember
            "จำไว้ว่า",
            "จำไว้",
            "จำว่า",
            "ช่วยจำ",
            "remember",

            # Forget
            "ลืม",
            "ลบความจำ",
            "forget",

            # Preferences
            "ฉันชอบ",
            "ผมชอบ",
            "ฉันไม่ชอบ",
            "ผมไม่ชอบ",

            # Name
            "ฉันชื่อ",
            "ผมชื่อ",
            "ชื่อของฉัน",
            "ชื่อผม",

            # Recall
            "ฉันชอบอะไร",
            "ผมชอบอะไร",
            "ฉันไม่ชอบอะไร",
            "ผมไม่ชอบอะไร",
            "ฉันชื่ออะไร",
            "ผมชื่ออะไร",
            "ชื่ออะไร",

            # Status
            "memory status",
            "สถานะ memory",
            "สถานะความจำ",
            "เช็ค memory",
            "เช็ก memory",
        ]

        return any(pattern in lower for pattern in patterns)

    # ========================================================
    # EXECUTE
    # ========================================================

    def execute(self, text):

        if not text:
            return "ไม่มีคำสั่งเกี่ยวกับความจำครับ"

        original = text.strip()
        lower = original.lower()

        # ====================================================
        # STATUS
        # ====================================================

        if (
            "memory status" in lower
            or "สถานะ memory" in lower
            or "สถานะความจำ" in lower
            or "เช็ค memory" in lower
            or "เช็ก memory" in lower
        ):
            try:
                return self.memory.status()
            except Exception as e:
                return f"ไม่สามารถตรวจสอบ Memory ได้ครับ: {e}"

        # ====================================================
        # FORGET
        # ====================================================

        if (
            lower.startswith("ลืม")
            or lower.startswith("ลบความจำ")
            or lower.startswith("forget")
        ):
            return self._forget_text(original)

        # ====================================================
        # RECALL
        # ====================================================

        # ----------------------------------------------------
        # สิ่งที่ชอบ
        # ----------------------------------------------------

        if (
            "ฉันชอบ" in lower
            and "อะไร" in lower
        ):
            results = self.memory.search("ฉันชอบ")

            if results:
                item = results[-1]

                return (
                    f"คุณชอบ {item['value']} ครับ"
                )

            return (
                "ตอนนี้ผมยังไม่มีข้อมูล "
                "เรื่องสิ่งที่คุณชอบครับ"
            )

        if (
            "ผมชอบ" in lower
            and "อะไร" in lower
        ):
            results = self.memory.search("ฉันชอบ")

            if not results:
                results = self.memory.search("ผมชอบ")

            if results:
                item = results[-1]

                return (
                    f"คุณชอบ {item['value']} ครับ"
                )

            return (
                "ตอนนี้ผมยังไม่มีข้อมูล "
                "เรื่องสิ่งที่คุณชอบครับ"
            )

        # ----------------------------------------------------
        # สิ่งที่ไม่ชอบ
        # ----------------------------------------------------

        if (
            "ฉันไม่ชอบ" in lower
            and "อะไร" in lower
        ):
            results = self.memory.search("ฉันไม่ชอบ")

            if results:
                item = results[-1]

                return (
                    f"คุณไม่ชอบ {item['value']} ครับ"
                )

            return (
                "ตอนนี้ผมยังไม่มีข้อมูล "
                "เรื่องสิ่งที่คุณไม่ชอบครับ"
            )

        if (
            "ผมไม่ชอบ" in lower
            and "อะไร" in lower
        ):
            results = self.memory.search("ผมไม่ชอบ")

            if results:
                item = results[-1]

                return (
                    f"คุณไม่ชอบ {item['value']} ครับ"
                )

            return (
                "ตอนนี้ผมยังไม่มีข้อมูล "
                "เรื่องสิ่งที่คุณไม่ชอบครับ"
            )

        # ----------------------------------------------------
        # ชื่อผู้ใช้
        # ----------------------------------------------------

        if (
            "ฉันชื่ออะไร" in lower
            or "ผมชื่ออะไร" in lower
            or "ชื่อของฉัน" in lower
            or "ชื่อผม" in lower
            or "ชื่ออะไร" in lower
        ):
            value = self.memory.recall("ชื่อผู้ใช้")

            if value:
                return f"คุณชื่อ {value} ครับ"

            return (
                "ตอนนี้ผมยังไม่ทราบชื่อของคุณครับ"
            )

        # ====================================================
        # REMEMBER
        # ====================================================

        # ต้องตรวจสอบหลัง RECALL
        # เพื่อป้องกันคำถาม เช่น
        # "ฉันชอบรถอะไร"
        # ถูกมองว่าเป็นคำสั่งจำ

        if (
            lower.startswith("จำไว้ว่า")
            or lower.startswith("จำไว้")
            or lower.startswith("จำว่า")
            or lower.startswith("ช่วยจำ")
            or lower.startswith("remember")
        ):
            return self._remember_text(original)

        # ====================================================
        # PREFERENCE
        # ====================================================

        if (
            "ฉันชอบ" in lower
            or "ผมชอบ" in lower
        ):
            return self._remember_preference(
                original,
                "สิ่งที่ฉันชอบ"
            )

        if (
            "ฉันไม่ชอบ" in lower
            or "ผมไม่ชอบ" in lower
        ):
            return self._remember_preference(
                original,
                "สิ่งที่ฉันไม่ชอบ"
            )

        # ====================================================
        # NAME
        # ====================================================

        if (
            lower.startswith("ฉันชื่อ")
            or lower.startswith("ผมชื่อ")
        ):
            name = self._extract_after_prefix(
                original,
                [
                    "ฉันชื่อ",
                    "ผมชื่อ",
                ]
            )

            if name:
                self.memory.remember(
                    "ชื่อผู้ใช้",
                    name
                )

                return (
                    f"รับทราบครับ "
                    f"ผมจะจำไว้ว่าคุณชื่อ {name} ครับ"
                )

        # ====================================================
        # FALLBACK
        # ====================================================

        return (
            "ผมเข้าใจว่าเป็นคำสั่งเกี่ยวกับความจำครับ "
            "แต่ยังไม่ทราบว่าต้องการให้ผมจำอะไร"
        )

    # ========================================================
    # REMEMBER TEXT
    # ========================================================

    def _remember_text(self, text):

        value = text.strip()

        prefixes = [
            "จำไว้ว่า",
            "จำไว้",
            "จำว่า",
            "ช่วยจำ",
            "remember",
        ]

        for prefix in prefixes:

            if value.lower().startswith(prefix.lower()):

                value = value[len(prefix):].strip()

                break

        if not value:
            return (
                "ต้องการให้ผมจำเรื่องอะไรครับ"
            )

        # ----------------------------------------------------
        # หา key / value
        # ----------------------------------------------------

        separators = [
            "คือ",
            "เป็น",
            "=",
            ":",
        ]

        for separator in separators:

            if separator in value:

                parts = value.split(
                    separator,
                    1
                )

                key = parts[0].strip()
                val = parts[1].strip()

                if key and val:

                    self.memory.remember(
                        key,
                        val
                    )

                    return (
                        f"รับทราบครับ "
                        f"ผมบันทึกเรื่อง {key} "
                        f"ไว้แล้วครับ"
                    )

        # ----------------------------------------------------
        # กรณีรูปแบบ
        #
        # จำไว้ว่า รถที่ฉันชอบ รถสีดำ
        # ----------------------------------------------------

        words = value.split()

        if len(words) >= 2:

            # พยายามแบ่ง key/value
            # โดยใช้ครึ่งแรกเป็น key

            midpoint = max(
                1,
                len(words) // 2
            )

            key = " ".join(
                words[:midpoint]
            ).strip()

            val = " ".join(
                words[midpoint:]
            ).strip()

            if key and val:

                self.memory.remember(
                    key,
                    val
                )

                return (
                    f"รับทราบครับ "
                    f"ผมบันทึกเรื่อง {key} "
                    f"ไว้แล้วครับ"
                )

        # ----------------------------------------------------
        # ถ้าแยกไม่ได้ ให้เก็บเป็น note
        # ----------------------------------------------------

        try:

            self.memory.add_note(
                value
            )

            return (
                "รับทราบครับ "
                "ผมบันทึกข้อมูลนี้ไว้แล้วครับ"
            )

        except Exception as e:

            return (
                f"ไม่สามารถบันทึกความจำได้ครับ: {e}"
            )

    # ========================================================
    # REMEMBER PREFERENCE
    # ========================================================

    def _remember_preference(
        self,
        text,
        key
    ):

        value = text.strip()

        prefixes = [
            "ฉันไม่ชอบ",
            "ผมไม่ชอบ",
            "ฉันชอบ",
            "ผมชอบ",
        ]

        matched = None

        for prefix in prefixes:

            if value.lower().startswith(
                prefix.lower()
            ):

                matched = prefix

                break

        if matched:

            value = value[
                len(matched):
            ].strip()

        if not value:

            return (
                "ต้องการให้ผมจำความชอบอะไรครับ"
            )

        self.memory.remember(
            key,
            value
        )

        if "ไม่ชอบ" in matched:

            return (
                f"รับทราบครับ "
                f"ผมจะจำไว้ว่าคุณไม่ชอบ "
                f"{value} ครับ"
            )

        return (
            f"รับทราบครับ "
            f"ผมจะจำไว้ว่าคุณชอบ "
            f"{value} ครับ"
        )

    # ========================================================
    # FORGET
    # ========================================================

    def _forget_text(self, text):

        value = text.strip()

        prefixes = [
            "ลบความจำ",
            "ลืม",
            "forget",
        ]

        for prefix in prefixes:

            if value.lower().startswith(
                prefix.lower()
            ):

                value = value[
                    len(prefix):
                ].strip()

                break

        if not value:

            return (
                "ต้องการให้ผมลืมเรื่องอะไรครับ"
            )

        try:

            result = self.memory.forget(
                value
            )

            if result:

                return (
                    f"เรียบร้อยครับ "
                    f"ผมลืมเรื่อง {value} แล้วครับ"
                )

            return (
                f"ผมไม่พบข้อมูล {value} "
                f"ในความจำครับ"
            )

        except Exception as e:

            return (
                f"ไม่สามารถลบความจำได้ครับ: {e}"
            )

    # ========================================================
    # EXTRACT PREFIX
    # ========================================================

    def _extract_after_prefix(
        self,
        text,
        prefixes
    ):

        value = text.strip()

        for prefix in prefixes:

            if value.lower().startswith(
                prefix.lower()
            ):

                return value[
                    len(prefix):
                ].strip()

        return ""

    # ========================================================
    # STATUS
    # ========================================================

    def status(self):

        try:

            return self.memory.status()

        except Exception as e:

            return (
                f"MEMORY OFFLINE\nERROR: {e}"
            )