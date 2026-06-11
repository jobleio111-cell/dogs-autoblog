"""
Pinterest Pinner Module
Pinterest API v5 se automatic pins create karta hai
SEO-optimized title, description, tags ke saath
"""

import json
import os
import requests
from datetime import datetime


class PinterestPinner:
    def __init__(self, config: dict):
        self.config = config
        self.access_token = config.get("pinterest_access_token", "")
        self.board_id = config.get("pinterest_board_id", "")
        self.base_url = "https://api.pinterest.com/v5"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def create_pin(self, post_data: dict, image_data: dict, blog_url: str) -> dict:
        """
        Pinterest par pin create karo
        post_data: ai_writer ka data (title, description, tags)
        image_data: image_handler ka data (local_path)
        blog_url: Blogger par published URL
        """
        print(f"\n📌 Pinterest par pin create kar raha hoon...")

        try:
            # Step 1: Image upload karo Pinterest par
            media_id = self._upload_image(image_data["local_path"])

            if not media_id:
                print("   ❌ Image upload fail - fallback URL use kar raha hoon")
                return self._create_pin_with_url(post_data, image_data, blog_url)

            # Step 2: Pin create karo uploaded image se
            return self._create_pin_with_media_id(post_data, media_id, blog_url)

        except Exception as e:
            print(f"   ❌ Pinterest pin error: {e}")
            # Fallback: URL se pin karo
            return self._create_pin_with_url(post_data, image_data, blog_url)

    def _upload_image(self, image_path: str) -> str:
        """Image ko Pinterest par upload karo"""
        try:
            print("   📤 Image upload kar raha hoon Pinterest par...")

            # Step 1: Upload URL request karo
            upload_response = requests.post(
                f"{self.base_url}/media",
                headers=self.headers,
                json={"media_type": "image"}
            )

            if upload_response.status_code != 201:
                print(f"   ❌ Upload URL request failed: {upload_response.status_code}")
                return None

            upload_data = upload_response.json()
            media_id = upload_data.get("media_id")
            upload_url = upload_data.get("upload_url")
            upload_parameters = upload_data.get("upload_parameters", {})

            if not upload_url:
                return None

            # Step 2: Image file upload karo
            with open(image_path, "rb") as img_file:
                files = {"file": img_file}
                upload_result = requests.post(
                    upload_url,
                    data=upload_parameters,
                    files=files,
                    timeout=60
                )

            if upload_result.status_code in [200, 204]:
                print(f"   ✅ Image uploaded, media_id: {media_id}")
                return media_id
            else:
                print(f"   ❌ Image upload failed: {upload_result.status_code}")
                return None

        except Exception as e:
            print(f"   ❌ Upload error: {e}")
            return None

    def _create_pin_with_media_id(self, post_data: dict, media_id: str, blog_url: str) -> dict:
        """Uploaded image se pin create karo"""
        pin_title = post_data["seo_title"][:100]  # Pinterest max 100 chars
        pin_description = self._prepare_description(post_data)

        pin_body = {
            "board_id": self.board_id,
            "title": pin_title,
            "description": pin_description,
            "link": blog_url,
            "media_source": {
                "source_type": "media_id",
                "media_id": media_id
            }
        }

        response = requests.post(
            f"{self.base_url}/pins",
            headers=self.headers,
            json=pin_body
        )

        return self._handle_pin_response(response, blog_url)

    def _create_pin_with_url(self, post_data: dict, image_data: dict, blog_url: str) -> dict:
        """Image URL se directly pin create karo (fallback)"""
        pin_title = post_data["seo_title"][:100]
        pin_description = self._prepare_description(post_data)

        pin_body = {
            "board_id": self.board_id,
            "title": pin_title,
            "description": pin_description,
            "link": blog_url,
            "media_source": {
                "source_type": "image_url",
                "url": image_data.get("url", "")
            }
        }

        response = requests.post(
            f"{self.base_url}/pins",
            headers=self.headers,
            json=pin_body
        )

        return self._handle_pin_response(response, blog_url)

    def _prepare_description(self, post_data: dict) -> str:
        """
        Pinterest pin description banana
        Max 500 characters + hashtags
        """
        base_desc = post_data.get("pin_description", "")

        # Agar pin_description nahi hai toh meta description use karo
        if not base_desc:
            base_desc = post_data.get("meta_description", "")

        # Hashtags add karo
        tags = post_data.get("pinterest_tags", [])
        tags_str = " ".join(tags[:15])  # Max 15 hashtags

        # Full description
        description = f"{base_desc}\n\n{tags_str}"

        # Pinterest limit 500 chars
        if len(description) > 498:
            # Truncate description, keep tags
            available_for_desc = 498 - len(tags_str) - 2
            description = f"{base_desc[:available_for_desc]}\n\n{tags_str}"

        return description

    def _handle_pin_response(self, response, blog_url: str) -> dict:
        """API response handle karo"""
        if response.status_code in [200, 201]:
            pin_data = response.json()
            pin_id = pin_data.get("id", "")
            pin_url = f"https://pinterest.com/pin/{pin_id}/"

            print(f"   ✅ Pin created successfully!")
            print(f"   🔗 Pin URL: {pin_url}")

            return {
                "success": True,
                "pin_id": pin_id,
                "pin_url": pin_url,
                "blog_url": blog_url,
                "created_at": datetime.now().isoformat()
            }
        else:
            error_msg = response.json() if response.text else "Unknown error"
            print(f"   ❌ Pin creation failed: {response.status_code}")
            print(f"   Error: {error_msg}")

            return {
                "success": False,
                "error": str(error_msg),
                "status_code": response.status_code,
                "created_at": datetime.now().isoformat()
            }

    def get_boards(self) -> list:
        """Apne Pinterest boards ki list fetch karo"""
        try:
            response = requests.get(
                f"{self.base_url}/boards",
                headers=self.headers,
                params={"page_size": 25}
            )
            if response.status_code == 200:
                return response.json().get("items", [])
        except Exception as e:
            print(f"Boards fetch error: {e}")
        return []

    def test_connection(self) -> bool:
        """Pinterest API connection test karo"""
        try:
            response = requests.get(
                f"{self.base_url}/user_account",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                user = response.json()
                print(f"   ✅ Pinterest connected as: {user.get('username', 'Unknown')}")
                return True
            else:
                print(f"   ❌ Pinterest connection failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Pinterest test error: {e}")
            return False


if __name__ == "__main__":
    # Test karo
    with open("config.json") as f:
        config = json.load(f)

    pinner = PinterestPinner(config)
    if pinner.test_connection():
        boards = pinner.get_boards()
        print(f"\nYour Pinterest Boards:")
        for board in boards:
            print(f"  - {board['name']} (ID: {board['id']})")
