
import traceback
import re
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from copy import copy



from scrapy.exceptions import IgnoreRequest

from public_digital.dataclasses.base_dataclasses import (
    PackedCase, CaseDocket,
    CaseData, Case, CaseParty
)

from public_digital.items.base_case_items import CaseItem
from public_digital.utils.funcs import create_datetime_object, write_to_file

from .datastructures import (
    GARNISHMENT_PATTERN, EMPLOYER_PATTERN, SERVE_STATUS_PATTERN,
    SERVE_STATUS_DATE_PATTERN, JUDGMENT_PATTERNS,  DISMISSED_PATTERN,
    HEARING_DATE_PATTERN, BANKRUPTCY_PATTERN, COURT_CASE_TYPES_MAP
)


def _validate_type(docket_type: str) -> bool:
    """
    Validate if the given docket type string contains only alphanumeric characters, hyphens, and underscores.
    :param docket_type: The docket type string to be validated.
    :return: True if the docket type string is valid, False otherwise.
    """
    return bool(re.match(r'^[A-Za-z0-9_-]+$', docket_type))

def _validate_date(date_str: str) -> bool:
    """
    Validate if the given date string is in the format 'MM/DD/YYYY'.
    :param date_str: The date string to be validated.
    :return: True if the date string is valid, False otherwise.
    """
    try:
        datetime.strptime(date_str, '%m/%d/%Y')
        return True
    except ValueError:
        return False
    
def _format_description(description: str) -> str:
    """
    Format the given description string by removing extra whitespace and leading/trailing spaces.
    :param description: The description string to be formatted.
    :return: The formatted description string.
    """
    formatted_description = re.sub(r'\s+', ' ', description).strip()
    return formatted_description

def parse_docket_entries(soup) -> List[Dict[str, Optional[str]]]:

    """
    Extracts docket information from an HTML table with the id "dgrdResults".
    Returns a list of dictionaries containing the docket date, type, and description.
    """
    # Find the table with id "dgrdResults"
    docket_table = soup.find('table', {'id': 'dgrdResults'})
    # Extract the rows in the table
    rows = docket_table.find_all('tr')
    docket_entries = []
    # Iterate through the rows, starting from the second row (skipping the header)
    for count, row in enumerate(rows[1:-1]):
        columns = row.find_all('td')
        # Get the description text, if it exists
        description = columns[2].get_text(
            strip=True) if len(columns) > 2 else None
        # Only proceed if there is a description
        if description:
            # Extract date and docket type from the columns
            date = columns[0].get_text(strip=True)
            docket_type = columns[1].get_text(
                strip=True) if len(columns) > 1 else None
            # Validate the date format
            if _validate_date(date):
                # Validate the docket type, set to an empty string if invalid
                docket_type = docket_type if _validate_type(
                    docket_type) else ""
                # Format the description text
                formatted_description = _format_description(
                    description)
                # Add the extracted and formatted data to the list of docket entries
                docket_entries.append(
                    {'date_time': date, 'type': docket_type, 'entry': formatted_description, 'unique_id': count})
    return docket_entries


def parse_case_related_data(soup, county):
    case_number = soup.select('#lblCaseNumber')[0].text
    if "CV" in case_number:
        case_type = ''
        try:
            case_type = COURT_CASE_TYPES_MAP[soup.select('#lblDescription')[0].get_text(strip=True).lower()]
        except:
            write_to_file('case_types.txt', soup.select('#lblDescription')[0].get_text(strip=True)+'\n')
        return {
            'file_date': soup.select('#lblDateFiled')[0].get_text(strip=True),
            'case_status_date': soup.select('#lblDateFiled')[0].get_text(strip=True),
            'case_title': soup.select('#lblCaption')[0].get_text(strip=True),
            'plaintiff': '',
            'case_number': case_number,
            'county': county,
            'judge': soup.select('#lblJudgeName')[0].get_text(strip=True),
            'case_type': case_type,
        }
    return None
    
