import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup
import responses
from pathlib import Path
import shutil
import tempfile

from app.main import app
from app.routes.scraper import Crawler
from app.schemas.scraper import ScraperRequest, CrawlerConfig

client = TestClient(app)

@pytest.fixture
def mock_html():
    """Sample HTML content for testing"""
    return """
    <html>
        <body>
            <article>
                <h1>Test Page</h1>
                <p>Test content</p>
                <a href="/docs/app/page1">Link 1</a>
                <a href="/docs/app/page2">Link 2</a>
                <a href="/docs/pages/old">Old Link</a>
                <a href="https://external.com">External Link</a>
            </article>
        </body>
    </html>
    """

@pytest.fixture
def temp_dir():
    """Create temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

class TestCrawler:
    """Test Crawler functionality"""

    def test_url_normalization(self, sample_request):
        crawler = Crawler(sample_request)
        urls = [
            "https://nextjs.org/docs/app/",
            "https://nextjs.org/docs/app",
            "https://nextjs.org:443/docs/app",
        ]
        normalized = [crawler.normalize_url(url) for url in urls]
        assert len(set(normalized)) == 1

    def test_should_crawl_url(self, sample_request):
        crawler = Crawler(sample_request)

        # Should crawl
        assert crawler.should_crawl_url("https://nextjs.org/docs/app/page1")

        # Should not crawl
        assert not crawler.should_crawl_url("https://nextjs.org/docs/pages/old")
        assert not crawler.should_crawl_url("https://external.com/docs")
        assert not crawler.should_crawl_url("https://nextjs.org/blog")

    @responses.activate
    def test_extract_links(self, sample_request, mock_html):
        crawler = Crawler(sample_request)

        # Mock response
        responses.add(
            responses.GET,
            "https://nextjs.org/docs/app",
            body=mock_html,
            status=200
        )

        soup = BeautifulSoup(mock_html, 'lxml')
        links = crawler.extract_links(soup, "https://nextjs.org/docs/app")

        assert len(links) == 2
        assert "https://nextjs.org/docs/app/page1" in links
        assert "https://nextjs.org/docs/app/page2" in links

    @responses.activate
    def test_content_processing(self, sample_request, mock_html):
        crawler = Crawler(sample_request)
        processor = crawler.content_processor

        # Test HTML processing
        processed_html = processor.process_html(mock_html)
        assert "<script>" not in processed_html
        assert "<style>" not in processed_html

        # Test Markdown conversion
        markdown = processor.convert_to_markdown(processed_html)
        assert "# Test Page" in markdown
        assert "[Link 1]" in markdown

    @responses.activate
    @pytest.mark.asyncio
    async def test_crawl_max_pages(self, sample_request, mock_html):
        crawler = Crawler(sample_request)

        # Mock multiple pages
        base_url = "https://nextjs.org/docs/app"
        responses.add(responses.GET, base_url, body=mock_html, status=200)
        for i in range(1, 6):
            responses.add(
                responses.GET,
                f"{base_url}/page{i}",
                body=mock_html,
                status=200
            )

        result = await crawler.crawl()
        assert len(result.pages_crawled) <= sample_request.crawler_config.max_pages

    def test_file_saving(self, sample_request, temp_dir, mock_html):
        # Create content directory in temp_dir
        content_path = Path(temp_dir) / "content"
        content_path.mkdir(exist_ok=True)

        with patch('app.routes.scraper.Path') as mock_path:
            # Make Path return our temp path
            mock_path.return_value = content_path
            crawler = Crawler(sample_request)
            filepath = crawler.save_content(
                "https://nextjs.org/docs/app/test",
                "# Test Content"
            )
            assert Path(filepath).exists()

class TestAPI:
    """Test API endpoints"""

    @responses.activate
    def test_scrape_endpoint(self, mock_html):
        responses.add(
            responses.GET,
            "https://nextjs.org/docs/app",
            body=mock_html,
            status=200
        )

        test_data = {
            "url": "https://nextjs.org/docs/app",
            "selector": "article",
            "save_to_file": True,
            "use_proxy": False,
            "custom_headers": None,
            "wait_time": 0.001,
            "crawler_config": {
                "max_depth": 2,
                "max_pages": 5,
                "include_patterns": ["/docs/app.*"],
                "exclude_patterns": ["/docs/pages.*"]
            }
        }

        response = client.post("/api/v1/scrape", json=test_data)

        if response.status_code != 200:
            print(f"Response Error: {response.json()}")

        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/zip"

    def test_invalid_request(self):
        response = client.post(
            "/api/v1/scrape",
            json={
                "url": "not-a-url",
                "selector": "article"
            }
        )
        assert response.status_code == 422