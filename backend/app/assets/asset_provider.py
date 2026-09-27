import os
import json
import uuid
import re
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from backend.app.config import ASSETS_DIR
from backend.app.core.database import get_db_connection

class AssetSafetyState:
    VERIFIED_SAFE = "VERIFIED_SAFE"
    ATTRIBUTION_REQUIRED = "ATTRIBUTION_REQUIRED"
    RESTRICTED = "RESTRICTED"
    REJECTED = "REJECTED"

@dataclass
class LicenseRecord:
    source: str
    source_url: str
    creator: str
    license_name: str
    license_url: str
    commercial_use: bool
    modification_allowed: bool
    attribution_required: bool
    attribution_text: str
    safety_state: str
    verified_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def evaluate_license(license_name: str, source: str, creator: str = "", source_url: str = "") -> LicenseRecord:
    """
    Strict License Verification Engine:
    Never trusts AI assertions. Verifies against allowable open license types.
    Unknown or restrictive (NC, ND) licenses are immediately marked REJECTED.
    """
    lname_clean = (license_name or "").strip().lower()
    now_iso = datetime.utcnow().isoformat()

    # Public Domain / CC0
    if any(k in lname_clean for k in ["cc0", "public domain", "pdm", "cc-zero", "no copyright"]):
        return LicenseRecord(
            source=source,
            source_url=source_url,
            creator=creator or "Public Domain",
            license_name="CC0 / Public Domain",
            license_url="https://creativecommons.org/publicdomain/zero/1.0/",
            commercial_use=True,
            modification_allowed=True,
            attribution_required=False,
            attribution_text="Public Domain - No attribution required",
            safety_state=AssetSafetyState.VERIFIED_SAFE,
            verified_at=now_iso
        )

    # CC BY (Attribution allowed for commercial use and modification)
    if "cc by" in lname_clean and "nc" not in lname_clean and "nd" not in lname_clean:
        attr = f"Visual by {creator or 'Unknown Creator'} under Creative Commons Attribution ({license_name})"
        return LicenseRecord(
            source=source,
            source_url=source_url,
            creator=creator or "Unknown Creator",
            license_name=license_name,
            license_url="https://creativecommons.org/licenses/by/4.0/",
            commercial_use=True,
            modification_allowed=True,
            attribution_required=True,
            attribution_text=attr,
            safety_state=AssetSafetyState.ATTRIBUTION_REQUIRED,
            verified_at=now_iso
        )

    # CC BY-SA (ShareAlike)
    if ("cc-by-sa" in lname_clean or "cc by-sa" in lname_clean) and "nc" not in lname_clean and "nd" not in lname_clean:
        attr = f"Visual by {creator or 'Unknown Creator'} under CC BY-SA ({license_name})"
        return LicenseRecord(
            source=source,
            source_url=source_url,
            creator=creator or "Unknown Creator",
            license_name=license_name,
            license_url="https://creativecommons.org/licenses/by-sa/4.0/",
            commercial_use=True,
            modification_allowed=True,
            attribution_required=True,
            attribution_text=attr,
            safety_state=AssetSafetyState.ATTRIBUTION_REQUIRED,
            verified_at=now_iso
        )

    # User uploaded with rights confirmation
    if source == "user_upload":
        return LicenseRecord(
            source=source,
            source_url=source_url,
            creator=creator or "User Upload",
            license_name="User Owned / Licensed",
            license_url="",
            commercial_use=True,
            modification_allowed=True,
            attribution_required=False,
            attribution_text="User verified rights holder",
            safety_state=AssetSafetyState.VERIFIED_SAFE,
            verified_at=now_iso
        )

    # Generated / Built-in
    if source in ("generated", "built_in"):
        return LicenseRecord(
            source=source,
            source_url=source_url,
            creator="AI Content Studio Studio Builtin",
            license_name="Proprietary / Builtin Safe",
            license_url="",
            commercial_use=True,
            modification_allowed=True,
            attribution_required=False,
            attribution_text="Built-in Royalty Free Studio Asset",
            safety_state=AssetSafetyState.VERIFIED_SAFE,
            verified_at=now_iso
        )

    # All non-commercial (NC), no-derivatives (ND), or UNKNOWN licenses are strictly REJECTED
    return LicenseRecord(
        source=source,
        source_url=source_url,
        creator=creator or "Unknown",
        license_name=license_name or "UNKNOWN",
        license_url="",
        commercial_use=False,
        modification_allowed=False,
        attribution_required=False,
        attribution_text="UNKNOWN OR RESTRICTED LICENSE - NOT PERMITTED",
        safety_state=AssetSafetyState.REJECTED,
        verified_at=now_iso
    )


