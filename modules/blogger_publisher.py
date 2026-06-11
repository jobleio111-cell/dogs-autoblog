"""
Blogger Publisher Module
Google Blogger API v3 se blog post publish karta hai
"""

import json
import os
import base64
import requests
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


# Blogger API scope
SCOPES = ['https://www.googleapis.com/auth/blogger']


class BloggerPublisher:
    def __init__(self, config: dict):
        self.config = config
        self.blog_id = config.get("blogger_blog_id", "")
        self.client_secrets_file = config.get("blogger_client_secrets_file", "auth/client_secrets.json")
        self.token_file = "auth/blogger_token.json"
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Google OAuth2 se authenticate karo"""
        print("   🔐 Blogger authentication...")
        creds = None

        # Saved token check karo
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)

        # Token invalid ya expired ho toh refresh karo
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Pehli baar OAuth flow run karo
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, SCOPES
                )
                creds = flow.run_local_server(port=0, open_browser=False)

            # Token save karo
            os.makedirs("auth", exist_ok=True)
            with open(self.token_file, "w") as f:
                f.write(creds.to_json())

        self.service = build('blogger', 'v3', credentials=creds)
        print("   ✅ Blogger authenticated!")

    def upload_image_to_blogger(self, image_bytes: bytes, filename: str) -> str:
        """
        Image ko Blogger media mein upload karo
        NOTE: Blogger API direct media upload support nahi karta
        Isliye hum image ko post HTML mein base64 embed karenge
        ya phir ek workaround use karenge
        """
        # Base64 encode
        img_base64 = base64.b64encode(image_bytes).decode('utf-8')
        # Data URL banana
        img_data_url = f"data:image/jpeg;base64,{img_base64}"
        return img_data_url

    def publish_post(self, post_data: dict, image_data: dict) -> dict:
        """
        Blog post publish karo
        post_data: ai_writer se aya hua data
        image_data: image_handler se aya hua data
        """
        print(f"\n📤 Blogger par post publish kar raha hoon...")
        print(f"   📝 Title: {post_data['seo_title']}")

        try:
            # Image prepare karo
            image_html = ""
            img_url = ""
            if image_data:
                # Use direct HTTP URL so RSS feeds and Make.com can parse it properly
                img_url = image_data.get("url")
                
                if img_url:
                    image_html = f'''
<div style="display:none; visibility:hidden;">
    <img src="{img_url}" alt="{post_data['seo_title']}" data-pin-media="true" />
</div>
<div style="text-align:center; margin-bottom:20px;">
    <img src="{img_url}" 
         alt="{post_data['seo_title']}" 
         style="max-width:100%; height:auto; border-radius:8px;"
         title="{post_data['seo_title']}"/>
    <p style="font-size:12px; color:#666; margin-top:5px;">
        Image: Dog Photography
    </p>
</div>'''

            pin_description = post_data.get("pin_description", "").replace("\\n", " ").strip()

            # Full post HTML banana
            # Bypassed SEO comments because Blogger API blocks <!-- comments --> and <meta> tags with 403 Forbidden!
            full_content = f"""
{image_html}

{post_data['html_content']}

<hr style="margin: 30px 0;"/>
<div style="background:#f8f9fa; padding:20px; border-radius:8px; margin-top:20px;">
    <h4 style="color:#333; margin-top:0;">📌 Found This Helpful?</h4>
    <p>Save this post and share it with a fellow dog lover! 
    Follow us for more <strong>dog care tips, puppy training advice, and pet health guides</strong>.</p>
</div>
<!-- HIDDEN MARKERS FOR MAKE.COM PINTEREST AUTOMATION -->
<span style="display:none;" id="pin-image-url">{image_data.get('url', '')}</span>
<span style="display:none;" id="pin-description">{pin_description}</span>
"""

            # Blogger API post object
            post = {
                "kind": "blogger#post",
                "title": post_data["seo_title"],
                "content": full_content,
                "labels": post_data.get("blogger_labels", [])[:5],
            }

            # Add meta description as custom meta (Blogger limitation workaround)
            if post_data.get("meta_description"):
                post["customMetaData"] = json.dumps({
                    "description": post_data["meta_description"]
                })

            # Publish karo
            result = self.service.posts().insert(
                blogId=self.blog_id,
                body=post,
                isDraft=False,  # True karo agar draft rakhna ho
                fetchBody=False
            ).execute()

            published_url = result.get("url", "")
            post_id = result.get("id", "")

            print(f"   ✅ Post published!")
            print(f"   🔗 URL: {published_url}")

            return {
                "success": True,
                "post_id": post_id,
                "url": published_url,
                "published_at": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"   ❌ Blogger publish error: {e}")
            return {
                "success": False,
                "error": str(e),
                "published_at": datetime.now().isoformat()
            }

    def get_blog_info(self) -> dict:
        """Blog ki basic info fetch karo (test ke liye)"""
        try:
            blog = self.service.blogs().get(blogId=self.blog_id).execute()
            return {
                "name": blog.get("name"),
                "url": blog.get("url"),
                "posts_count": blog.get("posts", {}).get("totalItems", 0)
            }
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    # Test karo
    with open("config.json") as f:
        config = json.load(f)

    publisher = BloggerPublisher(config)
    info = publisher.get_blog_info()
    print(f"Blog Info: {info}")
