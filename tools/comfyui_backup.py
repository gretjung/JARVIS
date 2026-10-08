import os
import time
import uuid
import json
import subprocess
import threading

import requests


# ============================================================
# CONFIG
# ============================================================

COMFY_URL = (
    "http://127.0.0.1:8188"
)

COMFY_BAT = (
    r"C:\ComfyUI\ComfyUI_windows_portable_nvidia"
    r"\ComfyUI_windows_portable"
    r"\run_nvidia_gpu.bat"
)

COMFY_ROOT = (
    r"C:\ComfyUI\ComfyUI_windows_portable_nvidia"
    r"\ComfyUI_windows_portable"
)

JARVIS_IMAGE_DIR = (
    r"C:\JARVIS\media\images"
)

MODEL_NAME = (
    "flux1-schnell-fp8.safetensors"
)


# ============================================================
# STATE
# ============================================================

_image_mode = False

_comfy_process = None

_state_lock = threading.Lock()


# ============================================================
# IMAGE DIRECTORY
# ============================================================

os.makedirs(
    JARVIS_IMAGE_DIR,
    exist_ok=True
)


# ============================================================
# CHECK COMFYUI
# ============================================================

def is_comfyui_running():

    try:

        response = requests.get(
            f"{COMFY_URL}/system_stats",
            timeout=2
        )

        return response.status_code == 200

    except Exception:

        return False


# ============================================================
# WAIT FOR COMFYUI
# ============================================================

def wait_for_comfyui(
    timeout=120
):

    start = time.time()

    while (
        time.time() - start
        < timeout
    ):

        if is_comfyui_running():

            return True

        time.sleep(
            1
        )

    return False


# ============================================================
# START
# ============================================================

def start_comfyui():

    global _comfy_process

    # --------------------------------------------------------
    # Already running
    # --------------------------------------------------------

    if is_comfyui_running():

        print(
            "[JARVIS] ComfyUI already running."
        )

        return True

    # --------------------------------------------------------
    # Check BAT
    # --------------------------------------------------------

    if not os.path.exists(
        COMFY_BAT
    ):

        print(
            "[JARVIS] ComfyUI BAT not found:"
        )

        print(
            COMFY_BAT
        )

        return False

    try:

        print(
            "[JARVIS] Starting ComfyUI..."
        )

        _comfy_process = (
            subprocess.Popen(
                [
                    "cmd.exe",
                    "/c",
                    COMFY_BAT
                ],

                cwd=os.path.dirname(
                    COMFY_BAT
                ),

                creationflags=(
                    subprocess.CREATE_NEW_PROCESS_GROUP
                    |
                    subprocess.CREATE_NEW_CONSOLE
                )
            )
        )

        print(
            "[JARVIS] "
            f"ComfyUI PID: "
            f"{_comfy_process.pid}"
        )

    except Exception as e:

        print(
            "[JARVIS] "
            f"ComfyUI start error: {e}"
        )

        return False

    # --------------------------------------------------------
    # Wait
    # --------------------------------------------------------

    if wait_for_comfyui(
        120
    ):

        print(
            "[JARVIS] "
            "ComfyUI ONLINE"
        )

        return True

    print(
        "[JARVIS] "
        "ComfyUI did not start."
    )

    return False


# ============================================================
# STOP
# ============================================================

def stop_comfyui():

    global _comfy_process

    # --------------------------------------------------------
    # ถ้า API ไม่ทำงานอยู่แล้ว
    # --------------------------------------------------------

    if not is_comfyui_running():

        _comfy_process = None

        print(
            "[JARVIS] ComfyUI already OFF."
        )

        return True

    # --------------------------------------------------------
    # ถ้ามี PID ที่เราสตาร์ทไว้
    # --------------------------------------------------------

    if _comfy_process is not None:

        try:

            pid = (
                _comfy_process.pid
            )

            print(
                "[JARVIS] "
                f"Stopping ComfyUI PID {pid}..."
            )

            subprocess.run(

                [
                    "taskkill",
                    "/PID",
                    str(pid),
                    "/T",
                    "/F"
                ],

                capture_output=True,

                text=True,

                timeout=15
            )

        except Exception as e:

            print(
                "[JARVIS] "
                f"Stop error: {e}"
            )

    else:

        print(
            "[JARVIS] "
            "No tracked ComfyUI process."
        )

    _comfy_process = None

    # --------------------------------------------------------
    # Wait
    # --------------------------------------------------------

    start = time.time()

    while (
        time.time() - start
        < 15
    ):

        if not is_comfyui_running():

            print(
                "[JARVIS] "
                "ComfyUI OFF"
            )

            return True

        time.sleep(
            0.5
        )

    print(
        "[JARVIS] "
        "ComfyUI may still be running."
    )

    return False