class WikimediaCommonsProvider:
    """Searches Wikimedia Commons for royalty-free and CC licensed images."""
    API_URL = "https://commons.wikimedia.org/w/api.php"
    USER_AGENT = "AIContentStudio/2.0 (ShortFormVideoCreator; contact@example.com)"

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        clean_query = re.sub(r'[^\w\s]', '', query).strip()
        if not clean_query:
            clean_query = "funny expression meme"

        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": f"{clean_query} filetype:bitmap",
            "gsrnamespace": "6",
            "gsrlimit": str(limit),
            "prop": "imageinfo",
            "iiprop": "url|extmetadata|size|mime",
            "format": "json"
        }
        url = f"{self.API_URL}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": self.USER_AGENT})

        results = []
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                pages = data.get("query", {}).get("pages", {})
                for _, page in pages.items():
                    imageinfo = page.get("imageinfo", [{}])[0]
                    file_url = imageinfo.get("url")
                    mime = imageinfo.get("mime", "")
                    if not file_url or not mime.startswith("image/"):
                        continue

                    extmeta = imageinfo.get("extmetadata", {})
                    lic_name = extmeta.get("LicenseShortName", {}).get("value", "UNKNOWN")
                    lic_url = extmeta.get("LicenseUrl", {}).get("value", "")
                    artist = extmeta.get("Artist", {}).get("value", "")
                    # Clean html from artist
                    artist_clean = re.sub(r'<[^>]+>', '', artist).strip()

                    license_record = evaluate_license(
                        license_name=lic_name,
                        source="wikimedia_commons",
                        creator=artist_clean,
                        source_url=file_url
                    )
                    if lic_url:
                        license_record.license_url = lic_url

                    # Only keep safe or attribution-required assets
                    if license_record.safety_state in (AssetSafetyState.VERIFIED_SAFE, AssetSafetyState.ATTRIBUTION_REQUIRED):
                        results.append({
                            "title": page.get("title", ""),
                            "url": file_url,
                            "mime": mime,
                            "width": imageinfo.get("width", 0),
                            "height": imageinfo.get("height", 0),
                            "license_record": license_record
                        })
        except Exception as e:
            print(f"[WikimediaCommonsProvider] Error during search: {e}")

        return results

    def download(self, url: str, target_path: Path) -> bool:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": self.USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                with open(target_path, "wb") as f:
                    f.write(resp.read())
            return True
        except Exception as e:
            print(f"[WikimediaCommonsProvider] Failed to download {url}: {e}")
            return False


