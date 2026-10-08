# JARVIS VOICE LISTENER v2.2
# Native Windows Audio + FFmpeg DirectShow
# Wake Word + Command Retry

import os
import subprocess
import tempfile
import threading
import time

import speech_recognition as sr


class VoiceListener:
    VERSION = "2.2.0"

    MICROPHONE = "Microphone (2- Usb Audio Device)"
    WAKE_WORDS = [
        "จาร์วิส",
        "จาวิส",
        "jarvis",
    ]

    def __init__(self, agent=None):
        self.agent = agent

        self.running = False
        self.thread = None
        self.listening = False

        print("[JARVIS LISTENER] Native Windows Audio Mode v2.2")
        print(f"[JARVIS LISTENER] Microphone: {self.MICROPHONE}")

    # ---------------------------------------------------------
    # FFMPEG
    # ---------------------------------------------------------

    def _find_ffmpeg(self):
        candidates = [
            "ffmpeg.exe",
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        ]

        for path in candidates:
            if os.path.isabs(path):
                if os.path.exists(path):
                    return path
            else:
                try:
                    result = subprocess.run(
                        ["where.exe", path],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    if result.returncode == 0:
                        lines = result.stdout.strip().splitlines()
                        if lines:
                            return lines[0].strip()
                except Exception:
                    pass

        # WinGet FFmpeg
        winget_root = os.path.expandvars(
            r"%LOCALAPPDATA%\Microsoft\WinGet\Packages"
        )

        if os.path.exists(winget_root):
            for root, dirs, files in os.walk(winget_root):
                if "ffmpeg.exe" in files:
                    return os.path.join(root, "ffmpeg.exe")

        return None

    # ---------------------------------------------------------
    # MICROPHONE
    # ---------------------------------------------------------

    def microphone_available(self):
        ffmpeg = self._find_ffmpeg()

        if not ffmpeg:
            print("[JARVIS LISTENER] FFmpeg not found")
            return False

        print(
            f"[JARVIS LISTENER] Microphone OK: "
            f"{self.MICROPHONE}"
        )

        return True

    # ---------------------------------------------------------
    # RECORD AUDIO
    # ---------------------------------------------------------

    def _record_audio(self, seconds=6):
        ffmpeg = self._find_ffmpeg()

        if not ffmpeg:
            print("[JARVIS LISTENER] FFmpeg unavailable")
            return None

        output = os.path.join(
            tempfile.gettempdir(),
            "jarvis_listener.wav"
        )

        try:
            command = [
                ffmpeg,

                "-y",
                "-hide_banner",
                "-loglevel",
                "error",

                "-f",
                "dshow",

                "-i",
                f"audio={self.MICROPHONE}",

                "-t",
                str(seconds),

                "-ac",
                "1",

                "-ar",
                "16000",

                "-c:a",
                "pcm_s16le",

                output
            ]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=seconds + 10
            )

            if result.returncode != 0:
                print(
                    "[JARVIS LISTENER] Recording error:",
                    result.stderr.strip()
                )
                return None

            if not os.path.exists(output):
                print("[JARVIS LISTENER] Audio file missing")
                return None

            return output

        except subprocess.TimeoutExpired:
            print("[JARVIS LISTENER] Recording timeout")
            return None

        except Exception as e:
            print("[JARVIS LISTENER] Record error:", e)
            return None

    # ---------------------------------------------------------
    # SPEECH RECOGNITION
    # ---------------------------------------------------------

    def _recognize_file(self, filename):
        if not filename or not os.path.exists(filename):
            return ""

        recognizer = sr.Recognizer()

        try:
            with sr.AudioFile(filename) as source:
                audio = recognizer.record(source)

            text = recognizer.recognize_google(
                audio,
                language="th-TH"
            )

            text = text.strip()

            if text:
                print(f"[JARVIS LISTENER] Heard: {text}")

            return text

        except sr.UnknownValueError:
            return ""

        except sr.RequestError as e:
            print(
                "[JARVIS LISTENER] Speech API error:",
                e
            )
            return ""

        except Exception as e:
            print(
                "[JARVIS LISTENER] Recognition error:",
                e
            )
            return ""

    # ---------------------------------------------------------
    # WAKE WORD
    # ---------------------------------------------------------

    def _contains_wake_word(self, text):
        if not text:
            return False

        text = text.lower().strip()

        for word in self.WAKE_WORDS:
            if word in text:
                return True

        return False

    # ---------------------------------------------------------
    # SPEAK ACKNOWLEDGEMENT
    # ---------------------------------------------------------

    def _say_ack(self):
        try:
            if self.agent and getattr(self.agent, "voice", None):
                self.agent.voice.speak(
                    "ครับ",
                    wait=True
                )
                return
        except Exception as e:
            print(
                "[JARVIS LISTENER] Voice ACK error:",
                e
            )

    # ---------------------------------------------------------
    # LISTEN FOR COMMAND
    # ---------------------------------------------------------

    def _listen_for_command(self):
        print(
            "[JARVIS LISTENER] Listening for command..."
        )

        # ให้ระบบเสียง "ครับ" จบก่อน
        time.sleep(0.4)

        # ลองสูงสุด 2 ครั้ง
        for attempt in range(1, 3):

            print(
                f"[JARVIS LISTENER] "
                f"Command attempt {attempt}/2"
            )

            filename = self._record_audio(
                seconds=7
            )

            if not filename:
                continue

            command = self._recognize_file(
                filename
            )

            if command:

                # ถ้า recognition จับ wake word ติดมาด้วย
                # ตัดคำว่า จาร์วิส ออก
                cleaned = command

                for wake in self.WAKE_WORDS:
                    cleaned = cleaned.replace(
                        wake,
                        ""
                    )

                cleaned = cleaned.strip()

                if cleaned:
                    print(
                        f"[JARVIS LISTENER] "
                        f"COMMAND: {cleaned}"
                    )

                    return cleaned

                # ได้ยินแค่ wake word
                print(
                    "[JARVIS LISTENER] "
                    "Only wake word detected"
                )

            if attempt == 1:
                print(
                    "[JARVIS LISTENER] "
                    "No command detected - retrying..."
                )

                time.sleep(0.3)

        print(
            "[JARVIS LISTENER] "
            "No command detected"
        )

        return None

    # ---------------------------------------------------------
    # WAKE UP
    # ---------------------------------------------------------

    def _wake_up(self):

        print(
            "[JARVIS LISTENER] "
            "JARVIS ACTIVATED"
        )

        self._say_ack()

        command = self._listen_for_command()

        if not command:
            return

        if self.agent:
            try:
                self.agent.handle(command)

            except Exception as e:
                print(
                    "[JARVIS LISTENER] "
                    f"Agent error: {e}"
                )

    # ---------------------------------------------------------
    # MAIN LOOP
    # ---------------------------------------------------------

    def _listen_loop(self):

        print(
            "[JARVIS LISTENER] "
            "Listening for wake word..."
        )

        while self.running:

            try:

                self.listening = True

                filename = self._record_audio(
                    seconds=5
                )

                self.listening = False

                if not filename:
                    time.sleep(1)
                    continue

                text = self._recognize_file(
                    filename
                )

                if not text:
                    continue

                if self._contains_wake_word(text):

                    print(
                        f"[JARVIS LISTENER] "
                        f"WAKE WORD: {text}"
                    )

                    self._wake_up()

                    # กันการจับเสียงซ้ำทันที
                    time.sleep(0.8)

            except Exception as e:

                self.listening = False

                print(
                    "[JARVIS LISTENER] "
                    f"Loop error: {e}"
                )

                time.sleep(1)

        self.listening = False

        print(
            "[JARVIS LISTENER] OFFLINE"
        )

    # ---------------------------------------------------------
    # START
    # ---------------------------------------------------------

    def start(self):

        if self.running:
            print(
                "[JARVIS LISTENER] "
                "Already running"
            )
            return False

        if not self.microphone_available():
            return False

        self.running = True

        self.thread = threading.Thread(
            target=self._listen_loop,
            daemon=True
        )

        self.thread.start()

        print(
            "[JARVIS LISTENER] ONLINE"
        )

        return True

    # ---------------------------------------------------------
    # STOP
    # ---------------------------------------------------------

    def stop(self):

        self.running = False

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3)

        self.thread = None
        self.listening = False

        print(
            "[JARVIS LISTENER] OFFLINE"
        )

        return True

    # ---------------------------------------------------------
    # TOGGLE
    # ---------------------------------------------------------

    def toggle(self):

        if self.running:
            return self.stop()

        return self.start()

    # ---------------------------------------------------------
    # STATUS
    # ---------------------------------------------------------

    def status(self):

        if self.running:
            if self.listening:
                return "VOICE LISTENER: LISTENING"

            return "VOICE LISTENER: ONLINE"

        return "VOICE LISTENER: OFFLINE"