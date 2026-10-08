# ============================================================
# JARVIS VISUAL CORE v2.0
# ============================================================

import re
import requests
from datetime import datetime


class VisualCore:

    VERSION = "2.0.0"
    MODEL = "qwen3:8b"
    OLLAMA_URL = "http://127.0.0.1:11434/api/chat"

    SUBJECT_RULES = {

        "รถสปอร์ตสีดำ": {
            "positive": (
                "a realistic modern black sports car, "
                "high-performance black automobile, "
                "four wheels, aerodynamic car body, "
                "road-going performance vehicle"
            ),
            "negative": (
                "train, railway, locomotive, subway, tram, "
                "railroad, railway carriage, bus, truck"
            ),
        },

        "รถสปอร์ต": {
            "positive": (
                "a realistic modern sports car, "
                "high-performance automobile, "
                "four wheels, aerodynamic car body, "
                "road-going performance vehicle"
            ),
            "negative": (
                "train, railway, locomotive, subway, tram, "
                "railroad, railway carriage"
            ),
        },

        "รถยนต์": {
            "positive": (
                "a realistic automobile, passenger car, "
                "four wheels, road vehicle"
            ),
            "negative": (
                "train, railway, locomotive, subway, tram"
            ),
        },

        "รถไฟ": {
            "positive": (
                "a realistic railway train, locomotive, "
                "multiple train carriages, railway vehicle"
            ),
            "negative": (
                "sports car, automobile, supercar, sedan"
            ),
        },

        "มอเตอร์ไซค์": {
            "positive": (
                "a realistic motorcycle, two-wheeled motorbike, "
                "street motorcycle"
            ),
            "negative": (
                "car, automobile, train, bus"
            ),
        },

        "เครื่องบิน": {
            "positive": (
                "a realistic passenger airplane, aircraft, "
                "large commercial jet"
            ),
            "negative": (
                "car, train, motorcycle, helicopter"
            ),
        },

        "คน": {
            "positive": (
                "a realistic human person, "
                "natural human anatomy, detailed face and body"
            ),
            "negative": (
                "robot, mannequin, statue, distorted anatomy"
            ),
        },

        "ผู้ชาย": {
            "positive": (
                "a realistic adult man, "
                "natural human anatomy, detailed face"
            ),
            "negative": (
                "woman, child, mannequin, statue"
            ),
        },

        "ผู้หญิง": {
            "positive": (
                "a realistic adult woman, "
                "natural human anatomy, detailed face"
            ),
            "negative": (
                "man, child, mannequin, statue"
            ),
        },

        "แมว": {
            "positive": (
                "a realistic domestic cat, "
                "natural feline anatomy, detailed fur"
            ),
            "negative": (
                "dog, fox, wolf, cartoon animal"
            ),
        },

        "สุนัข": {
            "positive": (
                "a realistic domestic dog, "
                "natural canine anatomy, detailed fur"
            ),
            "negative": (
                "cat, fox, wolf, cartoon animal"
            ),
        },
    }

    GENERAL_NEGATIVE = (
        "low quality, blurry, distorted, deformed, "
        "bad anatomy, malformed object, duplicate object, "
        "extra limbs, missing limbs, distorted proportions, "
        "extra wheels, missing wheels, text, watermark, logo, "
        "incorrect subject, unrelated object"
    )

    def __init__(self):

        self.last_prompt = ""
        self.last_negative_prompt = ""
        self.last_subject = ""
        self.last_result = {}

    def detect_subject(self, text):

        if not text:
            return None

        subjects = sorted(
            self.SUBJECT_RULES.keys(),
            key=len,
            reverse=True
        )

        for subject in subjects:

            if subject in text:
                return subject

        return None

    def get_subject_rule(self, subject):

        if not subject:
            return None

        return self.SUBJECT_RULES.get(subject)

    def clean_ai_response(self, text):

        if not text:
            return ""

        text = text.strip()

        text = re.sub(
            r"<think>.*?</think>",
            "",
            text,
            flags=re.I | re.S
        )

        text = re.sub(
            r"```(?:text|prompt|english)?",
            "",
            text,
            flags=re.I
        )

        text = text.replace("```", "")

        text = re.sub(
            r"^(prompt|english prompt|description)\s*:\s*",
            "",
            text,
            flags=re.I
        )

        return text.strip()

    def translate_with_ai(
        self,
        user_prompt,
        subject=None
    ):

        rule = self.get_subject_rule(subject)

        subject_anchor = ""

        if rule:

            subject_anchor = f"""
IMPORTANT SUBJECT ANCHOR:

{rule["positive"]}

The main subject MUST remain this exact type
of object or entity.

Do not reinterpret it.
"""

        system_prompt = f"""
You are the JARVIS Visual Prompt Core.

Convert the user's Thai image request into ONE
detailed English prompt optimized for FLUX.

Rules:

1. Preserve the user's intended subject exactly.
2. Never change one object type into another.
3. Clearly describe the main subject.
4. Preserve important colors and characteristics.
5. Add environment and composition when useful.
6. Add realistic lighting and camera details when useful.
7. Do not invent unrelated objects.
8. Output ONLY the final English image prompt.
9. Do not output JSON.
10. Do not explain your reasoning.

{subject_anchor}
"""

        payload = {
            "model": self.MODEL,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "options": {
                "temperature": 0.2,
                "top_p": 0.8,
            },
        }

        try:

            response = requests.post(
                self.OLLAMA_URL,
                json=payload,
                timeout=120
            )

            response.raise_for_status()

            data = response.json()

            content = (
                data
                .get("message", {})
                .get("content", "")
            )

            return self.clean_ai_response(content)

        except Exception as e:

            print(
                f"[JARVIS VISUAL] "
                f"Qwen translation error: {e}"
            )

            return ""

    def apply_subject_anchor(
        self,
        prompt,
        subject
    ):

        rule = self.get_subject_rule(subject)

        if not rule:
            return prompt

        anchor = rule["positive"]

        if anchor.lower() not in prompt.lower():

            prompt = (
                f"{anchor}. "
                f"{prompt}"
            )

        return prompt

    def build_negative_prompt(
        self,
        subject=None
    ):

        negatives = []

        rule = self.get_subject_rule(subject)

        if rule:
            negatives.append(
                rule["negative"]
            )

        negatives.append(
            self.GENERAL_NEGATIVE
        )

        parts = []

        for block in negatives:

            for item in block.split(","):

                item = item.strip()

                if item:
                    parts.append(item)

        unique = []
        seen = set()

        for item in parts:

            key = item.lower()

            if key not in seen:

                seen.add(key)
                unique.append(item)

        return ", ".join(unique)

    def validate_prompt(
        self,
        prompt,
        subject=None
    ):

        if not prompt:
            return False, "empty prompt"

        if len(prompt.strip()) < 10:
            return False, "prompt too short"

        if subject in (
            "รถสปอร์ต",
            "รถสปอร์ตสีดำ"
        ):

            forbidden = [
                "train",
                "railway",
                "locomotive",
                "subway",
                "tram",
                "railroad",
            ]

            lower = prompt.lower()

            for word in forbidden:

                if word in lower:

                    return False, (
                        f"subject conflict: {word}"
                    )

        return True, "valid"

    def fallback_prompt(
        self,
        user_prompt,
        subject=None
    ):

        rule = self.get_subject_rule(subject)

        if rule:

            return (
                f"{rule['positive']}. "
                f"{user_prompt}. "
                "realistic photography, "
                "high detail, natural lighting, "
                "cinematic composition"
            )

        return (
            f"{user_prompt}. "
            "high quality, detailed, "
            "realistic, cinematic composition"
        )

    def process(
        self,
        user_prompt
    ):

        if not user_prompt:

            return {
                "success": False,
                "prompt": "",
                "negative_prompt": "",
                "subject": None,
                "error": "empty prompt",
            }

        print(
            "[JARVIS VISUAL] Processing prompt..."
        )

        subject = self.detect_subject(
            user_prompt
        )

        if subject:

            print(
                f"[JARVIS VISUAL] "
                f"Subject detected: {subject}"
            )

        else:

            print(
                "[JARVIS VISUAL] "
                "Subject detected: generic"
            )

        prompt = self.translate_with_ai(
            user_prompt,
            subject
        )

        if not prompt:

            print(
                "[JARVIS VISUAL] "
                "Using deterministic fallback..."
            )

            prompt = self.fallback_prompt(
                user_prompt,
                subject
            )

        prompt = self.apply_subject_anchor(
            prompt,
            subject
        )

        valid, reason = self.validate_prompt(
            prompt,
            subject
        )

        if not valid:

            print(
                f"[JARVIS VISUAL] "
                f"Prompt rejected: {reason}"
            )

            prompt = self.fallback_prompt(
                user_prompt,
                subject
            )

            prompt = self.apply_subject_anchor(
                prompt,
                subject
            )

        negative_prompt = (
            self.build_negative_prompt(
                subject
            )
        )

        self.last_prompt = prompt
        self.last_negative_prompt = negative_prompt
        self.last_subject = subject

        result = {
            "success": True,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "subject": subject,
            "timestamp": datetime.now().isoformat(),
        }

        self.last_result = result

        print()
        print(
            "[JARVIS VISUAL] FINAL PROMPT:"
        )
        print(prompt)

        print()
        print(
            "[JARVIS VISUAL] NEGATIVE PROMPT:"
        )
        print(negative_prompt)

        return result

    def status(self):

        return {
            "core": "VISUAL CORE",
            "version": self.VERSION,
            "model": self.MODEL,
            "last_subject": self.last_subject,
            "last_prompt": self.last_prompt,
            "last_negative_prompt":
                self.last_negative_prompt,
        }


visual_core = VisualCore()


if __name__ == "__main__":

    print("=" * 60)
    print("JARVIS VISUAL CORE v2.0")
    print("=" * 60)

    result = visual_core.process(
        "สร้างภาพ รถสปอร์ตสีดำ "
        "จอดอยู่บนถนนกรุงเทพตอนกลางคืน"
    )

    print()
    print("RESULT")
    print(result)

    print("=" * 60)