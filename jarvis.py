import ollama
import pyttsx3
import speech_recognition as sr

import webbrowser
import subprocess
import datetime
import os
import re
import difflib
import platform
import json


# =========================================================
# J.A.R.V.I.S CONFIG
# =========================================================

MODEL = "qwen3:8b"


# =========================================================
# CONVERSATION
# =========================================================

conversation = [
    {
        "role": "system",
        "content": """
คุณคือ J.A.R.V.I.S ผู้ช่วย AI บน Windows

บุคลิก:
- สุภาพ
- ฉลาด
- ใจเย็น
- ตอบกระชับ
- มีอารมณ์ขันเล็กน้อย
- ถ้าผู้ใช้พูดภาษาไทย ให้ตอบภาษาไทย
- ถ้าผู้ใช้พูดภาษาอังกฤษ ให้ตอบภาษาอังกฤษ

คุณกำลังทำงานอยู่บนคอมพิวเตอร์ Windows
และมีระบบ Python สำหรับควบคุม Windows

สำคัญ:
คำสั่งเปิดโปรแกรม ตรวจสเปค และควบคุมระบบ
จะถูกจัดการโดย Python ก่อนส่งมาถึง AI

ดังนั้นอย่าบอกผู้ใช้ว่าคุณไม่สามารถเปิดโปรแกรมได้
"""
    }
]


# =========================================================
# TEXT TO SPEECH
# =========================================================

try:

    engine = pyttsx3.init()

    engine.setProperty(
        "rate",
        175
    )

    engine.setProperty(
        "volume",
        1.0
    )

except Exception:

    engine = None


def speak(text):

    print(f"\nJARVIS: {text}")

    if engine:

        try:

            engine.say(text)
            engine.runAndWait()

        except Exception:

            pass


# =========================================================
# VOICE INPUT
# =========================================================

def listen():

    recognizer = sr.Recognizer()

    try:

        with sr.Microphone() as source:

            print("\n🎤 กำลังฟัง...")

            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.5
            )

            audio = recognizer.listen(
                source,
                timeout=5,
                phrase_time_limit=10
            )

        text = recognizer.recognize_google(
            audio,
            language="th-TH"
        )

        print(
            f"YOU: {text}"
        )

        return text

    except sr.WaitTimeoutError:

        print(
            "หมดเวลารอเสียง"
        )

    except sr.UnknownValueError:

        print(
            "ไม่เข้าใจเสียง"
        )

    except sr.RequestError:

        print(
            "ระบบรู้จำเสียงมีปัญหา"
        )

    except Exception as e:

        print(
            f"Voice Error: {e}"
        )

    return ""


# =========================================================
# CLEAN COMMAND
# =========================================================

def clean_command(command):

    command = command.lower().strip()

    wake_words = [

        "hello jarvis",
        "hey jarvis",
        "hi jarvis",
        "ok jarvis",
        "okay jarvis",
        "jarvis",

        "จาวิส",
        "เจวิส",
        "จาร์วิส"
    ]

    for word in wake_words:

        command = command.replace(
            word,
            ""
        )

    return command.strip()


# =========================================================
# EXTRACT APP NAME
# =========================================================

def extract_app_name(command):

    command = clean_command(
        command
    )

    remove_words = [

        "เปิด",
        "open",
        "launch",
        "start",
        "run",

        "โปรแกรม",
        "แอป",
        "แอพ",

        "ให้หน่อย",
        "หน่อย",
        "ที",
        "ด้วย",

        "please",
        "for me"
    ]

    for word in remove_words:

        command = command.replace(
            word,
            " "
        )

    command = re.sub(
        r"[^\w\s\-.+#]",
        " ",
        command,
        flags=re.UNICODE
    )

    command = re.sub(
        r"\s+",
        " ",
        command
    ).strip()

    return command


# =========================================================
# WINDOWS START MENU SHORTCUTS
# =========================================================

def get_start_menu_apps():

    apps = []

    start_menu_paths = [

        os.path.expandvars(
            r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"
        ),

        os.path.expandvars(
            r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs"
        )
    ]

    for base_path in start_menu_paths:

        if not os.path.exists(
            base_path
        ):
            continue

        for root, dirs, files in os.walk(
            base_path
        ):

            for file in files:

                if file.lower().endswith(
                    ".lnk"
                ):

                    full_path = os.path.join(
                        root,
                        file
                    )

                    app_name = os.path.splitext(
                        file
                    )[0]

                    apps.append(
                        {
                            "name": app_name,
                            "path": full_path
                        }
                    )

    return apps


# =========================================================
# WINDOWS START APPS
# =========================================================

