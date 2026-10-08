# ============================================================
# JARVIS HUD 3.0 - SPIDER MODE
# GUI ONLY
#
# Backend preserved:
# Agent / Voice / VoiceListener / Router / Memory /
# Windows / ComfyUI / Image Generation
# ============================================================

import os
import re
import math
import time
import threading
import tkinter as tk
from tkinter import filedialog

from core.agent import Agent
from core.voice import Voice
from core.listener import VoiceListener


class HUD(tk.Tk):

    BG = "#05070b"
    PANEL = "#090d14"
    PANEL2 = "#0d121b"

    RED = "#e5092f"
    RED_DARK = "#5f0718"
    BLUE = "#149cff"
    BLUE_DARK = "#07345a"

    WHITE = "#e8f4ff"
    GREY = "#718096"
    GREEN = "#20d98a"
    YELLOW = "#ffc857"

    FONT = "Segoe UI"

    def __init__(self):

        super().__init__()

        self.title("JARVIS — SPIDER MODE")

        self.geometry("1500x900")
        self.minsize(1100, 700)

        self.configure(bg=self.BG)

        self.running = True

        # ----------------------------------------------------
        # BACKEND — DO NOT CHANGE
        # ----------------------------------------------------

        self.voice = Voice()
        self.agent = Agent(voice=self.voice)

        self.voice_listener = VoiceListener(
            agent=self.agent
        )

        # ----------------------------------------------------
        # GUI STATE
        # ----------------------------------------------------

        self.current_state = "ONLINE"
        self.listener_online = False
        self.last_image_path = None

        self.chat_history = []

        # ----------------------------------------------------
        # REALTIME AGENT STATE
        # ----------------------------------------------------

        self.agent_future = None
        self.agent_streaming = False
        self.agent_stream_buffer = ""
        self.agent_request_text = ""

        self.animation_phase = 0

        # ----------------------------------------------------
        # WINDOW
        # ----------------------------------------------------

        self.protocol(
            "WM_DELETE_WINDOW",
            self.on_close
        )

        self._build_gui()

        self.after(
            100,
            self.animation_loop
        )

        self.after(
            500,
            self.update_status
        )

    # ========================================================
    # GUI BUILD
    # ========================================================

    def _build_gui(self):

        self._build_topbar()

        self._build_main_area()

        self._build_bottom()

    # ========================================================
    # TOP BAR
    # ========================================================

    def _build_topbar(self):

        self.topbar = tk.Frame(
            self,
            bg=self.BG,
            height=70
        )

        self.topbar.pack(
            fill="x",
            padx=18,
            pady=(12, 5)
        )

        self.topbar.pack_propagate(False)

        # Spider emblem

        self.logo_canvas = tk.Canvas(
            self.topbar,
            width=48,
            height=48,
            bg=self.BG,
            highlightthickness=0
        )

        self.logo_canvas.pack(
            side="left",
            padx=(8, 10)
        )

        self._draw_spider_logo()

        title_frame = tk.Frame(
            self.topbar,
            bg=self.BG
        )

        title_frame.pack(
            side="left"
        )

        tk.Label(
            title_frame,
            text="JARVIS",
            font=(self.FONT, 22, "bold"),
            fg=self.WHITE,
            bg=self.BG
        ).pack(anchor="w")

        tk.Label(
            title_frame,
            text="SPIDER MODE  •  PERSONAL ARTIFICIAL INTELLIGENCE",
            font=(self.FONT, 8, "bold"),
            fg=self.RED,
            bg=self.BG
        ).pack(anchor="w")

        # Right side

        status_frame = tk.Frame(
            self.topbar,
            bg=self.BG
        )

        status_frame.pack(
            side="right",
            padx=10
        )

        self.system_status = tk.Label(
            status_frame,
            text="● SYSTEM ONLINE",
            font=(self.FONT, 10, "bold"),
            fg=self.GREEN,
            bg=self.BG
        )

        self.system_status.pack(
            anchor="e"
        )

        self.clock_label = tk.Label(
            status_frame,
            text="",
            font=(self.FONT, 9),
            fg=self.GREY,
            bg=self.BG
        )

        self.clock_label.pack(
            anchor="e"
        )

    # ========================================================
    # MAIN AREA
    # ========================================================

    def _build_main_area(self):

        self.main = tk.Frame(
            self,
            bg=self.BG
        )

        self.main.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=5
        )

        # 3 columns

        self.left = tk.Frame(
            self.main,
            bg=self.PANEL,
            width=260,
            highlightbackground=self.RED_DARK,
            highlightthickness=1
        )

        self.left.pack(
            side="left",
            fill="y",
            padx=(0, 7)
        )

        self.left.pack_propagate(False)

        self.center = tk.Frame(
            self.main,
            bg=self.PANEL,
            highlightbackground=self.BLUE_DARK,
            highlightthickness=1
        )

        self.center.pack(
            side="left",
            fill="both",
            expand=True,
            padx=7
        )

        self.right = tk.Frame(
            self.main,
            bg=self.PANEL,
            width=320,
            highlightbackground=self.RED_DARK,
            highlightthickness=1
        )

        self.right.pack(
            side="right",
            fill="y",
            padx=(7, 0)
        )

        self.right.pack_propagate(False)

        self._build_system_panel()
        self._build_neural_panel()
        self._build_visual_panel()

    # ========================================================
    # SYSTEM PANEL
    # ========================================================

    def _build_system_panel(self):

        self.panel_title(
            self.left,
            "SYSTEM CORE",
            self.RED
        )

        self.system_items = {}

        items = [
            ("AI CORE", "ONLINE"),
            ("IDENTITY", "JARVIS"),
            ("VOICE", "PATTARA"),
            ("LISTENER", "OFFLINE"),
            ("OLLAMA", "ONLINE"),
            ("MEMORY", "ONLINE"),
            ("ROUTER", "ONLINE"),
            ("COMFYUI", "READY"),
            ("IMAGE MODE", "OFF"),
        ]

        for name, value in items:

            row = tk.Frame(
                self.left,
                bg=self.PANEL
            )

            row.pack(
                fill="x",
                padx=15,
                pady=5
            )

            tk.Label(
                row,
                text=name,
                font=(self.FONT, 8, "bold"),
                fg=self.GREY,
                bg=self.PANEL
            ).pack(
                side="left"
            )

            label = tk.Label(
                row,
                text=value,
                font=(self.FONT, 8, "bold"),
                fg=self.GREEN,
                bg=self.PANEL
            )

            label.pack(
                side="right"
            )

            self.system_items[name] = label

        tk.Frame(
            self.left,
            bg=self.RED_DARK,
            height=1
        ).pack(
            fill="x",
            padx=15,
            pady=12
        )

        tk.Label(
            self.left,
            text="VOICE CONTROL",
            font=(self.FONT, 9, "bold"),
            fg=self.RED,
            bg=self.PANEL
        ).pack(
            anchor="w",
            padx=15
        )

        self.listener_button = tk.Button(
            self.left,
            text="◉  START LISTENER",
            command=self.toggle_voice_listener,
            font=(self.FONT, 9, "bold"),
            fg=self.WHITE,
            bg=self.PANEL2,
            activeforeground=self.WHITE,
            activebackground=self.RED_DARK,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=10,
            pady=10
        )

        self.listener_button.pack(
            fill="x",
            padx=15,
            pady=(8, 4)
        )

        self.voice_button = tk.Button(
            self.left,
            text="♪  VOICE TEST",
            command=self.test_voice,
            font=(self.FONT, 9, "bold"),
            fg=self.WHITE,
            bg=self.PANEL2,
            activeforeground=self.WHITE,
            activebackground=self.BLUE_DARK,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=10,
            pady=10
        )

        self.voice_button.pack(
            fill="x",
            padx=15,
            pady=4
        )

        self.panel_footer = tk.Label(
            self.left,
            text="SPIDER NEURAL SYSTEM\nv3.0",
            font=(self.FONT, 8, "bold"),
            fg=self.RED,
            bg=self.PANEL,
            justify="left"
        )

        self.panel_footer.pack(
            side="bottom",
            anchor="w",
            padx=15,
            pady=15
        )

    # ========================================================
    # NEURAL PANEL
    # ========================================================

    def _build_neural_panel(self):

        self.panel_title(
            self.center,
            "NEURAL CORE",
            self.BLUE
        )

        self.core_canvas = tk.Canvas(
            self.center,
            bg=self.PANEL,
            highlightthickness=0
        )

        self.core_canvas.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        self.core_canvas.bind(
            "<Configure>",
            lambda e: self.draw_neural_core()
        )

        # Chat section

        chat_frame = tk.Frame(
            self.center,
            bg=self.PANEL,
            height=230
        )

        chat_frame.pack(
            fill="x",
            padx=15,
            pady=(0, 12)
        )

        chat_frame.pack_propagate(False)

        self.panel_title(
            chat_frame,
            "NEURAL INTERFACE",
            self.RED
        )

        self.chat = tk.Text(
            chat_frame,
            bg="#04060a",
            fg=self.WHITE,
            insertbackground=self.RED,
            selectbackground=self.RED_DARK,
            selectforeground=self.WHITE,
            font=(self.FONT, 10),
            relief="flat",
            bd=0,
            wrap="word"
        )

        self.chat.pack(
            fill="both",
            expand=True,
            padx=1,
            pady=1
        )

        self.chat.configure(
            state="disabled"
        )

        self.chat.tag_configure(
            "user",
            foreground=self.BLUE
        )

        self.chat.tag_configure(
            "jarvis",
            foreground=self.RED
        )

        self.chat.tag_configure(
            "system",
            foreground=self.GREEN
        )

    # ========================================================
    # VISUAL PANEL
    # ========================================================

    def _build_visual_panel(self):

        self.panel_title(
            self.right,
            "VISUAL CORE",
            self.RED
        )

        self.visual_status = tk.Label(
            self.right,
            text="● IMAGE MODE READY",
            font=(self.FONT, 9, "bold"),
            fg=self.GREEN,
            bg=self.PANEL
        )

        self.visual_status.pack(
            anchor="w",
            padx=15,
            pady=(0, 8)
        )

        self.image_canvas = tk.Canvas(
            self.right,
            bg="#030508",
            highlightbackground=self.RED_DARK,
            highlightthickness=1
        )

        self.image_canvas.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=5
        )

        self.image_canvas.create_text(
            160,
            220,
            text="VISUAL CORE\n\nNO IMAGE",
            fill=self.GREY,
            font=(self.FONT, 11, "bold"),
            justify="center",
            tags="placeholder"
        )

        tk.Button(
            self.right,
            text="OPEN LAST IMAGE",
            command=self.open_last_image,
            font=(self.FONT, 8, "bold"),
            fg=self.WHITE,
            bg=self.PANEL2,
            activebackground=self.RED_DARK,
            activeforeground=self.WHITE,
            relief="flat",
            bd=0,
            cursor="hand2",
            pady=9
        ).pack(
            fill="x",
            padx=15,
            pady=10
        )

    # ========================================================
    # BOTTOM
    # ========================================================

    def _build_bottom(self):

        bottom = tk.Frame(
            self,
            bg=self.BG,
            height=70
        )

        bottom.pack(
            fill="x",
            padx=18,
            pady=(5, 15)
        )

        bottom.pack_propagate(False)

        self.listener_status_label = tk.Label(
            bottom,
            text="● LISTENER OFFLINE",
            font=(self.FONT, 8, "bold"),
            fg=self.GREY,
            bg=self.BG,
            width=22
        )

        self.listener_status_label.pack(
            side="left",
            padx=(0, 8)
        )

        self.entry = tk.Entry(
            bottom,
            bg="#080b11",
            fg=self.WHITE,
            insertbackground=self.RED,
            selectbackground=self.RED_DARK,
            selectforeground=self.WHITE,
            font=(self.FONT, 11),
            relief="flat",
            bd=1
        )

        self.entry.pack(
            side="left",
            fill="both",
            expand=True,
            ipady=12
        )

        self.entry.bind(
            "<Return>",
            self.send_command
        )

        # Clipboard shortcuts

        self.entry.bind(
            "<Control-a>",
            self._select_all
        )

        self.entry.bind(
            "<Control-c>",
            self._copy
        )

        self.entry.bind(
            "<Control-x>",
            self._cut
        )

        self.entry.bind(
            "<Control-v>",
            self._paste
        )

        self.entry.bind(
            "<Control-Insert>",
            self._copy
        )

        self.entry.bind(
            "<Shift-Insert>",
            self._paste
        )

        self.execute_button = tk.Button(
            bottom,
            text="EXECUTE  ▶",
            command=self.send_command,
            font=(self.FONT, 10, "bold"),
            fg=self.WHITE,
            bg=self.RED_DARK,
            activeforeground=self.WHITE,
            activebackground=self.RED,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=25
        )

        self.execute_button.pack(
            side="right",
            fill="y",
            padx=(8, 0)
        )

    # ========================================================
    # PANEL TITLE
    # ========================================================

    def panel_title(self, parent, text, color):

        frame = tk.Frame(
            parent,
            bg=parent.cget("bg"),
            height=40
        )

        frame.pack(
            fill="x",
            padx=15,
            pady=(12, 5)
        )

        frame.pack_propagate(False)

        tk.Label(
            frame,
            text=text,
            font=(self.FONT, 10, "bold"),
            fg=color,
            bg=parent.cget("bg")
        ).pack(
            side="left"
        )

        tk.Frame(
            frame,
            bg=color,
            height=1
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(10, 0)
        )

    # ========================================================
    # SPIDER LOGO
    # ========================================================

    def _draw_spider_logo(self):

        c = self.logo_canvas

        c.delete("all")

        cx = 24
        cy = 24

        c.create_oval(
            5,
            5,
            43,
            43,
            outline=self.RED_DARK,
            width=1
        )

        c.create_oval(
            10,
            10,
            38,
            38,
            outline=self.RED,
            width=1
        )

        # Spider body

        c.create_oval(
            20,
            16,
            28,
            31,
            fill=self.RED,
            outline=""
        )

        c.create_oval(
            21,
            10,
            27,
            18,
            fill=self.RED,
            outline=""
        )

        # Legs

        for side in (-1, 1):

            for i in range(3):

                y = 17 + i * 6

                c.create_line(
                    cx + side * 4,
                    y,
                    cx + side * 13,
                    y - 5,
                    fill=self.RED,
                    width=2
                )

                c.create_line(
                    cx + side * 13,
                    y - 5,
                    cx + side * 18,
                    y,
                    fill=self.RED,
                    width=1
                )

    # ========================================================
    # NEURAL CORE DRAWING
    # ========================================================

    def draw_neural_core(self):

        if not self.running:
            return

        c = self.core_canvas

        c.delete("core")

        width = max(
            c.winfo_width(),
            500
        )

        height = max(
            c.winfo_height(),
            400
        )

        cx = width / 2
        cy = height / 2 - 20

        base = min(
            width,
            height
        )

        phase = self.animation_phase

        # Background web

        self._draw_web(
            c,
            cx,
            cy,
            base * 0.43
        )

        # Outer rings

        for i in range(5):

            radius = (
                base * 0.12
                + i * base * 0.045
            )

            offset = math.sin(
                phase * 0.02 + i
            ) * 3

            color = (
                self.BLUE
                if i % 2 == 0
                else self.RED
            )

            c.create_oval(
                cx - radius - offset,
                cy - radius - offset,
                cx + radius + offset,
                cy + radius + offset,
                outline=color,
                width=1,
                tags="core"
            )

        # Crosshair

        r = base * 0.31

        c.create_line(
            cx - r,
            cy,
            cx + r,
            cy,
            fill=self.BLUE_DARK,
            width=1,
            tags="core"
        )

        c.create_line(
            cx,
            cy - r,
            cx,
            cy + r,
            fill=self.BLUE_DARK,
            width=1,
            tags="core"
        )

        # Rotating scan arcs

        for i in range(4):

            radius = base * (
                0.20 + i * 0.055
            )

            start = (
                phase * (1.5 + i * 0.25)
            ) % 360

            color = (
                self.RED
                if i % 2 == 0
                else self.BLUE
            )

            c.create_arc(
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
                start=start,
                extent=75,
                outline=color,
                width=3,
                style="arc",
                tags="core"
            )

        # Central Spider Core

        core_r = base * 0.09

        c.create_oval(
            cx - core_r,
            cy - core_r,
            cx + core_r,
            cy + core_r,
            fill="#080b12",
            outline=self.RED,
            width=2,
            tags="core"
        )

        # Spider emblem

        self._draw_core_spider(
            c,
            cx,
            cy,
            core_r * 0.8
        )

        # Status

        state_text = self.current_state

        state_color = {
            "ONLINE": self.GREEN,
            "LISTENING": self.BLUE,
            "THINKING": self.YELLOW,
            "SPEAKING": self.RED,
            "EXECUTING": self.RED,
            "GENERATING": self.BLUE,
            "ERROR": self.RED,
        }.get(
            state_text,
            self.WHITE
        )

        c.create_text(
            cx,
            cy + base * 0.39,
            text=state_text,
            fill=state_color,
            font=(self.FONT, 11, "bold"),
            tags="core"
        )

        c.create_text(
            cx,
            cy + base * 0.44,
            text="SPIDER NEURAL NETWORK",
            fill=self.GREY,
            font=(self.FONT, 7, "bold"),
            tags="core"
        )

    # ========================================================
    # WEB
    # ========================================================

    def _draw_web(self, c, cx, cy, radius):

        # Radial lines

        for i in range(12):

            angle = (
                math.pi * 2 * i / 12
            )

            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius

            c.create_line(
                cx,
                cy,
                x,
                y,
                fill="#24101a",
                width=1,
                tags="core"
            )

        # Curved web rings

        for ring in range(1, 6):

            r = radius * ring / 5

            points = []

            for i in range(49):

                angle = (
                    math.pi * 2 * i / 48
                )

                x = cx + math.cos(angle) * r
                y = cy + math.sin(angle) * r

                points.extend(
                    [x, y]
                )

            if points:

                c.create_line(
                    *points,
                    fill="#24101a",
                    width=1,
                    smooth=True,
                    tags="core"
                )

    # ========================================================
    # CORE SPIDER
    # ========================================================

    def _draw_core_spider(self, c, cx, cy, size):

        c.create_oval(
            cx - size * 0.22,
            cy - size * 0.48,
            cx + size * 0.22,
            cy + size * 0.42,
            fill=self.RED,
            outline=""
        )

        c.create_oval(
            cx - size * 0.18,
            cy - size * 0.72,
            cx + size * 0.18,
            cy - size * 0.35,
            fill=self.RED,
            outline=""
        )

        for side in (-1, 1):

            for i in range(4):

                y = (
                    cy
                    - size * 0.35
                    + i * size * 0.22
                )

                x1 = (
                    cx
                    + side * size * 0.16
                )

                x2 = (
                    cx
                    + side * size * (
                        0.55 + i * 0.06
                    )
                )

                c.create_line(
                    x1,
                    y,
                    x2,
                    y - size * 0.18,
                    fill=self.RED,
                    width=2,
                    tags="core"
                )

    # ========================================================
    # COMMAND — REALTIME AGENT
    # ========================================================

    def send_command(self, event=None):

        text = self.entry.get().strip()

        if not text:
            return

        # Prevent accidental command stacking.
        if self.agent.is_busy():

            self.add_chat(
                "SYSTEM",
                "JARVIS กำลังทำงานอยู่ครับ"
            )

            return

        self.entry.delete(
            0,
            "end"
        )

        self.add_chat(
            "YOU",
            text
        )

        self.agent_request_text = text
        self.agent_streaming = False
        self.agent_stream_buffer = ""

        self.set_state(
            "THINKING"
        )

        try:

            self.agent_future = self.agent.handle_async(
                text,
                callback=self._agent_gui_callback,
                stream=True
            )

            if self.agent_future is None:

                self.add_chat(
                    "SYSTEM",
                    "ไม่สามารถเริ่มคำสั่งได้ครับ"
                )

                self.set_state(
                    "ERROR"
                )

                self.after(
                    1000,
                    lambda: self.set_state("ONLINE")
                )

        except Exception as e:

            error = (
                f"เกิดข้อผิดพลาดครับ: {e}"
            )

            self.add_chat(
                "JARVIS",
                error
            )

            self.set_state(
                "ERROR"
            )

            self.after(
                1000,
                lambda: self.set_state("ONLINE")
            )

    def _agent_gui_callback(self, token, final_result):

        # ----------------------------------------------------
        # STREAMING TOKEN
        # ----------------------------------------------------

        if token is not None:

            token = str(token)

            if not token:
                return

            self.after(
                0,
                lambda t=token:
                self._append_stream_token(t)
            )

            return

        # ----------------------------------------------------
        # FINAL RESULT
        # ----------------------------------------------------

        result = final_result

        if result is None:
            result = "ดำเนินการเสร็จแล้วครับ"

        result = str(result)

        self.after(
            0,
            lambda r=result:
            self._finish_agent_response(r)
        )

    def _append_stream_token(self, token):

        if not self.agent_streaming:

            self.agent_streaming = True
            self.agent_stream_buffer = ""

            self.chat.configure(
                state="normal"
            )

            self.chat.insert(
                "end",
                "\nJARVIS\n",
                "jarvis"
            )

        self.agent_stream_buffer += token

        self.chat.insert(
            "end",
            token
        )

        self.chat.see(
            "end"
        )

        self.chat.configure(
            state="disabled"
        )

        self.set_state(
            "THINKING"
        )

    def _finish_agent_response(self, result):

        # ----------------------------------------------------
        # STREAMING RESPONSE
        # ----------------------------------------------------

        if self.agent_streaming:

            # Agent already streamed the complete response.
            # Only finish the UI state here.

            self.chat.configure(
                state="normal"
            )

            self.chat.insert(
                "end",
                "\n"
            )

            self.chat.see(
                "end"
            )

            self.chat.configure(
                state="disabled"
            )

        # ----------------------------------------------------
        # NORMAL SKILL RESPONSE
        # ----------------------------------------------------

        else:

            self.add_chat(
                "JARVIS",
                result
            )

        # ----------------------------------------------------
        # IMAGE RESULT
        # ----------------------------------------------------

        match = re.search(
            r"IMAGE_PATH:\s*(.+)",
            result
        )

        if match:

            path = match.group(1).strip()

            if os.path.exists(path):

                self.last_image_path = path

                self.show_image(
                    path
                )

        # ----------------------------------------------------
        # FINAL STATE
        # ----------------------------------------------------

        self.agent_streaming = False
        self.agent_stream_buffer = ""
        self.agent_future = None

        self.set_state(
            "ONLINE"
        )

    # ========================================================
    # CHAT
    # ========================================================

    def add_chat(self, speaker, text):

        self.chat.configure(
            state="normal"
        )

        if speaker == "YOU":

            self.chat.insert(
                "end",
                "\nYOU\n",
                "user"
            )

        elif speaker == "JARVIS":

            self.chat.insert(
                "end",
                "\nJARVIS\n",
                "jarvis"
            )

        else:

            self.chat.insert(
                "end",
                "\nSYSTEM\n",
                "system"
            )

        self.chat.insert(
            "end",
            text + "\n"
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

        self.after(
            0,
            self.draw_neural_core
        )

        if state == "LISTENING":

            self.system_status.configure(
                text="● LISTENING",
                fg=self.BLUE
            )

        elif state == "THINKING":

            self.system_status.configure(
                text="● THINKING",
                fg=self.YELLOW
            )

        elif state == "EXECUTING":

            self.system_status.configure(
                text="● EXECUTING",
                fg=self.RED
            )

        elif state == "SPEAKING":

            self.system_status.configure(
                text="● SPEAKING",
                fg=self.RED
            )

        elif state == "GENERATING":

            self.system_status.configure(
                text="● GENERATING",
                fg=self.BLUE
            )

        elif state == "ERROR":

            self.system_status.configure(
                text="● ERROR",
                fg=self.RED
            )

        else:

            self.system_status.configure(
                text="● SYSTEM ONLINE",
                fg=self.GREEN
            )

    # ========================================================
    # VOICE LISTENER
    # ========================================================

    def toggle_voice_listener(self):

        try:

            if self.voice_listener.running:

                self.voice_listener.stop()

                self.listener_online = False

                self.listener_button.configure(
                    text="◉  START LISTENER"
                )

                self.set_state(
                    "ONLINE"
                )

            else:

                success = self.voice_listener.start()

                if success:

                    self.listener_online = True

                    self.listener_button.configure(
                        text="■  STOP LISTENER"
                    )

                    self.set_state(
                        "LISTENING"
                    )

        except Exception as e:

            self.add_chat(
                "SYSTEM",
                f"Listener error: {e}"
            )

    # ========================================================
    # STATUS UPDATE
    # ========================================================

    def update_status(self):

        if not self.running:
            return

        try:

            listener_online = (
                self.voice_listener.running
            )

            if listener_online:

                self.system_items[
                    "LISTENER"
                ].configure(
                    text="ONLINE",
                    fg=self.GREEN
                )

                self.listener_status_label.configure(
                    text="● LISTENER ONLINE",
                    fg=self.BLUE
                )

            else:

                self.system_items[
                    "LISTENER"
                ].configure(
                    text="OFFLINE",
                    fg=self.GREY
                )

                self.listener_status_label.configure(
                    text="● LISTENER OFFLINE",
                    fg=self.GREY
                )

            self.clock_label.configure(
                text=time.strftime(
                    "%Y-%m-%d  %H:%M:%S"
                )
            )

            self.after(
                500,
                self.update_status
            )

        except Exception:
            pass

    # ========================================================
    # VOICE TEST
    # ========================================================

    def test_voice(self):

        def worker():

            try:

                self.set_state(
                    "SPEAKING"
                )

                self.voice.test_voice()

            except Exception as e:

                self.after(
                    0,
                    lambda: self.add_chat(
                        "SYSTEM",
                        f"Voice error: {e}"
                    )
                )

            finally:

                self.set_state(
                    "ONLINE"
                )

        threading.Thread(
            target=worker,
            daemon=True
        ).start()

    # ========================================================
    # IMAGE
    # ========================================================

    def show_image(self, path):

        try:

            from PIL import Image, ImageTk

            image = Image.open(
                path
            )

            width = max(
                self.image_canvas.winfo_width(),
                250
            )

            height = max(
                self.image_canvas.winfo_height(),
                250
            )

            image.thumbnail(
                (width - 20, height - 20)
            )

            self._image_tk = ImageTk.PhotoImage(
                image
            )

            self.image_canvas.delete(
                "all"
            )

            self.image_canvas.create_image(
                width / 2,
                height / 2,
                image=self._image_tk,
                anchor="center"
            )

            self.visual_status.configure(
                text="● IMAGE GENERATED",
                fg=self.GREEN
            )

        except Exception as e:

            self.add_chat(
                "SYSTEM",
                f"ไม่สามารถแสดงภาพได้ครับ: {e}"
            )

    def open_last_image(self):

        if not self.last_image_path:
            return

        if not os.path.exists(
            self.last_image_path
        ):
            return

        os.startfile(
            self.last_image_path
        )

    # ========================================================
    # CLIPBOARD
    # ========================================================

    def _select_all(self, event=None):

        self.entry.select_range(
            0,
            "end"
        )

        self.entry.icursor(
            "end"
        )

        return "break"

    def _copy(self, event=None):

        try:

            self.entry.event_generate(
                "<<Copy>>"
            )

        except Exception:
            pass

        return "break"

    def _cut(self, event=None):

        try:

            self.entry.event_generate(
                "<<Cut>>"
            )

        except Exception:
            pass

        return "break"

    def _paste(self, event=None):

        try:

            self.entry.event_generate(
                "<<Paste>>"
            )

        except Exception:
            pass

        return "break"

    # ========================================================
    # ANIMATION
    # ========================================================

    def animation_loop(self):

        if not self.running:
            return

        self.animation_phase += 2

        self.draw_neural_core()

        self.after(
            45,
            self.animation_loop
        )

    # ========================================================
    # CLOSE
    # ========================================================

    def on_close(self):

        self.running = False

        try:

            if self.voice_listener.running:
                self.voice_listener.stop()

        except Exception:
            pass

        try:

            self.voice.stop()

        except Exception:
            pass

        self.destroy()


if __name__ == "__main__":

    app = HUD()

    app.mainloop()