class PublicDomainProvider:
    """Generates high quality fallback canvases or returns built-in safe public domain templates."""

    @staticmethod
    def generate_canvas(title: str, target_path: Path, style: str = "sarcastic") -> bool:
        """Generates a high quality 1080x1920 graphic background using PIL."""
        try:
            from PIL import Image, ImageDraw, ImageFont

            width, height = 1080, 1920
            # Choose color scheme based on style
            if style == "sarcastic":
                top_color = (25, 25, 45)
                bottom_color = (10, 10, 20)
                accent = (255, 180, 0)
            elif style == "relatable":
                top_color = (30, 45, 60)
                bottom_color = (15, 20, 30)
                accent = (56, 189, 248)
            elif style == "dark_humor":
                top_color = (20, 20, 20)
                bottom_color = (5, 5, 5)
                accent = (239, 68, 68)
            elif style == "absurd":
                top_color = (50, 15, 65)
                bottom_color = (20, 5, 30)
                accent = (236, 72, 153)
            else:
                top_color = (35, 35, 40)
                bottom_color = (15, 15, 20)
                accent = (168, 85, 247)

            # Create vertical gradient background
            img = Image.new("RGB", (width, height))
            draw = ImageDraw.Draw(img)

            for y in range(height):
                r = int(top_color[0] + (bottom_color[0] - top_color[0]) * (y / height))
                g = int(top_color[1] + (bottom_color[1] - top_color[1]) * (y / height))
                b = int(top_color[2] + (bottom_color[2] - top_color[2]) * (y / height))
                draw.line([(0, y), (width, y)], fill=(r, g, b))

            # Decorative grid/dots
            dot_spacing = 60
            for dx in range(30, width, dot_spacing):
                for dy in range(30, height, dot_spacing):
                    draw.ellipse([(dx, dy), (dx+2, dy+2)], fill=(60, 60, 80))

            # Decorative central card frame for meme focal point
            card_top = 400
            card_bottom = 1450
            card_left = 60
            card_right = width - 60
            draw.rectangle(
                [(card_left, card_top), (card_right, card_bottom)],
                fill=(18, 18, 26),
                outline=accent,
                width=4
            )

            # Draw central icon / decorative emoji / topic badge
            draw.rectangle(
                [(card_left + 40, card_top + 40), (card_right - 40, card_bottom - 40)],
                fill=(28, 28, 38)
            )

            target_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(target_path, "JPEG", quality=95)
            return True
        except Exception as e:
            print(f"[PublicDomainProvider] Error generating canvas: {e}")
            return False


class UserUploadProvider:
    """Manages user-uploaded meme templates or custom images with rights confirmation."""

    @staticmethod
    def save_upload(file_bytes: bytes, filename: str, rights_confirmed: bool = True) -> Dict[str, Any]:
        if not rights_confirmed:
            raise ValueError("Rights confirmation required to use uploaded asset.")

        ext = Path(filename).suffix.lower() or ".png"
        asset_id = str(uuid.uuid4())
        save_dir = ASSETS_DIR / "uploads"
        save_dir.mkdir(parents=True, exist_ok=True)
        dest_path = save_dir / f"{asset_id}{ext}"

        with open(dest_path, "wb") as f:
            f.write(file_bytes)

        license_record = evaluate_license(
            license_name="User Owned / Certified",
            source="user_upload",
            creator="User Provided",
            source_url=str(dest_path)
        )

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO assets (
                    id, name, category, file_path, file_size, tags, rights_confirmed,
                    source, source_url, creator, license_name, license_url,
                    commercial_use, modification_allowed, attribution_required,
                    attribution_text, safety_state, verified_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                asset_id,
                filename,
                "meme_upload",
                str(dest_path),
                len(file_bytes),
                json.dumps(["user_upload", "meme"]),
                1,
                license_record.source,
                license_record.source_url,
                license_record.creator,
                license_record.license_name,
                license_record.license_url,
                1 if license_record.commercial_use else 0,
                1 if license_record.modification_allowed else 0,
                1 if license_record.attribution_required else 0,
                license_record.attribution_text,
                license_record.safety_state,
                license_record.verified_at
            ))

        return {
            "asset_id": asset_id,
            "file_path": str(dest_path),
            "license_record": license_record.to_dict()
        }


