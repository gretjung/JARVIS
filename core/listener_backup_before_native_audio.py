# ============================================================
# JARVIS VOICE LISTENER v1.0
# Wake Word + Voice Command
# ============================================================

import threading
import time
import speech_recognition as sr


class VoiceListener:

    def __init__(self, agent=None):

        self.agent = agent
        self.recognizer = sr.Recognizer()
        self.microphone = None

        self.running = False
        self.listening = False
        self.thread = None

        self.wake_words = (
            "jarvis",
            "จาร์วิส",
            "จาวิส",
        )

        try:
            self.microphone = sr.Microphone()

        except Exception as e:

            print(
                f"[JARVIS LISTENER] Microphone error: {e}"
            )

    def start(self):

        if self.running:
            return

        if self.microphone is None:

            print(
                "[JARVIS LISTENER] Microphone unavailable."
            )

            return

        self.running = True

        self.thread = threading.Thread(
            target=self._listen_loop,
            daemon=True
        )

        self.thread.start()

        print(
            "[JARVIS LISTENER] ONLINE"
        )

    def stop(self):

        self.running = False
        self.listening = False

        print(
            "[JARVIS LISTENER] OFFLINE"
        )

    def calibrate(self):

        if self.microphone is None:
            return

        try:

            print(
                "[JARVIS LISTENER] Calibrating microphone..."
            )

            with self.microphone as source:

                self.recognizer.adjust_for_ambient_noise(
                    source,
                    duration=1
                )

            print(
                "[JARVIS LISTENER] Microphone ready."
            )

        except Exception as e:

            print(
                f"[JARVIS LISTENER] Calibration error: {e}"
            )

    def _listen_loop(self):

        self.calibrate()

        while self.running:

            try:

                self.listening = True

                with self.microphone as source:

                    audio = self.recognizer.listen(
                        source,
                        timeout=2,
                        phrase_time_limit=5
                    )

                self.listening = False

                text = self._recognize(audio)

                if not text:
                    continue

                print(
                    f"[JARVIS LISTENER] HEARD: {text}"
                )

                if self._is_wake_word(text):

                    print(
                        "[JARVIS LISTENER] WAKE WORD DETECTED"
                    )

                    self._wake_up()

            except sr.WaitTimeoutError:

                self.listening = False

            except Exception as e:

                self.listening = False

                print(
                    f"[JARVIS LISTENER] Error: {e}"
                )

                time.sleep(1)

    def _recognize(self, audio):

        try:

            return self.recognizer.recognize_google(
                audio,
                language="th-TH"
            ).strip()

        except sr.UnknownValueError:

            return ""

        except sr.RequestError as e:

            print(
                f"[JARVIS LISTENER] Speech API error: {e}"
            )

            return ""

        except Exception as e:

            print(
                f"[JARVIS LISTENER] Recognition error: {e}"
            )

            return ""

    def _is_wake_word(self, text):

        lower = text.lower().strip()

        for word in self.wake_words:

            if word.lower() in lower:

                return True

        return False

    def _wake_up(self):

        if not self.running:
            return

        if self.agent and self.agent.voice:

            try:

                self.agent.voice.speak(
                    "ครับ",
                    wait=True
                )

            except Exception as e:

                print(
                    f"[JARVIS LISTENER] Voice error: {e}"
                )

        command = self._listen_command()

        if not command:
            return

        print(
            f"[JARVIS LISTENER] COMMAND: {command}"
        )

        if self.agent:

            try:

                self.agent.handle(
                    command
                )

            except Exception as e:

                print(
                    f"[JARVIS LISTENER] Agent error: {e}"
                )

    def _listen_command(self):

        try:

            print(
                "[JARVIS LISTENER] Listening for command..."
            )

            with self.microphone as source:

                audio = self.recognizer.listen(
                    source,
                    timeout=5,
                    phrase_time_limit=10
                )

            return self._recognize(audio)

        except sr.WaitTimeoutError:

            print(
                "[JARVIS LISTENER] Command timeout."
            )

            return ""

        except Exception as e:

            print(
                f"[JARVIS LISTENER] Command error: {e}"
            )

            return ""

    def status(self):

        if self.running:

            if self.listening:
                return "VOICE LISTENER: LISTENING"

            return "VOICE LISTENER: ONLINE"

        return "VOICE LISTENER: OFFLINE"


__all__ = [
    "VoiceListener"
]
