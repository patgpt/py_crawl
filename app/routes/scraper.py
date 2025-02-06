from fastapi import APIRouter, HTTPException
from bs4 import BeautifulSoup
import requests
import html2text
from typing import Dict, Any, Set, List
import time
from pathlib import Path
from slugify import slugify
import os
import logging
from urllib.parse import urlparse, urljoin
import re
from collections import deque
import json
from fastapi.responses import FileResponse
import shutil
import tempfile
from datetime import datetime, timedelta
import zipfile
import asyncio
import psutil
import structlog
from app.utils.events import broadcaster

from app.schemas.scraper import ScraperRequest, ScraperResponse, PageResult
from app.config import settings

router = APIRouter()
logger = structlog.get_logger()

class ScrapingError(Exception):
    """Custom exception for scraping errors"""
    pass

def get_headers(custom_headers: Dict[str, str] = None) -> Dict[str, str]:
    """
    Get headers for HTTP requests

    Args:
        custom_headers (Dict[str, str], optional): Custom headers to merge

    Returns:
        Dict[str, str]: Headers dictionary
    """
    try:
        default_headers = {
            "User-Agent": settings.DEFAULT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

        if custom_headers:
            logger.debug(f"Merging custom headers: {custom_headers}")
            default_headers.update(custom_headers)

        return default_headers
    except Exception as e:
        logger.error(f"Error in get_headers: {str(e)}")
        raise

def convert_to_markdown(html_content: str) -> str:
    """
    Convert HTML content to Markdown

    Args:
        html_content (str): HTML content to convert

    Returns:
        str: Converted Markdown content
    """
    try:
        logger.debug("Converting HTML to Markdown")
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.ignore_tables = False
        h.body_width = 0  # Disable line wrapping
        return h.handle(html_content)
    except Exception as e:
        logger.error(f"Error converting HTML to Markdown: {str(e)}")
        raise ScrapingError(f"Markdown conversion failed: {str(e)}")

def save_to_file(url: str, content: str, is_markdown: bool = True) -> str:
    """
    Save content to a file based on URL pathname

    Args:
        url (str): Source URL
        content (str): Content to save
        is_markdown (bool): Whether the content is markdown

    Returns:
        str: Path to saved file
    """
    try:
        logger.debug(f"Saving content from URL: {url}")

        # Create content directory if it doesn't exist
        content_dir = Path("content")
        content_dir.mkdir(exist_ok=True)

        # Generate filename from URL pathname
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip("/").split("/")

        # Create subdirectories based on URL path
        current_dir = content_dir
        for part in path_parts[:-1]:
            if part:
                current_dir = current_dir / slugify(part)
                current_dir.mkdir(exist_ok=True)

        # Generate filename
        filename = path_parts[-1] if path_parts[-1] else "index"
        filename = slugify(filename)
        extension = ".md" if is_markdown else ".html"
        filepath = current_dir / f"{filename}{extension}"

        logger.debug(f"Saving to file: {filepath}")

        # Save content
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return str(filepath)
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        raise ScrapingError(f"File saving failed: {str(e)}")

class RateLimiter:
    def __init__(self, requests_per_second: float):
        self.rate = requests_per_second
        self.last_request = datetime.min
        self.minimum_interval = timedelta(seconds=1/requests_per_second)

    async def wait(self):
        """Wait for rate limit"""
        now = datetime.now()
        elapsed = now - self.last_request
        if elapsed < self.minimum_interval:
            wait_time = (self.minimum_interval - elapsed).total_seconds()
            await asyncio.sleep(wait_time)
        self.last_request = datetime.now()

class CrawlProgress:
    def __init__(self):
        self.total_pages = 0
        self.processed_pages = 0
        self.failed_pages = 0
        self.start_time = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_pages": self.total_pages,
            "processed_pages": self.processed_pages,
            "failed_pages": self.failed_pages,
            "elapsed_time": (datetime.now() - self.start_time).seconds
        }

class ContentProcessor:
    def process_html(self, html: str) -> str:
        """Process HTML content"""
        soup = BeautifulSoup(html, 'lxml')
        for script in soup.find_all('script'):
            script.decompose()
        for style in soup.find_all('style'):
            style.decompose()
        return str(soup)

    def convert_to_markdown(self, html: str) -> str:
        """Convert HTML to Markdown"""
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.ignore_tables = False
        h.body_width = 0
        return h.handle(html)

