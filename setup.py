"""
One-Time Setup Script
Pehli baar yeh chalaao - sab kuch configure ho jaega
"""

import json
import os
import sys
import subprocess


def print_banner():
    print("""
╔══════════════════════════════════════════════════════╗
║         🤖 AUTO BLOGGING SYSTEM SETUP               ║
║         Finance & Money Making Niche                ║
╚══════════════════════════════════════════════════════╝
""")


def install_packages():
    """Required packages install karo"""
    print("📦 Python packages install kar raha hoon...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"])
        print("✅ Sab packages install ho gaye!\n")
    except Exception as e:
        print(f"❌ Package install error: {e}")
        print("Manually run karo: pip install -r requirements.txt")


def setup_config():
    """API keys configure karo"""
    print("="*55)
    print("🔑 API KEYS SETUP")
    print("="*55)
    print()

    config = {}

    # Gemini API Key
    print("1️⃣  GEMINI API KEY")
    print("   Yahan jao: https://aistudio.google.com/app/apikey")
    print("   Free API key lo aur neeche paste karo:")
    config["gemini_api_key"] = input("   Gemini API Key: ").strip()

    print()

    # Pexels API Key
    print("2️⃣  PEXELS API KEY (Free Images ke liye)")
    print("   Yahan jao: https://www.pexels.com/api/")
    print("   Free account banao aur API key lo:")
    config["pexels_api_key"] = input("   Pexels API Key: ").strip()

    print()

    # Pinterest Access Token
    print("3️⃣  PINTEREST ACCESS TOKEN")
    print("   Steps:")
    print("   a) Jao: https://developers.pinterest.com/apps/")
    print("   b) 'Create App' karo")
    print("   c) App approved hone par Access Token copy karo")
    config["pinterest_access_token"] = input("   Pinterest Access Token: ").strip()

    print()

    # Pinterest Board ID
    print("4️⃣  PINTEREST BOARD ID")
    print("   Apna Pinterest board URL kholो jis par pin karna hai")
    print("   URL: https://pinterest.com/username/board-name/")
    print("   Board ID find karne ke liye: python setup.py --boards")
    config["pinterest_board_id"] = input("   Pinterest Board ID: ").strip()

    print()

    # Blogger Blog ID
    print("5️⃣  BLOGGER BLOG ID")
    print("   Apna Blogspot blog kholо")
    print("   URL mein number hoga: blogger.com/blog/posts/1234567890")
    print("   Woh number paste karo:")
    config["blogger_blog_id"] = input("   Blogger Blog ID: ").strip()

    # Default settings
    config.update({
        "blogger_client_secrets_file": "auth/client_secrets.json",
        "niche": "Finance & Money Making",
        "posts_per_day": 2,
        "language": "English",
        "min_word_count": 1000,
        "pinterest_hashtags_count": 15,
        "image_width": 1000,
        "image_height": 1500
    })

    # Save config
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)

    print("\n✅ config.json save ho gaya!")
    return config


def setup_google_oauth():
    """Google OAuth2 client secrets setup karo"""
    print("\n" + "="*55)
    print("🔐 GOOGLE BLOGGER AUTHENTICATION SETUP")
    print("="*55)
    print("""
Steps:
1. Jao: https://console.cloud.google.com/
2. New project banao ya existing select karo
3. 'APIs & Services' → 'Enable APIs' mein jao
4. 'Blogger API v3' enable karo
5. 'Credentials' mein jao
6. 'Create Credentials' → 'OAuth Client ID'
7. Application type: 'Desktop App' select karo
8. Download JSON button dabao
9. Woh file yahan paste karo: auth/client_secrets.json
""")
    input("auth/client_secrets.json file set karne ke baad ENTER dabao...")

    if os.path.exists("auth/client_secrets.json"):
        print("✅ client_secrets.json found!")
        # First time OAuth karo - browser kholega
        print("\n🌐 Browser kholega - Google account se login karo aur allow karo...")
        try:
            from modules.blogger_publisher import BloggerPublisher
            with open("config.json") as f:
                config = json.load(f)
            publisher = BloggerPublisher(config)
            info = publisher.get_blog_info()
            print(f"✅ Blogger connected! Blog: {info.get('name', 'Unknown')}")
        except Exception as e:
            print(f"❌ Blogger auth error: {e}")
    else:
        print("❌ auth/client_secrets.json nahi mila! Phir se try karo.")


