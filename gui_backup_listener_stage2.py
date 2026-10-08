# -*- coding: utf-8 -*-

"""
JARVIS RED HUD
Version 2.0.0

Futuristic black/red AI interface
"""

import os
import re
import threading
import time
import tkinter as tk
from tkinter import messagebox

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

try:
    import win32clipboard
    import win32con
except ImportError:
    win32clipboard = None
    win32con = None

from core.agent import Agent
from core.voice import Voice
from core.listener import VoiceListener
from core.identity import (
    JARVIS_NAME,
    JARVIS_VERSION,
    get_color,
)


# ============================================================
# COLORS
# ============================================================

BLACK = "#030303"
BG = "#050505"
PANEL = "#090909"
PANEL_2 = "#0D0D0D"
PANEL_3 = "#111111"

RED = "#FF1A1A"
RED_BRIGHT = "#FF3333"
RED_DARK = "#7A0000"
RED_DEEP = "#3A0000"

WHITE = "#EAEAEA"
GRAY = "#888888"
GRAY_DARK = "#444444"

GREEN = "#FF1A1A"


# ============================================================
# HUD
# ============================================================

class HUD(tk.Tk):

    def __init__(self):

        super().__init__()

        self.title("JARVIS")

        self.geometry("1400x850")

        self.minsize(
            1100,
            700
        )

        self.configure(
            bg=BLACK
        )

        self.protocol(
            "WM_DELETE_WINDOW",
            self.on_close
        )

        # ----------------------------------------------------
        # STATE
        # ----------------------------------------------------

        self.current_state = "ONLINE"

        self.voice = Voice()

        self.agent = Agent(
            voice=self.voice
        )

        self.voice_listener = VoiceListener(
            agent=self.agent
        )


        self.current_image = None

        self.preview_window = None

        self.running = True

        # ----------------------------------------------------
        # BUILD
        # ----------------------------------------------------

        self.build_background()

        self.build_top_bar()

        self.build_main_area()

        self.build_left_panel()

        self.build_center_panel()

        self.build_right_panel()

        self.build_bottom_bar()

        self.bind_keyboard()

        self.after(
            500,
            self.update_status
        )

        self.after(
            1000,
            self.animate_hud
        )


    # ========================================================
    # BACKGROUND
    # ========================================================

    def build_background(self):

        self.canvas = tk.Canvas(
            self,
            bg=BLACK,
            highlightthickness=0
        )

        self.canvas.place(
            x=0,
            y=0,
            relwidth=1,
            relheight=1
        )

        self.draw_grid()

        self.bind(
            "<Configure>",
            self.on_resize
        )


    def draw_grid(self):

        self.canvas.delete(
            "grid"
        )

        width = max(
            self.winfo_width(),
            1100
        )

        height = max(
            self.winfo_height(),
            700
        )

        step = 45

        # vertical
        for x in range(
            0,
            width,
            step
        ):

            self.canvas.create_line(
                x,
                0,
                x,
                height,
                fill="#120606",
                tags="grid"
            )

        # horizontal
        for y in range(
            0,
            height,
            step
        ):

            self.canvas.create_line(
                0,
                y,
                width,
                y,
                fill="#120606",
                tags="grid"
            )


    def on_resize(self, event):

        if event.widget == self:

            self.draw_grid()


    # ========================================================
    # TOP BAR
    # ========================================================

    def build_top_bar(self):

        self.top = tk.Frame(
            self,
            bg=BLACK,
            height=70
        )

        self.top.place(
            x=0,
            y=0,
            relwidth=1
        )

        # ----------------------------------------------------
        # LOGO
        # ----------------------------------------------------

        self.logo = tk.Label(
            self.top,
            text="â—‰",
            font=(
                "Segoe UI",
                34,
                "bold"
            ),
            fg=RED,
            bg=BLACK
        )

        self.logo.pack(
            side="left",
            padx=(25, 8)
        )

        # ----------------------------------------------------
        # NAME
        # ----------------------------------------------------

        name_frame = tk.Frame(
            self.top,
            bg=BLACK
        )

        name_frame.pack(
            side="left"
        )

        tk.Label(
            name_frame,
            text="JARVIS",
            font=(
                "Segoe UI",
                22,
                "bold"
            ),
            fg=WHITE,
            bg=BLACK
        ).pack(
            anchor="w"
        )

        tk.Label(
            name_frame,
            text=f"PERSONAL AI SYSTEM  //  V{JARVIS_VERSION}",
            font=(
                "Consolas",
                8
            ),
            fg=RED,
            bg=BLACK
        ).pack(
            anchor="w"
        )

        # ----------------------------------------------------
        # TOP RIGHT STATUS
        # ----------------------------------------------------

        self.top_status = tk.Label(
            self.top,
            text="â— SYSTEM ONLINE",
            font=(
                "Consolas",
                10,
                "bold"
            ),
            fg=RED,
            bg=BLACK
        )

        self.top_status.pack(
            side="right",
            padx=30
        )


    # ========================================================
    # MAIN AREA
    # ========================================================

    def build_main_area(self):

        self.main = tk.Frame(
            self,
            bg=BLACK
        )

        self.main.place(
            x=18,
            y=78,
            relwidth=0.976,
            relheight=0.84
        )


    # ========================================================
    # LEFT PANEL
    # ========================================================

    def build_left_panel(self):

        self.left = tk.Frame(
            self.main,
            bg=PANEL,
            highlightbackground=RED_DARK,
            highlightthickness=1
        )

        self.left.place(
            relx=0,
            rely=0,
            relwidth=0.205,
            relheight=1
        )

        # Header

        tk.Label(
            self.left,
            text="SYSTEM CORE",
            font=(
                "Consolas",
                11,
                "bold"
            ),
            fg=RED,
            bg=PANEL
        ).pack(
            anchor="w",
            padx=18,
            pady=(18, 2)
        )

        tk.Label(
            self.left,
            text="JARVIS // CORE MONITOR",
            font=(
                "Consolas",
                7
            ),
            fg=GRAY,
            bg=PANEL
        ).pack(
            anchor="w",
            padx=18,
            pady=(0, 18)
        )

        # ----------------------------------------------------
        # CORE STATUS
        # ----------------------------------------------------

        self.core_items = {}

        self.add_core_item(
            "AI CORE"
        )

        self.add_core_item(
            "IDENTITY"
        )

        self.add_core_item(
            "VOICE"
        )

        self.add_core_item(
            "COMFYUI"
        )

        self.add_core_item(
            "IMAGE MODE"
        )

        # ----------------------------------------------------
        # SEPARATOR
        # ----------------------------------------------------

        tk.Frame(
            self.left,
            bg=RED_DARK,
            height=1
        ).pack(
            fill="x",
            padx=15,
            pady=20
        )

        # ----------------------------------------------------
        # SYSTEM INFO
        # ----------------------------------------------------

        tk.Label(
            self.left,
            text="OPERATING PROFILE",
            font=(
                "Consolas",
                9,
                "bold"
            ),
            fg=RED,
            bg=PANEL
        ).pack(
            anchor="w",
            padx=18
        )

        self.info_text = tk.Label(
            self.left,
            text=(
                "PERSONAL AI\n"
                "MALE VOICE\n"
                "THAI / ENGLISH\n"
                "LOCAL PROCESSING\n"
                "QWEN 8B CORE"
            ),
            justify="left",
            font=(
                "Consolas",
                8
            ),
            fg=GRAY,
            bg=PANEL
        )

        self.info_text.pack(
            anchor="w",
            padx=18,
            pady=12
        )

        # ----------------------------------------------------
        # COMMAND HINT
        # ----------------------------------------------------

        tk.Label(
            self.left,
            text="QUICK COMMANDS",
            font=(
                "Consolas",
                9,
                "bold"
            ),
            fg=RED,
            bg=PANEL
        ).pack(
            anchor="w",
            padx=18,
            pady=(15, 5)
        )

        tk.Label(
            self.left,
            text=(
                "à¸ªà¸–à¸²à¸™à¸°à¸£à¸°à¸šà¸š\n"
                "à¹€à¸›à¸´à¸” Chrome\n"
                "à¹€à¸›à¸´à¸”à¹€à¸ªà¸µà¸¢à¸‡\n"
                "à¹€à¸›à¸´à¸”à¹‚à¸«à¸¡à¸”à¹€à¸ˆà¸™à¸ à¸²à¸ž\n"
                "à¸ªà¸£à¹‰à¸²à¸‡à¸ à¸²à¸ž ..."
            ),
            justify="left",
            font=(
                "Consolas",
                8
            ),
            fg=GRAY,
            bg=PANEL
        ).pack(
            anchor="w",
            padx=18
        )


    def add_core_item(self, name):

        frame = tk.Frame(
            self.left,
            bg=PANEL
        )

        frame.pack(
            fill="x",
            padx=15,
            pady=5
        )

        dot = tk.Label(
            frame,
            text="â—",
            font=(
                "Segoe UI",
                10
            ),
            fg=RED,
            bg=PANEL
        )

        dot.pack(
            side="left"
        )

        label = tk.Label(
            frame,
            text=name,
            font=(
                "Consolas",
                8,
                "bold"
            ),
            fg=WHITE,
            bg=PANEL
        )

        label.pack(
            side="left",
            padx=8
        )

        status = tk.Label(
            frame,
            text="ONLINE",
            font=(
                "Consolas",
                7
            ),
            fg=RED,
            bg=PANEL
        )

        status.pack(
            side="right"
        )

        self.core_items[name] = {
            "dot": dot,
            "label": label,
            "status": status
        }


    # ========================================================
    # CENTER PANEL
    # ========================================================

    def build_center_panel(self):

        self.center = tk.Frame(
            self.main,
            bg=BLACK
        )

        self.center.place(
            relx=0.215,
            rely=0,
            relwidth=0.55,
            relheight=1
        )

        # ----------------------------------------------------
        # CORE VISUAL
        # ----------------------------------------------------

        self.core_canvas = tk.Canvas(
            self.center,
            bg=BLACK,
            highlightthickness=0,
            height=250
        )

        self.core_canvas.pack(
            fill="x"
        )

        self.core_canvas.bind(
            "<Configure>",
            self.draw_core
        )

        # ----------------------------------------------------
        # STATE
        # ----------------------------------------------------

        self.state_label = tk.Label(
            self.center,
            text="ONLINE",
            font=(
                "Consolas",
                11,
                "bold"
            ),
            fg=RED,
            bg=BLACK
        )

        self.state_label.pack(
            pady=(0, 5)
        )

        self.state_detail = tk.Label(
            self.center,
            text="JARVIS CORE READY",
            font=(
                "Consolas",
                8
            ),
            fg=GRAY,
            bg=BLACK
        )

        self.state_detail.pack(
            pady=(0, 15)
        )

        # ----------------------------------------------------
        # CHAT
        # ----------------------------------------------------

        chat_frame = tk.Frame(
            self.center,
            bg=PANEL,
            highlightbackground=RED_DARK,
            highlightthickness=1
        )

        chat_frame.pack(
            fill="both",
            expand=True
        )

        header = tk.Frame(
            chat_frame,
            bg=PANEL_2,
            height=35
        )

        header.pack(
            fill="x"
        )

        tk.Label(
            header,
            text="NEURAL INTERFACE",
            font=(
                "Consolas",
                9,
                "bold"
            ),
            fg=RED,
            bg=PANEL_2
        ).pack(
            side="left",
            padx=12
        )

        self.chat_status = tk.Label(
            header,
            text="READY",
            font=(
                "Consolas",
                8
            ),
            fg=GRAY,
            bg=PANEL_2
        )

        self.chat_status.pack(
            side="right",
            padx=12
        )

        # ----------------------------------------------------
        # CHAT TEXT
        # ----------------------------------------------------

        text_frame = tk.Frame(
            chat_frame,
            bg=PANEL
        )

        text_frame.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=8
        )

        self.chat = tk.Text(
            text_frame,
            bg=PANEL,
            fg=WHITE,
            insertbackground=RED,
            selectbackground=RED_DARK,
            selectforeground=WHITE,
            relief="flat",
            borderwidth=0,
            font=(
                "Consolas",
                10
            ),
            wrap="word",
            padx=12,
            pady=12
        )

        self.chat.pack(
            fill="both",
            expand=True
        )

        self.chat.configure(
            state="disabled"
        )

        # ----------------------------------------------------
        # TAGS
        # ----------------------------------------------------

        self.chat.tag_configure(
            "user",
            foreground=WHITE,
            spacing1=8,
            spacing3=8
        )

        self.chat.tag_configure(
            "jarvis",
            foreground=RED_BRIGHT,
            spacing1=8,
            spacing3=8
        )

        self.chat.tag_configure(
            "system",
            foreground=GRAY,
            spacing1=5,
            spacing3=5
        )

        self.chat.tag_configure(
            "error",
            foreground="#FF4444"
        )

        # ----------------------------------------------------
        # IMAGE
        # ----------------------------------------------------

        self.image_label = tk.Label(
            chat_frame,
            text="",
            bg=PANEL,
            fg=GRAY
        )

        self.image_label.pack(
            pady=5
        )

        self.image_label.bind(
            "<Button-1>",
            self.open_image
        )


    # ========================================================
    # RIGHT PANEL
    # ========================================================

    def build_right_panel(self):

        self.right = tk.Frame(
            self.main,
            bg=PANEL,
            highlightbackground=RED_DARK,
            highlightthickness=1
        )

        self.right.place(
            relx=0.775,
            rely=0,
            relwidth=0.225,
            relheight=1
        )

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        tk.Label(
            self.right,
            text="VISUAL CORE",
            font=(
                "Consolas",
                11,
                "bold"
            ),
            fg=RED,
            bg=PANEL
        ).pack(
            anchor="w",
            padx=18,
            pady=(18, 2)
        )

        tk.Label(
            self.right,
            text="COMFYUI / IMAGE PROCESSOR",
            font=(
                "Consolas",
                7
            ),
            fg=GRAY,
            bg=PANEL
        ).pack(
            anchor="w",
            padx=18,
            pady=(0, 18)
        )

        # ----------------------------------------------------
        # IMAGE DISPLAY
        # ----------------------------------------------------

        self.preview = tk.Label(
            self.right,
            text=(
                "â—‰\n\n"
                "NO IMAGE\n"
                "OUTPUT"
            ),
            font=(
                "Consolas",
                11,
                "bold"
            ),
            fg=GRAY_DARK,
            bg=PANEL_2,
            justify="center"
        )

        self.preview.pack(
            fill="x",
            padx=15,
            ipady=75
        )

        self.preview.bind(
            "<Button-1>",
            self.open_image
        )

        # ----------------------------------------------------
        # IMAGE INFO
        # ----------------------------------------------------

        self.image_info = tk.Label(
            self.right,
            text="VISUAL BUFFER: EMPTY",
            font=(
                "Consolas",
                8
            ),
            fg=GRAY,
            bg=PANEL
        )

        self.image_info.pack(
            anchor="w",
            padx=18,
            pady=12
        )

        # ----------------------------------------------------
        # DIVIDER
        # ----------------------------------------------------

        tk.Frame(
            self.right,
            bg=RED_DARK,
            height=1
        ).pack(
            fill="x",
            padx=15,
            pady=10
        )

        # ----------------------------------------------------
        # IMAGE MODE
        # ----------------------------------------------------

        tk.Label(
            self.right,
            text="IMAGE GENERATION",
            font=(
                "Consolas",
                9,
                "bold"
            ),
            fg=RED,
            bg=PANEL
        ).pack(
            anchor="w",
            padx=18
        )

        self.image_mode_label = tk.Label(
            self.right,
            text="â— OFFLINE",
            font=(
                "Consolas",
                9,
                "bold"
            ),
            fg=GRAY,
            bg=PANEL
        )

        self.image_mode_label.pack(
            anchor="w",
            padx=18,
            pady=8
        )

        # ----------------------------------------------------
        # HELP
        # ----------------------------------------------------

        tk.Label(
            self.right,
            text=(
                "à¹€à¸›à¸´à¸”à¹‚à¸«à¸¡à¸”à¹€à¸ˆà¸™à¸ à¸²à¸ž\n"
                "à¸ªà¸£à¹‰à¸²à¸‡à¸ à¸²à¸ž à¸£à¸–à¸ªà¸›à¸­à¸£à¹Œà¸•à¸ªà¸µà¸”à¸³\n"
                "à¸›à¸´à¸”à¹‚à¸«à¸¡à¸”à¸ªà¸£à¹‰à¸²à¸‡à¸ à¸²à¸ž"
            ),
            justify="left",
            font=(
                "Consolas",
                8
            ),
            fg=GRAY,
            bg=PANEL
        ).pack(
            anchor="w",
            padx=18,
            pady=10
        )


    # ========================================================
    # BOTTOM BAR
    # ========================================================

    def build_bottom_bar(self):

        self.bottom = tk.Frame(
            self,
            bg=BLACK,
            height=55
        )

        self.bottom.place(
            x=18,
            rely=0.925,
            relwidth=0.976
        )

        # ----------------------------------------------------
        # INPUT
        # ----------------------------------------------------

        self.input_frame = tk.Frame(
            self.bottom,
            bg=PANEL,
            highlightbackground=RED_DARK,
            highlightthickness=1
        )

        self.input_frame.pack(
            fill="both",
            expand=True,
            side="left",
            padx=(0, 10)
        )

        tk.Label(
            self.input_frame,
            text=">",
            font=(
                "Consolas",
                13,
                "bold"
            ),
            fg=RED,
            bg=PANEL
        ).pack(
            side="left",
            padx=(12, 5)
        )

        self.entry = tk.Entry(
            self.input_frame,
            bg=PANEL,
            fg=WHITE,
            insertbackground=RED,
            selectbackground=RED_DARK,
            selectforeground=WHITE,
            relief="flat",
            font=(
                "Consolas",
                10
            )
        )

        self.entry.pack(
            fill="both",
            expand=True,
            side="left",
            padx=5
        )

        self.entry.focus_set()

        # ----------------------------------------------------
        # SEND
        # ----------------------------------------------------

        self.send_button = tk.Button(
            self.bottom,
            text="EXECUTE",
            command=self.send_message,
            font=(
                "Consolas",
                9,
                "bold"
            ),
            fg=BLACK,
            bg=RED,
            activeforeground=WHITE,
            activebackground=RED_DARK,
            relief="flat",
            borderwidth=0,
            padx=22,
            cursor="hand2"
        )

        self.send_button.pack(
            side="right",
            fill="y"
        )


    # ========================================================
    # KEYBOARD / CLIPBOARD
    # ========================================================

    def bind_keyboard(self):

        self.entry.bind(
            "<Return>",
            self.send_message
        )

        self.entry.bind(
            "<Control-a>",
            self.select_all
        )

        self.entry.bind(
            "<Control-A>",
            self.select_all
        )

        self.entry.bind(
            "<Control-c>",
            self.copy_text
        )

        self.entry.bind(
            "<Control-C>",
            self.copy_text
        )

        self.entry.bind(
            "<Control-x>",
            self.cut_text
        )

        self.entry.bind(
            "<Control-X>",
            self.cut_text
        )

        self.entry.bind(
            "<Control-v>",
            self.paste_text
        )

        self.entry.bind(
            "<Control-V>",
            self.paste_text
        )

        self.entry.bind(
            "<Control-Insert>",
            self.copy_text
        )

        self.entry.bind(
            "<Shift-Insert>",
            self.paste_text
        )

        self.entry.bind(
            "<Button-3>",
            self.show_context_menu
        )

        self.entry.bind(
            "<Button-2>",
            self.paste_text
        )


    def select_all(self, event=None):

        self.entry.select_range(
            0,
            "end"
        )

        self.entry.icursor(
            "end"
        )

        return "break"


    def copy_text(self, event=None):

        try:

            selected = self.entry.selection_get()

        except tk.TclError:

            return "break"

        # ----------------------------------------------------
        # Windows clipboard
        # ----------------------------------------------------

        if win32clipboard:

            try:

                win32clipboard.OpenClipboard()

                win32clipboard.EmptyClipboard()

                win32clipboard.SetClipboardData(
                    win32con.CF_UNICODETEXT,
                    selected
                )

                win32clipboard.CloseClipboard()

                return "break"

            except Exception:

                try:
                    win32clipboard.CloseClipboard()
                except Exception:
                    pass

        # fallback

        self.clipboard_clear()

        self.clipboard_append(
            selected
        )

        return "break"


    def cut_text(self, event=None):

        self.copy_text()

        try:

            self.entry.delete(
                "sel.first",
                "sel.last"
            )

        except tk.TclError:
            pass

        return "break"


    def paste_text(self, event=None):

        text = ""

        # ----------------------------------------------------
        # Windows clipboard
        # ----------------------------------------------------

        if win32clipboard:

            try:

                win32clipboard.OpenClipboard()

                if win32clipboard.IsClipboardFormatAvailable(
                    win32con.CF_UNICODETEXT
                ):

                    text = win32clipboard.GetClipboardData(
                        win32con.CF_UNICODETEXT
                    )

                win32clipboard.CloseClipboard()

            except Exception:

                try:
                    win32clipboard.CloseClipboard()
                except Exception:
                    pass

        # ----------------------------------------------------
        # fallback
        # ----------------------------------------------------

        if not text:

            try:

                text = self.clipboard_get()

            except Exception:

                text = ""

        if text:

            try:

                self.entry.delete(
                    "sel.first",
                    "sel.last"
                )

            except tk.TclError:
                pass

            self.entry.insert(
                "insert",
                text
            )

        return "break"


    def show_context_menu(self, event):

        menu = tk.Menu(
            self,
            tearoff=0,
            bg=PANEL_2,
            fg=WHITE,
            activebackground=RED_DARK,
            activeforeground=WHITE
        )

        menu.add_command(
            label="Cut",
            command=self.cut_text
        )

        menu.add_command(
            label="Copy",
            command=self.copy_text
        )

        menu.add_command(
            label="Paste",
            command=self.paste_text
        )

        menu.add_separator()

        menu.add_command(
            label="Select All",
            command=self.select_all
        )

        menu.tk_popup(
            event.x_root,
            event.y_root
        )


    # ========================================================
    # SEND MESSAGE
    # ========================================================

    def send_message(self, event=None):

        text = self.entry.get().strip()

        if not text:

            return "break"

        self.entry.delete(
            0,
            "end"
        )

        self.add_message(
            "YOU",
            text,
            "user"
        )

        self.set_state(
            "THINKING"
        )

        self.send_button.configure(
            state="disabled"
        )

        thread = threading.Thread(
            target=self.process_message,
            args=(text,),
            daemon=False
        )

        thread.start()

        return "break"


    # ========================================================
    # PROCESS
    # ========================================================

    def process_message(self, text):

        try:

            response = self.agent.handle(
                text
            )

        except Exception as e:

            response = (
                f"à¹€à¸à¸´à¸”à¸‚à¹‰à¸­à¸œà¸´à¸”à¸žà¸¥à¸²à¸”à¹ƒà¸™ JARVIS Core: {e}"
            )

        self.after(
            0,
            lambda: self.handle_response(
                response
            )
        )


    # ========================================================
    # RESPONSE
    # ========================================================

    def handle_response(self, response):

        response = str(
            response
        )

        image_path = None

        # ----------------------------------------------------
        # IMAGE PATH
        # ----------------------------------------------------

        match = re.search(
            r"IMAGE_PATH:\s*(.+)",
            response,
            flags=re.IGNORECASE
        )

        if match:

            image_path = (
                match.group(1)
                .splitlines()[0]
                .strip()
            )

            response = re.sub(
                r"IMAGE_PATH:\s*.+",
                "",
                response,
                flags=re.IGNORECASE
            ).strip()

        # ----------------------------------------------------
        # DIRECT PATH RESPONSE
        # ----------------------------------------------------

        if (
            not image_path
            and os.path.isfile(
                response.strip()
            )
        ):

            image_path = response.strip()

            response = (
                "à¸ªà¸£à¹‰à¸²à¸‡à¸ à¸²à¸žà¹€à¸ªà¸£à¹‡à¸ˆà¹€à¸£à¸µà¸¢à¸šà¸£à¹‰à¸­à¸¢à¹à¸¥à¹‰à¸§à¸„à¸£à¸±à¸š"
            )

        # ----------------------------------------------------
        # CHAT
        # ----------------------------------------------------

        if response:

            self.add_message(
                "JARVIS",
                response,
                "jarvis"
            )

        # ----------------------------------------------------
        # IMAGE
        # ----------------------------------------------------

        if image_path:

            self.display_image(
                image_path
            )

            self.set_state(
                "GENERATING"
            )

        else:

            self.set_state(
                "SPEAKING"
            )

        # ----------------------------------------------------
        # VOICE
        # ----------------------------------------------------

        if response:

            self.chat_status.configure(
                text="SPEAKING",
                fg=RED
            )

            threading.Thread(
                target=self.speak_response,
                args=(response,),
                daemon=False
            ).start()

        else:

            self.send_button.configure(
                state="normal"
            )

            self.entry.focus_set()


    def speak_response(self, text):
        """
        GUI does not speak directly.
        Agent is the single owner of voice output.
        This prevents duplicate speech.
        """

        if not text:
            return

        try:
            # GUI only updates visual state.
            # Do NOT call self.voice.speak() here.
            self.set_state("SPEAKING")

        except Exception as e:
            print(f"[JARVIS GUI] Speaking state error: {e}")
    def finish_response(self):

        self.set_state(
            "ONLINE"
        )

        self.send_button.configure(
            state="normal"
        )

        self.entry.focus_set()


    # ========================================================
    # CHAT
    # ========================================================

    def add_message(
        self,
        sender,
        message,
        tag
    ):

        self.chat.configure(
            state="normal"
        )

        timestamp = time.strftime(
            "%H:%M:%S"
        )

        self.chat.insert(
            "end",
            f"\n[{timestamp}] ",
            "system"
        )

        self.chat.insert(
            "end",
            f"{sender}\n",
            tag
        )

        self.chat.insert(
            "end",
            f"{message}\n",
            tag
        )

        self.chat.see(
            "end"
        )

        self.chat.configure(
            state="disabled"
        )


    # ========================================================
    # STATE
    # ========================================================

    def set_state(self, state):

        self.current_state = state

        self.state_label.configure(
            text=state
        )

        self.state_detail.configure(
            text=self.state_description(
                state
            )
        )

        self.top_status.configure(
            text=f"â— {state}"
        )

        self.chat_status.configure(
            text=state
        )


    def state_description(self, state):

        descriptions = {

            "ONLINE":
                "JARVIS CORE READY",

            "THINKING":
                "ANALYZING USER REQUEST",

            "SPEAKING":
                "VOICE SYNTHESIS ACTIVE",

            "EXECUTING":
                "EXECUTING SYSTEM COMMAND",

            "GENERATING":
                "VISUAL CORE PROCESSING",

            "ERROR":
                "CORE ERROR DETECTED",

        }

        return descriptions.get(
            state,
            "SYSTEM ACTIVE"
        )


    # ========================================================
    # STATUS UPDATE
    # ========================================================

    def update_status(self):

        if not self.running:

            return

        # ----------------------------------------------------
        # OLLAMA
        # ----------------------------------------------------

        ai_online = False

        try:

            import requests

            r = requests.get(
                "http://127.0.0.1:11434/api/tags",
                timeout=1.5
            )

            ai_online = (
                r.status_code == 200
            )

        except Exception:
            pass

        self.set_core_status(
            "AI CORE",
            ai_online
        )

        # ----------------------------------------------------
        # IDENTITY
        # ----------------------------------------------------

        self.set_core_status(
            "IDENTITY",
            True
        )

        # ----------------------------------------------------
        # VOICE
        # ----------------------------------------------------

        self.set_core_status(
            "VOICE",
            self.voice is not None
        )

        # ----------------------------------------------------
        # COMFYUI
        # ----------------------------------------------------

        comfy_online = False

        try:

            import requests

            r = requests.get(
                "http://127.0.0.1:8188/system_stats",
                timeout=1.5
            )

            comfy_online = (
                r.status_code == 200
            )

        except Exception:
            pass

        self.set_core_status(
            "COMFYUI",
            comfy_online
        )

        # ----------------------------------------------------
        # IMAGE MODE
        # ----------------------------------------------------

        image_mode = False

        try:

            image_mode = bool(
                self.agent.image_mode
            )

        except Exception:
            pass

        self.set_core_status(
            "IMAGE MODE",
            image_mode
        )

        self.image_mode_label.configure(
            text=(
                "â— ONLINE"
                if image_mode
                else "â— OFFLINE"
            ),
            fg=(
                RED
                if image_mode
                else GRAY
            )
        )

        self.after(
            4000,
            self.update_status
        )


    def set_core_status(
        self,
        name,
        online
    ):

        if name not in self.core_items:

            return

        item = self.core_items[name]

        item["dot"].configure(
            fg=RED if online else GRAY_DARK
        )

        item["status"].configure(
            text=(
                "ONLINE"
                if online
                else "OFFLINE"
            ),
            fg=RED if online else GRAY_DARK
        )


    # ========================================================
    # CORE VISUAL
    # ========================================================

    def draw_core(self, event=None):

        self.core_canvas.delete(
            "core"
        )

        width = self.core_canvas.winfo_width()

        if width < 10:

            return

        height = self.core_canvas.winfo_height()

        cx = width // 2

        cy = height // 2

        # ----------------------------------------------------
        # OUTER RINGS
        # ----------------------------------------------------

        rings = [
            92,
            78,
            65,
            50
        ]

        for radius in rings:

            self.core_canvas.create_oval(
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
                outline=RED_DARK,
                width=1,
                tags="core"
            )

        # ----------------------------------------------------
        # CROSSHAIR
        # ----------------------------------------------------

        self.core_canvas.create_line(
            cx - 120,
            cy,
            cx - 85,
            cy,
            fill=RED_DARK,
            width=1,
            tags="core"
        )

        self.core_canvas.create_line(
            cx + 85,
            cy,
            cx + 120,
            cy,
            fill=RED_DARK,
            width=1,
            tags="core"
        )

        self.core_canvas.create_line(
            cx,
            cy - 120,
            cx,
            cy - 85,
            fill=RED_DARK,
            width=1,
            tags="core"
        )

        self.core_canvas.create_line(
            cx,
            cy + 85,
            cx,
            cy + 120,
            fill=RED_DARK,
            width=1,
            tags="core"
        )

        # ----------------------------------------------------
        # CENTER
        # ----------------------------------------------------

        self.core_canvas.create_oval(
            cx - 22,
            cy - 22,
            cx + 22,
            cy + 22,
            outline=RED,
            fill="#150000",
            width=2,
            tags="core"
        )

        self.core_canvas.create_text(
            cx,
            cy,
            text="â—‰",
            fill=RED,
            font=(
                "Segoe UI",
                18,
                "bold"
            ),
            tags="core"
        )

        # ----------------------------------------------------
        # LABELS
        # ----------------------------------------------------

        self.core_canvas.create_text(
            cx,
            cy - 145,
            text="JARVIS NEURAL CORE",
            fill=RED,
            font=(
                "Consolas",
                8,
                "bold"
            ),
            tags="core"
        )

        self.core_canvas.create_text(
            cx - 150,
            cy + 100,
            text="AI",
            fill=GRAY_DARK,
            font=(
                "Consolas",
                7
            ),
            tags="core"
        )

        self.core_canvas.create_text(
            cx + 150,
            cy + 100,
            text="ONLINE",
            fill=RED_DARK,
            font=(
                "Consolas",
                7
            ),
            tags="core"
        )


    def animate_hud(self):

        if not self.running:

            return

        # ----------------------------------------------------
        # PULSE LOGO
        # ----------------------------------------------------

        if self.current_state == "ONLINE":

            current = self.logo.cget(
                "fg"
            )

            self.logo.configure(
                fg=(
                    RED_BRIGHT
                    if current == RED
                    else RED
                )
            )

        # ----------------------------------------------------
        # ROTATING CORE EFFECT
        # ----------------------------------------------------

        try:

            self.core_canvas.delete(
                "pulse"
            )

            width = self.core_canvas.winfo_width()

            height = self.core_canvas.winfo_height()

            cx = width // 2

            cy = height // 2

            pulse = int(
                38 + 5 * (
                    time.time() % 1
                )
            )

            self.core_canvas.create_oval(
                cx - pulse,
                cy - pulse,
                cx + pulse,
                cy + pulse,
                outline=RED_DARK,
                width=1,
                tags="pulse"
            )

        except Exception:
            pass

        self.after(
            120,
            self.animate_hud
        )


    # ========================================================
    # IMAGE DISPLAY
    # ========================================================

    def display_image(self, path):

        if not os.path.isfile(
            path
        ):

            return

        self.current_image = path

        self.image_info.configure(
            text=(
                "VISUAL BUFFER: READY\n"
                + os.path.basename(path)
            ),
            fg=RED
        )

        # ----------------------------------------------------
        # RIGHT PREVIEW
        # ----------------------------------------------------

        if Image and ImageTk:

            try:

                image = Image.open(
                    path
                )

                image.thumbnail(
                    (
                        270,
                        260
                    )
                )

                photo = ImageTk.PhotoImage(
                    image
                )

                self.preview.configure(
                    image=photo,
                    text=""
                )

                self.preview.image = photo

            except Exception as e:

                self.preview.configure(
                    image="",
                    text=(
                        "IMAGE\n"
                        "LOAD ERROR"
                    )
                )

        else:

            self.preview.configure(
                text=(
                    "IMAGE READY\n\n"
                    + os.path.basename(path)
                )
            )

        # ----------------------------------------------------
        # CHAT IMAGE
        # ----------------------------------------------------

        if Image and ImageTk:

            try:

                image = Image.open(
                    path
                )

                image.thumbnail(
                    (
                        420,
                        280
                    )
                )

                photo = ImageTk.PhotoImage(
                    image
                )

                self.image_label.configure(
                    image=photo,
                    text=""
                )

                self.image_label.image = photo

            except Exception:
                pass


    # ========================================================
    # IMAGE OPEN
    # ========================================================

    def open_image(self, event=None):

        if not self.current_image:

            return

        if not os.path.isfile(
            self.current_image
        ):

            return

        if not Image or not ImageTk:

            os.startfile(
                self.current_image
            )

            return

        # ----------------------------------------------------
        # CLOSE OLD
        # ----------------------------------------------------

        if (
            self.preview_window
            and self.preview_window.winfo_exists()
        ):

            self.preview_window.destroy()

        # ----------------------------------------------------
        # WINDOW
        # ----------------------------------------------------

        window = tk.Toplevel(
            self
        )

        self.preview_window = window

        window.title(
            "JARVIS // VISUAL OUTPUT"
        )

        window.configure(
            bg=BLACK
        )

        window.geometry(
            "1000x750"
        )

        # ----------------------------------------------------
        # IMAGE
        # ----------------------------------------------------

        try:

            image = Image.open(
                self.current_image
            )

            max_w = 950

            max_h = 650

            image.thumbnail(
                (
                    max_w,
                    max_h
                )
            )

            photo = ImageTk.PhotoImage(
                image
            )

            label = tk.Label(
                window,
                image=photo,
                bg=BLACK
            )

            label.image = photo

            label.pack(
                expand=True
            )

            tk.Label(
                window,
                text=(
                    "JARVIS // VISUAL CORE\n"
                    + os.path.basename(
                        self.current_image
                    )
                ),
                font=(
                    "Consolas",
                    9
                ),
                fg=RED,
                bg=BLACK
            ).pack(
                pady=10
            )

        except Exception as e:

            tk.Label(
                window,
                text=str(e),
                fg=RED,
                bg=BLACK
            ).pack(
                expand=True
            )


    # ========================================================
    # CLOSE
    # ========================================================

    def on_close(self):

        self.running = False

        try:

            self.voice.stop()

        except Exception:
            pass

        self.destroy()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    app = HUD()

    app.mainloop()


