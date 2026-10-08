# ============================================================
# JARVIS SKILL REGISTRY v1.0
# ============================================================

class SkillRegistry:

    def __init__(self):

        self.skills = {}

    # ========================================================
    # REGISTER
    # ========================================================

    def register(self, skill):

        name = getattr(
            skill,
            "name",
            skill.__class__.__name__
        )

        self.skills[name] = skill

        print(
            f"[JARVIS REGISTRY] "
            f"Skill registered: {name}"
        )

        return skill

    # ========================================================
    # UNREGISTER
    # ========================================================

    def unregister(self, name):

        if name in self.skills:

            del self.skills[name]

            print(
                f"[JARVIS REGISTRY] "
                f"Skill removed: {name}"
            )

            return True

        return False

    # ========================================================
    # GET
    # ========================================================

    def get(self, name):

        return self.skills.get(name)

    # ========================================================
    # HAS
    # ========================================================

    def has(self, name):

        return name in self.skills

    # ========================================================
    # COUNT
    # ========================================================

    def count(self):

        return len(self.skills)

    # ========================================================
    # LIST
    # ========================================================

    def list_skills(self):

        return list(
            self.skills.keys()
        )

    # ========================================================
    # STATUS
    # ========================================================

    def status(self):

        if not self.skills:

            return (
                "SKILLS: 0 ACTIVE"
            )

        lines = [
            "JARVIS SKILLS",
            "=============="
        ]

        for name, skill in self.skills.items():

            enabled = getattr(
                skill,
                "enabled",
                True
            )

            state = (
                "ONLINE"
                if enabled
                else "OFFLINE"
            )

            lines.append(
                f"{name:<20} {state}"
            )

        lines.append(
            "=============="
        )

        lines.append(
            f"TOTAL: {len(self.skills)} ACTIVE"
        )

        return "\n".join(lines)


# ============================================================
# GLOBAL REGISTRY
# ============================================================

registry = SkillRegistry()