def test_all_apis():
    """Sab APIs test karo"""
    print("\n" + "="*55)
    print("🧪 API TESTING")
    print("="*55)

    with open("config.json") as f:
        config = json.load(f)

    all_passed = True

    # Gemini
    print("\n🤖 Gemini API test...")
    try:
        import google.generativeai as genai
        genai.configure(api_key=config["gemini_api_key"])
        model = genai.GenerativeModel("gemini-1.5-pro")
        result = model.generate_content("Reply with just: GEMINI_OK")
        print(f"   ✅ Gemini working!")
    except Exception as e:
        print(f"   ❌ Gemini error: {e}")
        all_passed = False

    # Pexels
    print("\n🖼️  Pexels API test...")
    try:
        import requests
        r = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": config["pexels_api_key"]},
            params={"query": "money", "per_page": 1}
        )
        if r.status_code == 200:
            print(f"   ✅ Pexels working! Results: {r.json().get('total_results', 0)}")
        else:
            print(f"   ❌ Pexels error: {r.status_code}")
            all_passed = False
    except Exception as e:
        print(f"   ❌ Pexels error: {e}")
        all_passed = False

    # Pinterest
    print("\n📌 Pinterest API test...")
    try:
        import requests
        r = requests.get(
            "https://api.pinterest.com/v5/user_account",
            headers={"Authorization": f"Bearer {config['pinterest_access_token']}"},
            timeout=10
        )
        if r.status_code == 200:
            user = r.json()
            print(f"   ✅ Pinterest working! User: @{user.get('username', '?')}")
        else:
            print(f"   ❌ Pinterest error: {r.status_code} - {r.text[:100]}")
            all_passed = False
    except Exception as e:
        print(f"   ❌ Pinterest error: {e}")
        all_passed = False

    print("\n" + "="*55)
    if all_passed:
        print("🎉 SABI APIs WORKING HAIN!")
        print("Ab GitHub par push karo aur system shuru ho jaega!")
    else:
        print("⚠️  Kuch APIs mein masla hai. Upar errors fix karo.")
    print("="*55)


def show_boards():
    """Pinterest boards show karo (ID dhundne ke liye)"""
    try:
        import requests
        with open("config.json") as f:
            config = json.load(f)

        r = requests.get(
            "https://api.pinterest.com/v5/boards",
            headers={"Authorization": f"Bearer {config['pinterest_access_token']}"},
            params={"page_size": 25}
        )
        if r.status_code == 200:
            boards = r.json().get("items", [])
            print("\n📌 Aapke Pinterest Boards:")
            print("-" * 40)
            for board in boards:
                print(f"Name: {board['name']}")
                print(f"ID:   {board['id']}")
                print("-" * 40)
            print("\nBoard ID copy karo aur config.json mein paste karo!")
        else:
            print(f"❌ Boards fetch error: {r.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")


def create_github_secrets_guide():
    """GitHub Secrets setup guide"""
    print("""
╔══════════════════════════════════════════════════════╗
║         📚 GITHUB SECRETS SETUP GUIDE              ║
╚══════════════════════════════════════════════════════╝

1. GitHub par apna repo banao (private rakhna):
   https://github.com/new

2. Apna code push karo:
   git init
   git add .
   git commit -m "Initial setup"
   git remote add origin https://github.com/USERNAME/REPO.git
   git push -u origin main

3. GitHub Secrets add karo:
   → Repo page par jao
   → Settings → Secrets and variables → Actions
   → "New repository secret" click karo
   
   Yeh secrets add karo:
   ┌─────────────────────────────┬──────────────────────────┐
   │ Secret Name                 │ Value                    │
   ├─────────────────────────────┼──────────────────────────┤
   │ GEMINI_API_KEY              │ Aapki Gemini key         │
   │ PEXELS_API_KEY              │ Aapki Pexels key         │
   │ PINTEREST_ACCESS_TOKEN      │ Pinterest token          │
   │ PINTEREST_BOARD_ID          │ Board ID                 │
   │ BLOGGER_BLOG_ID             │ Blog ID                  │
   │ BLOGGER_CLIENT_SECRETS      │ client_secrets.json content │
   │ BLOGGER_TOKEN               │ blogger_token.json content  │
   └─────────────────────────────┴──────────────────────────┘

4. Actions tab mein jao aur manually trigger karo test ke liye!

5. System automatically:
   - Har roz 9AM PKT post karega
   - Har roz 3PM PKT post karega
   - Bilkul FREE (GitHub Actions free hai)
""")


if __name__ == "__main__":
    print_banner()

    if len(sys.argv) > 1:
        if sys.argv[1] == "--boards":
            show_boards()
        elif sys.argv[1] == "--test":
            test_all_apis()
        elif sys.argv[1] == "--github":
            create_github_secrets_guide()
    else:
        # Full setup
        print("🚀 Full setup shuru kar raha hoon...\n")
        install_packages()
        config = setup_config()
        setup_google_oauth()
        test_all_apis()
        create_github_secrets_guide()
        print("\n🎉 SETUP COMPLETE! Ab system ready hai.")