# ============================================================
# ENABLE IMAGE MODE
# ============================================================

def enable_image_mode():

    global _image_mode

    with _state_lock:

        print(
            "[JARVIS] "
            "Enabling IMAGE GENERATION MODE..."
        )

        if not is_comfyui_running():

            success = start_comfyui()

            if not success:

                _image_mode = False

                print(
                    "[JARVIS] "
                    "IMAGE GENERATION MODE: FAILED"
                )

                return False

        _image_mode = True

        print(
            "[JARVIS] "
            "IMAGE GENERATION MODE: ON"
        )

        return True


# ============================================================
# DISABLE IMAGE MODE
# ============================================================

def disable_image_mode(
    close_comfyui=True
):

    global _image_mode

    with _state_lock:

        print(
            "[JARVIS] "
            "Disabling IMAGE GENERATION MODE..."
        )

        _image_mode = False

        if close_comfyui:

            stop_comfyui()

        print(
            "[JARVIS] "
            "IMAGE GENERATION MODE: OFF"
        )

        return True


# ============================================================
# STATUS
# ============================================================

def image_mode_enabled():

    return _image_mode


# ============================================================
# STATUS TEXT
# ============================================================

def image_mode_status():

    mode = (
        "ON"
        if _image_mode
        else "OFF"
    )

    comfy = (
        "ONLINE"
        if is_comfyui_running()
        else "OFFLINE"
    )

    return (
        "IMAGE GENERATION MODE\n\n"
        f"Mode: {mode}\n"
        f"ComfyUI: {comfy}"
    )


# ============================================================
# WORKFLOW
# ============================================================

def build_workflow(
    prompt,
    width=1024,
    height=1024
):

    seed = (
        int(
            uuid.uuid4().int
            % 4294967295
        )
    )

    workflow = {

        "6": {

            "class_type":
                "CheckpointLoaderSimple",

            "inputs": {

                "ckpt_name":
                    MODEL_NAME
            }
        },

        "8": {

            "class_type":
                "CLIPTextEncode",

            "inputs": {

                "text":
                    prompt,

                "clip":
                    [
                        "6",
                        1
                    ]
            }
        },

        "9": {

            "class_type":
                "EmptySD3LatentImage",

            "inputs": {

                "width":
                    width,

                "height":
                    height,

                "batch_size":
                    1
            }
        },

        "10": {

            "class_type":
                "KSamplerAdvanced",

            "inputs": {

                "add_noise":
                    "enable",

                "noise_seed":
                    seed,

                "steps":
                    4,

                "cfg":
                    8,

                "sampler_name":
                    "euler",

                "scheduler":
                    "simple",

                "start_at_step":
                    0,

                "end_at_step":
                    10000,

                "return_with_leftover_noise":
                    "disable",

                "model":
                    [
                        "6",
                        0
                    ],

                "positive":
                    [
                        "8",
                        0
                    ],

                "negative":
                    [
                        "8",
                        0
                    ],

                "latent_image":
                    [
                        "9",
                        0
                    ]
            }
        },

        "15": {

            "class_type":
                "VAEDecode",

            "inputs": {

                "samples":
                    [
                        "10",
                        0
                    ],

                "vae":
                    [
                        "6",
                        2
                    ]
            }
        },

        "16": {

            "class_type":
                "PreviewImage",

            "inputs": {

                "images":
                    [
                        "15",
                        0
                    ]
            }
        }
    }

    return workflow