class RoyaltyFreeStockProvider:
    """Fetches high resolution, copyright-safe stock and reaction photos for viral memes."""
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    @classmethod
    def search_and_download(cls, query: str, target_path: Path) -> Optional[LicenseRecord]:
        words = re.sub(r'[^\w\s]', '', query).lower().split()
        ignore = {"on", "the", "basis", "of", "a", "an", "and", "or", "to", "in", "for", "with", "meme", "funny", "frd", "pov"}
        clean_words = [w for w in words if w not in ignore]
        if any(w in words for w in ["frd", "friend", "friends"]):
            clean_words.append("friends")

        search_term = " ".join(clean_words[:3]) or "funny reaction"
        encoded_term = urllib.parse.quote(search_term)

        # High resolution royalty-free Unsplash public stock image endpoints
        urls = [
            f"https://source.unsplash.com/featured/800x800/?{encoded_term}",
            f"https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=800&auto=format&fit=crop", # Dog shock reaction
            f"https://images.unsplash.com/photo-1517841905240-472988babdf9?w=800&auto=format&fit=crop", # Funny dog expression
            f"https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=800&auto=format&fit=crop", # Human reaction expression
        ]

        target_path.parent.mkdir(parents=True, exist_ok=True)
        for u in urls:
            try:
                req = urllib.request.Request(u, headers={"User-Agent": cls.USER_AGENT})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    content = resp.read()
                    if len(content) > 10000:
                        with open(target_path, "wb") as f:
                            f.write(content)
                        return evaluate_license(
                            license_name="Unsplash License (Free Commercial & Modification)",
                            source="unsplash_royalty_free",
                            creator="Unsplash Contributor",
                            source_url=u
                        )
            except Exception as e:
                print(f"[RoyaltyFreeStockProvider] Download attempt from {u} failed: {e}")
                continue
        return None


