# ============================================================
# JARVIS COMMAND ROUTER v2.0
# Fast / Stable / Extensible Router
# ============================================================

import time


class CommandRouter:

    VERSION = "2.0.0"

    def __init__(self, registry):

        self.registry = registry

        self.last_skill = None
        self.last_command = ""
        self.last_duration_ms = 0.0

        print(
            f"[JARVIS ROUTER] Router v{self.VERSION} initialized."
        )

    # ========================================================
    # NORMALIZE
    # ========================================================

    def normalize(self, text):

        if text is None:
            return ""

        text = str(text).strip()

        if not text:
            return ""

        # Normalize repeated spaces
        text = " ".join(text.split())

        return text

    # ========================================================
    # SKILL PRIORITY
    # ========================================================

    def _get_skill_order(self):

        skills = list(
            self.registry.skills.items()
        )

        # Known fast-path skills first.
        priority = {
            "Voice": 10,
            "Windows": 20,
            "System": 30,
            "Memory": 40,
            "ImageGeneration": 50,
        }

        skills.sort(
            key=lambda item: priority.get(
                item[0],
                100
            )
        )

        return skills

    # ========================================================
    # ROUTE
    # ========================================================

    def route(self, text):

        text = self.normalize(text)

        if not text:
            return None

        self.last_command = text

        # ----------------------------------------------------
        # Fast skill lookup
        # ----------------------------------------------------

        for name, skill in self._get_skill_order():

            try:

                handler = getattr(
                    skill,
                    "can_handle",
                    None
                )

                if handler is None:
                    continue

                if handler(text):

                    self.last_skill = name

                    print(
                        "[JARVIS ROUTER] "
                        f"Route -> {name}"
                    )

                    return skill

            except Exception as e:

                print(
                    "[JARVIS ROUTER] "
                    f"Skill check error "
                    f"[{name}]: {e}"
                )

        self.last_skill = None

        return None

    # ========================================================
    # EXECUTE
    # ========================================================

    def execute(self, text):

        start = time.perf_counter()

        text = self.normalize(text)

        if not text:
            return None

        skill = self.route(text)

        if skill is None:

            self.last_duration_ms = (
                (time.perf_counter() - start)
                * 1000
            )

            return None

        try:

            execute = getattr(
                skill,
                "execute",
                None
            )

            if execute is None:

                print(
                    "[JARVIS ROUTER] "
                    f"Skill [{self.last_skill}] "
                    "has no execute()"
                )

                return None

            result = execute(text)

            self.last_duration_ms = (
                (time.perf_counter() - start)
                * 1000
            )

            print(
                "[JARVIS ROUTER] "
                f"Executed {self.last_skill} "
                f"in {self.last_duration_ms:.1f} ms"
            )

            return result

        except Exception as e:

            self.last_duration_ms = (
                (time.perf_counter() - start)
                * 1000
            )

            print(
                "[JARVIS ROUTER] "
                f"Execution error "
                f"[{self.last_skill}]: {e}"
            )

            return (
                f"ไม่สามารถทำคำสั่งได้ครับ: {e}"
            )

    # ========================================================
    # STATUS
    # ========================================================

    def status(self):

        return (
            f"ROUTER ONLINE\n"
            f"VERSION: {self.VERSION}\n"
            f"SKILLS: {self.registry.count()} ACTIVE\n"
            f"LAST SKILL: "
            f"{self.last_skill or 'NONE'}\n"
            f"LAST ROUTE TIME: "
            f"{self.last_duration_ms:.1f} ms"
        )


# ============================================================
# FACTORY
# ============================================================

def create_router(registry):

    return CommandRouter(
        registry
    )