def parse_plaintiffs_and_defendants(soup, link: str) -> Tuple[dict, str]:
    """
    Extract plaintiffs and defendants from the provided HTML using the soup object.
    :return: Tuple containing a list of CustomCaseParty objects representing defendants and a string containing plaintiffs' names
    """
    def names_list_to_string(names: List[str]) -> str:
        """
        Convert a list of names into a formatted string.
        :param names: List of strings representing names
        :return: Formatted string containing names separated by commas and 'and' before the last name
        """
        if len(names) == 0:
            return ""
        elif len(names) == 1:
            return names[0]
        elif len(names) == 2:
            return f"{names[0]}, and {names[1]}"
        else:
            return f"{', '.join(names[:-1])}, and {names[-1]}"
    def format_name(name):
        # Check if the name contains a comma
        if "," in name:
            # Split the name using the comma and strip extra spaces
            split_name = [part.strip() for part in name.split(",")]
            # Check if the name has two parts (e.g. 'Smith, Tom')
            if len(split_name) == 2:
                # Swap the order and join the parts with a space
                formatted_name = f"{split_name[1]} {split_name[0]}"
            else:
                # If the name doesn't have two parts, use the original name
                formatted_name = name
        else:
            # If the name doesn't contain a comma, use the original name
            formatted_name = name
        return formatted_name
    docket_table = soup.find('table', {'id': 'dgrdParties'})
    rows = docket_table.find_all('tr')[1:]
    defendants = []
    plaintiffs = []
    for row in rows:
        columns = row.find_all('td')
        party_type = columns[2].get_text(strip=True)
        # Format name
        name = format_name(columns[0].get_text(strip=True))
        if party_type == "P":
            plaintiffs.append(name)
        if party_type == "D":
            party = {}
            
            # Create address parts list
            address_parts = [t.strip()
                             for t in columns[3].stripped_strings]
            # If address exists
            if address_parts[0] != ',':
          
                parts = address_parts[-1].split(",")
                street = ', '.join(address_parts[:-1])
                city = parts[0].strip()
                state = " ".join(parts[-1].split()[:-1])
                zip_code = parts[-1].split()[-1].strip()
                total_address = columns[3].get_text(strip=True)

                party['link'] = link
                party['defendant'] = name
                party['total_address'] = total_address
                party['street'] = street
                party['city'] = city
                party['state'] = state
                party['zip_code'] = zip_code
            defendants.append(party)
    # Combine plaintiffs
    return defendants, names_list_to_string(plaintiffs)

