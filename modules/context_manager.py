"""
Context Manager Module
Project ki poori history aur state manage karta hai
project_context.json mein save karta rehta hai
"""

import json
import os
from datetime import datetime


class ContextManager:
    def __init__(self, context_file: str = "project_context.json"):
        self.context_file = context_file
        self.context = self._load_context()

    def _load_context(self) -> dict:
        """Context file load karo"""
        try:
            with open(self.context_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Context file nahi mili, nayi bana raha hoon: {self.context_file}")
            return self._create_default_context()
        except json.JSONDecodeError as e:
            print(f"❌ Context file corrupt hai: {e}")
            return self._create_default_context()

    def _create_default_context(self) -> dict:
        return {
            "project_name": "Auto Blogging System",
            "niche": "Finance & Money Making",
            "language": "English",
            "posts_per_day": 2,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "total_posts_published": 0,
            "total_pins_created": 0,
            "api_keys_configured": False,
            "published_topics": [],
            "failed_attempts": [],
            "sessions": [],
            "settings": {
                "post_times_utc": ["04:00", "10:00"],
                "image_source": "pexels",
                "ai_model": "gemini-1.5-pro",
                "seo_min_words": 1000,
                "pinterest_board": "",
                "blogger_blog_id": ""
            },
            "stats": {
                "this_week": 0,
                "this_month": 0,
                "all_time": 0
            }
        }

    def save(self):
        """Context ko file mein save karo"""
        self.context["last_updated"] = datetime.now().isoformat()
        try:
            with open(self.context_file, "w", encoding="utf-8") as f:
                json.dump(self.context, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Context save error: {e}")

    def add_published_post(self, post_data: dict, blogger_result: dict, pinterest_result: dict):
        """Ek published post ka record save karo"""
        record = {
            "topic": post_data.get("topic"),
            "title": post_data.get("seo_title"),
            "published_at": datetime.now().isoformat(),
            "blogger": {
                "success": blogger_result.get("success", False),
                "url": blogger_result.get("url", ""),
                "post_id": blogger_result.get("post_id", "")
            },
            "pinterest": {
                "success": pinterest_result.get("success", False),
                "pin_url": pinterest_result.get("pin_url", ""),
                "pin_id": pinterest_result.get("pin_id", "")
            },
            "keywords": post_data.get("focus_keywords", [])[:5],
            "word_count": post_data.get("word_count", 0)
        }

        # Published topics mein topic add karo
        topic = post_data.get("topic", "")
        if topic and topic not in self.context["published_topics"]:
            self.context["published_topics"].append(topic)

        # Stats update karo
        if blogger_result.get("success"):
            self.context["total_posts_published"] = self.context.get("total_posts_published", 0) + 1
            self.context["stats"]["all_time"] = self.context["stats"].get("all_time", 0) + 1
            self.context["stats"]["this_month"] = self.context["stats"].get("this_month", 0) + 1
            self.context["stats"]["this_week"] = self.context["stats"].get("this_week", 0) + 1

        if pinterest_result.get("success"):
            self.context["total_pins_created"] = self.context.get("total_pins_created", 0) + 1

        # Daily posts file mein save karo
        self._save_daily_record(record)
        self.save()

        return record

    def _save_daily_record(self, record: dict):
        """Aaj ke posts ko alag file mein save karo"""
        os.makedirs("published_posts", exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")
        daily_file = f"published_posts/{today}.json"

        daily_records = []
        if os.path.exists(daily_file):
            try:
                with open(daily_file, "r") as f:
                    daily_records = json.load(f)
            except:
                pass

        daily_records.append(record)

        with open(daily_file, "w", encoding="utf-8") as f:
            json.dump(daily_records, f, indent=2, ensure_ascii=False)

    def add_session_log(self, action: str, status: str, notes: str = ""):
        """Har session ka log add karo"""
        session = {
            "date": datetime.now().isoformat(),
            "action": action,
            "status": status,
            "notes": notes
        }
        if "sessions" not in self.context:
            self.context["sessions"] = []
        self.context["sessions"].append(session)

        # Last 50 sessions hi rakhein
        self.context["sessions"] = self.context["sessions"][-50:]
        self.save()

    def add_failed_attempt(self, topic: str, error: str):
        """Failed attempt record karo"""
        attempt = {
            "topic": topic,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        if "failed_attempts" not in self.context:
            self.context["failed_attempts"] = []
        self.context["failed_attempts"].append(attempt)
        self.context["failed_attempts"] = self.context["failed_attempts"][-20:]
        self.save()

    def is_topic_used(self, topic: str) -> bool:
        """Check karo yeh topic pehle use hua hai ya nahi"""
        used = self.context.get("published_topics", [])
        topic_lower = topic.lower()
        return any(t.lower() in topic_lower or topic_lower in t.lower() for t in used)

    def get_stats(self) -> dict:
        """Current stats return karo"""
        return {
            "total_posts": self.context.get("total_posts_published", 0),
            "total_pins": self.context.get("total_pins_created", 0),
            "topics_used": len(self.context.get("published_topics", [])),
            "this_week": self.context.get("stats", {}).get("this_week", 0),
            "this_month": self.context.get("stats", {}).get("this_month", 0),
            "last_updated": self.context.get("last_updated", "Never")
        }

    def write_log(self, message: str, level: str = "INFO"):
        """Log file mein message likhna"""
        os.makedirs("logs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"

        with open("logs/daily_log.txt", "a", encoding="utf-8") as f:
            f.write(log_entry)

        print(log_entry.strip())


if __name__ == "__main__":
    cm = ContextManager()
    stats = cm.get_stats()
    print(f"Current Stats: {json.dumps(stats, indent=2)}")
