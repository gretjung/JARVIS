# JARVIS MEMORY CORE v1.1

import json
import os
from datetime import datetime


class Memory:
    def __init__(self, memory_dir=None):
        if memory_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            memory_dir = os.path.join(base_dir, "memory")

        self.memory_dir = memory_dir
        self.memory_file = os.path.join(self.memory_dir, "memory.json")

        os.makedirs(self.memory_dir, exist_ok=True)

        self.data = {
            "facts": {},
            "preferences": {},
            "notes": [],
            "conversation": []
        }

        self.load()

        print("[JARVIS MEMORY] Memory Core v1.1 initialized.")

    # =========================================================
    # FILE
    # =========================================================

    def load(self):
        if not os.path.exists(self.memory_file):
            self.save()
            return

        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)

            if not isinstance(loaded, dict):
                print("[JARVIS MEMORY] Invalid memory format. Resetting.")
                self.save()
                return

            # -------------------------
            # FACTS
            # -------------------------
            facts = loaded.get("facts", {})

            if isinstance(facts, dict):
                self.data["facts"] = facts

            elif isinstance(facts, list):
                # รองรับรูปแบบเก่า
                converted = {}

                for item in facts:
                    if isinstance(item, dict):
                        key = item.get("key")
                        value = item.get("value")

                        if key is not None and value is not None:
                            converted[str(key)] = {
                                "value": str(value),
                                "updated": item.get(
                                    "updated",
                                    datetime.now().isoformat(timespec="seconds")
                                )
                            }

                self.data["facts"] = converted

            # -------------------------
            # PREFERENCES
            # -------------------------
            preferences = loaded.get("preferences", {})

            if isinstance(preferences, dict):
                self.data["preferences"] = preferences

            elif isinstance(preferences, list):
                converted = {}

                for item in preferences:
                    if isinstance(item, dict):
                        key = item.get("key")
                        value = item.get("value")

                        if key is not None and value is not None:
                            converted[str(key)] = {
                                "value": str(value),
                                "updated": item.get(
                                    "updated",
                                    datetime.now().isoformat(timespec="seconds")
                                )
                            }

                self.data["preferences"] = converted

            # -------------------------
            # NOTES
            # -------------------------
            notes = loaded.get("notes", [])

            if isinstance(notes, list):
                self.data["notes"] = notes

            # -------------------------
            # CONVERSATION
            # -------------------------
            conversation = loaded.get("conversation", [])

            if isinstance(conversation, list):
                self.data["conversation"] = conversation

            # บันทึกกลับเป็นโครงสร้างมาตรฐาน
            self.save()

        except Exception as e:
            print(f"[JARVIS MEMORY] Load error: {e}")

    def save(self):
        try:
            temp_file = self.memory_file + ".tmp"

            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(
                    self.data,
                    f,
                    ensure_ascii=False,
                    indent=2
                )

            os.replace(temp_file, self.memory_file)

            return True

        except Exception as e:
            print(f"[JARVIS MEMORY] Save error: {e}")
            return False

    # =========================================================
    # FACTS
    # =========================================================

    def remember(self, key, value):
        key = str(key).strip()
        value = str(value).strip()

        if not key or not value:
            return False

        self.data["facts"][key] = {
            "value": value,
            "updated": datetime.now().isoformat(timespec="seconds")
        }

        self.save()

        print(f"[JARVIS MEMORY] Remembered: {key} = {value}")

        return True

    def recall(self, key):
        key = str(key).strip()

        item = self.data["facts"].get(key)

        if not item:
            return None

        if isinstance(item, dict):
            return item.get("value")

        return str(item)

    def forget(self, key):
        key = str(key).strip()

        if key not in self.data["facts"]:
            return False

        del self.data["facts"][key]

        self.save()

        print(f"[JARVIS MEMORY] Forgotten: {key}")

        return True

    # =========================================================
    # SEARCH
    # =========================================================

    def search(self, query):
        query = str(query).strip().lower()

        if not query:
            return []

        results = []

        for key, item in self.data["facts"].items():

            if isinstance(item, dict):
                value = item.get("value", "")
            else:
                value = str(item)

            text = f"{key} {value}".lower()

            if query in text:
                results.append({
                    "key": key,
                    "value": value
                })

        return results

    # =========================================================
    # PREFERENCES
    # =========================================================

    def set_preference(self, key, value):
        key = str(key).strip()
        value = str(value).strip()

        if not key or not value:
            return False

        self.data["preferences"][key] = {
            "value": value,
            "updated": datetime.now().isoformat(timespec="seconds")
        }

        self.save()

        print(f"[JARVIS MEMORY] Preference: {key} = {value}")

        return True

    def get_preference(self, key):
        item = self.data["preferences"].get(str(key).strip())

        if not item:
            return None

        if isinstance(item, dict):
            return item.get("value")

        return str(item)

    # =========================================================
    # NOTES
    # =========================================================

    def add_note(self, text):
        text = str(text).strip()

        if not text:
            return False

        self.data["notes"].append({
            "text": text,
            "created": datetime.now().isoformat(timespec="seconds")
        })

        self.save()

        print(f"[JARVIS MEMORY] Note added: {text}")

        return True

    # =========================================================
    # CONVERSATION
    # =========================================================

    def add_conversation(self, role, content):
        if not content:
            return

        self.data["conversation"].append({
            "role": role,
            "content": content,
            "time": datetime.now().isoformat(timespec="seconds")
        })

        self.data["conversation"] = self.data["conversation"][-50:]

        self.save()

    def get_recent_conversation(self, limit=10):
        return self.data["conversation"][-limit:]

    # =========================================================
    # STATUS
    # =========================================================

    def count(self):
        return len(self.data["facts"])

    def status(self):
        return (
            "JARVIS MEMORY STATUS\n"
            "====================\n"
            f"FACTS        : {len(self.data['facts'])}\n"
            f"PREFERENCES  : {len(self.data['preferences'])}\n"
            f"NOTES        : {len(self.data['notes'])}\n"
            f"CONVERSATION : {len(self.data['conversation'])}\n"
            "STORAGE      : ONLINE\n"
            "===================="
        )

    # =========================================================
    # CLEAR
    # =========================================================

    def clear(self):
        self.data = {
            "facts": {},
            "preferences": {},
            "notes": [],
            "conversation": []
        }

        self.save()

        print("[JARVIS MEMORY] Memory cleared.")

        return True


memory = Memory()