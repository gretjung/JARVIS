import os
import time
import uuid
import subprocess
import threading

import requests


# ============================================================
# CONFIG
# ============================================================

COMFY_URL = "http://127.0.0.1:8188"

COMFY_BAT = (
    r"C:\ComfyUI\ComfyUI_windows_portable_nvidia"
    r"\ComfyUI_windows_portable"
    r"\run_nvidia_gpu.bat"
)

COMFY_ROOT = (
    r"C:\ComfyUI\ComfyUI_windows_portable_nvidia"
    r"\ComfyUI_windows_portable"
)

JARVIS_IMAGE_DIR = r"C:\JARVIS\media\images"

MODEL_NAME = "flux1-schnell-fp8.safetensors"


# ============================================================
# STATE
# ============================================================

_image_mode = False
_comfy_process = None
_state_lock = threading.Lock()


# ============================================================
# IMAGE DIRECTORY
# ============================================================

os.makedirs(JARVIS_IMAGE_DIR, exist_ok=True)


# ============================================================
# HTTP SESSION
# ============================================================

_session = requests.Session()


# ============================================================
# CHECK COMFYUI
# ============================================================

def is_comfyui_running():

    try:
        response = _session.get(
            f"{COMFY_URL}/system_stats",
            timeout=3
        )

        return response.status_code == 200

    except Exception:
        return False


# ============================================================
# WAIT FOR COMFYUI
# ============================================================

def wait_for_comfyui(timeout=120):

    start = time.time()

    while time.time() - start < timeout:

        if is_comfyui_running():
            return True

        time.sleep(1)

    return False


# ============================================================
# START COMFYUI
# ============================================================

def start_comfyui():

    global _comfy_process

    if is_comfyui_running():

        print("[JARVIS] ComfyUI already running.")

        return True

    if not os.path.exists(COMFY_BAT):

        print("[JARVIS] ComfyUI BAT not found:")
        print(COMFY_BAT)

        return False

    try:

        print("[JARVIS] Starting ComfyUI...")

        _comfy_process = subprocess.Popen(
            [
                "cmd.exe",
                "/c",
                COMFY_BAT
            ],
            cwd=os.path.dirname(COMFY_BAT),
            creationflags=(
                subprocess.CREATE_NEW_PROCESS_GROUP
                |
                subprocess.CREATE_NEW_CONSOLE
            )
        )

        print(
            f"[JARVIS] ComfyUI PID: {_comfy_process.pid}"
        )

    except Exception as e:

        print(
            f"[JARVIS] ComfyUI start error: {e}"
        )

        return False

    if wait_for_comfyui(120):

        print("[JARVIS] ComfyUI ONLINE")

        return True

    print("[JARVIS] ComfyUI did not start.")

    return False


# ============================================================
# STOP COMFYUI
# ============================================================

def stop_comfyui():

    global _comfy_process

    if not is_comfyui_running():

        _comfy_process = None

        print("[JARVIS] ComfyUI already OFF.")

        return True

    if _comfy_process is not None:

        try:

            pid = _comfy_process.pid

            print(
                f"[JARVIS] Stopping ComfyUI PID {pid}..."
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
                f"[JARVIS] Stop error: {e}"
            )

    else:

        print(
            "[JARVIS] No tracked ComfyUI process."
        )

    _comfy_process = None

    start = time.time()

    while time.time() - start < 15:

        if not is_comfyui_running():

            print("[JARVIS] ComfyUI OFF")

            return True

        time.sleep(0.5)

    print(
        "[JARVIS] ComfyUI may still be running."
    )

    return False


# ============================================================
# ENABLE IMAGE MODE
# ============================================================

def enable_image_mode():

    global _image_mode

    with _state_lock:

        print(
            "[JARVIS] Enabling IMAGE GENERATION MODE..."
        )

        if not is_comfyui_running():

            if not start_comfyui():

                _image_mode = False

                print(
                    "[JARVIS] IMAGE GENERATION MODE: FAILED"
                )

                return False

        _image_mode = True

        print(
            "[JARVIS] IMAGE GENERATION MODE: ON"
        )

        return True


# ============================================================
# DISABLE IMAGE MODE
# ============================================================

def disable_image_mode(close_comfyui=True):

    global _image_mode

    with _state_lock:

        print(
            "[JARVIS] Disabling IMAGE GENERATION MODE..."
        )

        _image_mode = False

        if close_comfyui:

            stop_comfyui()

        print(
            "[JARVIS] IMAGE GENERATION MODE: OFF"
        )

        return True


# ============================================================
# IMAGE MODE STATUS
# ============================================================

def image_mode_enabled():

    return _image_mode


