"""File download utilities."""

import asyncio
import logging
from pathlib import Path

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class FileDownloader:
    """Async file downloader with retry logic."""

    def __init__(self, timeout: int = 300):
        """Initialize downloader with timeout."""
        self.timeout = timeout

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def download_file(self, url: str, dest_path: Path) -> Path:
        """Download a single file with retry logic.

        Args:
            url: URL to download from
            dest_path: Destination file path

        Returns:
            Path to downloaded file
        """
        logger.info(f"Downloading {url}")

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()

            dest_path.write_bytes(response.content)
            logger.info(f"Downloaded {dest_path.name} ({len(response.content)} bytes)")

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
                filename = url.split("/")[-1].split("?")[0]
                dest_path = dest_dir / filename
                return await self.download_file(url, dest_path)

        tasks = [download_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        downloaded = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Download failed: {result}")
            else:
                downloaded.append(result)

        logger.info(f"Downloaded {len(downloaded)}/{len(urls)} files successfully")
        return downloaded