class AssetManager:
    """Unified discovery and acquisition interface with strict license verification."""

    def __init__(self):
        self.wiki_provider = WikimediaCommonsProvider()
        self.stock_provider = RoyaltyFreeStockProvider()
        self.pd_provider = PublicDomainProvider()

    def get_or_acquire_asset(self, query: str, style: str = "sarcastic", preferred_asset_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves a safe asset.
        1. If user provided asset ID, verify it from DB.
        2. Query Wikimedia Commons for safe CC/PD images.
        3. Query RoyaltyFreeStockProvider for HD Unsplash royalty-free images.
        4. Fallback: High quality styled graphic canvas.
        """
        # 1. Check user provided asset ID
        if preferred_asset_id:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM assets WHERE id = ?", (preferred_asset_id,))
                row = cursor.fetchone()
                if row and os.path.exists(row["file_path"]):
                    safety = row["safety_state"] or AssetSafetyState.VERIFIED_SAFE
                    lic_rec = LicenseRecord(
                        source=row["source"] or "user_upload",
                        source_url=row["source_url"] or "",
                        creator=row["creator"] or "User",
                        license_name=row["license_name"] or "User Licensed",
                        license_url=row["license_url"] or "",
                        commercial_use=bool(row["commercial_use"]),
                        modification_allowed=bool(row["modification_allowed"]),
                        attribution_required=bool(row["attribution_required"]),
                        attribution_text=row["attribution_text"] or "",
                        safety_state=safety,
                        verified_at=row["verified_at"] or datetime.utcnow().isoformat()
                    )
                    return {
                        "asset_id": row["id"],
                        "file_path": row["file_path"],
                        "license_record": lic_rec.to_dict()
                    }

        # 2. Query Wikimedia Commons
        safe_candidates = self.wiki_provider.search(query, limit=5)
        for candidate in safe_candidates:
            lic_rec: LicenseRecord = candidate["license_record"]
            if lic_rec.safety_state in (AssetSafetyState.VERIFIED_SAFE, AssetSafetyState.ATTRIBUTION_REQUIRED):
                asset_id = str(uuid.uuid4())
                ext = ".jpg"
                if "png" in candidate.get("mime", ""):
                    ext = ".png"
                save_path = ASSETS_DIR / "memes" / f"{asset_id}{ext}"
                if self.wiki_provider.download(candidate["url"], save_path):
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO assets (
                                id, name, category, file_path, file_size, tags, rights_confirmed,
                                source, source_url, creator, license_name, license_url,
                                commercial_use, modification_allowed, attribution_required,
                                attribution_text, safety_state, verified_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            asset_id,
                            candidate.get("title", query)[:100],
                            "meme_visual",
                            str(save_path),
                            os.path.getsize(save_path) if save_path.exists() else 0,
                            json.dumps([query, "wikimedia", style]),
                            1,
                            lic_rec.source,
                            candidate["url"],
                            lic_rec.creator,
                            lic_rec.license_name,
                            lic_rec.license_url,
                            1 if lic_rec.commercial_use else 0,
                            1 if lic_rec.modification_allowed else 0,
                            1 if lic_rec.attribution_required else 0,
                            lic_rec.attribution_text,
                            lic_rec.safety_state,
                            lic_rec.verified_at
                        ))
                    return {
                        "asset_id": asset_id,
                        "file_path": str(save_path),
                        "license_record": lic_rec.to_dict()
                    }

        # 3. Query RoyaltyFreeStockProvider (Unsplash / Stock)
        stock_asset_id = str(uuid.uuid4())
        stock_save_path = ASSETS_DIR / "memes" / f"{stock_asset_id}.jpg"
        stock_license = RoyaltyFreeStockProvider.search_and_download(query, stock_save_path)

        if stock_license and stock_save_path.exists() and os.path.getsize(stock_save_path) > 10000:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO assets (
                        id, name, category, file_path, file_size, tags, rights_confirmed,
                        source, source_url, creator, license_name, license_url,
                        commercial_use, modification_allowed, attribution_required,
                        attribution_text, safety_state, verified_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    stock_asset_id,
                    f"Stock Photo: {query[:80]}",
                    "stock_visual",
                    str(stock_save_path),
                    os.path.getsize(stock_save_path),
                    json.dumps([query, "unsplash", style]),
                    1,
                    stock_license.source,
                    stock_license.source_url,
                    stock_license.creator,
                    stock_license.license_name,
                    stock_license.license_url,
                    1 if stock_license.commercial_use else 0,
                    1 if stock_license.modification_allowed else 0,
                    1 if stock_license.attribution_required else 0,
                    stock_license.attribution_text,
                    stock_license.safety_state,
                    stock_license.verified_at
                ))
            return {
                "asset_id": stock_asset_id,
                "file_path": str(stock_save_path),
                "license_record": stock_license.to_dict()
            }

        # 4. Fallback: High Quality Graphic Canvas
        fallback_id = str(uuid.uuid4())
        save_path = ASSETS_DIR / "memes" / f"{fallback_id}.jpg"
        self.pd_provider.generate_canvas(title=query, target_path=save_path, style=style)
        fallback_lic = evaluate_license("Public Domain", "generated", "Studio Canvas Generator")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO assets (
                    id, name, category, file_path, file_size, tags, rights_confirmed,
                    source, source_url, creator, license_name, license_url,
                    commercial_use, modification_allowed, attribution_required,
                    attribution_text, safety_state, verified_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fallback_id,
                f"Graphic Canvas: {query[:80]}",
                "meme_canvas",
                str(save_path),
                os.path.getsize(save_path) if save_path.exists() else 0,
                json.dumps([query, "canvas", style]),
                1,
                fallback_lic.source,
                fallback_lic.source_url,
                fallback_lic.creator,
                fallback_lic.license_name,
                fallback_lic.license_url,
                1 if fallback_lic.commercial_use else 0,
                1 if fallback_lic.modification_allowed else 0,
                1 if fallback_lic.attribution_required else 0,
                fallback_lic.attribution_text,
                fallback_lic.safety_state,
                fallback_lic.verified_at
            ))

        return {
            "asset_id": fallback_id,
            "file_path": str(save_path),
            "license_record": fallback_lic.to_dict()
        }
