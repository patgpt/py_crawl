import pytest
import logging
from pathlib import Path
import shutil

# Minimal configuration, no pytest_configure
@pytest.fixture(autouse=True)
def setup_logging():
    logging.basicConfig(level=logging.DEBUG)

@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path

@pytest.fixture(autouse=True)
def cleanup_files():
    yield
    dirs_to_clean = ['content', 'downloads', 'debug']
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path)

import pytest
import pytest_asyncio
from app.schemas.scraper import ScraperRequest, CrawlerConfig

# Configure asyncio
pytest.register_assert_rewrite('pytest_asyncio')

@pytest.fixture
def sample_request():
    return ScraperRequest(
        url="https://nextjs.org/docs/app",
        selector="article",
        save_to_file=True,
        wait_time=1.0,
        crawler_config=CrawlerConfig(
            max_depth=2,
            max_pages=5,
            include_patterns=["/docs/app.*"],
            exclude_patterns=["/docs/pages.*"]
        )
    )

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

def pytest_configure(config):
    config.addinivalue_line(
        "asyncio_mode",
        "strict"
    )
    config.addinivalue_line(
        "asyncio_fixture_loop_scope",
        "function"
    )

# Configure pytest-asyncio
pytest_plugins = ['pytest_asyncio']