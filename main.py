"""
Main Runner - Auto Blogging System
Yeh poora system run karta hai:
Pinterest Trends → AI Write → Image → Blogger → Pinterest Pin
"""

import json
import sys
import os
import time
from datetime import datetime

# Modules import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modules.trend_finder import TrendFinder
from modules.ai_writer import AIWriter
from modules.image_handler import ImageHandler
from modules.blogger_publisher import BloggerPublisher
from modules.pinterest_pinner import PinterestPinner
from modules.context_manager import ContextManager


def load_config() -> dict:
    """Config file load karo"""
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Validate required keys (Gemini OR Groq)
    has_ai_key = bool(config.get("gemini_api_key")) or bool(config.get("groq_api_key"))
    missing = []
    if not has_ai_key:
        missing.append("gemini_api_key ya groq_api_key")
    if not config.get("blogger_blog_id") or "YOUR_" in str(config.get("blogger_blog_id", "")):
        missing.append("blogger_blog_id")
        
    if missing:
        raise ValueError(f"❌ Config mein yeh keys missing hain: {missing}\nGitHub Secrets check karo!")
    return config


def run_single_post(config: dict, context_manager: ContextManager, topic: str = None) -> bool:
    """
    Ek complete post run karo:
    Topic → Write → Image → Publish → Pin
    Returns: True if success, False if failed
    """
    print("\n" + "="*60)
    print(f"🚀 New Post Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    try:
        # Step 1: Topic find karo (agar manually nahi diya)
        if not topic:
            print("\n📊 STEP 1: Trending Topic Dhundh Raha Hoon...")
            context_data = context_manager.context
            finder = TrendFinder(config, context_data)
            topics = finder.select_best_topic(num_topics=1)
            if not topics:
                context_manager.write_log("No fresh topics found", "ERROR")
                return False
            topic = topics[0]

        print(f"\n🎯 Topic Selected: '{topic}'")
        context_manager.write_log(f"Topic selected: {topic}", "INFO")

        # Step 2: AI se post likhwana
        print("\n✍️ STEP 2: AI Se Blog Post Likh Raha Hoon...")
        writer = AIWriter(config)
        post_data = writer.generate_full_post(topic)

        if not post_data or not post_data.get("html_content"):
            context_manager.write_log(f"AI writing failed for: {topic}", "ERROR")
            return False

        # Step 3: Image fetch karo
        print("\n🖼️ STEP 3: Image Fetch Kar Raha Hoon...")
        image_handler = ImageHandler(config)
        image_data = image_handler.fetch_image_for_topic(topic, post_data["seo_title"])

        if not image_data:
            context_manager.write_log("Image fetch failed, continuing without image", "WARNING")
            image_data = {"local_path": None, "url": None}

        # Step 4: Blogger par publish
        print("\n📤 STEP 4: Blogspot Par Publish Kar Raha Hoon...")
        blogger = BloggerPublisher(config)
        blogger_result = blogger.publish_post(post_data, image_data)

        if not blogger_result.get("success"):
            context_manager.write_log(f"Blogger publish failed: {blogger_result.get('error')}", "ERROR")
            context_manager.add_failed_attempt(topic, blogger_result.get("error", "Unknown"))

        # Step 5: Pinterest par pin karo (Make.com ab handle kar raha hai!)
        print("\n📌 STEP 5: Pinterest Make.com ke hawale (Skipping local upload)...")
        # blog_url = blogger_result.get("url", "https://your-blog.blogspot.com")
        # pinner = PinterestPinner(config)
        # pinterest_result = pinner.create_pin(post_data, image_data, blog_url)
        pinterest_result = {"success": True, "pin_url": "Handled by Make.com"}

        # Step 6: Context save karo
        print("\n💾 STEP 6: Context Save Kar Raha Hoon...")
        record = context_manager.add_published_post(post_data, blogger_result, pinterest_result)

        # Summary print karo
        print("\n" + "="*60)
        print("✅ POST COMPLETE!")
        print(f"   📝 Title: {post_data['seo_title']}")
        print(f"   🔗 Blog URL: {blogger_result.get('url', 'Failed')}")
        print(f"   📌 Pin URL: {pinterest_result.get('pin_url', 'Failed')}")
        print(f"   📊 Word Count: {post_data.get('word_count', 0)}")
        print("="*60)

        context_manager.write_log(
            f"SUCCESS: {post_data['seo_title']} | Blog: {blogger_result.get('success')} | Pin: {pinterest_result.get('success')}",
            "SUCCESS"
        )

        # Temp images cleanup
        image_handler.cleanup_temp_images()

        return blogger_result.get("success", False)

    except Exception as e:
        error_msg = f"Critical error in run_single_post: {str(e)}"
        print(f"\n❌ {error_msg}")
        context_manager.write_log(error_msg, "CRITICAL")
        import traceback
        traceback.print_exc()
        return False


def run_daily_posts(posts_per_day: int = 2):
    """
    Daily posts run karo
    GitHub Actions se yeh call hoga
    """
    print("\n🌟 AUTO BLOGGING SYSTEM STARTED")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Posts to publish: {posts_per_day}")

    try:
        config = load_config()
        context_manager = ContextManager()

        context_manager.add_session_log(
            f"Daily run started - {posts_per_day} posts",
            "started"
        )

        success_count = 0
        fail_count = 0

        # Topics pehle se fetch karo (sab unique hon)
        print(f"\n📊 Aaj ke {posts_per_day} topics select kar raha hoon...")
        finder = TrendFinder(config, context_manager.context)
        topics = finder.select_best_topic(num_topics=posts_per_day)

        if not topics:
            print("❌ No topics found!")
            return

        print(f"✅ Topics ready: {topics}")

        # Har topic ke liye post banao
        for i, topic in enumerate(topics[:posts_per_day], 1):
            print(f"\n\n{'*'*60}")
            print(f"📝 POST {i}/{posts_per_day}")
            print(f"{'*'*60}")

            success = run_single_post(config, context_manager, topic)

            if success:
                success_count += 1
            else:
                fail_count += 1

            # Posts ke darmiyan wait karo (rate limiting)
            if i < posts_per_day:
                wait_time = 60  # 1 minute between posts
                print(f"\n⏳ Agli post se pehle {wait_time} second wait kar raha hoon...")
                time.sleep(wait_time)

        # Final summary
        stats = context_manager.get_stats()
        print(f"\n\n{'='*60}")
        print("🏁 DAILY RUN COMPLETE!")
        print(f"   ✅ Successful: {success_count}")
        print(f"   ❌ Failed: {fail_count}")
        print(f"   📊 Total all-time posts: {stats['total_posts']}")
        print(f"   📌 Total pins: {stats['total_pins']}")
        print(f"{'='*60}")

        context_manager.add_session_log(
            f"Daily run complete: {success_count} success, {fail_count} failed",
            "completed",
            f"Total posts ever: {stats['total_posts']}"
        )

    except Exception as e:
        print(f"\n❌ SYSTEM ERROR: {e}")
        import traceback
        traceback.print_exc()


def test_run():
    """
    Test mode: Sab APIs test karo aur 1 test post karo
    Actually publish nahi karega
    """
    print("\n🧪 TEST MODE - APIs check kar raha hoon...")
    try:
        config = load_config()
        context_manager = ContextManager()
        all_ok = True

        try:
            import requests
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={config['gemini_api_key']}"
            headers = {"Content-Type": "application/json"}
            data = {"contents": [{"parts": [{"text": "Say 'Gemini API working!' in one line"}]}]}
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                result = response.json()['candidates'][0]['content']['parts'][0]['text']
                print(f"   ✅ Gemini: {result.strip()}")
            else:
                # Try fallback model
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={config['gemini_api_key']}"
                response = requests.post(url, headers=headers, json=data)
                if response.status_code == 200:
                    result = response.json()['candidates'][0]['content']['parts'][0]['text']
                    print(f"   ✅ Gemini: {result.strip()}")
                else:
                    print(f"   ❌ Gemini error: {response.text}")
                    all_ok = False
        except Exception as e:
            print(f"   ❌ Gemini error: {e}")
            all_ok = False

        # (Pexels removed, using AI images)

        # Pinterest test
        print("\n3. Pinterest API test...")
        try:
            pinner = PinterestPinner(config)
            if pinner.test_connection():
                boards = pinner.get_boards()
                print(f"   ✅ Pinterest: Connected! Boards: {len(boards)}")
                for b in boards[:3]:
                    print(f"      - {b.get('name')} (ID: {b.get('id')})")
            else:
                all_ok = False
        except Exception as e:
            print(f"   ❌ Pinterest error: {e}")
            all_ok = False

        # Blogger test
        print("\n4. Blogger API test...")
        try:
            publisher = BloggerPublisher(config)
            info = publisher.get_blog_info()
            if "error" not in info:
                print(f"   ✅ Blogger: '{info['name']}' - {info['posts_count']} posts")
            else:
                print(f"   ❌ Blogger: {info['error']}")
                all_ok = False
        except Exception as e:
            print(f"   ❌ Blogger error: {e}")
            all_ok = False

        print(f"\n{'='*40}")
        if all_ok:
            print("🎉 Sab APIs working hain! System ready hai.")
            print("Run: python main.py --run")
        else:
            print("⚠️ Kuch APIs mein masla hai. Upar errors dekho.")
        print(f"{'='*40}")

    except ValueError as e:
        print(f"\n❌ Config error: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            test_run()
        elif sys.argv[1] == "--run":
            posts_count = int(sys.argv[2]) if len(sys.argv) > 2 else 2
            run_daily_posts(posts_count)
        elif sys.argv[1] == "--single":
            topic = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None
            config = load_config()
            cm = ContextManager()
            run_single_post(config, cm, topic)
        else:
            print("Usage:")
            print("  python main.py --test         # APIs test karo")
            print("  python main.py --run          # Daily posts run karo (2 posts)")
            print("  python main.py --run 1        # 1 post run karo")
            print("  python main.py --single       # Ek post (auto topic)")
            print("  python main.py --single 'How to save money'  # Custom topic")
    else:
        # Default: daily run
        run_daily_posts(posts_per_day=2)
