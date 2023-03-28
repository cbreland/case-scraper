# Public Digital Case Scraper

This repository contains the Docker image and configuration for a Python-based web scraping tool using Scrapy to scrape court cases and associated data from courts all over the country. The project is designed to make it easy for employees and contract workers to quickly write web scrapers for Public Digital.

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
```
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
```
### GitHub Repo

```
└── spiders
    ├── __init__.py
    ├── county
    │   ├── datastructures.py
    │   ├── parse.py
    │   └── scraper.py
    ├── extensions
    │   ├── MyExtension_300.py
    └── requirements.txt
    
```


## Development Environment

To set up your development environment, follow these steps:

1. **Attach Visual Studio Code to the running container:**

    When your container is running, using the Docker extension in Visual Studio Code (VSCode), you should see your running container. Right-click on it and select "Attach Visual Studio Code". 

2. **Run and Debug:**

    When VSCode is attached, click the 'Run and Debug' button on the left-hand side. At the top of the toolbar, you can run the default example spider.

3. **Update `launch.json`:**

    By clicking the settings cog, you will get the following `launch.json` file that begins running the script:

```
{
    "version": "0.1.0",
    "configurations": [
        {
            "name": "Python: Launch Scrapy Spider",
            "type": "python",
            "request": "launch",
            "program": "case_scraper/app-main.py",
            "args": [
                "--county","lorain",
                "--state", "oh",
                "-y", "2023,478452,None",
                "-y", "2022,461472,478451",
                "-y", "2021,442891,461471",
                "-y", "2020,420000,442890",
                "--update_crawl_status", "True",
            ],
            "console": "integratedTerminal"
        }
    ]
}
```

    This file starts the main entrance point for the program. The arguments can be changed based on your directive and instructions from Public Digital. This example `launch.json` file is for Lorain County in Ohio denoted by the `--county` and `--state` arguments. The `-y` can be passed in a comma-separated style to include the first year, the starting case number, and the end case number. Use `None` if the end case number is unknown. The `--update_crawl_status` flag will be removed in the future and should not be changed.

    All of these arguments will be translated and added as instance variables on the `CaseScraper` class in `/app/case_scraper/spiders/county/scraper.py`. This will be your base 'Spider' used to create your scraper. Do not change the name of this Class.

    In the next section, we will go over how to use this `CaseScraper` to scrape, parse, and send scraped case data to Public Digital's server.
