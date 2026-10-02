from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import requests
from requests import Response
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


class APIClient:
    """
    Reusable HTTP client for NEXUS 360.

    Features:
        - request timeout
        - automatic retries
        - exponential backoff
        - JSON validation
        - deterministic local caching
        - standard User-Agent
        - HTTP error handling
    """

    def __init__(
        self,
        timeout_seconds: int = 30,
        cache_enabled: bool = True,
        cache_directory: str = "data/cache/api",
    ) -> None:

        self.timeout_seconds = (
            timeout_seconds
        )

        self.cache_enabled = (
            cache_enabled
        )

        self.cache_directory = Path(
            cache_directory
        )

        self.cache_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent":
                    "NEXUS360-Analytics-Platform/1.0",

                "Accept":
                    "application/json",
            }
        )

    @staticmethod
    def _build_cache_key(
        url: str,
        params: dict[str, Any] | None,
    ) -> str:

        payload = json.dumps(
            {
                "url": url,
                "params": params or {},
            },
            sort_keys=True,
            default=str,
        )

        return hashlib.sha256(
            payload.encode("utf-8")
        ).hexdigest()

    def _cache_path(
        self,
        url: str,
        params: dict[str, Any] | None,
    ) -> Path:

        key = self._build_cache_key(
            url=url,
            params=params,
        )

        return (
            self.cache_directory
            / f"{key}.json"
        )

    def _read_cache(
        self,
        url: str,
        params: dict[str, Any] | None,
    ) -> Any | None:

        if not self.cache_enabled:
            return None

        path = self._cache_path(
            url=url,
            params=params,
        )

        if not path.exists():
            return None

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    def _write_cache(
        self,
        url: str,
        params: dict[str, Any] | None,
        data: Any,
    ) -> None:

        if not self.cache_enabled:
            return

        path = self._cache_path(
            url=url,
            params=params,
        )

        with path.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
                default=str,
            )

    @retry(
        retry=retry_if_exception_type(
            (
                requests.Timeout,
                requests.ConnectionError,
            )
        ),
        stop=stop_after_attempt(4),
        wait=wait_exponential(
            multiplier=1,
            min=1,
            max=10,
        ),
        reraise=True,
    )
    def _request(
        self,
        url: str,
        params: dict[str, Any] | None,
    ) -> Response:

        response = self.session.get(
            url,
            params=params,
            timeout=self.timeout_seconds,
        )

        response.raise_for_status()

        return response

    def get_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        force_refresh: bool = False,
    ) -> Any:

        if not force_refresh:

            cached = self._read_cache(
                url=url,
                params=params,
            )

            if cached is not None:

                print(
                    f"[CACHE] {url}"
                )

                return cached

        print(
            f"[API] {url}"
        )

        response = self._request(
            url=url,
            params=params,
        )

        try:

            data = response.json()

        except requests.JSONDecodeError as exc:

            raise ValueError(
                f"API did not return valid JSON: "
                f"{url}"
            ) from exc

        self._write_cache(
            url=url,
            params=params,
            data=data,
        )

        return data