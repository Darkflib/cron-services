"""File download utilities."""

import asyncio
import hashlib
import logging
from pathlib import Path
from urllib.parse import unquote, urlparse

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


def is_retryable_exception(exception: Exception) -> bool:
    """Determine if an exception is retryable (transient errors only).

    Args:
        exception: The exception to check

    Returns:
        True if the exception is retryable, False otherwise
    """
    # Network/timeout errors are retryable
    if isinstance(exception, (httpx.ConnectError, httpx.TimeoutException)):
        return True

    # HTTP errors with transient status codes are retryable
    if isinstance(exception, httpx.HTTPStatusError):
        status_code = exception.response.status_code
        # Retry on 429 (rate limit), 502, 503, 504 (server errors)
        if status_code == 429 or 500 <= status_code < 600:
            return True

    # All other errors (404, 403, 400, etc.) are not retryable
    return False


class FileDownloader:
    """Async file downloader with retry logic."""

    def __init__(self, timeout: int = 300):
        """Initialize downloader with timeout."""
        self.timeout = timeout
        self._path_alloc_lock = asyncio.Lock()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
        retry=retry_if_exception(is_retryable_exception),
    )
    async def download_file(self, url: str, dest_path: Path) -> Path:
        """Download a single file with retry logic.

        Args:
            url: URL to download from
            dest_path: Destination file path

        Returns:
            Path to downloaded file
        """
        logger.info("Downloading %s", url)

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                total_size = 0
                with dest_path.open("wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
                        total_size += len(chunk)
                logger.info("Downloaded %s (%d bytes)", dest_path.name, total_size)

        return dest_path

    async def download_urls(
        self, urls: list[str], dest_dir: Path, max_concurrent: int = 4
    ) -> list[Path]:
        """Download multiple URLs concurrently.

        Args:
            urls: List of URLs to download
            dest_dir: Destination directory
            max_concurrent: Maximum concurrent downloads

        Returns:
            List of downloaded file paths
        """
        dest_dir.mkdir(parents=True, exist_ok=True)

        semaphore = asyncio.Semaphore(max_concurrent)

        async def download_with_semaphore(url: str) -> Path:
            async with semaphore:
                parsed = urlparse(url)
                filename = (
                    unquote(parsed.path.split("/")[-1])
                    or f"download_{hashlib.md5(url.encode()).hexdigest()[:8]}"
                )
                # Handle potential filename collisions with lock
                async with self._path_alloc_lock:
                    dest_path = dest_dir / filename
                    if dest_path.exists():
                        stem, suffix = dest_path.stem, dest_path.suffix
                        counter = 1
                        while dest_path.exists():
                            dest_path = dest_dir / f"{stem}_{counter}{suffix}"
                            counter += 1
                # Download outside the lock to allow concurrent downloads
                return await self.download_file(url, dest_path)

        tasks = [download_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        downloaded = []
        for url, result in zip(urls, results, strict=True):
            if isinstance(result, Exception):
                logger.error("Download failed for %s: %s", url, result)
            else:
                downloaded.append(result)

        logger.info("Downloaded %d/%d files successfully", len(downloaded), len(urls))
        return downloaded