def image_mode_status():

    mode = "ON" if _image_mode else "OFF"

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

    seed = int(
        uuid.uuid4().int % 4294967295
    )

    workflow = {

        "6": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": MODEL_NAME
            }
        },

        "8": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": prompt,
                "clip": [
                    "6",
                    1
                ]
            }
        },

        "9": {
            "class_type": "EmptySD3LatentImage",
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": 1
            }
        },

        "10": {
            "class_type": "KSamplerAdvanced",
            "inputs": {
                "add_noise": "enable",
                "noise_seed": seed,
                "steps": 4,
                "cfg": 8,
                "sampler_name": "euler",
                "scheduler": "simple",
                "start_at_step": 0,
                "end_at_step": 10000,
                "return_with_leftover_noise": "disable",

                "model": [
                    "6",
                    0
                ],

                "positive": [
                    "8",
                    0
                ],

                "negative": [
                    "8",
                    0
                ],

                "latent_image": [
                    "9",
                    0
                ]
            }
        },

        "15": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": [
                    "10",
                    0
                ],
                "vae": [
                    "6",
                    2
                ]
            }
        },

        "16": {
            "class_type": "PreviewImage",
            "inputs": {
                "images": [
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

def find_history_image(history):

    if not isinstance(history, dict):
        return None

    outputs = history.get("outputs", {})

    if not isinstance(outputs, dict):
        return None

    # Prefer PreviewImage output node 16
    preferred_nodes = ["16"]

    for node_id in preferred_nodes:

        node = outputs.get(node_id)

        if not isinstance(node, dict):
            continue

        images = node.get("images", [])

        if isinstance(images, list) and images:

            for image in images:

                if isinstance(image, dict):

                    if image.get("filename"):
                        return image

    # Fallback: search every output node
    for node in outputs.values():

        if not isinstance(node, dict):
            continue

        images = node.get("images", [])

        if not isinstance(images, list):
            continue

        for image in images:

            if isinstance(image, dict):

                if image.get("filename"):
                    return image

    return None


# ============================================================
# DOWNLOAD IMAGE
# ============================================================

def download_image(
    image_info,
    output_path
):

    if not isinstance(image_info, dict):

        raise RuntimeError(
            "Invalid image information"
        )

    filename = image_info.get("filename")

    subfolder = image_info.get(
        "subfolder",
        ""
    )

    folder_type = image_info.get(
        "type",
        "output"
    )

    if not filename:

        raise RuntimeError(
            "ComfyUI returned an empty filename"
        )

    print(
        "[JARVIS] Downloading:"
        f" {filename}"
    )

    print(
        "[JARVIS] Type:"
        f" {folder_type}"
    )

    params = {
        "filename": filename,
        "subfolder": subfolder,
        "type": folder_type
    }

    last_error = None

    for attempt in range(1, 6):

        try:

            print(
                f"[JARVIS] Download attempt "
                f"{attempt}/5..."
            )

            response = _session.get(
                f"{COMFY_URL}/view",
                params=params,
                timeout=60
            )

            print(
                "[JARVIS] /view status:"
                f" {response.status_code}"
            )

            if response.status_code != 200:

                last_error = (
                    f"HTTP {response.status_code}: "
                    f"{response.text[:500]}"
                )

                time.sleep(1)

                continue

            content = response.content

            if not content:

                last_error = (
                    "ComfyUI returned an empty image"
                )

                time.sleep(1)

                continue

            with open(
                output_path,
                "wb"
            ) as f:

                f.write(content)

            file_size = os.path.getsize(
                output_path
            )

            if file_size <= 0:

                try:
                    os.remove(output_path)
                except Exception:
                    pass

                last_error = (
                    "Saved image has zero bytes"
                )

                time.sleep(1)

                continue

            print(
                "[JARVIS] Image saved:"
                f" {output_path}"
            )

            print(
                "[JARVIS] Image size:"
                f" {file_size:,} bytes"
            )

            return output_path

        except Exception as e:

            last_error = str(e)

            print(
                "[JARVIS] Download error:"
                f" {e}"
            )

            time.sleep(1)

    raise RuntimeError(
        "Image download failed after 5 attempts: "
        f"{last_error}"
    )


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

    if not prompt or not str(prompt).strip():

        raise ValueError(
            "Image prompt is empty"
        )

    prompt = str(prompt).strip()

    # --------------------------------------------------------
    # Ensure ComfyUI is running
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
    # Send prompt
    # --------------------------------------------------------

    try:

        response = _session.post(
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

    try:

        data = response.json()

    except Exception as e:

        raise RuntimeError(
            f"Invalid ComfyUI response: {e}"
        )

    prompt_id = data.get("prompt_id")

    if not prompt_id:

        raise RuntimeError(
            "ComfyUI did not return prompt_id"
        )

    print(
        "[JARVIS] Generation ID:"
        f" {prompt_id}"
    )

    # --------------------------------------------------------
    # Poll history
    # --------------------------------------------------------

    timeout = 300

    start = time.time()

    while time.time() - start < timeout:

        time.sleep(1)

        try:

            history_response = _session.get(
                f"{COMFY_URL}/history/{prompt_id}",
                timeout=10
            )

            if history_response.status_code != 200:

                continue

            history_data = (
                history_response.json()
            )

        except Exception:

            continue

        job = history_data.get(prompt_id)

        if not isinstance(job, dict):

            continue

        # ----------------------------------------------------
        # Check status
        # ----------------------------------------------------

        status = job.get(
            "status",
            {}
        )

        if isinstance(status, dict):

            status_str = status.get(
                "status_str",
                ""
            )

            completed = status.get(
                "completed",
                False
            )

            if status_str == "error":

                raise RuntimeError(
                    "ComfyUI generation error: "
                    f"{status}"
                )

            if not completed:

                continue

        # ----------------------------------------------------
        # Get image
        # ----------------------------------------------------

        image_info = find_history_image(
            job
        )

        if not image_info:

            continue

        # ----------------------------------------------------
        # Create unique JARVIS filename
        # ----------------------------------------------------

        output_name = (
            "JARVIS_"
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
        # Download
        # ----------------------------------------------------

        return download_image(
            image_info,
            output_path
        )

    raise TimeoutError(
        "Image generation timed out after "
        f"{timeout} seconds"
    )