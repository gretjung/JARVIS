import os
import re
import json
import subprocess
import difflib
import platform

import psutil


# =========================================================
# JARVIS WINDOWS CONTROL
# =========================================================

START_MENU_PATHS = [
    os.path.expandvars(
        r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"
    ),
    os.path.expandvars(
        r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs"
    ),
]


# =========================================================
# NORMALIZE APP NAME
# =========================================================

def normalize_name(name):
    """
    ทำให้ชื่อแอปอยู่ในรูปแบบที่ค้นหาได้ง่าย
    """

    if not name:
        return ""

    name = name.lower().strip()

    # ตัดคำสั่งที่ผู้ใช้อาจพิมพ์ติดมาด้วย
    prefixes = [
        "ให้หน่อย",
        "ด้วย",
        "ที",
        "ครับ",
        "ค่ะ",
        "please",
        "now",
    ]

    for prefix in prefixes:
        name = name.replace(prefix, "")

    # ลบอักขระพิเศษ
    name = re.sub(r"[^\wก-๙\s.-]", "", name)

    # รวมช่องว่าง
    name = re.sub(r"\s+", " ", name).strip()

    return name


# =========================================================
# START MENU APPS
# =========================================================

def scan_start_menu():

    apps = []

    for base_path in START_MENU_PATHS:

        if not os.path.exists(base_path):
            continue

        for root, dirs, files in os.walk(base_path):

            for file in files:

                if not file.lower().endswith(".lnk"):
                    continue

                full_path = os.path.join(
                    root,
                    file
                )

                app_name = os.path.splitext(file)[0]

                apps.append({
                    "name": app_name,
                    "path": full_path,
                    "type": "lnk"
                })

    return apps


# =========================================================
# WINDOWS STORE / UWP APPS
# =========================================================

def scan_windows_apps():

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

        if not result.stdout.strip():
            return apps

        data = json.loads(result.stdout)

        if isinstance(data, dict):
            data = [data]

        for item in data:

            name = item.get("Name")
            app_id = item.get("AppID")

            if not name or not app_id:
                continue

            apps.append({
                "name": name,
                "path": app_id,
                "type": "uwp"
            })

    except Exception:
        pass

    return apps


# =========================================================
# ALL WINDOWS APPS
# =========================================================

def get_all_apps():

    apps = []

    apps.extend(
        scan_start_menu()
    )

    apps.extend(
        scan_windows_apps()
    )

    # ลบชื่อซ้ำ
    unique = {}

    for app in apps:

        key = (
            app["name"].lower(),
            app["type"]
        )

        unique[key] = app

    return list(
        unique.values()
    )


# =========================================================
# ROBLOX
# =========================================================

def open_roblox():

    # -----------------------------------------------------
    # วิธีที่ 1: Roblox Protocol
    # -----------------------------------------------------

    try:

        os.startfile(
            "roblox-player:"
        )

        return (
            "กำลังเปิด Roblox ครับ"
        )

    except Exception:
        pass


    # -----------------------------------------------------
    # วิธีที่ 2: ค้นหา RobloxPlayerBeta.exe
    # -----------------------------------------------------

    search_paths = [

        os.path.expandvars(
            r"%LOCALAPPDATA%\Roblox"
        ),

        os.path.expandvars(
            r"%PROGRAMFILES%\Roblox"
        ),

        os.path.expandvars(
            r"%PROGRAMFILES(X86)%\Roblox"
        ),

    ]


    for base_path in search_paths:

        if not os.path.exists(base_path):
            continue

        try:

            for root, dirs, files in os.walk(base_path):

                for file in files:

                    if file.lower() == "robloxplayerbeta.exe":

                        full_path = os.path.join(
                            root,
                            file
                        )

                        try:

                            subprocess.Popen(
                                [full_path],
                                cwd=root
                            )

                            return (
                                "กำลังเปิด Roblox ครับ"
                            )

                        except Exception:
                            pass

        except Exception:
            pass


    return (
        "ไม่พบ Roblox ในเครื่องครับ"
    )


# =========================================================
# MATCH APP
# =========================================================

def find_app(name):

    target = normalize_name(name)

    if not target:
        return None


    apps = get_all_apps()


    if not apps:
        return None


    # -----------------------------------------------------
    # Exact Match
    # -----------------------------------------------------

    for app in apps:

        app_name = normalize_name(
            app["name"]
        )

        if app_name == target:

            return app


    # -----------------------------------------------------
    # Target อยู่ในชื่อแอป
    # -----------------------------------------------------

    contains_matches = []

    for app in apps:

        app_name = normalize_name(
            app["name"]
        )

        if target in app_name:

            contains_matches.append(
                app
            )


    if contains_matches:

        # เลือกชื่อที่สั้นที่สุด
        contains_matches.sort(
            key=lambda x: len(
                x["name"]
            )
        )

        return contains_matches[0]


    # -----------------------------------------------------
    # Target หลักอยู่ในชื่อ
    # -----------------------------------------------------

    target_words = target.split()

    for app in apps:

        app_name = normalize_name(
            app["name"]
        )

        if all(
            word in app_name
            for word in target_words
        ):

            return app


    # -----------------------------------------------------
    # Fuzzy Match
    # -----------------------------------------------------

    names = [
        normalize_name(
            app["name"]
        )
        for app in apps
    ]


    matches = difflib.get_close_matches(
        target,
        names,
        n=1,
        cutoff=0.45
    )


    if matches:

        matched_name = matches[0]

        for app in apps:

            if normalize_name(
                app["name"]
            ) == matched_name:

                return app


    return None


