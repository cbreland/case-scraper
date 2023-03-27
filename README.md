# Public Digital Case Scraper

This repository contains the Docker image and configuration for a Python-based web scraping tool using Scrapy to scrape court cases and associated data from courts all over the country. The project is designed to make it easy for contract workers to quickly write web scrapers for Public Digital.

## Getting Started

Follow these steps to set up your environment and start developing your scraper:

### Prerequisites

To get started, you will need the following credentials as environment variables:

- `DATA_EXCHANGE_API_KEY`: API key for sending scraped data to Public Digital's API endpoints in the Scrapy pipeline.
- `PROXY_PASSWORD`: Password for Public Digital's Proxy server.
- `PROXY_USER`: Username for the proxy.
- `DOCKER_TOKEN`: Token required for logging into the account allowed to pull Docker images from Public Digital's DockerHub repo.

### Setup

1. **Login to Docker account with the provided token:**

    ```
    echo "<DOCKER_TOKEN>" | docker login --username pbcasedev --password-stdin
    ```

2. **Pull the Docker image and tag the image under a new name `case-scraper`:**

    ```
    docker pull cbreland/case-scraper && \
    docker tag cbreland/case-scraper case-scraper
    ```

3. **Clone the GitHub repo that has Public Digital's sample base scraper and middleware:**

    ```
    git clone https://github.com/cbreland/spiders.git
    ```

4. **Run the Docker image with the provided environment variables and bind/mount the `spiders` directory cloned from GitHub with the internal `spiders` directory:**

    ```
    docker run -it \
    -v /path/to/spiders:/app/case_scraper/spiders \
    -e DATA_EXCHANGE_API_KEY='<DATA_EXCHANGE_API_KEY>' \
    -e PROXY_PASSWORD='<PROXY_PASSWORD>' \
    -e PROXY_USER='<PROXY_USER>' \
    case-scraper \
    /bin/bash
    ```

## File Structure

### Docker Image

── Dockerfile
├── case_scraper
│   ├── app-main.py
│   ├── app.py
│   ├── public_digital
│   │   ├── __init__.py
│   │   ├── data_exchange
│   │   │   └── public_digital_interface.py
│   │   ├── dataclasses
│   │   │   └── base_dataclasses.py
│   │   ├── extensions
│   │   │   └── base_extensions.py
│   │   ├── items
│   │   │   └── base_case_items.py
│   │   ├── middlewares
│   │   │   ├── base_middlewares.py
│   │   │   └── proxy.py
│   │   ├── pipelines
│   │   │   └── base_pipelines.py
│   │   ├── protocols
│   │   │   └── base_protocols.py
│   │   ├── spiders
│   │   │   ├── BaseScraper.py
│   │   │   ├── __init__.py
│   │   └── utils
│   │       ├── decorators.py
│   │       ├── funcs.py
│   │       ├── logging.py
│   │       ├── proxies.py
│   │       └── save_case.py
│   ├── readme.txt
│   ├── scrapy.cfg
│   ├── settings.py
│   └── spiders
├── entrypoint.sh
└── requirements.txt

### GitHub Repo


└── spiders
    ├── __init__.py
    ├── county
    │   ├── datastructures.py
    │   ├── parse.py
    │   └── scraper.py
    ├── extensions
    │   ├── MyExtension_300.py
    └── requirements.txt
