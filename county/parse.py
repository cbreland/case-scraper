
import traceback
import re
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from copy import copy

from scrapy.exceptions import IgnoreRequest

from public_digital.dataclasses.base_dataclasses import (
    BaseCasePacked, CaseDocket,
    CaseData, Case,
)

from public_digital.items.base_case_items import CaseItem
from public_digital.utils.funcs import create_datetime_object, write_to_file

from .datastructures import (
    GARNISHMENT_PATTERN, EMPLOYER_PATTERN, SERVE_STATUS_PATTERN,
    SERVE_STATUS_DATE_PATTERN, JUDGMENT_PATTERNS,  DISMISSED_PATTERN,
    HEARING_DATE_PATTERN, BANKRUPTCY_PATTERN, COURT_CASE_TYPES_MAP,
    CustomCaseParty
)


def instantiate_case(data: dict) -> Case:
    """Create Case Object (dataclass)
    """
    return Case(**data)
 

def instantiate_docket(data: dict) -> CaseDocket:
    """Create CaseDocket Object (dataclass)
    """
    return CaseDocket(
        entry=data['entry'],
        date_time=data['date_time'],
        unique_id=data['unique_id']
    )


def instantiate_case_data(docket_entries: List[Dict[str, str]], case: Case) -> CaseData:
    """
    Instantiate and return a CaseData object containing Case, CustomCaseParty, and docket_entries.

    :param docket_entries: A list of dictionaries containing docket entry information.
    :return: An instance of the CaseData dataclass containing the instantiated Case, CustomCaseParty, and docket_entries.
    """
    return CaseData(
        case=case,
        case_party=CustomCaseParty(),
        docket_entries=docket_entries
    )


class DocketProcessor:
    def __init__(self, docket_data: CaseData) -> CaseData:
        # Initialize the DocketProcessor with CaseData containing the docket entries, Case, and CaseParty instances.
        self.docket_data = docket_data
        self.process_entries()

    @property
    def results(self):
        return self.docket_data, self.docket_data.docket_entries

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
            self.docket_data.case.case_status_date = entry['date_time']
            # Update garnishment status, flag, and date in the case party docket data
            self.docket_data.case_party.garnishment_status = 'issued'
            self.docket_data.case_party.is_garnishment = True
            self.docket_data.case_party.garnishment_date = date

            # Search for the employer information in the entry description
            employer_match = EMPLOYER_PATTERN.search(description)

            if employer_match:
                # Update employer information in the case party docket data
                self.docket_data.case_party.employer_info = employer_match.group(
                    1)

    def parse_served_status(self, entry: Dict[str, str]) -> None:
        """
        Parse the served status and date from a docket entry and update the corresponding fields in docket_data.

        :param entry: A dictionary representing a single docket entry.
        """

        description = entry['entry']

        # Check if the entry has a "served" status
        if SERVE_STATUS_PATTERN.search(description):
            self.docket_data.case_party.serve_status = "Served"
            self.docket_data.case.case_status_date = entry['date_time']
            self.docket_data.case_party.serve_status_date = entry['date_time']

            # Extract the date from the description
#            date_match = SERVE_STATUS_DATE_PATTERN.search(description)
#            if date_match:
#                date_str = date_match.group(0)
#                if date_match.group(1):  # MM/DD/YYYY format
#                    date_obj = datetime.strptime(
#                        date_str, "%m/%d/%Y" if len(date_str.split('/')[-1]) == 4 else "%m/%d/%y")
#                else:  # Month DD, YYYY format
#                    date_obj = datetime.strptime(date_str, "%B %d, %Y")
#
#                # Update the served date in docket_data
#                self.docket_data.case_party.serve_status_date = date_obj.strftime(
#                    "%m/%d/%Y")
#
                

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
            self.docket_data.case.case_status = 'DISPOSED'
            self.docket_data.case.case_status_date = entry['date_time']
            # Find the largest amount in the description
            largest_amount = find_largest_amount(description)
            if largest_amount is not None:
                self.docket_data.case.amount = largest_amount

    def test_dismissed(self, entry: Dict[str, str]) -> None:
        """
        Parse the dismissal status from a docket entry and update the corresponding fields in docket_data.

        :param entry: A dictionary representing a single docket entry.
        """

        description = entry['entry']

        # Check if the entry has a dismissal status
        if DISMISSED_PATTERN.search(description):
            self.docket_data.case.case_status_date = entry['date_time']
            self.docket_data.case.case_dismiss_date = entry['date_time']
            self.docket_data.case.case_status = 'DISMISSED'

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
                self.docket_data.case.hearing_date = date

    def bankruptcy_test(self, entry: Dict[str, str]) -> None:
        """
        Check if the docket entry contains the word "bankruptcy" and update the corresponding fields in docket_data.

        :param entry: A dictionary representing a single docket entry.
        """

        description = entry['entry']
        date = entry['date_time']

        # Check if the description contains the word "bankruptcy"
        if BANKRUPTCY_PATTERN.search(description):
            self.docket_data.case_party.bankruptcy_filed_date = date
            self.docket_data.case_party.is_bankruptcy_filed = True

    def process_entries(self) -> None:
        """
        Process all docket entries by calling the `process_entry` method for each entry.
        Create a CaseDocket object and append to the CaseData.docket_entries
        """
        for i, entry in enumerate(self.docket_data.docket_entries):

            self.process_entry(entry)
            del self.docket_data.docket_entries[i]
            entry['unique_id'] = i+1
            self.docket_data.docket_entries = [
                instantiate_docket(entry)] + self.docket_data.docket_entries

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


