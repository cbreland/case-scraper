# Public Digital Case Scraper

Welcome to the Public Digital Case Scraper repository! This repository serves as a hub for our Python-based web scraping tool, which utilizes the Scrapy framework. Our main goal is to efficiently scrape court cases and related data from courts across the nation.

This repository provides an example file structure specifically designed to bind/mount to a centralized Docker Image. This setup ensures a consistent environment, making it easier for employees and contract workers to develop and maintain web scrapers for Public Digital.

By leveraging the power and flexibility of our scraping tool, we aim to streamline the extraction of valuable legal information so attorneys can better inform the public and subsequently help those most in need.

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
  - [Yielding to ItemPipeline and CaseItem object](#yielding-to-itempipeline-and-caseitem-object)
  - [Parsing HTML & Data Structures](#parsing-html-&-data-structures)
  - [Additional Utilities](#additional-utilities)
    - Middlewares
    - Extensions
    - Additional Python Packages 
  - [Challenges](#challenges)  

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

4. **Run the Docker image with the provided environment variables and bind/mount the `spiders` directory cloned from GitHub with the internal `spiders` directory:**

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

```javascript

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

  This file starts the main entrance point for the program. The arguments under `"args"` can be changed based on your directive and instructions from Public Digital. This example `launch.json` file is for Lorain County in Ohio, denoted by the `--county` and `--state` arguments. The `-y` can be passed in a comma-separated style to include the first year, the starting case number, and the end case number. Use `None` if the end case number is unknown. The `--update_crawl_status` flag will be removed in the future and should not be changed.

  All of these arguments will be translated and added as instance variables on the `CaseScraper` class in `/app/case_scraper/spiders/county/scraper.py`. This will be your base 'Spider' used to create your scraper. Do not change the name of this Class.

  In the next section, we will go over how to use this `CaseScraper` to scrape, parse, and send scraped case data to Public Digital's server.

## Using the CaseScraper for Scraping, Parsing, and Sending Data

### Useful Utilities

  The easiest and suggested method for writing your scraper is by modifying the `CaseScraper` class at `/app/case_scraper/spiders/county/scraper.py`. The file and class should keep the same name and only its contents be modified. In this file, you have access to some tools by the imported `pd` object as `from public_digital.spiders import BaseScraper as pd`. 

Here are some tools you have access to by the `pd` object. 

1. **`@pd.return_soup` This decorator converts the response to a BeautifulSoup instance with the original response accessible by `soup.response`**

2. **`pd.write_to_file()` A handy function for debugging and development. Just pass (`filename`, `content`) and a file will be created or appended in the directory it was called.**

3. **`pd.info_log()` If you need to log information for debugging, you can use this function to do so. Just pass (`your message`).**

4. **`pd.Request` and `pd.FormRequest` These are the base Scrapy request objects.**

5. **`pd.urljoin()` This is the base urljoin function.**


### On the `CaseScraper` instance, you will have access to the following variables as `self` or `spider` in middleware

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
  
  Our objective is to keep the `CaseScraper` and parsing of the `HTML` separate. In order to do this, you can add a list of `soup` objects to the `pd.CaseItem` object under the `soup` field. You will also need the `link` or URL for the case, `case_number`, the case number for the case, and `county`, which can be received using `self.county`.
  
  > Note: See `pd.CaseItem` below.

```Python

# Example parse function @ (this repo) /app/case_scraper/spiders/county/scraper.py

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

```

```Python
# CaseItem that will be used @ (docker image) /app/case_scraper/public_digital/items/base_case_items.py

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

```
### Parsing HTML & Data Structures

   When you are ready to start parsing the HTML that was passed in the `CaseItem` object, you can use the `parse_case_data` function below. This will be in the `parse.py`. This file and function name can't be changed. Arguments that are passed are `(CaseItem, CaseScraper)` so you have full access to the instance variables. Please note the following..
   1. **Data Structure:** As you will notice below. This project offers `@dataclass` objects to help serialize the data going to Public Digital's servers in order for it to be successfully accepted by the endpoints.
   2. **Submitting Scraped Data:** After you have successfully parsed and organized the data into the `@dataclass` objects, a final `@dataclass` object will package everything. This object is called `PackedCase`. This should be returned by the `parse_case_data` function as in the example below. This is all you will have to do in order to submit the scraped case to Public Digital's endpoint.

> Example: This is an example `parse_case_data` function. See `/app/case_scraper/spiders/parse_utils` for example functions and classes used for parsing.
   ```Python
    # --------------------------------------------------------------------
    # Example parse.py file @ /app/case_scraper/spiders/county/parse.py
    #├── app
    #    ├── case_scraper
    #    │   └── spiders
    #    │       └── county
    #    │           └── parse.py  
    # --------------------------------------------------------------------
   from ..parse_utils.parse_functions import (
       parse_docket_entries, parse_case_related_data,
       parse_plaintiffs_and_defendants, parse_docket_fields
   )
   
   from public_digital.dataclasses.base_dataclasses import (
       CaseDocket, Case, CaseParty, PackedCase
   )
   
   from public_digital.items.base_case_items import CaseItem
   from ..county.scraper import CaseScraper
   
   
   def parse_case_data(item: CaseItem, spider: CaseScraper) -> PackedCase:
       """ This function is for parsing data from the BeautifulSoup Object(s) and creating the 
       required dataclass objects. See steps 1 - 8 below.
       """
   
       # ITEM DATA AVAILABLE
       soup = item['soup']
       case_number = item['case_number']
       link = item['link']
       county = item['county']
       
       """ -------------------------------------------------------------------------------------
       
       #
       # (STEP 1) THE FOLLOWING STEPS ARE BASED ON GETTING CASE AND PARTY DATA FROM DOCKET ENTRIES
       #
       # Create a dictionary of initial case data as key, value pairs
       # In the following data structure
       
       case_dict
           file_date: datestring format '01/01/1900 
           case_status_date: datestring 'start with filed_date'
           case_title: str
           case_number: str
           county: str
           judge: str
           case_type: str
       """
       case_dict = parse_case_related_data(soup, county)
       
       """ -------------------------------------------------------------------------------------
   
       #
       # (STEP 2)
       #
       # Create a list of dictionaries containing the docket entry data as key, value pairs
       # In the following data structure
       
       docket_dicts
           entry: str
           date_time: datestring format '01/01/1900 
           unique_id: int
       """
       docket_dicts = parse_docket_entries(soup)
   
       """ -------------------------------------------------------------------------------------
   
       #
       # (STEP 3)
       #
       # Create a list of dictionaries with defendant data as key, value pairs
       # In the following data structure
      
       defendant_dicts
           defendant: str (defendant name)
           total_address: str (combined address)
           street: str
           city: str
           state: str
           zip_code: str
           attorney: str (optional if not available)
       plaintiffs
           'John Doe 1, John Doe 2, and Jane Doe'
       """
       defendant_dicts, plaintiffs = parse_plaintiffs_and_defendants(soup, link)
   
       """ -------------------------------------------------------------------------------------
   
       #
       # (STEP 4)
       #
       # Create a dictionary with defendant and plaintiff data as key, value pairs
       # from parsing the docket entries
       #
       # Return a tuple with each dictionary included
       # In the following data structure
      
       case_docket_data: dict
           hearing_date: datestring format '01/01/1900 
           case_status: str
           amount: str
           case_dismiss_date: datestring format '01/01/1900 
       case_party_docket_data: dict
           link: str = None
           serve_status: str
           serve_status_date: datestring format '01/01/1900 
           garnishment_status: str
           garnishment_answer: str
           is_agreement: str
           employer_info: str
           last_pay_date: datestring format '01/01/1900 
           bankruptcy_filed_date: datestring format '01/01/1900 
           is_garnishment: bool
           garnishment_date: datestring format '01/01/1900 
           answer_date: datestring format '01/01/1900 
           agreement_date: datestring format '01/01/1900 
           is_bankruptcy_filed: bool
       """
       case_docket_data, case_party_docket_data = parse_docket_fields(
           docket_dicts, case_dict, plaintiffs, case_number
       )
   
       """ -------------------------------------------------------------------------------------
   
       #
       # STEPS (5 - 8) PACKAGING DATA INTO DATACLASSES
       #
       """
       
       """
       #
       # (STEP 5)
       #
       # Create a list of CaseDocket objects
       """
       dockets = [
           CaseDocket(**docket_entry)
           for docket_entry in docket_dicts
       ]
   
       """ -------------------------------------------------------------------------------------
   
       #
       # (STEP 6)
       #
       # Create a Case object
       """
       case = Case(**case_docket_data)
       
       """ -------------------------------------------------------------------------------------
   
       #
       # (STEP 7)
       #
       # Create a list of CaseParty objects with dictionaries that were created
       # Also add the list of CaseDockets as a dictionary.
       """
       case_parties = [
           CaseParty(
               **case_party_docket_data,
               **defendant_dict,
               docket_entries=dockets
           )
           for defendant_dict in defendant_dicts
       ]
   
       """ -------------------------------------------------------------------------------------
   
       #
       # (STEP 8)
       #
       # Create BaseCasePacked object with the list of Case and list of CaseParty objects
       """
       return PackedCase(case, case_parties)

   ```
   

### Additional Utilities

1. **Middlewares:**
    If you need to add additional middlewares they can be automatically added to the scraper.
    ```
    
    File Structure ...
    ├── app
        ├── case_scraper
        │   └── spiders
        │       └── middlewares
        │           └── MyMiddleware__500.py  
        
    ```
    Notice the file name `MyMiddleware__500.py`. This naming convention will need to be used especially the `__500.py`. Your class name should be the same as your file name before the `__` such as `MyMiddleware`. This will conver to this setting. the `__500` will indicate the sequence.
    ```Python
    
    SETTINGS = {
        "DOWNLOADER_MIDDLEWARES": {
            'app.case_scraper.spiders.middlewares.MyMiddleware__500.MyMiddleware': 500
        }
    }
    
    ```
    
    See example below.
    ```Python
    
    # Example Middleware @ (this repo) /app/case_scraper/spiders/middlewares/MyMiddleware__500.py
    
    from scrapy import signals

    # useful for handling different item types with a single interface
    from itemadapter import is_item, ItemAdapter


    class MyMiddleware:
        # Not all methods need to be defined. If a method is not defined,
        # scrapy acts as if the spider middleware does not modify the
        # passed objects.

        @classmethod
        def from_crawler(cls, crawler):
            # This method is used by Scrapy to create your spiders.
            s = cls()
            crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
          return s
    
    ```
2. **Extensions:**
    If you need to add additional extensions they can be automatically added to the scraper.
    ```
    
    File Structure ...
    ├── app
        ├── case_scraper
        │   └── spiders
        │       └── extensions
        │           └── MyExtension__500.py  
        
    ```
    Notice the file name `MyExtension__500.py`. This naming convention will need to be used especially the `__500.py`. Your class name should be the same as your file name before the `__` such as `MyExtension`. This will conver to this setting. the `__500` will indicate the sequence.
    ```Python
    
    SETTINGS = {
        "EXTENSIONS": {
            'app.case_scraper.spiders.middlewares.MyExtension__500.MyExtension': 500
        }
    }
    
    ```
    
    See example below.
    ```Python
    
    # Example Middleware @ (this repo) /app/case_scraper/spiders/extensions/MyExtension__500.py
    
    class MyExtension:
      pass
    
    ```
    
 3. **Python Packages:**
    If you need additional python packages, they can be installed by adding them to the `requirements.txt` file. When the docker image is run, the packages will automatically be installed. Having them in the `requirements.txt` file will help Public Digital know they are required for your code to execute properly. 
    > `requirements.txt location`
    ```Bash
        File Structure ...
        
        # /app/case_scraper/spiders/requirements.txt
        
        ├── app
            ├── case_scraper
            │   └── spiders
            │       └── requirements.txt

    ```
    
    
## Challenges
    
1. **Dynamic content:** Websites that load content dynamically using JavaScript can be challenging to scrape, as the data may not be present in the initial HTML source. Scraping such sites often requires using tools like Selenium or Scrapy with Splash to render and interact with the dynamic content.

    ```If you need `Scrapy Splash` we can add this to the docker image.```

2. **Inconsistent HTML structure:** Websites with inconsistent or poorly structured HTML can make it difficult to reliably extract structured data. This may require additional logic or more complex parsing techniques to accurately locate and extract the desired information.

3. **Rate limiting and IP blocking:** Web servers may implement rate limiting or IP blocking to prevent automated scraping. This requires implementing techniques like using proxies, rotating user agents, and implementing delays to avoid detection and continue scraping.

    ```Our Docker image already comes with a rotating proxy. This can be changed any time by calling `self.change_proxy()'.```

4. **Pagination and infinite scrolling:** Websites with paginated content or infinite scrolling can pose challenges in terms of locating and following the correct links or scrolling actions to load additional data, while also avoiding duplicate content.

5. **Captchas and anti-bot measures:** Some websites employ Captchas or other anti-bot measures to prevent automated scraping. Bypassing these measures may require using third-party services, OCR tools, or other techniques, which can increase the complexity of the scraping process.

6. **Data extraction from non-text sources:** In cases where structured data is embedded within non-text sources like images, PDFs, or other media formats, additional tools or techniques such as OCR or PDF parsing libraries may be required to extract the information.