def get_windows_apps():

    apps = []

    try:

        result = subprocess.run(

            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-StartApps | ConvertTo-Json -Compress"
            ],

            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode != 0:

            return apps

        output = result.stdout.strip()

        if not output:

            return apps

        data = json.loads(
            output
        )

        if isinstance(
            data,
            dict
        ):

            data = [
                data
            ]

        for item in data:

            name = item.get(
                "Name",
                ""
            )

            app_id = item.get(
                "AppID",
                ""
            )

            if name:

                apps.append(
                    {
                        "name": name,
                        "appid": app_id
                    }
                )

    except Exception as e:

        print(
            f"Windows App Search Error: {e}"
        )

    return apps


# =========================================================
# SEARCH APPLICATION
# =========================================================

def search_application(
    app_name
):

    print(
        f"\n🔎 กำลังค้นหาโปรแกรม: {app_name}"
    )

    start_apps = get_start_menu_apps()

    windows_apps = get_windows_apps()

    candidates = []

    # -----------------------------------------------------
    # START MENU
    # -----------------------------------------------------

    for app in start_apps:

        candidates.append(
            {
                "name": app["name"],
                "type": "shortcut",
                "path": app["path"]
            }
        )

    # -----------------------------------------------------
    # WINDOWS APPS
    # -----------------------------------------------------

    for app in windows_apps:

        candidates.append(
            {
                "name": app["name"],
                "type": "windows",
                "appid": app.get(
                    "appid",
                    ""
                )
            }
        )

    if not candidates:

        return None

    query = app_name.lower().strip()

    # -----------------------------------------------------
    # EXACT MATCH
    # -----------------------------------------------------

    for app in candidates:

        name = app["name"].lower().strip()

        if name == query:

            return app

    # -----------------------------------------------------
    # CONTAINS MATCH
    # -----------------------------------------------------

    contains_matches = []

    for app in candidates:

        name = app["name"].lower()

        if query in name:

            contains_matches.append(
                app
            )

    if contains_matches:

        contains_matches.sort(
            key=lambda x: len(
                x["name"]
            )
        )

        return contains_matches[0]

    # -----------------------------------------------------
    # FUZZY MATCH
    # -----------------------------------------------------

    names = [
        app["name"]
        for app in candidates
    ]

    matches = difflib.get_close_matches(

        app_name,
        names,

        n=1,

        cutoff=0.45
    )

    if matches:

        best_name = matches[0]

        for app in candidates:

            if app["name"] == best_name:

                return app

    return None


# =========================================================
# OPEN APPLICATION
# =========================================================

def open_application(
    app_name
):

    app = search_application(
        app_name
    )

    if not app:

        return False

    print(
        f"✓ พบโปรแกรม: {app['name']}"
    )

    # -----------------------------------------------------
    # SHORTCUT
    # -----------------------------------------------------

    if app["type"] == "shortcut":

        try:

            os.startfile(
                app["path"]
            )

            speak(
                f"พบ {app['name']} แล้วครับ กำลังเปิดให้"
            )

            return True

        except Exception as e:

            print(
                f"เปิดโปรแกรมไม่สำเร็จ: {e}"
            )

    # -----------------------------------------------------
    # WINDOWS APP
    # -----------------------------------------------------

    if app["type"] == "windows":

        try:

            appid = app.get(
                "appid",
                ""
            )

            if appid:

                subprocess.Popen(
                    [
                        "explorer.exe",
                        f"shell:AppsFolder\\{appid}"
                    ]
                )

                speak(
                    f"กำลังเปิด {app['name']} ครับ"
                )

                return True

        except Exception as e:

            print(
                f"Windows App Error: {e}"
            )

    return False


# =========================================================
# OPEN WEBSITE
# =========================================================

def open_website(
    command
):

    command = command.lower()

    # GOOGLE

    if (

        "google" in command

        and
        (
            "open" in command
            or "เปิด" in command
        )

    ):

        webbrowser.open(
            "https://www.google.com"
        )

        speak(
            "เปิด Google ให้แล้วครับ"
        )

        return True

    # YOUTUBE

    if (

        "youtube" in command

        and
        (
            "open" in command
            or "เปิด" in command
        )

    ):

        webbrowser.open(
            "https://www.youtube.com"
        )

        speak(
            "เปิด YouTube ให้แล้วครับ"
        )

        return True

    return False


# =========================================================
# SYSTEM SPECIFICATIONS
# =========================================================

