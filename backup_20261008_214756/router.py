# ============================================================
# JARVIS COMMAND ROUTER v1.0
# ============================================================

class CommandRouter:

    def __init__(self, registry):

        self.registry = registry

    # ========================================================
    # ROUTE
    # ========================================================

    def route(self, text):

        if not text:

            return None

        text = text.strip()

        if not text:

            return None

        # ----------------------------------------------------
        # Try every registered skill
        # ----------------------------------------------------

        for name, skill in self.registry.skills.items():

            try:

                handler = getattr(
                    skill,
                    "can_handle",
                    None
                )

                if not handler:

                    continue

                if handler(text):

                    print(
                        "[JARVIS ROUTER] "
                        f"Route -> {name}"
                    )

                    return skill

            except Exception as e:

                print(
                    "[JARVIS ROUTER] "
                    f"Skill check error [{name}]: {e}"
                )

        return None

    # ========================================================
    # EXECUTE
    # ========================================================

    def execute(self, text):

        skill = self.route(text)

        if skill is None:

            return None

        try:

            execute = getattr(
                skill,
                "execute",
                None
            )

            if execute is None:

                return None

            return execute(text)

        except Exception as e:

            print(
                "[JARVIS ROUTER] "
                f"Execution error: {e}"
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
            f"SKILLS: {self.registry.count()} ACTIVE"
        )


# ============================================================
# FACTORY
# ============================================================

def create_router(registry):

    return CommandRouter(
        registry
    )