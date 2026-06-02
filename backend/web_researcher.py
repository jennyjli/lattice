"""
Web research module.

Fetches a representative Wikipedia image for a concept and extracts
dominant colors to ground the particle visualization in real visual data.
"""

import io
import urllib.parse
from collections import Counter
from typing import Optional

import httpx
from PIL import Image


class WebResearcher:
    def __init__(self):
        self.timeout = 6.0

    def get_search_query(self, text: str, entities: list[str]) -> str:
        """Extract the best Wikipedia search term from concept text + entities."""
        if entities:
            return entities[0].replace("_", " ").strip()
        first_line = text.strip().split("\n")[0]
        return " ".join(first_line.split()[:6])

    def search_concept(self, query: str) -> dict:
        """
        Search Wikipedia + Wikimedia Commons for the concept.

        Returns:
            {
                found: bool,
                image_url: str | None,          # Wikipedia thumbnail (for color extraction)
                dominant_color: str | None,      # hex, boosted for dark background
                secondary_color: str | None,
                description: str,
                reference_images: list[dict],    # Wikimedia Commons image results
            }
        """
        result: dict = {
            "found": False,
            "image_url": None,
            "dominant_color": None,
            "secondary_color": None,
            "description": "",
            "reference_images": [],
        }

        image_url, description = self._wikipedia_summary(query)
        if not image_url:
            image_url, description = self._wikipedia_search(query)

        if image_url:
            result["image_url"] = image_url
            result["description"] = description
            result["found"] = True
            dominant, secondary = self._extract_colors(image_url)
            result["dominant_color"] = dominant
            result["secondary_color"] = secondary
            print(f"🔍 Web research found: {query!r} → colors {dominant}, {secondary}")
        else:
            print(f"🔍 Web research: no Wikipedia image for {query!r}")

        # Fetch reference images from Wikimedia Commons
        result["reference_images"] = self.search_multiple_images(query, limit=4)

        # Supplement with iNaturalist when Commons returns fewer than 2 results
        if len(result["reference_images"]) < 2:
            needed = 4 - len(result["reference_images"])
            inat = self.search_inaturalist(query, limit=needed)
            result["reference_images"].extend(inat)
            if inat:
                print(f"🌿 iNaturalist fallback: +{len(inat)} images for {query!r}")

        print(f"🖼  Reference images total: {len(result['reference_images'])}")
        return result

    def search_multiple_images(self, query: str, limit: int = 4) -> list[dict]:
        """
        Search Wikimedia Commons for photographic reference images.

        Returns a list of { thumb_url, title, page_url } dicts, skipping SVGs
        and sorting by the search relevance rank returned by the API.
        """
        try:
            r = httpx.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query",
                    "generator": "search",
                    "gsrnamespace": "6",        # File namespace
                    "gsrsearch": query,
                    "gsrlimit": str(min(limit * 3, 20)),
                    "prop": "imageinfo",
                    "iiprop": "url|mime",
                    "iiurlwidth": "320",
                    "format": "json",
                },
                timeout=self.timeout,
            )
            if r.status_code != 200:
                return []

            pages = r.json().get("query", {}).get("pages", {}).values()
            # Sort by API-assigned index (relevance rank)
            sorted_pages = sorted(pages, key=lambda p: p.get("index", 9999))

            results: list[dict] = []
            for page in sorted_pages:
                title = page.get("title", "")
                imageinfo = page.get("imageinfo", [])
                if not imageinfo:
                    continue
                info = imageinfo[0]
                mime = info.get("mime", "")
                thumb_url = info.get("thumburl", "")
                if not thumb_url or not mime.startswith("image/") or "svg" in mime:
                    continue
                # Strip "File:" prefix, extension, underscores for display
                display = title.replace("File:", "").rsplit(".", 1)[0].replace("_", " ")
                results.append({
                    "thumb_url": thumb_url,
                    "title": display,
                    "page_url": f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(title, safe=':/')}",
                })
                if len(results) >= limit:
                    break

            return results

        except Exception as e:
            print(f"Wikimedia image search failed for {query!r}: {e}")
            return []

    def search_inaturalist(self, query: str, limit: int = 4) -> list[dict]:
        """
        Search iNaturalist taxa for biological / botanical organism photos.

        Returns the `default_photo` of the top matching taxa — each is a
        verified, research-grade representative photo. Only useful for
        organisms; returns [] gracefully for abstract concepts.
        """
        try:
            r = httpx.get(
                "https://api.inaturalist.org/v1/taxa",
                params={
                    "q": query,
                    "photos": "true",
                    "per_page": str(limit),
                    "rank": "species,genus,family,order",
                },
                timeout=self.timeout,
            )
            if r.status_code != 200:
                return []

            images: list[dict] = []
            for taxon in r.json().get("results", []):
                # High observation_count is a reliable proxy for "real, well-documented
                # organism" — filters out spurious text matches (e.g. Badnavirus for "DNA").
                if taxon.get("observations_count", 0) < 10_000:
                    continue
                photo = taxon.get("default_photo") or {}
                square_url = photo.get("square_url", "")
                if not square_url:
                    continue
                # Replace 'square' (75 px) with 'small' (~240 px) for more detail.
                thumb = square_url.replace("/square.", "/small.")
                name = taxon.get("preferred_common_name") or taxon.get("name", "")
                images.append({
                    "thumb_url": thumb,
                    "title": f"{name} — iNaturalist",
                    "page_url": f"https://www.inaturalist.org/taxa/{taxon['id']}",
                })
                if len(images) >= limit:
                    break

            return images

        except Exception as e:
            print(f"iNaturalist search failed for {query!r}: {e}")
            return []

    # ── Wikipedia helpers ──────────────────────────────────────────────────────

    def _wikipedia_summary(self, query: str) -> tuple[Optional[str], str]:
        """Direct Wikipedia REST summary lookup by title."""
        try:
            url = (
                "https://en.wikipedia.org/api/rest_v1/page/summary/"
                + urllib.parse.quote(query, safe="")
            )
            r = httpx.get(url, timeout=self.timeout, follow_redirects=True)
            if r.status_code == 200:
                data = r.json()
                thumbnail = data.get("thumbnail", {})
                image_url = thumbnail.get("source")
                description = data.get("extract", "")[:300]
                return image_url, description
        except Exception as e:
            print(f"Wikipedia direct lookup failed: {e}")
        return None, ""

    def _wikipedia_search(self, query: str) -> tuple[Optional[str], str]:
        """Fall back to Wikipedia search API then re-fetch the top result."""
        try:
            r = httpx.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "format": "json",
                    "srlimit": 1,
                },
                timeout=self.timeout,
            )
            if r.status_code == 200:
                results = r.json().get("query", {}).get("search", [])
                if results:
                    return self._wikipedia_summary(results[0]["title"])
        except Exception as e:
            print(f"Wikipedia search failed: {e}")
        return None, ""

    # ── Color extraction ───────────────────────────────────────────────────────

    def _extract_colors(self, image_url: str) -> tuple[Optional[str], Optional[str]]:
        """
        Download thumbnail and extract 2 dominant vivid colors.

        Colors are brightness-boosted for use as glowing particles on a dark
        background — keeps hue but ensures they read well against #030303.
        """
        try:
            r = httpx.get(image_url, timeout=self.timeout, follow_redirects=True)
            img = Image.open(io.BytesIO(r.content)).convert("RGB")
            img = img.resize((80, 80), Image.LANCZOS)

            quantized = img.quantize(colors=12)
            palette = quantized.getpalette()
            counts = Counter(list(quantized.getdata()))

            candidates: list[str] = []
            for color_idx, _ in counts.most_common():
                rv = palette[color_idx * 3]
                gv = palette[color_idx * 3 + 1]
                bv = palette[color_idx * 3 + 2]
                brightness = (rv + gv + bv) / 3
                saturation = max(rv, gv, bv) - min(rv, gv, bv)
                # Skip near-white, near-black, and grey/desaturated tones
                if 35 < brightness < 215 and saturation > 22:
                    # Boost brightness so particles glow on the dark background
                    peak = max(rv, gv, bv)
                    scale = min(255 / peak * 1.35, 1.8) if peak > 0 else 1.0
                    candidates.append(
                        f"#{min(255, int(rv * scale)):02x}"
                        f"{min(255, int(gv * scale)):02x}"
                        f"{min(255, int(bv * scale)):02x}"
                    )
                    if len(candidates) == 2:
                        break

            primary   = candidates[0] if candidates else None
            secondary = candidates[1] if len(candidates) > 1 else primary
            return primary, secondary

        except Exception as e:
            print(f"Color extraction failed for {image_url}: {e}")
            return None, None
