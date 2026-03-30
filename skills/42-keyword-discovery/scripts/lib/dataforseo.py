"""
DataForSEO client — shared from seo-agi.
Handles keyword suggestions, related keywords, search volume, and SERP data.
"""

import json
import base64
import ssl
import urllib.request
import urllib.error
from typing import Optional


def _make_ssl_context() -> ssl.SSLContext:
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    import os
    for ca_path in [
        "/etc/ssl/cert.pem",
        "/usr/local/etc/openssl/cert.pem",
        "/opt/homebrew/etc/openssl@3/cert.pem",
    ]:
        if os.path.exists(ca_path):
            return ssl.create_default_context(cafile=ca_path)
    import warnings
    warnings.warn(
        "No trusted CA bundle found, using unverified SSL. "
        "Run 'pip install certifi' to fix.",
        stacklevel=2,
    )
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


class DataForSEOClient:
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
        url = f"{self.BASE_URL}{endpoint}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data,
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
            raise RuntimeError(f"DataForSEO API error {e.code}: {body}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"DataForSEO connection error: {e.reason}") from e

    def keyword_suggestions(
        self, keyword: str, location_code: int = 2840,
        language_code: str = "en", limit: int = 50,
    ) -> list[dict]:
        payload = [{
            "keyword": keyword,
            "location_code": location_code,
            "language_code": language_code,
            "limit": limit,
        }]
        result = self._request(
            "/dataforseo_labs/google/keyword_suggestions/live", payload
        )
        return self._extract_keywords(result)

    def related_keywords(
        self, keyword: str, location_code: int = 2840,
        language_code: str = "en", limit: int = 50,
    ) -> list[dict]:
        payload = [{
            "keyword": keyword,
            "location_code": location_code,
            "language_code": language_code,
            "limit": limit,
        }]
        result = self._request(
            "/dataforseo_labs/google/related_keywords/live", payload
        )
        return self._extract_keywords(result)

    def search_volume(
        self, keywords: list[str], location_code: int = 2840,
        language_code: str = "en",
    ) -> list[dict]:
        payload = [{
            "keywords": keywords[:1000],
            "location_code": location_code,
            "language_code": language_code,
        }]
        result = self._request(
            "/dataforseo_labs/google/bulk_keyword_difficulty/live", payload
        )
        return self._extract_bulk(result)

    def _extract_keywords(self, raw: dict) -> list[dict]:
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
            keywords.append({
                "keyword": kw_data.get("keyword", ""),
                "volume": keyword_info.get("search_volume", 0),
                "cpc": keyword_info.get("cpc", 0),
                "competition": keyword_info.get("competition", 0),
                "difficulty": kw_data.get("keyword_properties", {}).get(
                    "keyword_difficulty", 0
                ),
            })
        return sorted(keywords, key=lambda x: x["volume"] or 0, reverse=True)

    def _extract_bulk(self, raw: dict) -> list[dict]:
        tasks = raw.get("tasks", [])
        if not tasks:
            return []
        result = tasks[0].get("result", [])
        if not result:
            return []
        items = result[0].get("items") or []
        keywords = []
        for item in items:
            keywords.append({
                "keyword": item.get("keyword", ""),
                "volume": item.get("search_volume", 0),
                "difficulty": item.get("keyword_difficulty", 0),
                "cpc": item.get("cpc", 0),
                "competition": item.get("competition", 0),
            })
        return sorted(keywords, key=lambda x: x["volume"] or 0, reverse=True)
