# JARVIS VOICE LISTENER v3.0
# Realtime Native Windows Audio + FFmpeg PCM Stream
# Wake Word + Voice Activity Detection + Command Retry
#
# Preserves the public API used by GUI / Agent:
# start()
# stop()
# toggle()
# status()
# microphone_available()
# _record_audio()
# _recognize_file()

import os
import subprocess
import tempfile
import threading
import time
import audioop

import speech_recognition as sr


class VoiceListener:
    VERSION = "3.0.0"

    MICROPHONE = "Microphone (2- Usb Audio Device)"

    WAKE_WORDS = [
        "จาร์วิส",
        "จาวิส",
        "jarvis",
    ]

    # ---------------------------------------------------------
    # REALTIME AUDIO SETTINGS
    # ---------------------------------------------------------

    SAMPLE_RATE = 16000
    CHANNELS = 1
    SAMPLE_WIDTH = 2

    FRAME_MS = 100
    FRAME_BYTES = int(
        SAMPLE_RATE * SAMPLE_WIDTH * FRAME_MS / 1000
    )

    # เสียงที่ต่ำกว่าค่านี้ถือว่าเป็น silence
    ENERGY_THRESHOLD = 450

    # ต้องมีเสียงต่อเนื่องอย่างน้อยประมาณนี้
    MIN_SPEECH_MS = 180

    # หลังเสียงหยุด ให้รอเท่านี้ก่อนส่ง STT
    SILENCE_END_MS = 650

    # เก็บเสียงก่อนเริ่มพูดเล็กน้อย
    PRE_ROLL_MS = 300

    # จำกัดความยาว utterance
    MAX_UTTERANCE_MS = 8000

    # เวลารอ Google STT
    RECOGNITION_TIMEOUT = 12

    def __init__(self, agent=None):
        self.agent = agent

        self.running = False
        self.thread = None
        self.listening = False

        self.ffmpeg_process = None
        self.audio_lock = threading.Lock()

        self.last_error = ""
        self.last_text = ""

        print("[JARVIS LISTENER] Realtime Native Windows Audio v3.0")
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
                    return os.path.join(
                        root,
                        "ffmpeg.exe"
                    )

        return None

    # ---------------------------------------------------------
    # MICROPHONE
    # ---------------------------------------------------------

    def microphone_available(self):

        ffmpeg = self._find_ffmpeg()

        if not ffmpeg:
            print(
                "[JARVIS LISTENER] FFmpeg not found"
            )

            return False

        print(
            "[JARVIS LISTENER] Microphone OK:",
            self.MICROPHONE
        )

        return True

    # ---------------------------------------------------------
    # START REALTIME AUDIO STREAM
    # ---------------------------------------------------------

    def _start_audio_stream(self):

        with self.audio_lock:

            if self.ffmpeg_process:
                if self.ffmpeg_process.poll() is None:
                    return True

                self.ffmpeg_process = None

            ffmpeg = self._find_ffmpeg()

            if not ffmpeg:
                self.last_error = "FFmpeg not found"

                print(
                    "[JARVIS LISTENER]",
                    self.last_error
                )

                return False

            command = [
                ffmpeg,

                "-hide_banner",
                "-loglevel",
                "error",

                "-f",
                "dshow",

                "-i",
                f"audio={self.MICROPHONE}",

                "-ac",
                "1",

                "-ar",
                str(self.SAMPLE_RATE),

                "-f",
                "s16le",

                "pipe:1",
            ]

            try:

                self.ffmpeg_process = subprocess.Popen(
                    command,

                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,

                    bufsize=0,

                    creationflags=(
                        subprocess.CREATE_NO_WINDOW
                    )
                )

                print(
                    "[JARVIS LISTENER] "
                    "Realtime audio stream started"
                )

                return True

            except Exception as e:

                self.last_error = str(e)

                print(
                    "[JARVIS LISTENER] "
                    f"Audio stream error: {e}"
                )

                self.ffmpeg_process = None

                return False

    # ---------------------------------------------------------
    # STOP REALTIME AUDIO STREAM
    # ---------------------------------------------------------

    def _stop_audio_stream(self):

        with self.audio_lock:

            process = self.ffmpeg_process

            self.ffmpeg_process = None

        if not process:
            return

        try:

            if process.poll() is None:

                process.terminate()

                try:
                    process.wait(timeout=1.5)

                except subprocess.TimeoutExpired:

                    process.kill()

                    try:
                        process.wait(timeout=1)

                    except Exception:
                        pass

        except Exception as e:

            print(
                "[JARVIS LISTENER] "
                f"Audio stream cleanup error: {e}"
            )

        print(
            "[JARVIS LISTENER] "
            "Realtime audio stream stopped"
        )

    # ---------------------------------------------------------
    # READ AUDIO FRAME
    # ---------------------------------------------------------

    def _read_frame(self):

        process = self.ffmpeg_process

        if not process:
            return None

        try:

            data = process.stdout.read(
                self.FRAME_BYTES
            )

            if not data:
                return None

            if len(data) < self.FRAME_BYTES:
                return None

            return data

        except Exception as e:

            self.last_error = str(e)

            print(
                "[JARVIS LISTENER] "
                f"Audio read error: {e}"
            )

            return None

    # ---------------------------------------------------------
    # AUDIO ENERGY
    # ---------------------------------------------------------

    def _audio_energy(self, frame):

        if not frame:
            return 0

        try:

            return audioop.rms(
                frame,
                self.SAMPLE_WIDTH
            )

        except Exception:
            return 0

    # ---------------------------------------------------------
    # CAPTURE ONE UTTERANCE
    # ---------------------------------------------------------

    def _capture_utterance(self, timeout=8):

        if not self.ffmpeg_process:

            if not self._start_audio_stream():
                return None

        start_time = time.monotonic()

        speech_started = False

        speech_ms = 0
        silence_ms = 0

        audio_frames = []

        pre_roll = []

        max_pre_roll_frames = max(
            1,
            int(
                self.PRE_ROLL_MS /
                self.FRAME_MS
            )
        )

        while self.running:

            elapsed = (
                time.monotonic() -
                start_time
            )

            if elapsed >= timeout:
                break

            frame = self._read_frame()

            if frame is None:
                break

            energy = self._audio_energy(frame)

            is_speech = (
                energy >= self.ENERGY_THRESHOLD
            )

            # ---------------------------------------------
            # BEFORE SPEECH
            # ---------------------------------------------

            if not speech_started:

                pre_roll.append(frame)

                if len(pre_roll) > max_pre_roll_frames:
                    pre_roll.pop(0)

                if is_speech:

                    speech_started = True

                    audio_frames.extend(
                        pre_roll
                    )

                    pre_roll.clear()

                    speech_ms += self.FRAME_MS

                    silence_ms = 0

                continue

            # ---------------------------------------------
            # DURING SPEECH
            # ---------------------------------------------

            audio_frames.append(frame)

            if is_speech:

                speech_ms += self.FRAME_MS
                silence_ms = 0

            else:

                silence_ms += self.FRAME_MS

            # ---------------------------------------------
            # SPEECH END
            # ---------------------------------------------

            if (
                speech_ms >= self.MIN_SPEECH_MS
                and
                silence_ms >= self.SILENCE_END_MS
            ):

                break

            # ---------------------------------------------
            # MAX UTTERANCE
            # ---------------------------------------------

            if (
                speech_ms >= self.MAX_UTTERANCE_MS
            ):

                break

        if not audio_frames:
            return None

        if speech_ms < self.MIN_SPEECH_MS:
            return None

        return b"".join(audio_frames)

    # ---------------------------------------------------------
    # RECOGNIZE RAW PCM
    # ---------------------------------------------------------

    def _recognize_audio(self, raw_audio):

        if not raw_audio:
            return ""

        recognizer = sr.Recognizer()

        try:

            audio = sr.AudioData(
                raw_audio,
                self.SAMPLE_RATE,
                self.SAMPLE_WIDTH
            )

            text = recognizer.recognize_google(
                audio,
                language="th-TH"
            )

            text = text.strip()

            if text:

                self.last_text = text

                print(
                    "[JARVIS LISTENER] "
                    f"Heard: {text}"
                )

            return text

        except sr.UnknownValueError:

            return ""

        except sr.RequestError as e:

            self.last_error = str(e)

            print(
                "[JARVIS LISTENER] "
                f"Speech API error: {e}"
            )

            return ""

        except Exception as e:

            self.last_error = str(e)

            print(
                "[JARVIS LISTENER] "
                f"Recognition error: {e}"
            )

            return ""

    # ---------------------------------------------------------
    # LEGACY RECORD AUDIO
    # ---------------------------------------------------------
    # เก็บไว้เพื่อ compatibility กับระบบเดิม

    def _record_audio(self, seconds=6):

        ffmpeg = self._find_ffmpeg()

        if not ffmpeg:
            print(
                "[JARVIS LISTENER] "
                "FFmpeg unavailable"
            )

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
                    "[JARVIS LISTENER] "
                    "Recording error:",
                    result.stderr.strip()
                )

                return None

            if not os.path.exists(output):

                print(
                    "[JARVIS LISTENER] "
                    "Audio file missing"
                )

                return None

            return output

        except subprocess.TimeoutExpired:

            print(
                "[JARVIS LISTENER] "
                "Recording timeout"
            )

            return None

        except Exception as e:

            print(
                "[JARVIS LISTENER] "
                f"Record error: {e}"
            )

            return None

    # ---------------------------------------------------------
    # LEGACY FILE RECOGNITION
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

                self.last_text = text

                print(
                    "[JARVIS LISTENER] "
                    f"Heard: {text}"
                )

            return text

        except sr.UnknownValueError:

            return ""

        except sr.RequestError as e:

            print(
                "[JARVIS LISTENER] "
                "Speech API error:",
                e
            )

            return ""

        except Exception as e:

            print(
                "[JARVIS LISTENER] "
                "Recognition error:",
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
    # REMOVE WAKE WORD
    # ---------------------------------------------------------

    def _clean_command(self, text):

        if not text:
            return ""

        cleaned = text.lower().strip()

        for wake in self.WAKE_WORDS:

            cleaned = cleaned.replace(
                wake,
                ""
            )

        return cleaned.strip()

    # ---------------------------------------------------------
    # SPEAK ACK
    # ---------------------------------------------------------

    def _say_ack(self):

        try:

            if (
                self.agent
                and
                getattr(
                    self.agent,
                    "voice",
                    None
                )
            ):

                self.agent.voice.speak(
                    "ครับ",
                    wait=True
                )

                return True

        except Exception as e:

            print(
                "[JARVIS LISTENER] "
                f"Voice ACK error: {e}"
            )

        return False

    # ---------------------------------------------------------
    # LISTEN FOR COMMAND - REALTIME
    # ---------------------------------------------------------

    def _listen_for_command(self):

        print(
            "[JARVIS LISTENER] "
            "Listening for command..."
        )

        # ให้เสียง "ครับ" จบ
        time.sleep(0.15)

        for attempt in range(1, 3):

            if not self.running:
                return None

            print(
                "[JARVIS LISTENER] "
                f"Command attempt {attempt}/2"
            )

            raw_audio = self._capture_utterance(
                timeout=8
            )

            if not raw_audio:

                if attempt == 1:

                    print(
                        "[JARVIS LISTENER] "
                        "No speech detected - retrying..."
                    )

                    time.sleep(0.2)

                continue

            command = self._recognize_audio(
                raw_audio
            )

            if command:

                cleaned = self._clean_command(
                    command
                )

                if cleaned:

                    print(
                        "[JARVIS LISTENER] "
                        f"COMMAND: {cleaned}"
                    )

                    return cleaned

                print(
                    "[JARVIS LISTENER] "
                    "Only wake word detected"
                )

            if attempt == 1:

                print(
                    "[JARVIS LISTENER] "
                    "No command detected - retrying..."
                )

                time.sleep(0.2)

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

                self.agent.handle(
                    command
                )

            except Exception as e:

                print(
                    "[JARVIS LISTENER] "
                    f"Agent error: {e}"
                )

    # ---------------------------------------------------------
    # REALTIME MAIN LOOP
    # ---------------------------------------------------------

    def _listen_loop(self):

        print(
            "[JARVIS LISTENER] "
            "Starting realtime listener..."
        )

        if not self._start_audio_stream():

            self.running = False

            print(
                "[JARVIS LISTENER] "
                "Unable to start audio stream"
            )

            return

        print(
            "[JARVIS LISTENER] "
            "Listening for wake word..."
        )

        try:

            while self.running:

                self.listening = True

                raw_audio = self._capture_utterance(
                    timeout=10
                )

                self.listening = False

                if not self.running:
                    break

                if not raw_audio:
                    continue

                text = self._recognize_audio(
                    raw_audio
                )

                if not text:
                    continue

                if self._contains_wake_word(text):

                    print(
                        "[JARVIS LISTENER] "
                        f"WAKE WORD: {text}"
                    )

                    self._wake_up()

                    # กัน feedback / duplicate capture
                    time.sleep(0.25)

        except Exception as e:

            self.last_error = str(e)

            print(
                "[JARVIS LISTENER] "
                f"Loop error: {e}"
            )

        finally:

            self.listening = False

            self._stop_audio_stream()

            print(
                "[JARVIS LISTENER] "
                "OFFLINE"
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
            name="JARVIS-Realtime-Listener",
            daemon=True
        )

        self.thread.start()

        print(
            "[JARVIS LISTENER] "
            "ONLINE - REALTIME"
        )

        return True

    # ---------------------------------------------------------
    # STOP
    # ---------------------------------------------------------

    def stop(self):

        self.running = False

        self._stop_audio_stream()

        if (
            self.thread
            and
            self.thread.is_alive()
            and
            self.thread != threading.current_thread()
        ):

            self.thread.join(
                timeout=3
            )

        self.thread = None

        self.listening = False

        print(
            "[JARVIS LISTENER] "
            "OFFLINE"
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

                return (
                    "VOICE LISTENER: "
                    "REALTIME LISTENING"
                )

            return (
                "VOICE LISTENER: "
                "REALTIME ONLINE"
            )

        return "VOICE LISTENER: OFFLINE"
