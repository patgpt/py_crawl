from pydantic import BaseModel, AnyHttpUrl, Field, ConfigDict
from typing import Optional, List, Pattern
import re
from pydantic import validator, field_validator

class CrawlerConfig(BaseModel):
    """
    Configuration for crawler behavior

    Attributes:
        max_depth (int): Maximum depth to crawl
        max_pages (int): Maximum number of pages to crawl
        include_patterns (list[str]): Regex patterns for URLs to include
        exclude_patterns (list[str]): Regex patterns for URLs to exclude
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    max_depth: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum depth to crawl"
    )
    max_pages: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of pages to crawl"
    )
    include_patterns: List[str] = Field(
        default=[],
        description="Regex patterns for URLs to include"
    )
    exclude_patterns: List[str] = Field(
        default=[],
        description="Regex patterns for URLs to exclude"
    )

    @field_validator('include_patterns', 'exclude_patterns')
    def validate_patterns(cls, patterns):
        """Validate regex patterns"""
        for pattern in patterns:
            try:
                re.compile(pattern)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern '{pattern}': {str(e)}")
        return patterns

class ScraperRequest(BaseModel):
    """
    Schema for scraper request

    Attributes:
        url (AnyHttpUrl): Base URL to start crawling from
        selector (str | None): Optional CSS selector to extract specific elements
        save_to_file (bool): Whether to save the content to a file
        use_proxy (bool): Whether to use a proxy for the request
        custom_headers (dict | None): Optional custom headers for the request
        wait_time (float): Time to wait between requests in seconds
        crawler_config (CrawlerConfig): Configuration for crawler behavior
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    url: AnyHttpUrl
    selector: Optional[str] = None
    save_to_file: bool = True
    use_proxy: bool = False
    custom_headers: Optional[dict] = None
    wait_time: float = Field(default=1.0, ge=0.001, le=30.0)
    crawler_config: CrawlerConfig = CrawlerConfig()

    @field_validator('wait_time')
    def validate_wait_time(cls, v):
        if v <= 0:
            raise ValueError("wait_time must be greater than 0")
        return v

class PageResult(BaseModel):
    """
    Result for a single crawled page

    Attributes:
        url (str): Page URL
        content (str): Page content
        markdown_content (str | None): Converted markdown content
        saved_file_path (str | None): Path to saved file
        depth (int): Crawl depth of this page
    """
    url: str
    content: str
    markdown_content: Optional[str] = None
    saved_file_path: Optional[str] = None
    depth: int

class ScraperResponse(BaseModel):
    """
    Schema for scraper response

    Attributes:
        base_url (str): Original base URL
        pages_crawled (list[PageResult]): List of crawled pages
        total_pages (int): Total number of pages crawled
        status (str): Status of the crawling operation
    """
    base_url: str
    pages_crawled: List[PageResult]
    total_pages: int
    status: str