class Crawler:
    """
    Web crawler class to handle recursive crawling
    """
    def __init__(self, request: ScraperRequest, test_mode: bool = False):
        self.request = request
        self.visited_urls: Set[str] = set()
        self.results: List[PageResult] = []
        self.memory_limit = 500 * 1024 * 1024  # 500MB
        self.current_memory = 0
        parsed_url = urlparse(str(request.url))
        self.base_domain = parsed_url.netloc
        self.test_mode = test_mode
        if test_mode:
            self.session = requests.Session()
            self.session.mount(
                'https://',
                requests.adapters.HTTPAdapter(max_retries=3)
            )

        # Create debug directory
        self.debug_dir = Path("debug")
        self.debug_dir.mkdir(exist_ok=True)

        logger.info(f"""
        Initializing crawler:
        Base Domain: {self.base_domain}
        Start URL: {request.url}
        Selector: {request.selector}
        Max Depth: {request.crawler_config.max_depth}
        Max Pages: {request.crawler_config.max_pages}
        """)

        self.rate_limiter = RateLimiter(1/request.wait_time)
        self.content_processor = ContentProcessor()

    def debug_save(self, name: str, content: Any):
        """Save debug information to file"""
        try:
            filepath = self.debug_dir / f"{name}.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving debug info: {str(e)}")

    def should_crawl_url(self, url: str) -> bool:
        """
        Check if URL should be crawled based on configuration

        Args:
            url (str): URL to check

        Returns:
            bool: Whether the URL should be crawled
        """
        try:
            parsed_url = urlparse(url)
            path = parsed_url.path

            # Debug logging
            logger.debug(f"Checking URL: {url}")
            logger.debug(f"Path: {path}")

            # Skip if already visited
            if url in self.visited_urls:
                logger.debug(f"Skipping - already visited: {url}")
                return False

            # Check domain
            if parsed_url.netloc != self.base_domain:
                logger.debug(f"Skipping - wrong domain: {parsed_url.netloc}")
                return False

            # Must start with /docs
            if not path.startswith('/docs'):
                logger.debug(f"Skipping - not in docs: {path}")
                return False

            # Check exclude patterns from config
            if self.request.crawler_config.exclude_patterns:
                for pattern in self.request.crawler_config.exclude_patterns:
                    if re.search(pattern, path):
                        logger.debug(f"Skipping - matched exclude pattern {pattern}: {path}")
                        return False

            # Check include patterns from config
            if self.request.crawler_config.include_patterns:
                if not any(re.search(pattern, path) for pattern in self.request.crawler_config.include_patterns):
                    logger.debug(f"Skipping - did not match any include patterns: {path}")
                    return False

            logger.debug(f"URL approved for crawling: {url}")
            return True

        except Exception as e:
            logger.error(f"Error in should_crawl_url: {str(e)}")
            return False

    def extract_links(self, soup: BeautifulSoup, current_url: str) -> Set[str]:
        """
        Extract and normalize links from page

        Args:
            soup: BeautifulSoup object
            current_url: Current page URL

        Returns:
            Set[str]: Set of normalized URLs to crawl
        """
        links = set()
        debug_info = {
            "current_url": current_url,
            "found_links": []
        }

        try:
            anchors = soup.find_all('a', href=True)
            logger.info(f"Found {len(anchors)} anchor tags on {current_url}")

            for anchor in anchors:
                href = anchor['href']
                debug_entry = {"original_href": href}

                try:
                    # Skip invalid hrefs
                    if not href or href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                        debug_entry["skip_reason"] = "invalid_href"
                        continue

                    # Handle relative URLs
                    if href.startswith('/'):
                        parsed_base = urlparse(current_url)
                        href = f"{parsed_base.scheme}://{parsed_base.netloc}{href}"
                    elif not href.startswith(('http://', 'https://')):
                        href = urljoin(current_url, href)

                    debug_entry["normalized_href"] = href

                    # Remove fragments and query parameters
                    parsed = urlparse(href)
                    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    if clean_url.endswith('/'):
                        clean_url = clean_url[:-1]

                    debug_entry["clean_url"] = clean_url

                    # Check if URL should be crawled
                    if self.should_crawl_url(clean_url):
                        links.add(clean_url)
                        debug_entry["status"] = "added"
                    else:
                        debug_entry["status"] = "filtered"

                except Exception as e:
                    debug_entry["error"] = str(e)

                debug_info["found_links"].append(debug_entry)

            # Save debug information
            self.debug_save(f"links_{slugify(current_url)}", debug_info)

            logger.info(f"Extracted {len(links)} valid links from {current_url}")
            return links

        except Exception as e:
            logger.error(f"Error extracting links from {current_url}: {str(e)}")
            return set()

    async def send_update(self, message: str, progress: float = None):
        """Send a progress update to connected clients"""
        update = {
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "progress": progress
        }
        await broadcaster.broadcast(json.dumps(update))

    async def crawl(self) -> ScraperResponse:
        """Perform breadth-first crawl starting from base URL"""
        logger.info(
            "starting_crawl",
            url=str(self.request.url),
            max_pages=self.request.crawler_config.max_pages,
            max_depth=self.request.crawler_config.max_depth
        )
        start_url = str(self.request.url)
        queue = deque([(start_url, 0)])  # (url, depth)
        logger.info(f"""
        Starting crawl with configuration:
        - Start URL: {start_url}
        - Max Pages: {self.request.crawler_config.max_pages}
        - Max Depth: {self.request.crawler_config.max_depth}
        """)

        pages_processed = 0

        try:
            await self.send_update("Starting crawl...", 0)

            while queue and pages_processed < self.request.crawler_config.max_pages:
                url, depth = queue.popleft()
                await self.send_update(f"Processing {url}", progress=10)
                logger.info(f"Processing URL: {url} at depth {depth}")
                logger.info(f"Pages processed: {pages_processed}/{self.request.crawler_config.max_pages}")

                if depth > self.request.crawler_config.max_depth:
                    logger.debug(f"Skipping {url} - max depth reached")
                    continue

                if url in self.visited_urls:
                    logger.debug(f"Skipping {url} - already visited")
                    continue

                try:
                    # Respect rate limiting
                    await self.rate_limiter.wait()

                    # Make request
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
                        "Accept-Language": "en-US,en;q=0.5",
                    }

                    logger.debug(f"Requesting {url}")
                    try:
                        response = requests.get(url, headers=headers, timeout=30)
                        response.raise_for_status()
                    except requests.RequestException as e:
                        logger.error(f"Request failed for {url}: {str(e)}")
                        continue
                    except Exception as e:
                        logger.error(f"Unexpected error processing {url}: {str(e)}")
                        continue

                    # Parse HTML
                    soup = BeautifulSoup(response.text, 'lxml')

                    # Extract content
                    if self.request.selector:
                        elements = soup.select(self.request.selector)
                        if elements:
                            html_content = "\n".join([str(elem) for elem in elements])
                        else:
                            logger.warning(f"No elements found for selector '{self.request.selector}' at {url}")
                            html_content = str(soup.body) if soup.body else str(soup)
                    else:
                        html_content = str(soup.body) if soup.body else str(soup)

                    # Convert to markdown and save
                    h = html2text.HTML2Text()
                    h.ignore_links = False
                    h.ignore_images = False
                    h.ignore_tables = False
                    h.body_width = 0
                    markdown_content = h.handle(html_content)

                    # Save content
                    saved_file_path = None
                    if self.request.save_to_file:
                        saved_file_path = self.save_content(url, markdown_content)

                    # Store result
                    self.results.append(PageResult(
                        url=url,
                        content=html_content[:1000],
                        markdown_content=markdown_content,
                        saved_file_path=saved_file_path,
                        depth=depth
                    ))

                    # Increment pages processed counter
                    pages_processed += 1

                    # Mark URL as visited
                    self.visited_urls.add(url)

                    # Check if we've reached max pages
                    if pages_processed >= self.request.crawler_config.max_pages:
                        logger.info(f"Reached max pages limit: {self.request.crawler_config.max_pages}")
                        break

                    # Extract and queue new links
                    links = self.extract_links(soup, url)
                    logger.info(f"Found {len(links)} new links to crawl from {url}")

                    for link in links:
                        if link not in self.visited_urls:
                            queue.append((link, depth + 1))

                    logger.info(f"Queue size: {len(queue)}")

                    progress = (pages_processed / self.request.crawler_config.max_pages) * 100
                    await self.send_update(f"Processed {url}", progress=progress)

                except Exception as e:
                    logger.error(f"Error processing {url}: {str(e)}")
                    continue

            await self.send_update("Crawl completed successfully", 100)
            logger.info(f"""
            Crawl completed:
            - Pages processed: {pages_processed}
            - Max pages limit: {self.request.crawler_config.max_pages}
            - Total results: {len(self.results)}
            """)

            return ScraperResponse(
                base_url=start_url,
                pages_crawled=self.results,
                total_pages=len(self.results),
                status="success"
            )
        except Exception as e:
            await self.send_update(f"Error: {str(e)}", -1)
            raise

    async def cleanup_files(self):
        """Cleanup temporary files and empty directories"""
        try:
            # Cleanup temp files
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)

            # Cleanup empty directories in content
            content_dir = Path("content")
            if content_dir.exists():
                for root, dirs, files in os.walk(content_dir, topdown=False):
                    for dir_name in dirs:
                        dir_path = Path(root) / dir_name
                        if not any(dir_path.iterdir()):
                            dir_path.rmdir()
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")

    def check_memory_usage(self) -> bool:
        """Check if memory usage is within limits"""
        process = psutil.Process()
        memory_info = process.memory_info()
        self.current_memory = memory_info.rss
        return self.current_memory < self.memory_limit

    def normalize_url(self, url: str) -> str:
        """Normalize URL for consistent comparison"""
        parsed = urlparse(url)
        # Remove trailing slashes
        path = parsed.path.rstrip('/')
        # Remove default ports
        netloc = parsed.netloc.replace(':80', '').replace(':443', '')
        # Reconstruct URL
        return f"{parsed.scheme}://{netloc}{path}"

    def save_content(self, url: str, content: str) -> str:
        content_dir = Path("content")
        content_dir.mkdir(exist_ok=True)

        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip("/").split("/")

        current_dir = content_dir
        for part in path_parts[:-1]:
            if part:
                current_dir = current_dir / slugify(part)
                current_dir.mkdir(exist_ok=True)

        filename = path_parts[-1] if path_parts[-1] else "index"
        filepath = current_dir / f"{slugify(filename)}.md"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"""---
url: {url}
date: {time.strftime('%Y-%m-%d')}
---

{content}
""")
        return str(filepath)

