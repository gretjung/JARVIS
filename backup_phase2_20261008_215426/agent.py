# ============================================================
# JARVIS AGENT v5.1
# Single Voice Output
# ============================================================

import requests

from core.identity import (
    JARVIS_NAME,
    JARVIS_VERSION,
    get_system_prompt,
)

from core.memory import Memory
from core.registry import registry
from core.router import create_router

from skills.voice import VoiceSkill
from skills.windows import WindowsSkill
from skills.image_generation import ImageGenerationSkill
from skills.system import SystemSkill
from skills.memory import MemorySkill


class Agent:

    def __init__(self, voice=None):

        self.name = JARVIS_NAME
        self.version = JARVIS_VERSION
        self.model = "qwen3:8b"

        self.voice = voice

        self.conversation = []

        self.last_image_path = None

        # -------------------------------------------------
        # MEMORY
        # -------------------------------------------------

        self.memory = Memory()

        # -------------------------------------------------
        # ROUTER
        # -------------------------------------------------

        self.router = create_router(registry)

        self.register_skills()

        print(
            f"[JARVIS AGENT] Agent v5.1 initialized."
        )

    # =====================================================
    # SKILLS
    # =====================================================

    def register_skills(self):

        registry.skills.clear()

        # VOICE
        self.voice_skill = VoiceSkill(
            self.voice
        )

        registry.register(
            self.voice_skill
        )

        # WINDOWS
        self.windows_skill = WindowsSkill()

        registry.register(
            self.windows_skill
        )

        # IMAGE
        self.image_skill = ImageGenerationSkill()

        registry.register(
            self.image_skill
        )

        # SYSTEM
        self.system_skill = SystemSkill()

        registry.register(
            self.system_skill
        )

        # MEMORY
        self.memory_skill = MemorySkill(
            self.memory
        )

        registry.register(
            self.memory_skill
        )

    # =====================================================
    # VOICE
    # =====================================================

    def speak(self, text):

        if not self.voice:
            return

        if not text:
            return

        try:

            self.voice.speak(
                text,
                wait=False
            )

        except Exception as e:

            print(
                f"[JARVIS VOICE] Error: {e}"
            )

    # =====================================================
    # OLLAMA
    # =====================================================

    def ollama_status(self):

        try:

            response = requests.get(
                "http://127.0.0.1:11434/api/tags",
                timeout=3
            )

            return response.status_code == 200

        except Exception:

            return False

    # =====================================================
    # SYSTEM STATUS
    # =====================================================

    def system_status(self):

        ollama = self.ollama_status()

        voice = (
            self.voice is not None
        )

        return (
            "\n"
            "==================================================\n"
            "JARVIS SYSTEM STATUS\n"
            "==================================================\n"
            f"AI CORE       : "
            f"{'ONLINE' if ollama else 'OFFLINE'}\n"
            "IDENTITY      : ONLINE\n"
            f"VOICE         : "
            f"{'ONLINE' if voice else 'OFFLINE'}\n"
            "MEMORY        : ONLINE\n"
            "ROUTER        : ONLINE\n"
            f"SKILLS        : "
            f"{registry.count()} ACTIVE\n"
            "VISUAL CORE   : ONLINE\n"
            "=================================================="
        )

    # =====================================================
    # AI
    # =====================================================

    def ask_ai(self, text):

        if not self.ollama_status():

            return (
                "Ollama ไม่ออนไลน์ครับ"
            )

        # -------------------------------------------------
        # Memory context
        # -------------------------------------------------

        memory_context = ""

        recent_memory = (
            self.memory.get_recent_conversation(8)
        )

        if recent_memory:

            memory_context += (
                "\nRECENT MEMORY:\n"
            )

            for item in recent_memory:

                role = item.get(
                    "role",
                    ""
                )

                content = item.get(
                    "content",
                    ""
                )

                memory_context += (
                    f"{role}: {content}\n"
                )

        # -------------------------------------------------
        # Facts
        # -------------------------------------------------

        facts = self.memory.data.get(
            "facts",
            {}
        )

        if facts:

            memory_context += (
                "\nKNOWN USER FACTS:\n"
            )

            for key, item in facts.items():

                if isinstance(
                    item,
                    dict
                ):

                    value = item.get(
                        "value",
                        ""
                    )

                else:

                    value = str(item)

                memory_context += (
                    f"{key}: {value}\n"
                )

        # -------------------------------------------------
        # System prompt
        # -------------------------------------------------

        system_prompt = (
            get_system_prompt()
            + "\n\n"
            + memory_context
        )

        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        messages.extend(
            self.conversation[-12:]
        )

        messages.append(
            {
                "role": "user",
                "content": text
            }
        )

        payload = {

            "model": self.model,

            "stream": False,

            "messages": messages,

            "options": {
                "temperature": 0.7,
                "top_p": 0.9
            }
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
                .get(
                    "message",
                    {}
                )
                .get(
                    "content",
                    ""
                )
                .strip()
            )

            # -------------------------------------------------
            # Remove Qwen thinking
            # -------------------------------------------------

            if "<think>" in answer:

                start = answer.find(
                    "<think>"
                )

                end = answer.find(
                    "</think>"
                )

                if end != -1:

                    answer = (
                        answer[:start]
                        +
                        answer[end + 8:]
                    ).strip()

            # -------------------------------------------------
            # Conversation
            # -------------------------------------------------

            self.conversation.append(
                {
                    "role": "user",
                    "content": text
                }
            )

            self.conversation.append(
                {
                    "role": "assistant",
                    "content": answer
                }
            )

            self.conversation = (
                self.conversation[-20:]
            )

            # -------------------------------------------------
            # Persistent memory
            # -------------------------------------------------

            self.memory.add_conversation(
                "user",
                text
            )

            self.memory.add_conversation(
                "assistant",
                answer
            )

            return answer

        except Exception as e:

            print(
                f"[JARVIS AI] Error: {e}"
            )

            return (
                f"AI Core เกิดข้อผิดพลาดครับ: {e}"
            )

    # =====================================================
    # HANDLE
    # =====================================================

    def handle(self, text):

        if not text:
            return ""

        text = text.strip()

        if not text:
            return ""

        print(
            f"\n[JARVIS] USER: {text}"
        )

        # -------------------------------------------------
        # ROUTER
        # -------------------------------------------------

        try:

            result = self.router.execute(
                text
            )

        except Exception as e:

            print(
                f"[JARVIS ROUTER] Error: {e}"
            )

            result = None

        # -------------------------------------------------
        # SKILL RESPONSE
        # -------------------------------------------------

        if result is not None:

            print(
                f"[JARVIS] RESPONSE: {result}"
            )

            # -------------------------------------------------
            # IMAGE PATH
            # -------------------------------------------------

            if "IMAGE_PATH:" in result:

                try:

                    path = (
                        result
                        .split(
                            "IMAGE_PATH:",
                            1
                        )[1]
                        .strip()
                        .splitlines()[0]
                        .strip()
                    )

                    self.last_image_path = path

                except Exception:

                    pass

            # -------------------------------------------------
            # SINGLE VOICE OUTPUT
            # -------------------------------------------------

            self.speak(result)

            return result

        # -------------------------------------------------
        # AI FALLBACK
        # -------------------------------------------------

        print(
            "[JARVIS] No Skill matched. "
            "Sending to AI Core..."
        )

        answer = self.ask_ai(
            text
        )

        print(
            f"[JARVIS] RESPONSE: {answer}"
        )

        # -------------------------------------------------
        # SINGLE VOICE OUTPUT
        # -------------------------------------------------

        self.speak(answer)

        return answer