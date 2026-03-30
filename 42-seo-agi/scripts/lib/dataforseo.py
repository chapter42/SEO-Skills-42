"""
DataForSEO API client for SEO-AGI.
Handles SERP results, keyword data, People Also Ask, and content parsing.
"""

import json
import base64
import ssl
import urllib.request
import urllib.error
from typing import Optional


def _make_ssl_context() -> ssl.SSLContext:
    """Create an SSL context that works on macOS with standalone Python."""
    # Try certifi first (pip install certifi)
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass

    # Try macOS certificate install path
    import os
    for ca_path in [
        "/etc/ssl/cert.pem",
        "/usr/local/etc/openssl/cert.pem",
        "/opt/homebrew/etc/openssl@3/cert.pem",
    ]:
        if os.path.exists(ca_path):
            return ssl.create_default_context(cafile=ca_path)

    # Fallback: unverified (prints warning)
    import warnings
    warnings.warn(
        "DataForSEO: no trusted CA bundle found, using unverified SSL. "
        "Run 'pip install certifi' to fix.",
        stacklevel=2,
    )
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


class DataForSEOClient:
    """Client for DataForSEO REST API v3."""

    BASE_URL = "https://api.dataforseo.com/v3"

    def __init__(self, login: str, password: str):
        self.login = login
        self.password = password
        self._auth_header = self._make_auth_header(login, password)
        self._ssl_ctx = _make_ssl_context()

    @staticmethod
    def _make_auth_header(login: str, password: str) -> str:
        token = base64.b64encode(f"{login}:{password}".encode()).decode()
        return f"Basic {token}"

    def _request(self, endpoint: str, payload: list[dict]) -> dict:
        """Make a POST request to DataForSEO API."""
        url = f"{self.BASE_URL}{endpoint}"
        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": self._auth_header,
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30, context=self._ssl_ctx) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode() if e.fp else ""
            raise RuntimeError(
                f"DataForSEO API error {e.code}: {body}"
            ) from e
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"DataForSEO connection error: {e.reason}"
            ) from e

    def serp_live(
        self,
        keyword: str,
        location_code: int = 2840,
        language_code: str = "en",
        depth: int = 10,
    ) -> dict:
        """
        Get live SERP results for a keyword.
        Returns organic results with position, URL, title, description.
        """
        payload = [
            {
                "keyword": keyword,
                "location_code": location_code,
                "language_code": language_code,
                "depth": depth,
                "se_type": "organic",
            }
        ]
        result = self._request(
            "/serp/google/organic/live/advanced", payload
        )
        return self._extract_serp(result)

    def related_keywords(
        self,
        keyword: str,
        location_code: int = 2840,
        language_code: str = "en",
        limit: int = 30,
    ) -> list[dict]:
        """Get related keywords with search volume and difficulty."""
        payload = [
            {
                "keyword": keyword,
                "location_code": location_code,
                "language_code": language_code,
                "limit": limit,
            }
        ]
        result = self._request(
            "/dataforseo_labs/google/related_keywords/live", payload
        )
        return self._extract_keywords(result)

    def keyword_suggestions(
        self,
        keyword: str,
        location_code: int = 2840,
        language_code: str = "en",
        limit: int = 30,
    ) -> list[dict]:
        """Get keyword suggestions (broader ideation)."""
        payload = [
            {
                "keyword": keyword,
                "location_code": location_code,
                "language_code": language_code,
                "limit": limit,
            }
        ]
        result = self._request(
            "/dataforseo_labs/google/keyword_suggestions/live", payload
        )
        return self._extract_keywords(result)

    def content_parse(self, url: str) -> Optional[dict]:
        """Parse content from a URL (headings, word count, structure)."""
        payload = [{"url": url}]
        try:
            result = self._request(
                "/on_page/content_parsing/live", payload
            )
            return self._extract_content(result)
        except RuntimeError:
            return None

    def _extract_serp(self, raw: dict) -> dict:
        """Extract clean SERP data from API response."""
        tasks = raw.get("tasks", [])
        if not tasks:
            return {"organic": [], "paa": [], "featured_snippet": None}

        result = tasks[0].get("result", [])
        if not result:
            return {"organic": [], "paa": [], "featured_snippet": None}

        items = result[0].get("items", [])

        organic = []
        paa_questions = []
        featured_snippet = None

        for item in items:
            item_type = item.get("type", "")

            if item_type == "organic":
                organic.append(
                    {
                        "position": item.get("rank_absolute", 0),
                        "url": item.get("url", ""),
                        "domain": item.get("domain", ""),
                        "title": item.get("title", ""),
                        "description": item.get("description", ""),
                    }
                )

            elif item_type == "people_also_ask":
                for paa_item in item.get("items", []):
                    q = paa_item.get("title", "")
                    if q:
                        paa_questions.append(q)

            elif item_type == "featured_snippet":
                featured_snippet = {
                    "url": item.get("url", ""),
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                }

        return {
            "organic": organic,
            "paa": paa_questions,
            "featured_snippet": featured_snippet,
            "total_results": result[0].get("se_results_count", 0),
        }

    def _extract_keywords(self, raw: dict) -> list[dict]:
        """Extract keyword data from labs API response."""
        tasks = raw.get("tasks", [])
        if not tasks:
            return []

        result = tasks[0].get("result", [])
        if not result:
            return []

        items = result[0].get("items") or []
        keywords = []

        for item in items:
            kw_data = item.get("keyword_data", item)
            keyword_info = kw_data.get("keyword_info", {})
            keywords.append(
                {
                    "keyword": kw_data.get("keyword", ""),
                    "volume": keyword_info.get("search_volume", 0),
                    "cpc": keyword_info.get("cpc", 0),
                    "competition": keyword_info.get("competition", 0),
                    "difficulty": kw_data.get(
                        "keyword_properties", {}
                    ).get("keyword_difficulty", 0),
                }
            )

        return sorted(keywords, key=lambda x: x["volume"], reverse=True)

    def _extract_content(self, raw: dict) -> Optional[dict]:
        """Extract content structure from on-page parsing."""
        tasks = raw.get("tasks", [])
        if not tasks:
            return None

        result = tasks[0].get("result", [])
        if not result:
            return None

        items = result[0].get("items") or []
        if not items:
            return None

        page = items[0].get("page_content") or {}

        header = page.get("header") or {}
        return {
            "title": header.get("title", ""),
            "word_count": page.get("plain_text_word_count", 0),
            "headings": self._extract_headings(page),
            "plain_text_size": page.get("plain_text_size", 0),
        }

    @staticmethod
    def _extract_headings(page_content: dict) -> list[str]:
        """Pull heading tags from parsed content."""
        headings = []
        for level in ["h1", "h2", "h3"]:
            for heading in page_content.get(level, []):
                headings.append(f"{level.upper()}: {heading}")
        return headings