class ParseHtml:

    def __init__(self, item: CaseItem) -> None:

        self.soup = item['soup']
        self.county = item['county']
        self.link = item['link']

    def _validate_date(self, date_str: str) -> bool:
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

    def _validate_type(self, docket_type: str) -> bool:
        """
        Validate if the given docket type string contains only alphanumeric characters, hyphens, and underscores.

        :param docket_type: The docket type string to be validated.
        :return: True if the docket type string is valid, False otherwise.
        """
        return bool(re.match(r'^[A-Za-z0-9_-]+$', docket_type))

    def _format_description(self, description: str) -> str:
        """
        Format the given description string by removing extra whitespace and leading/trailing spaces.

        :param description: The description string to be formatted.
        :return: The formatted description string.
        """
        formatted_description = re.sub(r'\s+', ' ', description).strip()
        return formatted_description

    def extract_docket(self) -> List[Dict[str, Optional[str]]]:
        """
        Extracts docket information from an HTML table with the id "dgrdResults".
        Returns a list of dictionaries containing the docket date, type, and description.
        """

        # Find the table with id "dgrdResults"
        docket_table = self.soup.find('table', {'id': 'dgrdResults'})

        # Extract the rows in the table
        rows = docket_table.find_all('tr')

        docket_entries = []

        # Iterate through the rows, starting from the second row (skipping the header)
        for row in rows[1:-1]:
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
                if self._validate_date(date):
                    # Validate the docket type, set to an empty string if invalid
                    docket_type = docket_type if self._validate_type(
                        docket_type) else ""
                    # Format the description text
                    formatted_description = self._format_description(
                        description)
                    # Add the extracted and formatted data to the list of docket entries
                    docket_entries.append(
                        {'date_time': date, 'type': docket_type, 'entry': formatted_description})

        return docket_entries

    def extract_plaintiffs_and_defendants(self, party: CustomCaseParty) -> Tuple[List[CustomCaseParty], str]:
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

        docket_table = self.soup.find('table', {'id': 'dgrdParties'})
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
                party = copy(party)
                party.link = self.link
                # Create address parts list
                address_parts = [t.strip()
                                 for t in columns[3].stripped_strings]
                # If address exists
                if address_parts[0] != ',':
                    parts = address_parts[-1].split()
                    city = parts[0].strip(',')
                    state = parts[1]
                    zip_code = parts[2]
                    street = ', '.join(address_parts[:-1])
                    total_address = columns[3].get_text(strip=True)
                    party.defendant = name
                    party.total_address = total_address
                    party.street = street
                    party.city = city
                    party.state = state
                    party.zip_code = zip_code

                defendants.append(party)

        # Combine plaintiffs
        return defendants, names_list_to_string(plaintiffs)

    def map_case_types(self, case_type: str) -> str:
        """ Map case types to current database structure
        """
        return COURT_CASE_TYPES_MAP[case_type.lower()]

    def parse(self) -> BaseCasePacked:

        case_number = self.soup.select('#lblCaseNumber')[0].text
        base_case_packed = None
        if "CV" in case_number:

            case = {
                'case_status_date': self.soup.select('#lblDateFiled')[0].get_text(strip=True),
                'case_title': self.soup.select('#lblCaption')[0].get_text(strip=True),
                'plaintiff': '',
                'case_number': case_number,
                'county': self.county,
                'file_date': self.soup.select('#lblDateFiled')[0].get_text(strip=True),
                'judge': self.soup.select('#lblJudgeName')[0].get_text(strip=True),
                'case_type': self.map_case_types(self.soup.select('#lblDescription')[0].get_text(strip=True)),
            }

            # CREATE A CaseData OBJECT
            case_data = instantiate_case_data(
                self.extract_docket(),  # EXTRACT DOCKET INFO
                instantiate_case(case)  # CREATE Case OBJECT
            )
            # TODO Remove try statement

            # Process Dockets
            case_data, docket_entries = DocketProcessor(case_data).results

            case_data.case_party.docket_entries = docket_entries

            defendants, plaintiff = self.extract_plaintiffs_and_defendants(
                case_data.case_party)

            case_data.case.plaintiff = plaintiff
            
            base_case_packed = BaseCasePacked(
                case=case_data.case,
                case_parties=defendants,
            )

        if not base_case_packed:
            raise IgnoreRequest("Not A Civil Case")
        
        return base_case_packed


def parse_case_data(item):
    # Parse case from HTML
    return ParseHtml(item).parse()
