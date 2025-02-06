# 🕷️ py_crawl

[![Python](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.0-009688.svg)](https://fastapi.tiangolo.com)
[![Pydantic](https://img.shields.io/badge/pydantic-2.4.2-E92063.svg)](https://docs.pydantic.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.md)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A modern, async web crawler built with FastAPI and Python. Efficiently crawls websites, converts content to Markdown, and provides organized storage. 🚀

## ✨ Features

- 🌐 Configurable depth and page limit crawling
- 📝 Automatic HTML to Markdown conversion
- 🎯 URL filtering with regex patterns
- 💾 Structured content storage
- ⚡ Async processing with rate limiting
- 🛡️ Memory usage monitoring
- 🗂️ ZIP archive exports

## 🚀 Getting Started

1. **Set up your environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server**
   ```bash
   uvicorn app.main:app --reload
   ```

## 🔧 Usage

Make a POST request to `/api/v1/scrape`:
```json
{
"url": "https://example.com",
"selector": "article",
"save_to_file": true,
"wait_time": 1.0,
"crawler_config": {
"max_depth": 2,
"max_pages": 5,
"include_patterns": ["/docs/."],
"exclude_patterns": ["/old/."]
}
}```


## 📚 API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 Testing

Run tests with pytest:

```bash
pytest
```

## 🛠️ Development

Requirements:
- Python 3.13+
- FastAPI
- Pydantic
- BeautifulSoup4
- pytest

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## 📫 Contact

- Open an issue
- Start a discussion
- Report security issues via our security policy