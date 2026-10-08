# ============================================================
# JARVIS AGENT v6.0
# Realtime / Async Ready / Streaming AI / Single Voice
# ============================================================

import threading
import time
import requests
from concurrent.futures import ThreadPoolExecutor


from core.identity import (
    JARVIS_NAME,
    JARVIS_VERSION,
    get_system_prompt,
)

from core.memory import memory
from core.registry import registry
from core.router import create_router

from skills.voice import VoiceSkill
from skills.windows import WindowsSkill
from skills.image_generation import ImageGenerationSkill
from skills.system import SystemSkill
from skills.memory import MemorySkill


class Agent:

    VERSION = "6.0.0"

    OLLAMA_URL = "http://127.0.0.1:11434"
    OLLAMA_CHAT_URL = (
        "http://127.0.0.1:11434/api/chat"
    )

    MODEL = "qwen3:8b"

    # Normal request timeout
    AI_TIMEOUT = 120

    # Connection check timeout
    STATUS_TIMEOUT = 3

    def __init__(self, voice=None):

        self.name = JARVIS_NAME
        self.version = JARVIS_VERSION
        self.model = self.MODEL

        self.voice = voice

        # ----------------------------------------------------
        # MEMORY
        # ----------------------------------------------------

        # Use global singleton.
        self.memory = memory

        # ----------------------------------------------------
        # CONVERSATION
        # ----------------------------------------------------

        self.conversation = []

        # ----------------------------------------------------
        # IMAGE
        # ----------------------------------------------------

        self.last_image_path = None

        # ----------------------------------------------------
        # REALTIME STATE
        # ----------------------------------------------------

        self.state = "ONLINE"

        self.busy = False

        self.last_command = ""

        self.last_response = ""

        self.last_error = ""

        self.last_duration_ms = 0.0

        self.request_id = 0

        self._cancel_event = threading.Event()

        self._state_lock = threading.RLock()

        self._conversation_lock = threading.RLock()

        self._busy_lock = threading.RLock()

        # ----------------------------------------------------
        # ASYNC EXECUTOR
        # ----------------------------------------------------

        self.executor = ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="JARVIS-Agent"
        )

        # ----------------------------------------------------
        # ROUTER
        # ----------------------------------------------------

        self.router = create_router(registry)

        self.register_skills()

        print(
            f"[JARVIS AGENT] Agent v{self.VERSION} initialized."
        )

    # ========================================================
    # SKILLS
    # ========================================================

    def register_skills(self):

        registry.skills.clear()

        self.voice_skill = VoiceSkill(self.voice)
        registry.register(self.voice_skill)

        self.windows_skill = WindowsSkill()
        registry.register(self.windows_skill)

        self.image_skill = ImageGenerationSkill()
        registry.register(self.image_skill)

        self.system_skill = SystemSkill()
        registry.register(self.system_skill)

        self.memory_skill = MemorySkill(self.memory)
        registry.register(self.memory_skill)

    # ========================================================
    # STATE
    # ========================================================

    def set_state(self, state):

        with self._state_lock:
            self.state = str(state)

        print(
            f"[JARVIS AGENT] STATE -> {self.state}"
        )

    def get_state(self):

        with self._state_lock:
            return self.state

    def is_busy(self):

        with self._busy_lock:
            return self.busy

    # ========================================================
    # BUSY CONTROL
    # ========================================================

    def _begin_request(self, text):

        with self._busy_lock:

            if self.busy:
                return False

            self.busy = True

        self._cancel_event.clear()

        self.request_id += 1

        self.last_command = text
        self.last_response = ""
        self.last_error = ""

        return True

    def _end_request(self):

        with self._busy_lock:
            self.busy = False

        if self.get_state() != "OFFLINE":
            self.set_state("ONLINE")

    # ========================================================
    # CANCEL
    # ========================================================

    def cancel(self):

        self._cancel_event.set()

        self.set_state("ONLINE")

        print(
            "[JARVIS AGENT] Cancellation requested."
        )

        return True

    # ========================================================
    # VOICE
    # ========================================================

    def speak(self, text):

        if not self.voice:
            return

        if not text:
            return

        try:

            self.set_state("SPEAKING")

            self.voice.speak(
                text,
                wait=False
            )

        except Exception as e:

            print(
                f"[JARVIS VOICE] Error: {e}"
            )

        finally:

            if not self.is_busy():
                self.set_state("ONLINE")

    # ========================================================
    # OLLAMA STATUS
    # ========================================================

    def ollama_status(self):

        try:

            response = requests.get(
                f"{self.OLLAMA_URL}/api/tags",
                timeout=self.STATUS_TIMEOUT
            )

            return response.status_code == 200

        except Exception:

            return False

    # ========================================================
    # SYSTEM STATUS
    # ========================================================

    def system_status(self):

        ollama = self.ollama_status()

        voice = self.voice is not None

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
            f"AGENT         : {self.VERSION}\n"
            f"STATE         : {self.get_state()}\n"
            f"BUSY          : "
            f"{'YES' if self.is_busy() else 'NO'}\n"
            "=================================================="
        )

    # ========================================================
    # MEMORY CONTEXT
    # ========================================================

    def _build_memory_context(self):

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

        facts = self.memory.data.get(
            "facts",
            {}
        )

        if facts:

            memory_context += (
                "\nKNOWN USER FACTS:\n"
            )

            for key, item in facts.items():

                if isinstance(item, dict):

                    value = item.get(
                        "value",
                        ""
                    )

                else:

                    value = str(item)

                memory_context += (
                    f"{key}: {value}\n"
                )

        return memory_context

    # ========================================================
    # CLEAN THINK TAGS
    # ========================================================

    def _clean_ai_answer(self, answer):

        if not answer:
            return ""

        answer = str(answer)

        while "<think>" in answer:

            start = answer.find(
                "<think>"
            )

            end = answer.find(
                "</think>",
                start
            )

            if end == -1:
                answer = answer[:start]
                break

            answer = (
                answer[:start]
                + answer[end + 8:]
            )

        return answer.strip()

    # ========================================================
    # SAVE CONVERSATION
    # ========================================================

    def _save_conversation(
        self,
        user_text,
        answer
    ):

        with self._conversation_lock:

            self.conversation.append(
                {
                    "role": "user",
                    "content": user_text
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

        self.memory.add_conversation(
            "user",
            user_text
        )

        self.memory.add_conversation(
            "assistant",
            answer
        )

    # ========================================================
    # AI REQUEST - NORMAL
    # ========================================================

    def ask_ai(self, text):

        if not self.ollama_status():

            return (
                "Ollama ไม่ออนไลน์ครับ"
            )

        self.set_state("THINKING")

        memory_context = (
            self._build_memory_context()
        )

        system_prompt = (
            get_system_prompt()
            + "\n\n"
            + memory_context
        )

        with self._conversation_lock:

            history = list(
                self.conversation[-12:]
            )

        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        messages.extend(history)

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

        start = time.perf_counter()

        try:

            response = requests.post(
                self.OLLAMA_CHAT_URL,
                json=payload,
                timeout=self.AI_TIMEOUT
            )

            response.raise_for_status()

            data = response.json()

            answer = (
                data
                .get("message", {})
                .get("content", "")
                .strip()
            )

            answer = self._clean_ai_answer(
                answer
            )

            self.last_duration_ms = (
                (
                    time.perf_counter()
                    - start
                )
                * 1000
            )

            self._save_conversation(
                text,
                answer
            )

            return answer

        except requests.Timeout:

            self.last_error = (
                "Ollama request timeout"
            )

            print(
                "[JARVIS AI] Ollama timeout."
            )

            return (
                "AI ใช้เวลานานเกินไปครับ"
            )

        except Exception as e:

            self.last_error = str(e)

            print(
                f"[JARVIS AI] Error: {e}"
            )

            return (
                f"AI Core เกิดข้อผิดพลาดครับ: {e}"
            )

    # ========================================================
    # AI REQUEST - STREAMING
    # ========================================================

    def ask_ai_stream(
        self,
        text,
        on_token=None
    ):

        if not self.ollama_status():

            answer = (
                "Ollama ไม่ออนไลน์ครับ"
            )

            if on_token:
                on_token(answer)

            return answer

        self.set_state("THINKING")

        memory_context = (
            self._build_memory_context()
        )

        system_prompt = (
            get_system_prompt()
            + "\n\n"
            + memory_context
        )

        with self._conversation_lock:

            history = list(
                self.conversation[-12:]
            )

        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        messages.extend(history)

        messages.append(
            {
                "role": "user",
                "content": text
            }
        )

        payload = {
            "model": self.model,
            "stream": True,
            "messages": messages,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9
            }
        }

        answer_parts = []

        start = time.perf_counter()

        try:

            with requests.post(
                self.OLLAMA_CHAT_URL,
                json=payload,
                stream=True,
                timeout=self.AI_TIMEOUT
            ) as response:

                response.raise_for_status()

                for line in response.iter_lines(
                    decode_unicode=True
                ):

                    if self._cancel_event.is_set():

                        print(
                            "[JARVIS AI] "
                            "Streaming cancelled."
                        )

                        break

                    if not line:
                        continue

                    try:

                        import json

                        data = json.loads(line)

                    except Exception:

                        continue

                    token = (
                        data
                        .get("message", {})
                        .get("content", "")
                    )

                    if not token:
                        continue

                    answer_parts.append(
                        token
                    )

                    if on_token:

                        try:

                            on_token(token)

                        except Exception as callback_error:

                            print(
                                "[JARVIS AI] "
                                f"Token callback error: "
                                f"{callback_error}"
                            )

            answer = "".join(
                answer_parts
            )

            answer = self._clean_ai_answer(
                answer
            )

            self.last_duration_ms = (
                (
                    time.perf_counter()
                    - start
                )
                * 1000
            )

            if answer:

                self._save_conversation(
                    text,
                    answer
                )

            return answer

        except requests.Timeout:

            self.last_error = (
                "Ollama stream timeout"
            )

            print(
                "[JARVIS AI] "
                "Ollama stream timeout."
            )

            return (
                "AI ใช้เวลานานเกินไปครับ"
            )

        except Exception as e:

            self.last_error = str(e)

            print(
                f"[JARVIS AI] "
                f"Streaming error: {e}"
            )

            return (
                f"AI Core เกิดข้อผิดพลาดครับ: {e}"
            )

    # ========================================================
    # CORE HANDLE
    # ========================================================

    def _handle_internal(
        self,
        text,
        speak=True,
        stream=False,
        on_token=None
    ):

        if not text:
            return ""

        text = str(text).strip()

        if not text:
            return ""

        print(
            f"\n[JARVIS] USER: {text}"
        )

        if not self._begin_request(text):

            print(
                "[JARVIS] Agent is busy."
            )

            return (
                "JARVIS กำลังทำงานอยู่ครับ"
            )

        start = time.perf_counter()

        try:

            # ------------------------------------------------
            # ROUTER / SKILLS FIRST
            # ------------------------------------------------

            self.set_state("EXECUTING")

            try:

                result = self.router.execute(
                    text
                )

            except Exception as e:

                print(
                    "[JARVIS ROUTER] "
                    f"Error: {e}"
                )

                result = None

            # ------------------------------------------------
            # SKILL RESULT
            # ------------------------------------------------

            if result is not None:

                result = str(result)

                print(
                    f"[JARVIS] RESPONSE: {result}"
                )

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

                self.last_response = result

                self.last_duration_ms = (
                    (
                        time.perf_counter()
                        - start
                    )
                    * 1000
                )

                if speak:

                    self.speak(result)

                return result

            # ------------------------------------------------
            # AI CORE
            # ------------------------------------------------

            print(
                "[JARVIS] No Skill matched. "
                "Sending to AI Core..."
            )

            if stream:

                answer = self.ask_ai_stream(
                    text,
                    on_token=on_token
                )

            else:

                answer = self.ask_ai(
                    text
                )

            self.last_response = answer

            print(
                f"[JARVIS] RESPONSE: {answer}"
            )

            if speak and answer:

                self.speak(answer)

            return answer

        except Exception as e:

            self.last_error = str(e)

            print(
                f"[JARVIS AGENT] "
                f"Error: {e}"
            )

            answer = (
                f"JARVIS เกิดข้อผิดพลาดครับ: {e}"
            )

            self.last_response = answer

            if speak:

                self.speak(answer)

            return answer

        finally:

            self.last_duration_ms = (
                (
                    time.perf_counter()
                    - start
                )
                * 1000
            )

            self._end_request()

    # ========================================================
    # PUBLIC HANDLE
    # ========================================================

    def handle(self, text):

        return self._handle_internal(
            text,
            speak=True,
            stream=False
        )

    # ========================================================
    # ASYNC HANDLE
    # ========================================================

    def handle_async(
        self,
        text,
        callback=None,
        stream=True
    ):

        def worker():

            result = self._handle_internal(
                text,
                speak=True,
                stream=stream,
                on_token=callback
            )

            if callback:

                try:

                    callback(
                        None,
                        result
                    )

                except Exception as e:

                    print(
                        "[JARVIS AGENT] "
                        f"Callback error: {e}"
                    )

            return result

        try:

            return self.executor.submit(
                worker
            )

        except Exception as e:

            print(
                "[JARVIS AGENT] "
                f"Async submit error: {e}"
            )

            return None

    # ========================================================
    # STATUS
    # ========================================================

    def status(self):

        return (
            "\n"
            "==================================================\n"
            "JARVIS AGENT STATUS\n"
            "==================================================\n"
            f"VERSION       : {self.VERSION}\n"
            f"MODEL         : {self.model}\n"
            f"STATE         : {self.get_state()}\n"
            f"BUSY          : "
            f"{'YES' if self.is_busy() else 'NO'}\n"
            f"LAST COMMAND  : "
            f"{self.last_command or 'NONE'}\n"
            f"LAST TIME     : "
            f"{self.last_duration_ms:.1f} ms\n"
            f"SKILLS        : "
            f"{registry.count()} ACTIVE\n"
            f"OLLAMA        : "
            f"{'ONLINE' if self.ollama_status() else 'OFFLINE'}\n"
            "=================================================="
        )

    # ========================================================
    # SHUTDOWN
    # ========================================================

    def shutdown(self):

        print(
            "[JARVIS AGENT] "
            "Shutting down..."
        )

        self.cancel()

        try:

            self.executor.shutdown(
                wait=False,
                cancel_futures=True
            )

        except Exception as e:

            print(
                "[JARVIS AGENT] "
                f"Shutdown error: {e}"
            )

        self.set_state("OFFLINE")

        print(
            "[JARVIS AGENT] OFFLINE"
        )
