# ============================================================
# JARVIS ROUTER TEST
# ============================================================

from core.registry import registry
from core.router import create_router
from skills.system import SystemSkill


print()
print("=" * 60)
print("JARVIS ROUTER TEST")
print("=" * 60)


# ============================================================
# REGISTER SKILL
# ============================================================

registry.register(
    SystemSkill()
)


# ============================================================
# CREATE ROUTER
# ============================================================

router = create_router(
    registry
)


# ============================================================
# STATUS
# ============================================================

print()
print(
    registry.status()
)

print()

print(
    router.status()
)


# ============================================================
# TEST COMMAND
# ============================================================

print()
print(
    "[TEST] ทดสอบ skill"
)

result = router.execute(
    "ทดสอบ skill"
)

print(
    "[RESULT]",
    result
)


# ============================================================
# TEST UNKNOWN
# ============================================================

print()
print(
    "[TEST] คำสั่งที่ไม่มี Skill"
)

result = router.execute(
    "สวัสดี JARVIS"
)

print(
    "[RESULT]",
    result
)


print()
print("=" * 60)
print("ROUTER TEST COMPLETE")
print("=" * 60)