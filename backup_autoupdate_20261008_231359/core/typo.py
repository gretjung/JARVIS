import json
import os
import re
from difflib import SequenceMatcher


# ============================================================
# PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

MEMORY_DIR = os.path.join(
    BASE_DIR,
    "memory"
)

TYPO_FILE = os.path.join(
    MEMORY_DIR,
    "typos.json"
)


# ============================================================
# KNOWN COMMANDS
# ============================================================

KNOWN_COMMANDS = [

    # IMAGE MODE
    "เปิดโหมดเจนภาพ",
    "ปิดโหมดสร้างภาพ",
    "สถานะโหมดเจนภาพ",

    # IMAGE
    "สร้างภาพ",
    "สร้างรูป",
    "เจนภาพ",
    "เจนรูป",
    "วาดภาพ",
    "สร้างรูปภาพ",

    # SYSTEM
    "ข้อมูลระบบ",
    "สเป็คคอม",

    # WEB
    "ค้นเว็บ",
    "ค้นหาในเว็บ",
    "ค้นข่าว",
    "ค้นข้อมูล",

    # MEMORY
    "จำไว้ว่",
    "จำไว้ว่า",

    # ENGLISH
    "generate image",
    "generate picture",
    "create image",
    "search web",
    "system info",
]


# ============================================================
# NORMALIZE
# ============================================================

def normalize(text):

    if text is None:
        return ""

    text = str(text)

    text = text.strip()

    text = text.lower()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


# ============================================================
# LOAD
# ============================================================

def load_typos():

    os.makedirs(
        MEMORY_DIR,
        exist_ok=True
    )

    if not os.path.exists(TYPO_FILE):
        return {}

    try:

        with open(
            TYPO_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if isinstance(data, dict):
            return data

    except Exception as e:

        print(
            f"[TYPO] Load error: {e}"
        )

    return {}


# ============================================================
# SAVE
# ============================================================

def save_typos(data):

    os.makedirs(
        MEMORY_DIR,
        exist_ok=True
    )

    try:

        with open(
            TYPO_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2
            )

    except Exception as e:

        print(
            f"[TYPO] Save error: {e}"
        )


# ============================================================
# LEARN TYPO
# ============================================================

def learn_typo(
    wrong,
    correct
):

    wrong = normalize(wrong)

    correct = normalize(correct)

    if not wrong:
        return

    if not correct:
        return

    if wrong == correct:
        return

    data = load_typos()

    if wrong not in data:

        data[wrong] = {
            "correct": correct,
            "count": 1
        }

    else:

        old_correct = normalize(
            data[wrong].get(
                "correct",
                ""
            )
        )

        if old_correct == correct:

            data[wrong]["count"] = (
                data[wrong].get(
                    "count",
                    0
                ) + 1
            )

        else:

            data[wrong] = {
                "correct": correct,
                "count": 1
            }

    save_typos(data)

    print(
        "[TYPO LEARN] "
        f"{wrong} -> {correct}"
    )


# ============================================================
# GET LEARNED TYPO
# ============================================================

def get_learned_typo(text):

    text = normalize(text)

    data = load_typos()

    if text in data:

        return data[text].get(
            "correct"
        )

    return None


# ============================================================
# SIMILARITY
# ============================================================

def similarity(
    a,
    b
):

    a = normalize(a)

    b = normalize(b)

    if not a or not b:
        return 0.0

    return SequenceMatcher(
        None,
        a,
        b
    ).ratio()


# ============================================================
# FIND BEST COMMAND
# ============================================================

def find_best_command(text):

    text = normalize(text)

    if not text:

        return (
            None,
            0.0
        )

    # EXACT MATCH

    for command in KNOWN_COMMANDS:

        if text == normalize(command):

            return (
                command,
                1.0
            )

    # FUZZY

    best_command = None

    best_score = 0.0

    for command in KNOWN_COMMANDS:

        score = similarity(
            text,
            command
        )

        if score > best_score:

            best_score = score

            best_command = command

    return (
        best_command,
        best_score
    )


# ============================================================
# CORRECT COMMAND
# ============================================================

def correct_command(text):

    original = text

    normalized = normalize(text)

    # --------------------------------------------------------
    # LEARNED TYPO
    # --------------------------------------------------------

    learned = get_learned_typo(
        normalized
    )

    if learned:

        return {

            "original": original,

            "corrected": learned,

            "confidence": 1.0,

            "changed": (
                learned != normalized
            ),

            "source": "learned"
        }

    # --------------------------------------------------------
    # FUZZY
    # --------------------------------------------------------

    best, score = find_best_command(
        normalized
    )

    if best is None:

        return {

            "original": original,

            "corrected": original,

            "confidence": 0.0,

            "changed": False,

            "source": "none"
        }

    # --------------------------------------------------------
    # HIGH
    # --------------------------------------------------------

    if score >= 0.90:

        return {

            "original": original,

            "corrected": best,

            "confidence": score,

            "changed": (
                best != normalized
            ),

            "source": "fuzzy_high"
        }

    # --------------------------------------------------------
    # MEDIUM
    # --------------------------------------------------------

    if score >= 0.75:

        return {

            "original": original,

            "corrected": best,

            "confidence": score,

            "changed": (
                best != normalized
            ),

            "source": "fuzzy_medium"
        }

    # --------------------------------------------------------
    # LOW
    # --------------------------------------------------------

    return {

        "original": original,

        "corrected": original,

        "confidence": score,

        "changed": False,

        "source": "fuzzy_low"
    }


# ============================================================
# SUGGEST
# ============================================================

def suggest_correction(text):

    result = correct_command(
        text
    )

    return {

        "input": text,

        "suggestion": result[
            "corrected"
        ],

        "confidence": result[
            "confidence"
        ],

        "source": result[
            "source"
        ]
    }


# ============================================================
# YES
# ============================================================

def is_yes(text):

    text = normalize(text)

    yes_words = [

        "ใช่",
        "ใช่ครับ",
        "ใช่ค่ะ",

        "ถูก",
        "ถูกต้อง",

        "เอาอันนี้",
        "ตกลง",

        "โอเค",
        "โอเคครับ",
        "โอเคค่ะ",

        "ok",
        "okay",

        "yes",
        "y"
    ]

    return text in yes_words


# ============================================================
# NO
# ============================================================

def is_no(text):

    text = normalize(text)

    no_words = [

        "ไม่",
        "ไม่ใช่",
        "ไม่ครับ",
        "ไม่ค่ะ",

        "ผิด",
        "ไม่ถูก",

        "ยกเลิก",

        "cancel",

        "no",
        "n"
    ]

    return text in no_words