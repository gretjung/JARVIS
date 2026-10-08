# -*- coding: utf-8 -*-

import asyncio
import os
import re
import tempfile
import threading
import winsound

try:
    from winsdk.windows.media.speechsynthesis import SpeechSynthesizer
    from winsdk.windows.storage.streams import DataReader
    WINSDK_OK = True
except Exception as e:
    SpeechSynthesizer = None
    DataReader = None
    WINSDK_OK = False
    print(f"[JARVIS VOICE] WinSDK load error: {e}")


class Voice:
    def __init__(self):
        self.enabled = True
        self.rate = 0
        self.volume = 100
        self.current_voice = None
        self.speaking = False
        self._stop_event = threading.Event()
        self._thread = None

        self.thai_voice = None
        self.english_voice = None

        self._scan_voices()

    # =========================================================
    # VOICE SCAN
    # =========================================================

    def _scan_voices(self):
        if not WINSDK_OK:
            print("[JARVIS VOICE] WinSDK unavailable.")
            return

        try:
            voices = SpeechSynthesizer.all_voices

            for v in voices:
                name = getattr(v, "display_name", "") or ""
                language = getattr(v, "language", "") or ""

                print(f"[JARVIS VOICE] Found: {name} | {language}")

                # Thai
                if (
                    "th-th" in language.lower()
                    or "thai" in name.lower()
                    or "pattara" in name.lower()
                ):
                    if self.thai_voice is None or "pattara" in name.lower():
                        self.thai_voice = v

                # English
                if language.lower().startswith("en-"):
                    if self.english_voice is None:
                        self.english_voice = v

                    lname = name.lower()

                    if "david" in lname or "mark" in lname:
                        self.english_voice = v

            if self.thai_voice:
                print(
                    f"[JARVIS VOICE] Thai voice: "
                    f"{self.thai_voice.display_name}"
                )

            if self.english_voice:
                print(
                    f"[JARVIS VOICE] English voice: "
                    f"{self.english_voice.display_name}"
                )

        except Exception as e:
            print(f"[JARVIS VOICE] Voice scan error: {e}")

    # =========================================================
    # TEXT CLEAN
    # =========================================================

    def remove_emojis(self, text):
        return re.sub(
            r"[\U00010000-\U0010ffff]",
            "",
            text
        )

    def clean_text(self, text):
        if not text:
            return ""

        text = str(text)

        # Code blocks
        text = re.sub(r"```.*?```", "", text, flags=re.S)

        # URLs
        text = re.sub(r"https?://\S+", "", text)

        # Windows paths
        text = re.sub(r"[A-Za-z]:\\[^\n]+", "", text)

        # Image path markers
        text = re.sub(r"IMAGE_PATH\s*:\s*[^\n]+", "", text)

        # Markdown links
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

        # Markdown headings
        text = re.sub(r"^\s*#+\s*", "", text, flags=re.M)

        # Bullets
        text = re.sub(r"^\s*[-*•]\s*", "", text, flags=re.M)

        # Numbered lists
        text = re.sub(r"^\s*\d+\.\s*", "", text, flags=re.M)

        # Markdown symbols
        text = re.sub(r"[*_`~]", "", text)

        # UI symbols
        text = re.sub(r"[▶►▼▲◆◇●○■□★☆✓✔✕✖⚡]", "", text)

        # Emoji
        text = self.remove_emojis(text)

        # Repeated punctuation
        text = re.sub(r"([!?.,])\1+", r"\1", text)

        # Spaces
        text = re.sub(r"[ \t]+", " ", text)

        # Empty lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    # =========================================================
    # LANGUAGE
    # =========================================================

    def _is_thai(self, text):
        return bool(re.search(r"[\u0E00-\u0E7F]", text))

    def _select_voice(self, text):
        if self._is_thai(text):
            return self.thai_voice
        return self.english_voice or self.thai_voice

    # =========================================================
    # SPEECH
    # =========================================================

    def speak(self, text, wait=False):
        if not self.enabled:
            return

        text = self.clean_text(text)

        if not text:
            return

        self.stop()

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._speak_worker,
            args=(text,),
            daemon=False
        )

        self._thread.start()

        if wait:
            self._thread.join()

    def _speak_worker(self, text):
        self.speaking = True

        try:
            voice = self._select_voice(text)

            if voice is None:
                print("[JARVIS VOICE] No suitable voice found.")
                return

            self.current_voice = voice

            asyncio.run(
                self._synthesize_and_play(
                    text,
                    voice
                )
            )

        except Exception as e:
            print(f"[JARVIS VOICE] Error: {e}")

        finally:
            self.speaking = False

    async def _synthesize_and_play(self, text, voice):
        if self._stop_event.is_set():
            return

        synthesizer = SpeechSynthesizer()

        # IMPORTANT:
        # winsdk Python API uses voice property, not Voice
        synthesizer.voice = voice

        # IMPORTANT:
        # Python winsdk uses snake_case
        stream = await synthesizer.synthesize_text_to_stream_async(text)

        if self._stop_event.is_set():
            return

        size = stream.size

        reader = DataReader(stream.get_input_stream_at(0))

        await reader.load_async(size)

        data = reader.read_buffer(size)

        # Convert buffer to bytes
        from ctypes import string_at, addressof

        try:
            raw = bytes(data)
        except Exception:
            raw = bytes(
                string_at(
                    addressof(data),
                    size
                )
            )

        if self._stop_event.is_set():
            return

        fd, wav_path = tempfile.mkstemp(
            suffix=".wav",
            prefix="jarvis_voice_"
        )

        os.close(fd)

        try:
            with open(wav_path, "wb") as f:
                f.write(raw)

            if self._stop_event.is_set():
                return

            winsound.PlaySound(
                wav_path,
                winsound.SND_FILENAME
            )

        finally:
            try:
                os.remove(wav_path)
            except Exception:
                pass

    # =========================================================
    # CONTROL
    # =========================================================

    def stop(self):
        self._stop_event.set()

        if self.speaking:
            try:
                winsound.PlaySound(
                    None,
                    winsound.SND_PURGE
                )
            except Exception:
                pass

    def enable(self):
        self.enabled = True
        return "VOICE: ON"

    def disable(self):
        self.stop()
        self.enabled = False
        return "VOICE: OFF"

    def toggle(self):
        if self.enabled:
            return self.disable()
        return self.enable()

    def status(self):
        if not self.enabled:
            return "VOICE: OFF"

        if self.speaking:
            return "VOICE: SPEAKING"

        return "VOICE: ONLINE"

    def voice_status(self):
        thai = (
            self.thai_voice.display_name
            if self.thai_voice
            else "Not found"
        )

        english = (
            self.english_voice.display_name
            if self.english_voice
            else "Not found"
        )

        return (
            f"VOICE: {self.status()}\n"
            f"THAI: {thai}\n"
            f"ENGLISH: {english}"
        )

    # =========================================================
    # VOICE SELECTION
    # =========================================================

    def select_thai_voice(self):
        self._scan_voices()

        if self.thai_voice:
            return (
                f"Thai voice selected: "
                f"{self.thai_voice.display_name}"
            )

        return "Thai voice not found."

    def select_english_voice(self):
        self._scan_voices()

        if self.english_voice:
            return (
                f"English voice selected: "
                f"{self.english_voice.display_name}"
            )

        return "English voice not found."

    # =========================================================
    # SETTINGS
    # =========================================================

    def set_rate(self, rate):
        try:
            self.rate = max(-10, min(10, int(rate)))
            return f"Voice rate: {self.rate}"
        except Exception:
            return "Invalid voice rate."

    def set_volume(self, volume):
        try:
            self.volume = max(0, min(100, int(volume)))
            return f"Voice volume: {self.volume}"
        except Exception:
            return "Invalid voice volume."

    # =========================================================
    # TEST
    # =========================================================

    def test_voice(self):
        message = "สวัสดีครับ ผมคือจาร์วิส พร้อมทำงานแล้วครับ"

        print("[JARVIS] Voice test started.")

        self.speak(
            message,
            wait=False
        )

        return "VOICE TEST STARTED"

    def wait_until_finished(self):
        if self._thread and self._thread.is_alive():
            self._thread.join()


# Global voice instance
voice = Voice()