def get_system_specs():

    try:

        # -------------------------------------------------
        # OS
        # -------------------------------------------------

        windows_version = platform.platform()

        # -------------------------------------------------
        # ARCHITECTURE
        # -------------------------------------------------

        architecture = platform.machine()

        # -------------------------------------------------
        # CPU
        # -------------------------------------------------

        cpu = platform.processor()

        if not cpu:

            cpu = "ไม่ทราบ"

        # -------------------------------------------------
        # PYTHON
        # -------------------------------------------------

        python_version = platform.python_version()

        # -------------------------------------------------
        # RAM
        # -------------------------------------------------

        ram_gb = "ไม่ทราบ"

        try:

            result = subprocess.run(

                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)"
                ],

                capture_output=True,
                text=True,
                timeout=10
            )

            if result.stdout.strip():

                ram_gb = result.stdout.strip()

        except Exception:

            pass

        # -------------------------------------------------
        # GPU
        # -------------------------------------------------

        gpu_name = "ไม่ทราบ"

        gpu_vram = "ไม่ทราบ"

        try:

            result = subprocess.run(

                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM | ConvertTo-Json -Compress"
                ],

                capture_output=True,
                text=True,
                timeout=10
            )

            if result.stdout.strip():

                gpu_data = json.loads(
                    result.stdout
                )

                if isinstance(
                    gpu_data,
                    dict
                ):

                    gpu_data = [
                        gpu_data
                    ]

                for gpu in gpu_data:

                    name = gpu.get(
                        "Name",
                        ""
                    )

                    if name:

                        gpu_name = name

                        adapter_ram = gpu.get(
                            "AdapterRAM"
                        )

                        if adapter_ram:

                            gpu_vram = round(
                                adapter_ram /
                                (1024 ** 3),
                                1
                            )

                        break

        except Exception:

            pass

        # -------------------------------------------------
        # STORAGE
        # -------------------------------------------------

        drives = []

        try:

            powershell_disk_command = """

            Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" |

            Select-Object DeviceID,

            @{Name="SizeGB";Expression={[math]::Round($_.Size/1GB,1)}},

            @{Name="FreeGB";Expression={[math]::Round($_.FreeSpace/1GB,1)}} |

            ConvertTo-Json -Compress

            """

            result = subprocess.run(

                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    powershell_disk_command
                ],

                capture_output=True,
                text=True,
                timeout=10
            )

            if result.stdout.strip():

                disk_data = json.loads(
                    result.stdout
                )

                if isinstance(
                    disk_data,
                    dict
                ):

                    disk_data = [
                        disk_data
                    ]

                for disk in disk_data:

                    drives.append(

                        f"{disk.get('DeviceID', '?')} "
                        f"{disk.get('FreeGB', '?')} GB free / "
                        f"{disk.get('SizeGB', '?')} GB"

                    )

        except Exception:

            pass

        # -------------------------------------------------
        # DISPLAY
        # -------------------------------------------------

        print()

        print(
            "=" * 55
        )

        print(
            "             JARVIS SYSTEM SPECS"
        )

        print(
            "=" * 55
        )

        print(
            f"OS           : {windows_version}"
        )

        print(
            f"Architecture : {architecture}"
        )

        print(
            f"CPU          : {cpu}"
        )

        print(
            f"RAM          : {ram_gb} GB"
        )

        print(
            f"GPU          : {gpu_name}"
        )

        print(
            f"VRAM         : {gpu_vram} GB"
        )

        print(
            f"Python       : {python_version}"
        )

        if drives:

            print()
            print(
                "Storage:"
            )

            for drive in drives:

                print(
                    f"  {drive}"
                )

        print(
            "=" * 55
        )

        # -------------------------------------------------
        # VOICE
        # -------------------------------------------------

        speak(
            f"""
ตรวจสอบสเปคเครื่องเรียบร้อยครับ

ซีพียู {cpu}

แรม {ram_gb} กิกะไบต์

การ์ดจอ {gpu_name}

วีแรมประมาณ {gpu_vram} กิกะไบต์

Python เวอร์ชัน {python_version}
"""
        )

        return True

    except Exception as e:

        print(
            f"System Spec Error: {e}"
        )

        speak(
            "ขออภัยครับ ไม่สามารถอ่านข้อมูลสเปคเครื่องได้"
        )

        return False


# =========================================================
# SYSTEM COMMAND
# =========================================================