class DocketProcessor:
    def __init__(self, case_dict, plaintiffs):
        # Initialize the DocketProcessor with CaseData containing the docket entries, Case, and CaseParty instances.
        self.case_data = case_dict
        self.case_data['plaintiff'] = plaintiffs
        self.case_party_data = {}

    def bankruptcy_test(self, entry: Dict[str, str]) -> None:
        """
        Check if the docket entry contains the word "bankruptcy" and update the corresponding fields in docket_data.

        :param entry: A dictionary representing a single docket entry.
        """

        description = entry['entry']
        date = entry['date_time']

        # Check if the description contains the word "bankruptcy"
        if BANKRUPTCY_PATTERN.search(description):
            self.case_party_data['bankruptcy_filed_date'] = date
            self.case_party_data['is_bankruptcy_filed'] = True

    def process_hearing_date(self, entry: Dict[str, str]) -> None:
        """
        Parse the hearing date from a docket entry and update the corresponding field in docket_data.

        :param entry: A dictionary representing a single docket entry.
        """

        def parse_and_format_date(date_str: str) -> Optional[str]:
            for fmt in ('%B %d, %Y', '%m/%d/%Y', '%m/%d/%y'):
                try:
                    return datetime.strptime(date_str, fmt).strftime('%m/%d/%Y')
                except ValueError:
                    continue
            return None

        match = HEARING_DATE_PATTERN.search(entry['entry'])

        if match:
            date_str = match.group(1)
            date = parse_and_format_date(date_str)
            if date:
                self.case_data['hearing_date'] = date

    def parse_served_status(self, entry: Dict[str, str]) -> None:
        """
        Parse the served status and date from a docket entry and update the corresponding fields in docket_data.

        :param entry: A dictionary representing a single docket entry.
        """

        description = entry['entry']

        # Check if the entry has a "served" status
        if SERVE_STATUS_PATTERN.search(description):
            self.case_party_data['serve_status'] = "Served"
            self.case_data['case_status_date'] = entry['date_time']
            self.case_party_data['serve_status_date'] = entry['date_time']

    def judgment_test(self, entry: Dict[str, str]) -> None:
        """
        Parse the judgment status and largest amount from a docket entry and update the corresponding fields in docket_data.

        :param entry: A dictionary representing a single docket entry.
        """

        def find_largest_amount(description: str) -> Optional[float]:
            """
            Find the largest dollar amount in a given text.

            :param description: A string containing the text to search for dollar amounts.
            :return: The largest dollar amount found in the text or None if no amounts were found.
            """
            # Extract all dollar amounts with optional decimal point
            amounts = re.findall(r'\$\d+(?:\.\d{1,2})?', description)
            # Remove the dollar sign and convert extracted numbers to float
            float_amounts = [float(amount[1:]) for amount in amounts]
            # Return the largest amount found, or None if no amounts were found
            return max(float_amounts, default=None)
        
        description = entry['entry']

        # Check if the entry has a judgment status
        if JUDGMENT_PATTERNS.search(description):
            self.case_data['case_status'] = 'DISPOSED'
            self.case_data['case_status_date'] = entry['date_time']
            # Find the largest amount in the description
            largest_amount = find_largest_amount(description)
            if largest_amount is not None:
                self.case_data['amount'] = largest_amount

    def parse_garn_status(self, entry: Dict[str, str]) -> None:
        """
        This function updates the garnishment status, garnishment date, and employer information
        in the case party docket data based on the provided docket entry.

        :param entry: A dictionary representing a single docket entry.
        """

        # Extract date and description from the entry
        date = entry['date_time']
        description = entry['entry']

        # Check if the entry contains a garnishment
        is_garnishment = bool(GARNISHMENT_PATTERN.search(description))

        if is_garnishment:
            # update case status date
            self.case_data['case_status_date'] = entry['date_time']
            # Update garnishment status, flag, and date in the case party docket data
            self.case_party_data['garnishment_status'] = 'Issued'
            self.case_party_data['is_garnishment'] = True
            self.case_party_data['garnishment_date'] = date

            # Search for the employer information in the entry description
            employer_match = EMPLOYER_PATTERN.search(description)

            if employer_match:
                # Update employer information in the case party docket data
                self.case_party_data['employer_info'] = employer_match.group(
                    1)
                
    def test_dismissed(self, entry: Dict[str, str]) -> None:
        """
        Parse the dismissal status from a docket entry and update the corresponding fields in docket_data.

        :param entry: A dictionary representing a single docket entry.
        """

        description = entry['entry']

        # Check if the entry has a dismissal status
        if DISMISSED_PATTERN.search(description):
            self.case_data['case_status_date'] = entry['date_time']
            self.case_data['case_dismiss_date'] = entry['date_time']
            self.case_data['case_status'] = 'DISMISSED'

    def process_entries(self, dockets: dict) -> Tuple[dict, dict]:
        """
        Process all docket entries by calling the `process_entry` method for each entry.
        Create a CaseDocket object and append to the CaseData.docket_entries
        """
        for i, entry in enumerate(dockets):

            self.process_entry(entry)

        return self.case_data, self.case_party_data

    def process_entry(self, entry: Dict[str, Any]) -> None:
        """
        Process a single docket entry by calling various parsing methods to update the case and case party data.

        :param entry: A dictionary representing a docket entry.
        """
        self.bankruptcy_test(entry)
        self.process_hearing_date(entry)
        self.parse_served_status(entry)
        self.judgment_test(entry)
        self.parse_garn_status(entry)
        self.test_dismissed(entry)

def parse_docket_fields(dockets: List[dict], case_dict: dict, plaintiffs: str) -> Tuple[dict, dict]:

    processor = DocketProcessor(case_dict, plaintiffs)
    return processor.process_entries(dockets)
