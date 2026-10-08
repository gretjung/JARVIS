# ============================================================
# JARVIS VOICE SKILL TEST
# ============================================================

from core.voice import Voice
from skills.voice import VoiceSkill


print()
print("=" * 60)
print("JARVIS VOICE SKILL TEST")
print("=" * 60)


voice = Voice()

skill = VoiceSkill(
    voice
)


# ============================================================
# TEST 1
# ============================================================

print()
print("[TEST] ตรวจสอบ Voice Skill")

print(
    "CAN HANDLE:",
    skill.can_handle("สถานะเสียง")
)

print(
    "RESULT:",
    skill.execute("สถานะเสียง")
)


# ============================================================
# TEST 2
# ============================================================

print()
print("[TEST] ทดสอบเสียง")

print(
    "CAN HANDLE:",
    skill.can_handle("ทดสอบเสียง")
)

result = skill.execute(
    "ทดสอบเสียง"
)

print(
    "RESULT:",
    result
)


# ============================================================
# WAIT
# ============================================================

voice.wait_until_finished()


print()
print("=" * 60)
print("VOICE SKILL TEST COMPLETE")
print("=" * 60)