# ============================================================
# FIND OUTPUT IMAGE
# ============================================================

def find_history_image(
    history
):

    if not history:
        return None

    for node_id, node in history.items():

        if not isinstance(
            node,
            dict
        ):

            continue

        outputs = node.get(
            "outputs",
            {}
        )

        if not isinstance(
            outputs,
            dict
        ):

            continue

        images = outputs.get(
            "images",
            []
        )

        if not isinstance(
            images,
            list
        ):

            continue

        if images:

            return images[0]

    return None


# ============================================================
# GENERATE IMAGE
# ============================================================

def generate_image(
    prompt,
    width=1024,
    height=1024
):

    if not _image_mode:

        raise RuntimeError(
            "IMAGE GENERATION MODE is OFF"
        )

    # --------------------------------------------------------
    # Start ComfyUI if necessary
    # --------------------------------------------------------

    if not is_comfyui_running():

        if not start_comfyui():

            raise RuntimeError(
                "ComfyUI is not running"
            )

    # --------------------------------------------------------
    # Build workflow
    # --------------------------------------------------------

    workflow = build_workflow(
        prompt,
        width,
        height
    )

    payload = {
        "prompt": workflow
    }

    # --------------------------------------------------------
    # Send
    # --------------------------------------------------------

    try:

        response = requests.post(

            f"{COMFY_URL}/prompt",

            json=payload,

            timeout=30
        )

    except Exception as e:

        raise RuntimeError(
            f"Cannot connect to ComfyUI: {e}"
        )

    if response.status_code != 200:

        raise RuntimeError(
            "ComfyUI prompt failed: "
            f"{response.text}"
        )

    data = response.json()

    prompt_id = data.get(
        "prompt_id"
    )

    if not prompt_id:

        raise RuntimeError(
            "ComfyUI did not return prompt_id"
        )

    print(
        "[JARVIS] "
        f"Generation ID: {prompt_id}"
    )

    # --------------------------------------------------------
    # Poll history
    # --------------------------------------------------------

    start = time.time()

    timeout = 300

    while (
        time.time() - start
        < timeout
    ):

        time.sleep(
            1
        )

        try:

            history_response = requests.get(

                f"{COMFY_URL}/history/"
                f"{prompt_id}",

                timeout=10
            )

            if history_response.status_code != 200:

                continue

            history_data = (
                history_response.json()
            )

        except Exception:

            continue

        if prompt_id not in history_data:

            continue

        history = (
            history_data[prompt_id]
        )

        image_info = (
            find_history_image(
                history
            )
        )

        if not image_info:

            continue

        filename = image_info.get(
            "filename"
        )

        subfolder = image_info.get(
            "subfolder",
            ""
        )

        folder_type = image_info.get(
            "type",
            "output"
        )

        if not filename:

            continue

        # ----------------------------------------------------
        # Download image
        # ----------------------------------------------------

        try:

            params = {

                "filename":
                    filename,

                "subfolder":
                    subfolder,

                "type":
                    folder_type
            }

            image_response = requests.get(

                f"{COMFY_URL}/view",

                params=params,

                timeout=60
            )

        except Exception as e:

            raise RuntimeError(
                f"Image download failed: {e}"
            )

        if image_response.status_code != 200:

            raise RuntimeError(
                "Image download failed: "
                f"{image_response.status_code}"
            )

        # ----------------------------------------------------
        # Unique filename
        # ----------------------------------------------------

        output_name = (
            "jarvis_"
            + time.strftime(
                "%Y%m%d_%H%M%S"
            )
            + "_"
            + uuid.uuid4().hex[:6]
            + ".png"
        )

        output_path = os.path.join(
            JARVIS_IMAGE_DIR,
            output_name
        )

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        with open(
            output_path,
            "wb"
        ) as f:

            f.write(
                image_response.content
            )

        print(
            "[JARVIS] "
            f"Image saved: "
            f"{output_path}"
        )

        return output_path

    raise TimeoutError(
        "Image generation timed out"
    )