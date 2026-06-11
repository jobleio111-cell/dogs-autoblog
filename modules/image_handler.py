"""
Image Handler Module - AI Image Generator
Pollinations.ai (FREE, no API key) se AI-generated images banata hai
Blog post ke topic se directly related unique images!
Pinterest ke liye 1000x1500 portrait optimize karta hai
"""

import json
import os
import requests
import base64
import urllib.parse
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from datetime import datetime


class ImageHandler:
    def __init__(self, config: dict):
        self.config = config
        # Pollinations.ai - completely FREE, no API key needed
        self.pollinations_url = "https://image.pollinations.ai/prompt"

        # Pexels fallback (agar AI image fail ho)
        self.pexels_api_key = config.get("pexels_api_key", "")
        self.pexels_base_url = "https://api.pexels.com/v1"

    def fetch_image_for_topic(self, topic: str, title: str) -> dict:
        """
        Topic ke liye image fetch karo (Direct Pexels)
        Returns: dict with local_path, url, base64
        """
        print(f"\n🎨 Image dhoondh raha hoon: '{topic[:50]}'")

        # Method 1: Direct Pexels (kyunki Pollinations API ab paise maang rahi hai)
        return self._fetch_pexels_fallback(topic, title)

    def _generate_ai_image(self, topic: str, title: str) -> dict:
        """
        Pollinations.ai se FREE AI image generate karo
        - No API key needed
        - Topic se directly related unique image
        - High quality
        """
        try:
            # Image ke liye detailed prompt banana
            image_prompt = self._build_image_prompt(topic, title)
            print(f"   🖌️ AI Prompt: {image_prompt[:80]}...")

            # Pollinations.ai URL encode karo
            encoded_prompt = urllib.parse.quote(image_prompt)

            # Models available: flux, flux-realism, flux-cablyai, turbo
            # flux-realism best quality deta hai finance content ke liye
            image_url = (
                f"{self.pollinations_url}/{encoded_prompt}"
                f"?width=1000&height=1500"
                f"&model=flux-realism"
                f"&seed={abs(hash(topic)) % 99999}"
                f"&nologo=true"
                f"&enhance=true"
            )

            print(f"   ⏳ AI image generate ho raha hai (15-30 sec)...")

            # Image download karo (timeout thoda zyada - AI generation time leta hai)
            response = requests.get(image_url, timeout=60, stream=True)

            if response.status_code == 200 and len(response.content) > 10000:
                # Image valid hai
                img = Image.open(BytesIO(response.content))

                # RGB ensure karo
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Pinterest exact size (1000x1500) confirm karo
                img = img.resize((1000, 1500), Image.LANCZOS)

                # Local save karo
                os.makedirs("temp_images", exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                local_path = f"temp_images/ai_post_{timestamp}.jpg"
                img.save(local_path, "JPEG", quality=90)

                # Base64 encode
                with open(local_path, "rb") as f:
                    img_base64 = base64.b64encode(f.read()).decode('utf-8')

                print(f"   ✅ AI Image ready! Size: {img.size} | Path: {local_path}")

                return {
                    "local_path": local_path,
                    "url": image_url,
                    "base64": img_base64,
                    "width": 1000,
                    "height": 1500,
                    "source": "pollinations_ai",
                    "photographer": "AI Generated",
                    "prompt": image_prompt
                }
            else:
                print(f"   ❌ AI image response invalid: status={response.status_code}, size={len(response.content) if response.content else 0}")
                return None

        except requests.exceptions.Timeout:
            print("   ❌ AI image timeout (60s). Fallback use karunga.")
            return None
        except Exception as e:
            print(f"   ❌ AI image error: {e}")
            return None

    def _build_image_prompt(self, topic: str, title: str) -> str:
        """
        Topic se AI image ke liye professional prompt banana
        Finance niche ke liye optimized
        """
        topic_lower = topic.lower()

        # Topic-specific professional prompts
        prompt_templates = {
            "passive income": (
                "Professional finance concept, multiple income streams visualization, "
                "coins and dollar bills flowing into piggy bank, golden light, "
                "modern minimalist style, high quality, 8k"
            ),
            "dividend": (
                "Stock market dividend growth concept, financial charts going up, "
                "green upward arrows, dollar signs, professional business photography, "
                "blue and gold color scheme, ultra realistic"
            ),
            "saving money": (
                "Money saving concept, glass jar full of coins and bills, "
                "calculator and budget notebook, clean white background, "
                "professional product photography, soft lighting"
            ),
            "budget": (
                "Personal budgeting concept, laptop with financial charts, "
                "notebook with pen, coffee cup, organized desk, modern minimalist, "
                "natural light photography, professional"
            ),
            "invest": (
                "Investment growth concept, ascending bar charts, "
                "golden coins stacking up, stock market candlestick charts, "
                "blue financial background, 3D render style, professional"
            ),
            "side hustle": (
                "Side hustle income concept, laptop on desk with money, "
                "freelance work setup, coffee shop background, "
                "person working happily, warm lighting, lifestyle photography"
            ),
            "credit": (
                "Credit score concept, credit card with rising score meter, "
                "financial documents, professional business style, "
                "blue and silver color scheme, modern design"
            ),
            "debt": (
                "Debt freedom concept, scissors cutting credit card chains, "
                "person breaking free from financial burden, hopeful sunrise, "
                "motivational financial concept art, professional"
            ),
            "real estate": (
                "Real estate investment concept, beautiful house with money symbols, "
                "property value growth chart, keys on dollar bills, "
                "professional real estate photography, golden hour"
            ),
            "retire": (
                "Retirement planning concept, piggy bank with nest egg, "
                "calendar with retirement date circled, couple planning finances, "
                "warm sunset background, professional lifestyle photo"
            ),
            "stock": (
                "Stock market trading concept, financial charts and graphs, "
                "digital trading screen with green candles, "
                "professional trader setup, blue glow, modern technology"
            ),
            "cryptocurrency": (
                "Cryptocurrency investment concept, bitcoin and ethereum coins, "
                "digital blockchain background, glowing crypto symbols, "
                "futuristic financial technology, dark blue background"
            ),
            "emergency fund": (
                "Emergency fund savings concept, safety net of money, "
                "umbrella over coin jar, financial security visualization, "
                "blue and white professional style, clean background"
            ),
            "make money": (
                "Make money online concept, laptop with money coming out, "
                "dollar bills floating, successful entrepreneur lifestyle, "
                "bright modern office, inspirational financial photography"
            ),
            "financial freedom": (
                "Financial freedom concept, person standing on mountain of coins, "
                "arms raised in victory, freedom symbolism, sunset background, "
                "inspirational lifestyle photography, cinematic quality"
            ),
        }

        # Topic mein matching keyword dhundo
        for key, prompt in prompt_templates.items():
            if key in topic_lower:
                return prompt

        # Default generic finance prompt (if no match)
        return (
            f"Professional finance and money concept for '{topic}', "
            "dollar bills and coins arrangement, financial success visualization, "
            "modern minimalist photography, business professional style, "
            "sharp focus, high quality, 8k resolution, gold and navy blue color scheme"
        )

    def _fetch_pexels_fallback(self, topic: str, title: str) -> dict:
        """Pexels se fallback image (agar AI fail ho)"""
        if not self.pexels_api_key or "YOUR_" in self.pexels_api_key:
            print("   ❌ Pexels API key bhi nahi hai! Placeholder use karunga.")
            return self._create_placeholder_image(title)

        try:
            search_query = self._get_finance_query(topic)
            url = f"{self.pexels_base_url}/search"
            headers = {"Authorization": self.pexels_api_key}
            params = {"query": search_query, "per_page": 5, "orientation": "portrait"}

            response = requests.get(url, headers=headers, params=params, timeout=15)

            if response.status_code == 200:
                photos = response.json().get("photos", [])
                if photos:
                    import random
                    photo = random.choice(photos[:3])
                    img_url = photo["src"]["large2x"]
                    optimized = self._download_and_optimize(img_url, title)
                    optimized.update({
                        "source": "pexels",
                        "photographer": photo.get("photographer", "Pexels"),
                        "url": img_url
                    })
                    return optimized
        except Exception as e:
            print(f"   ❌ Pexels error: {e}")

        return self._create_placeholder_image(title)

    def _add_text_overlay(self, img: Image.Image, title: str) -> Image.Image:
        """Add a stylish text overlay to the image"""
        try:
            img = img.convert("RGBA")
            draw = ImageDraw.Draw(img)
            width, height = img.size
            
            # Draw semi-transparent dark rectangle at the bottom
            box_height = 400
            box_top = height - box_height
            draw.rectangle([(0, box_top), (width, height)], fill=(0, 0, 0, 180))
            
            # Load font (Download Nunito-Bold if not available)
            font_path = "Nunito-Bold.ttf"
            if not os.path.exists(font_path):
                try:
                    import urllib.request
                    font_url = "https://github.com/google/fonts/raw/main/ofl/nunito/Nunito-Bold.ttf"
                    urllib.request.urlretrieve(font_url, font_path)
                except Exception as e:
                    print(f"   ⚠️ Font download failed: {e}")
            
            font = None
            try:
                font = ImageFont.truetype(font_path, 80)
            except IOError:
                font = ImageFont.load_default()
                
            # Basic text wrapping
            words = title.split()
            lines = []
            current_line = []
            
            for word in words:
                current_line.append(word)
                test_line = ' '.join(current_line)
                try:
                    w = font.getlength(test_line)
                except AttributeError:
                    w = len(test_line) * 35 
                    
                if w > (width - 100):
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    
            if current_line:
                lines.append(' '.join(current_line))
                
            y_text = box_top + 80
            for line in lines:
                try:
                    line_w = font.getlength(line)
                    x_text = (width - line_w) / 2
                except AttributeError:
                    x_text = 100
                
                draw.text((x_text, y_text), line, font=font, fill=(255, 255, 255))
                y_text += 70
                
            return img
        except Exception as e:
            print(f"   ❌ Text overlay error: {e}")
            return img

    def _download_and_optimize(self, image_url: str, title: str) -> dict:
        """Image download karo aur Pinterest size mein optimize karo aur Title overlay lagao"""
        try:
            response = requests.get(image_url, timeout=30)
            img = Image.open(BytesIO(response.content))

            # 1000x1500 portrait size
            img = img.resize((1000, 1500), Image.LANCZOS)

            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            # TEXT OVERLAY
            img = self._add_text_overlay(img, title)
            
            # Convert back to RGB for JPEG saving
            if img.mode == 'RGBA':
                img = img.convert('RGB')

            os.makedirs("temp_images", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            local_path = f"temp_images/post_{timestamp}.jpg"
            img.save(local_path, "JPEG", quality=85)

            with open(local_path, "rb") as f:
                img_base64 = base64.b64encode(f.read()).decode('utf-8')

            return {
                "local_path": local_path,
                "base64": img_base64,
                "width": 1000,
                "height": 1500
            }
        except Exception as e:
            print(f"   ❌ Download/optimize error: {e}")
            return {"local_path": None, "base64": None}

    def _create_placeholder_image(self, title: str) -> dict:
        """Agar sab fail ho jain toh simple placeholder image"""
        try:
            img = Image.new('RGB', (1000, 1500), color=(26, 42, 74))
            draw = ImageDraw.Draw(img)

            # Simple text add karo
            draw.rectangle([50, 600, 950, 900], fill=(212, 175, 55))
            draw.text((500, 750), "Finance Tips", fill=(26, 42, 74), anchor="mm")

            os.makedirs("temp_images", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            local_path = f"temp_images/placeholder_{timestamp}.jpg"
            img.save(local_path, "JPEG", quality=85)

            with open(local_path, "rb") as f:
                img_base64 = base64.b64encode(f.read()).decode('utf-8')

            return {
                "local_path": local_path,
                "base64": img_base64,
                "url": None,
                "source": "placeholder",
                "photographer": "System Generated",
                "width": 1000,
                "height": 1500
            }
        except Exception as e:
            print(f"   ❌ Placeholder error: {e}")
            return {"local_path": None, "base64": None}

    def _get_finance_query(self, topic: str) -> str:
        """Pexels ke liye search query (Updated for Dogs)"""
        topic_lower = topic.lower()
        mapping = {
            "puppy": "cute puppy dog",
            "food": "dog eating food",
            "health": "healthy active dog",
            "vet": "veterinarian dog care",
            "grooming": "dog bathing grooming",
            "train": "dog training",
            "breed": "beautiful dog breeds",
            "toy": "dog playing with toy",
            "walk": "walking dog outdoor",
        }
        for key, query in mapping.items():
            if key in topic_lower:
                return query
        return "happy cute dog pet"

    def get_image_as_bytes(self, local_path: str) -> bytes:
        """Image bytes return karo"""
        with open(local_path, "rb") as f:
            return f.read()

    def cleanup_temp_images(self, max_age_hours=24):
        """Purani images delete karo"""
        import time
        if not os.path.exists("temp_images"):
            return
        now = time.time()
        for filename in os.listdir("temp_images"):
            filepath = os.path.join("temp_images", filename)
            if os.path.getmtime(filepath) < now - (max_age_hours * 3600):
                os.remove(filepath)


if __name__ == "__main__":
    with open("config.json") as f:
        config = json.load(f)

    handler = ImageHandler(config)
    result = handler.fetch_image_for_topic(
        "passive income streams",
        "7 Best Passive Income Ideas for 2024"
    )
    print(f"\n✅ Image Result:")
    print(f"   Path: {result.get('local_path')}")
    print(f"   Source: {result.get('source')}")
    print(f"   Size: {result.get('width')}x{result.get('height')}")