def system_command(
    text
):

    command = clean_command(
        text
    )

    # -----------------------------------------------------
    # EXIT
    # -----------------------------------------------------

    exit_words = [

        "exit",
        "quit",
        "close jarvis",

        "ปิดจาวิส",
        "ปิดเจวิส",

        "ออก"
    ]

    for word in exit_words:

        if word in command:

            speak(
                "รับทราบครับ แล้วพบกันใหม่"
            )

            return "exit"

    # -----------------------------------------------------
    # SYSTEM SPECS
    # -----------------------------------------------------

    spec_words = [

        "สเปคคอม",
        "สเปคเครื่อง",
        "สเปคคอมพิวเตอร์",

        "สเปคคอมเครื่องนี้",

        "spec คอม",
        "spec computer",

        "computer specs",
        "system specs",

        "system information",
        "computer information",

        "my pc specs",
        "pc specs"
    ]

    if any(
        word in command
        for word in spec_words
    ):

        get_system_specs()

        return True

    # -----------------------------------------------------
    # WEBSITE
    # -----------------------------------------------------

    if open_website(
        command
    ):

        return True

    # -----------------------------------------------------
    # TIME
    # -----------------------------------------------------

    if (

        "เวลา" in command

        or
        "กี่โมง" in command

        or
        "what time" in command

    ):

        now = datetime.datetime.now()

        speak(
            f"ตอนนี้เวลา {now.strftime('%H:%M')} นาฬิกาครับ"
        )

        return True

    # -----------------------------------------------------
    # DATE
    # -----------------------------------------------------

    if (

        "วันนี้วันที่" in command

        or
        "วันที่เท่าไหร่" in command

        or
        "date" in command

    ):

        now = datetime.datetime.now()

        speak(
            f"วันนี้วันที่ {now.strftime('%d/%m/%Y')} ครับ"
        )

        return True

    # -----------------------------------------------------
    # OPEN APPLICATION
    # -----------------------------------------------------

    open_words = [

        "เปิด",
        "open",
        "launch",
        "start",
        "run"
    ]

    is_open_command = any(

        word in command

        for word in open_words
    )

    if is_open_command:

        app_name = extract_app_name(
            command
        )

        if app_name:

            success = open_application(
                app_name
            )

            if success:

                return True

            speak(
                f"ผมหาโปรแกรม {app_name} ไม่พบครับ"
            )

            return True

    return False


# =========================================================
# ASK QWEN
# =========================================================

def ask_jarvis(
    text
):

    conversation.append(

        {
            "role": "user",
            "content": text
        }

    )

    try:

        response = ollama.chat(

            model=MODEL,

            messages=conversation

        )

        answer = response[
            "message"
        ][
            "content"
        ]

        conversation.append(

            {
                "role": "assistant",
                "content": answer
            }

        )

        return answer

    except Exception as e:

        return (
            f"เกิดข้อผิดพลาดในการเชื่อมต่อ AI: {e}"
        )


# =========================================================
# PROCESS COMMAND
# =========================================================

def process_command(
    text
):

    result = system_command(
        text
    )

    if result == "exit":

        return "exit"

    if result is True:

        return True

    # -----------------------------------------------------
    # ASK AI
    # -----------------------------------------------------

    answer = ask_jarvis(
        text
    )

    speak(
        answer
    )

    return True


# =========================================================
# VOICE MODE
# =========================================================

def voice_mode():

    speak(
        "เข้าสู่โหมดเสียงแล้วครับ"
    )

    while True:

        command = listen()

        if not command:

            continue

        cleaned = clean_command(
            command
        )

        if (

            "กลับโหมดข้อความ" in cleaned

            or
            "back to text" in cleaned

        ):

            speak(
                "กลับสู่โหมดข้อความครับ"
            )

            return

        result = process_command(
            command
        )

        if result == "exit":

            raise SystemExit


# =========================================================
# TEXT MODE
# =========================================================

def text_mode():

    print()

    print(
        "=" * 40
    )

    print(
        "             TEXT MODE"
    )

    print(
        "=" * 40
    )

    print(
        "พิมพ์คำสั่งเพื่อคุยกับ JARVIS"
    )

    print()

    print(
        "voice = เข้าโหมดเสียง"
    )

    print(
        "exit  = ปิด JARVIS"
    )

    print(
        "=" * 40
    )

    while True:

        try:

            text = input(
                "\nYOU > "
            ).strip()

        except KeyboardInterrupt:

            print()

            speak(
                "ปิดระบบครับ"
            )

            break

        if not text:

            continue

        if text.lower() == "voice":

            voice_mode()

            continue

        result = process_command(
            text
        )

        if result == "exit":

            break


# =========================================================
# MAIN
# =========================================================

def main():

    print()

    print(
        "=" * 40
    )

    print(
        "           J.A.R.V.I.S"
    )

    print(
        "=" * 40
    )

    print()

    print(
        "AI Engine : Ollama"
    )

    print(
        "Model     :",
        MODEL
    )

    print(
        "GPU       : RTX 4060"
    )

    print(
        "Input     : Keyboard + Microphone"
    )

    print()

    print(
        "=" * 40
    )

    print()

    print(
        "กำลังตรวจสอบ Ollama..."
    )

    try:

        ollama.list()

        print(
            "✓ Ollama พร้อมใช้งาน"
        )

    except Exception as e:

        print(
            "✗ Ollama ไม่พร้อมใช้งาน"
        )

        print(
            e
        )

        return

    print()

    speak(
        "ระบบ JARVIS พร้อมใช้งานครับ"
    )

    text_mode()


# =========================================================
# START JARVIS
# =========================================================

if __name__ == "__main__":

    main()