# =========================================================
# OPEN APP
# =========================================================

def open_app(name):

    original_name = name

    name = normalize_name(
        name
    )


    if not name:

        return (
            "ไม่ทราบว่าต้องการเปิดอะไรครับ"
        )


    # =====================================================
    # ROBLOX SPECIAL CASE
    # =====================================================

    roblox_words = [
        "roblox",
        "roblo",
        "roblx",
        "โรบล็อก",
        "โรบอก",
        "โรบลอก",
    ]


    if any(
        word in name
        for word in roblox_words
    ):

        return open_roblox()


    # =====================================================
    # GOOGLE
    # =====================================================

    if name in [
        "google",
        "กูเกิล",
        "กูเกิ้ล",
    ]:

        try:

            import webbrowser

            webbrowser.open(
                "https://www.google.com"
            )

            return (
                "กำลังเปิด Google ครับ"
            )

        except Exception as error:

            return (
                f"เปิด Google ไม่สำเร็จครับ: {error}"
            )


    # =====================================================
    # YOUTUBE
    # =====================================================

    if name in [
        "youtube",
        "ยูทูบ",
        "ยูทูป",
    ]:

        try:

            import webbrowser

            webbrowser.open(
                "https://www.youtube.com"
            )

            return (
                "กำลังเปิด YouTube ครับ"
            )

        except Exception as error:

            return (
                f"เปิด YouTube ไม่สำเร็จครับ: {error}"
            )


    # =====================================================
    # CHROME
    # =====================================================

    chrome_paths = [

        os.path.expandvars(
            r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"
        ),

        os.path.expandvars(
            r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"
        ),

        os.path.expandvars(
            r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
        ),

    ]


    if name in [
        "chrome",
        "google chrome",
        "โครม",
        "กูเกิลโครม",
    ]:

        for chrome in chrome_paths:

            if os.path.exists(chrome):

                try:

                    subprocess.Popen(
                        [chrome]
                    )

                    return (
                        "กำลังเปิด Google Chrome ครับ"
                    )

                except Exception:
                    pass


    # =====================================================
    # WINDOWS APP SEARCH
    # =====================================================

    app = find_app(
        name
    )


    if app:

        try:

            # ------------------------------------------------
            # .LNK
            # ------------------------------------------------

            if app["type"] == "lnk":

                os.startfile(
                    app["path"]
                )

                return (
                    f"กำลังเปิด {app['name']} ครับ"
                )


            # ------------------------------------------------
            # UWP / Windows App
            # ------------------------------------------------

            if app["type"] == "uwp":

                subprocess.Popen(
                    [
                        "explorer.exe",
                        f"shell:AppsFolder\\{app['path']}"
                    ]
                )

                return (
                    f"กำลังเปิด {app['name']} ครับ"
                )


        except Exception as error:

            return (
                f"พบ {app['name']} แล้ว "
                f"แต่เปิดไม่ได้ครับ: {error}"
            )


    # =====================================================
    # COMMON EXE FALLBACK
    # =====================================================

    common_apps = {

        "notepad": "notepad.exe",

        "notepad++": "notepad++.exe",

        "calculator": "calc.exe",
        "เครื่องคิดเลข": "calc.exe",

        "paint": "mspaint.exe",

        "explorer": "explorer.exe",
        "file explorer": "explorer.exe",

        "cmd": "cmd.exe",

        "powershell": "powershell.exe",

        "task manager": "taskmgr.exe",

        "ตัวจัดการงาน": "taskmgr.exe",

    }


    if name in common_apps:

        try:

            subprocess.Popen(
                common_apps[name]
            )

            return (
                f"กำลังเปิด {original_name} ครับ"
            )

        except Exception as error:

            return (
                f"เปิด {original_name} ไม่สำเร็จครับ: {error}"
            )


    # =====================================================
    # NOT FOUND
    # =====================================================

    return (
        f"ไม่พบแอป '{original_name}' "
        "ใน Windows ครับ"
    )


# =========================================================
# SYSTEM INFORMATION
# =========================================================

def system_info():

    info = {

        "OS": platform.system(),

        "OS Version": platform.version(),

        "Computer": platform.node(),

        "CPU": platform.processor(),

        "CPU Usage": f"{psutil.cpu_percent(interval=0.5)}%",

        "RAM Usage": f"{psutil.virtual_memory().percent}%",

        "RAM Total GB": round(
            psutil.virtual_memory().total / (1024 ** 3),
            2
        ),

        "RAM Available GB": round(
            psutil.virtual_memory().available / (1024 ** 3),
            2
        ),

    }


    # =====================================================
    # NVIDIA GPU
    # =====================================================

    try:

        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,utilization.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits"
            ],
            capture_output=True,
            text=True,
            timeout=5
        )


        if result.returncode == 0:

            gpu_lines = (
                result.stdout
                .strip()
                .splitlines()
            )


            if gpu_lines:

                gpu = gpu_lines[0]

                parts = [
                    x.strip()
                    for x in gpu.split(",")
                ]


                if len(parts) >= 4:

                    info["GPU"] = parts[0]

                    info["GPU Usage"] = (
                        f"{parts[1]}%"
                    )

                    info["GPU Memory"] = (
                        f"{parts[2]} / {parts[3]} MB"
                    )

    except Exception:
        pass


    return info