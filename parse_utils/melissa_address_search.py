import os
import logging
import requests
from collections import OrderedDict
from bs4 import BeautifulSoup as bs

MELISSA_USERNAME = os.environ.get('MELISSA_USERNAME')
MELISSA_PASSWORD = os.environ.get('MELISSA_PASSWORD')


class MissingCredentialsError(Exception):
    pass


class MelissaAPI:
    def __init__(self):
        self.session = requests.Session()
        self.login()

        self.matching_zips = []
        self.zip_code_keys, self.county_keys = self.get_zip_codes()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.session.close()

        if exc_type is not None:
            logging.error(
                f"An exception of type {exc_type} occurred with value: {exc_value}")

        return True

    @staticmethod
    def get_soup(response):
        if response.status_code == 200:
            return bs(response.text, 'html.parser')

    def get_zip_codes(self):
        with open('zips.txt', 'r') as file:
            file = file.read()

        zips = {}
        zip_dict = OrderedDict()

        for zip in file.split("\n")[:-1]:
            zip = zip.split("|")
            county_name = zip[1].replace(
                " County", ""
            )
            county_name = county_name.lower().replace(
                f" {zip[2].lower()}", ""
            ).title()
            county_name = county_name+f" {zip[2].title()}"
            zip_dict.setdefault(
                county_name,
                []
            ).append(zip[0])
            zips[zip[0]] = {'county': county_name, 'state': zip[2].title()}

        return zips, zip_dict

    def get_data(self, url, params={}):
        response = self.session.get(url, params=params)
        # Handle response
        return self.get_soup(response)

    def post_data(self, url, data):
        response = self.session.post(url, data=data)
        # Handle response
        return self.get_soup(response)

    def login(self):
        login_page = self.get_data(
            'https://apps.melissa.com/user/signin.aspx?src=/user/user_account.aspx')
        viewstate = login_page.find(
            'input', {'name': '__VIEWSTATE'}
        ).get('value')
        viewstategenerator = login_page.find(
            'input', {'name': '__VIEWSTATEGENERATOR'}
        ).get('value')
        formdata = {
            '__VIEWSTATE': viewstate,
            '__VIEWSTATEGENERATOR': viewstategenerator,
            'ctl00$ContentPlaceHolder1$Signin1$txtEmail': MELISSA_USERNAME,
            'ctl00$ContentPlaceHolder1$Signin1$txtPassword': MELISSA_PASSWORD,
            'ctl00$ContentPlaceHolder1$Signin1$btnLogin': 'Sign In'
        }

        return self.post_data(
            'https://apps.melissa.com/user/signin.aspx', formdata
        )

    def get_personator_search(self):

        return self.get_data(
            'https://lookups.melissa.com/home/personatorsearch/'
        )

    def search_personator(self, name, state):

        params = {
            "name": name,
            "state": state,
            "city": "",
            "postalCode": "",
            "melissaAddressKey": "",
            "phoneNumber": "",
            "emailAddress": "",
            "freeForm": ""
        }
        self.query = params

        self.search_soup = self.get_data(
            "https://lookups.melissa.com/home/personatorsearch/",
            params=params
        )
        return self.search_soup

    def extract_results(self, results):
        addresses = []
        if not results.find_all('table'):
            self.search_results = []
            return None
        for res in results.find_all('table')[0].find_all('tr')[1:]:
            addresses.append({
                'name': res.find_all('td')[0].string,
                'street': res.find_all('td')[1].string,
                'county': res.find_all('td')[2].string,
                'state': res.find_all('td')[3].string,
                'zip_code': res.find_all('td')[4].string,
            })

        self.search_results = addresses
        return addresses

    def verify_against_zips(self, results, county, state, zip_codes=None):

        county = county.lower().replace(f' {state.lower()}', '').title()
        zip_key = f'{county.title()} {state.title()}'

        zip_codes = zip_codes or self.county_keys[zip_key]

        matching_zips = []

        for search_data in results:

            if search_data['zip_code'] in zip_codes:
                matching_zips.append(search_data)
        self.matching_zips = matching_zips
        return matching_zips


if all((MELISSA_USERNAME, MELISSA_PASSWORD)):
    melissa_api = MelissaAPI()


def search_personator(name: str, state: str, county: str, zip_codes: list = None):

    if all((MELISSA_USERNAME, MELISSA_PASSWORD)):

        if zip_codes:
            zip_codes = [str(z) for z in zip_codes]

        melissa_api.matching_zips = []
        melissa_api.search_results = []
        melissa_api.query = {}
        melissa_api.search_soup = None

        melissa_api.get_personator_search()
        results = melissa_api.search_personator(name, state)
        extracted_results = melissa_api.extract_results(results)
        matching_addresses = []
        if extracted_results:
            matching_addresses = melissa_api.verify_against_zips(
                extracted_results, county, state, zip_codes)

        matching_addresses = (
            matching_addresses[0]
            if matching_addresses and len(matching_addresses) < 2
            else ''
        )

        return matching_addresses

    raise MissingCredentialsError(
        "Both username and password must be supplied in your .env file")