@router.post("/scrape")
async def scrape_url(request: ScraperRequest):
    """
    Crawl pages starting from a base URL and return both metadata and zipped content
    """
    zip_path = None
    try:
        # Perform crawling
        crawler = Crawler(request)
        result = await crawler.crawl()

        # Create timestamp for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"nextjs_docs_{timestamp}.zip"

        # Create zip in the current directory instead of temp
        content_dir = Path("content")
        if not content_dir.exists():
            raise HTTPException(
                status_code=404,
                detail="No content directory found to zip"
            )

        # Create zip in a known location
        zip_path = Path("downloads")
        zip_path.mkdir(exist_ok=True)
        zip_file = zip_path / zip_filename

        logger.info(f"Creating zip file at: {zip_file}")

        # Create zip file
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Walk through the content directory
            for root, dirs, files in os.walk(content_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Calculate path relative to content directory
                    arcname = os.path.relpath(file_path, content_dir)
                    logger.debug(f"Adding to zip: {arcname}")
                    zipf.write(file_path, arcname)

        # Verify zip file exists
        if not zip_file.exists():
            raise HTTPException(
                status_code=500,
                detail="Failed to create zip file"
            )

        logger.info(f"Zip file created successfully at: {zip_file}")

        # Schedule cleanup for later
        async def cleanup():
            try:
                await asyncio.sleep(60)  # Wait 60 seconds before cleanup
                if zip_file.exists():
                    os.remove(zip_file)
                    logger.info(f"Cleaned up zip file: {zip_file}")
            except Exception as e:
                logger.error(f"Error cleaning up zip file: {str(e)}")

        # Start cleanup task
        asyncio.create_task(cleanup())

        # Return the zip file
        return FileResponse(
            path=str(zip_file),
            media_type='application/zip',
            filename=zip_filename,
            headers={
                "Content-Disposition": f"attachment; filename={zip_filename}"
            }
        )

    except Exception as e:
        logger.error(f"Error in scrape_url: {str(e)}")
        # Clean up zip file if it exists
        if zip_path and zip_path.exists():
            try:
                os.remove(zip_path)
            except Exception as cleanup_error:
                logger.error(f"Error cleaning up zip file: {str(cleanup_error)}")
        raise HTTPException(status_code=500, detail=str(e))