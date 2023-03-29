# Public Digital Case Scraper

This repository contains the Docker image and configuration for a Python-based web scraping tool using Scrapy to scrape court cases and associated data from courts all over the country. The project is designed to make it easy for employees and contract workers to quickly write web scrapers for Public Digital.

## Table of Contents

- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
- [Development Environment](#development-environment)
  - [Configuring the launch.json File](#configuring-the-launchjson-file)
- [Using the CaseScraper for Scraping, Parsing, and Sending Data](#using-the-casescraper-for-scraping-parsing-and-sending-data)
  - [Useful Utilities](#useful-utilities)
  - [Instance Variables](#on-the-casescraper-instance-you-will-have-access-to-the-following-variables-as-self-or-spider-in-middleware)
  - [start_requests](#start-requests)
  - [Yielding to ItemPipeline and CaseItem object](#Yielding-to-itempipeline-and-caseitem-object)

## Getting Started

Follow these steps to set up your environment and start developing your scraper:

### Prerequisites

To get started, you will need the following credentials set as environment variables:

- `export DATA_EXCHANGE_API_KEY='provided key'`: API key for sending scraped data to Public Digital's API endpoints in the Scrapy pipeline.
- `export PROXY_PASSWORD='provided password'`: Password for Public Digital's Proxy server.
- `export PROXY_USER='provided username'`: Username for the proxy.
- `export DOCKER_TOKEN='provided token'`: Token required for logging into the account allowed to pull Docker images from Public Digital's DockerHub repo.

> Important: Don't forget to substitute the "provided key", "provided password", "provided username", and "provided token" placeholders with the real credentials in the `export` commands. If you haven't received these credentials, reach out to the project administrator to obtain them.

### Setup

1. **Clone the GitHub repo that has Public Digital's sample base scraper and middleware and set path to environment variable:**

    ```Bash
    git clone https://github.com/cbreland/spiders.git && cd spiders && export SPIDER_PATH=$(pwd) && cd ..
    ```

2. **Login to Docker account with the provided token:**

    ```Bash
    echo $DOCKER_TOKEN | docker login --username pbcasedev --password-stdin
    ```

3. **Pull the Docker image and tag the image under a new name `case-scraper`:**

    ```Bash
    docker pull cbreland/case-scraper && \
    docker tag cbreland/case-scraper case-scraper
    ```

5. **Run the Docker image with the provided environment variables and bind/mount the `spiders` directory cloned from GitHub with the internal `spiders` directory:**

    ```Bash
    docker run -it \
    -v $SPIDER_PATH:/app/case_scraper/spiders \
    -e DATA_EXCHANGE_API_KEY=$DATA_EXCHANGE_API_KEY \
    -e PROXY_PASSWORD=$PROXY_PASSWORD \
    -e PROXY_USER=$PROXY_USER \
    case-scraper \
    /bin/bash
    ```

## Development Environment

To set up your development environment, follow these steps:

1. **Attach Visual Studio Code to the running container:**

    When your container is running, using the Docker extension in Visual Studio Code (VSCode), you should see your running container. Right-click on it and select "Attach Visual Studio Code". 

2. **Run and Debug:**

    When VSCode is attached, click the 'Run and Debug' button on the left-hand side. At the top of the toolbar, you can run the default example spider.

3. **Update `launch.json`:**

    By clicking the settings cog, you will get the following `launch.json` file that begins running the script:

```Javascript
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
### Configuring the `launch.json` File

  This file starts the main entrance point for the program. The arguments under `"args"` can be changed based on your directive and instructions from     Public Digital. This example `launch.json` file is for Lorain County in Ohio denoted by the `--county` and `--state` arguments. The `-y` can be passed   in a comma-separated style to include the first year, the starting case number, and the end case number. Use `None` if the end case number is           unknown. The `--update_crawl_status` flag will be removed in the future and should not be changed.

  All of these arguments will be translated and added as instance variables on the `CaseScraper` class in `/app/case_scraper/spiders/county/scraper.py`.   This will be your base 'Spider' used to create your scraper. Do not change the name of this Class.

  In the next section, we will go over how to use this `CaseScraper` to scrape, parse, and send scraped case data to Public Digital's server.

## Using the CaseScraper for Scraping, Parsing, and Sending Data

### Useful Utilities

  The easiest and suggested method for writing your scraper is by modifying the `CaseScraper` class at `/app/case_scraper/spiders/county/scraper.py`. The file and class should keep the same name and only it's contents be modified. In this file you have access to some tools by the imported `pd` object as `from public_digital.spiders import BaseScraper as pd`. 

Here are some tools you have access to by the `pd` object. 


1. **`@pd.return_soup` This decorator converts the response to a BeautifulSoup instance with the original response accessable by `soup.response`**

2. **`pd.write_to_file` A handy function for debugging and development. Just pass (`filename`, `content`) and a file will be created or appended in the directory it was called.**

3. **`pd.info_log` If you need to log information for debugging, you can use this function to do so. Just pass (`your message`).**

4. **`pd.Request` and `pd.FormRequest` This are the base Scrapy request objects.**

5. **`pd.urljoin` This is the base urljoin function.**


### On the `CaseScraper` instance you will have access to the following variables as `self` or `spider` in middleware

1. **Instance Variables**
```Python
self.logger_id
self.master_crawl_id
self.county 
self.crawl_year
self.years
self.update_crawl_stats
self.case_numbers
self.base_url
self.username
self.password
self.crawl_number
self.base_case_numbers
self.case_package_size
self.parsing_location
self.threading
self.info_log
```

### Start Requests
  The normal `start_requests` method is called. You can start your scraping here as usual. 

### Yielding to ItemPipeline and CaseItem object
  > NOTE: You MUST use Public Digital's `pd.CaseItem` object. 
  
  Our objective is to keep the `CaseScraper` and parsing of the `HTML` separate. In order to do this, you can add a list of `soup` objects to the `pd.CaseItem` object under the `soup` field. You will also need the `link` or URL for the case, `case_number`, the case number for the case, and `county` which can be received using `self.county`.
  
  > Note: See `pd.CaseItem` below.




  ```Markdown
  <details>
<summary>filename.py</summary>
'''Python
# Example parse function

from public_digital.spiders import BaseScraper as pd

class CaseScraper(pd.CaseScraperBase):

    ..... # Do Stuff
    
    @pd.return_soup
    def parse_case(self, soup: pd.BeautifulSoup):
        """CASE DETAILS REQUEST"""

        yield pd.CaseItem(
            case_number=soup.response.meta['case_number'],
            soup=soup,
            link=soup.response.url,
            county=self.county
        )


# CaseItem that will be used (required)

import scrapy

from public_digital.utils.logging import info_log

class CaseItem(scrapy.Item):

    soup = scrapy.Field()
    case_number = scrapy.Field()
    link = scrapy.Field()
    county = scrapy.Field()

    def __repr__(self):
        """only print out 'case_number' after exiting the Pipeline"""

        log_string = f"""
        ***************
        ***************
        *************** CASE SCRAPED: {self['case_number']}
        ***************
        ***************
        ***************
        """
        info_log(log_string)
        return repr(log_string)
        '''
        <details>
```

