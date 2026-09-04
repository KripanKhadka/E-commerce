"""
Downloads real product photos for every Item and HeroSlide using the
Pexels API (https://www.pexels.com/api/). Pexels photos are free for
commercial use and don't require attribution.

Why this is a management command and not something already run for you:
this project is built in a sandboxed environment with no general internet
access, so real photos can't be fetched at build time. Run this yourself,
locally or on your server, where normal internet access is available.

Setup:
1. Get a free API key at https://www.pexels.com/api/ (instant signup).
2. Add it to your .env file:
       PEXELS_API_KEY=your-key-here
3. Run:
       python manage.py fetch_real_images

Options:
    --only-missing   Only fill in items that still have no image.
    --item <slug>     Fetch just one item by slug.
"""
import io
import ssl
import time
import urllib.request
import urllib.parse
import urllib.error

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from core.models import Item, HeroSlide

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"
OPENVERSE_SEARCH_URL = "https://api.openverse.org/v1/images/"


def _build_ssl_context():
    """Use certifi's up-to-date CA bundle when available, instead of
    relying on the OS trust store, which is a common source of
    'certificate has expired' / 'certificate verify failed' errors even
    when the remote server's certificate is perfectly valid."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()

# Search query used for each item, in plain descriptive terms rather than
# brand names, so results are real, relevant, generic-use product photos.
ITEM_QUERIES = {
    "rcb-authentic-jersey-2026": "cricket jersey",
    "sports-tshirt-pro": "sports t-shirt",
    "sports-shorts-quick-dry": "athletic shorts",
    "sports-watch-smartband": "fitness smartwatch",
    "sports-cap-baseball": "baseball cap",
    "gym-bag-duffel": "gym duffel bag",
    "sports-gloves-training": "training gloves",
    "air-jordan-performance": "athletic footwear",
    "pro-basketball": "basketball",
    "basketball-shoes-high-top": "high top basketball shoes",
    "basketball-backboard": "basketball hoop backboard",
    "basketball-socks-crew": "athletic crew socks",
    "nike-mercurial-superfly": "soccer cleats",
    "football": "soccer ball",
    "professional-soccer-ball": "soccer ball closeup",
    "soccer-cleats-premium": "football boots",
    "football-training-cones": "soccer training cones",
    "shin-guard-protection": "soccer shin guards",
    "trailmaster-hiking-pack": "hiking backpack",
    "hiking-backpack-50l": "large hiking backpack",
    "camping-tent-2-person": "camping tent",
    "hiking-boots-waterproof": "hiking boots",
    "sleeping-bag-summer": "sleeping bag",
    "portable-camping-stove": "camping stove",
    "asics-shoes": "running shoes",
    "running-shoes-pro": "running shoes pair",
    "yoga-mat-premium": "yoga mat",
    "dumbbell-set-10kg": "dumbbells",
    "sports-water-bottle": "water bottle",
    "jump-rope-speed": "jump rope",
    "wilson-pro-staff-97": "tennis racket",
    "professional-tennis-racket": "tennis racket closeup",
    "tennis-balls-can": "tennis balls",
    "badminton-racket-pair": "badminton racket",
    "squash-racket": "squash racket",
}

HERO_QUERIES = {
    "Train harder. Play better.": "athlete training gym",
    "Built for the trail.": "hiking trail mountains",
    "Game-day essentials.": "soccer stadium",
    "Elevate Your Game": "basketball game",
    "Train Harder": "gym workout",
    "Play Better": "tennis court action",
    "Explore The Outdoors": "Nepal Himalaya mountain landscape",
    "Summer Sports Special": "summer sports beach",
}


class Command(BaseCommand):
    help = "Fetch real product/hero photos from Pexels and attach them to Items and HeroSlides."

    def add_arguments(self, parser):
        parser.add_argument("--only-missing", action="store_true",
                             help="Only fetch images for records that currently have none.")
        parser.add_argument("--item", type=str, default=None,
                             help="Only fetch a single item, by slug.")

    def handle(self, *args, **options):
        api_key = getattr(settings, "PEXELS_API_KEY", "") or ""
        if not api_key:
            self.stdout.write("PEXELS_API_KEY is not set; using Openverse fallback.")

        only_missing = options["only_missing"]
        only_slug = options["item"]

        items = Item.objects.all().order_by("id")
        if only_slug:
            items = items.filter(slug=only_slug)
            if not items.exists():
                raise CommandError(f"No item with slug '{only_slug}'.")

        for item in items:
            if only_missing and item.image:
                continue
            query = ITEM_QUERIES.get(item.slug, item.title)
            self.stdout.write(f"Fetching '{query}' for item: {item.title}...")
            photo_bytes = self._fetch_photo(api_key, query, orientation="square")
            if photo_bytes:
                item.image.save(f"{item.slug}.jpg", ContentFile(photo_bytes), save=True)
                self.stdout.write(self.style.SUCCESS(f"  saved -> {item.image.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"  no result for '{query}', kept existing image"))
            time.sleep(0.3)  # be polite to the free API tier

        if not only_slug:
            for slide in HeroSlide.objects.all().order_by("id"):
                if only_missing and slide.image:
                    continue
                query = HERO_QUERIES.get(slide.title, slide.title)
                self.stdout.write(f"Fetching '{query}' for hero slide: {slide.title}...")
                photo_bytes = self._fetch_photo(api_key, query, orientation="landscape")
                if photo_bytes:
                    safe = "".join(ch if ch.isalnum() else "-" for ch in slide.title.lower()).strip("-")
                    slide.image.save(f"hero-{safe}.jpg", ContentFile(photo_bytes), save=True)
                    self.stdout.write(self.style.SUCCESS(f"  saved -> {slide.image.name}"))
                else:
                    self.stdout.write(self.style.WARNING(f"  no result for '{query}', kept existing image"))
                time.sleep(0.3)

        self.stdout.write(self.style.SUCCESS("Done."))

    def _fetch_photo(self, api_key, query, orientation="square"):
        if not api_key:
            return self._fetch_openverse_photo(query, orientation)
        params = urllib.parse.urlencode({
            "query": query, "per_page": 1, "orientation": orientation,
        })
        req = urllib.request.Request(
            f"{PEXELS_SEARCH_URL}?{params}",
            headers={"Authorization": api_key},
        )
        ctx = _build_ssl_context()
        try:
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                import json
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            response_body = exc.read().decode("utf-8", "replace")[:300]
            if exc.code == 403 and "1010" in response_body:
                self.stderr.write(self.style.ERROR(
                    "  Pexels blocked this network with Cloudflare error 1010. "
                    "Trying Openverse fallback."
                ))
            elif exc.code in (401, 403):
                self.stderr.write(self.style.ERROR(
                    f"  Pexels rejected the API key (HTTP {exc.code}). "
                    "Trying Openverse fallback."
                ))
            else:
                self.stderr.write(self.style.ERROR(f"  Pexels API error: HTTP {exc.code}"))
            return self._fetch_openverse_photo(query, orientation)
        except Exception as exc:
            if "CERTIFICATE_VERIFY_FAILED" in str(exc) or "certificate" in str(exc).lower():
                self.stderr.write(self.style.ERROR(
                    "  SSL certificate check failed talking to Pexels. This is almost "
                    "always local, not Pexels: either your computer's clock/date is "
                    "wrong, or your system's CA certificates are outdated. Check the "
                    "date/time first, then see the 'SSL certificate errors' section "
                    "in IMAGES_AND_ITEMS_GUIDE.md."
                ))
                raise CommandError(str(exc))
            self.stderr.write(self.style.ERROR(f"  Pexels API error: {exc}"))
            return self._fetch_openverse_photo(query, orientation)

        photos = data.get("photos") or []
        if not photos:
            return self._fetch_openverse_photo(query, orientation)
        image_url = photos[0]["src"]["large"]
        try:
            with urllib.request.urlopen(image_url, timeout=20, context=ctx) as img_resp:
                return img_resp.read()
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"  download error: {exc}"))
            return self._fetch_openverse_photo(query, orientation)

    def _fetch_openverse_photo(self, query, orientation):
        params = urllib.parse.urlencode({
            "q": query, "page_size": 10,
            "license": "by,by-sa,cc0,pdm",
        })
        req = urllib.request.Request(
            f"{OPENVERSE_SEARCH_URL}?{params}",
            headers={"User-Agent": "HamroSports image downloader/1.0"},
        )
        ctx = _build_ssl_context()
        try:
            with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
                import json
                results = json.loads(resp.read().decode("utf-8")).get("results", [])
            for result in results:
                width = result.get("width") or 0
                height = result.get("height") or 0
                if not width or not height:
                    continue
                ratio = width / height
                if orientation == "landscape" and ratio < 1.5:
                    continue
                if orientation == "square" and not 0.6 <= ratio <= 1.8:
                    continue
                image_url = result.get("url")
                if not image_url:
                    continue
                try:
                    with urllib.request.urlopen(image_url, timeout=30, context=ctx) as img_resp:
                        image_bytes = img_resp.read()
                except urllib.error.HTTPError:
                    continue
                self.stdout.write(
                    f"  Openverse source: {result.get('creator') or 'unknown creator'} "
                    f"({result.get('license') or 'license listed on source page'})"
                )
                return image_bytes
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"  Openverse error: {exc}"))
        return None
