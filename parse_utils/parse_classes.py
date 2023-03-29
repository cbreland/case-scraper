
import re
from datetime import datetime
from typing import Dict, Optional, Any, Tuple

from .datastructures import (
    GARNISHMENT_PATTERN, EMPLOYER_PATTERN, 
    SERVE_STATUS_PATTERN, JUDGMENT_PATTERNS,  
    DISMISSED_PATTERN, HEARING_DATE_PATTERN, 
    BANKRUPTCY_PATTERN
)

class DocketProcessor:
    def __init__(self, case_dict, plaintiffs, case_number):
        # Initialize the DocketProcessor with CaseData containing the docket entries, Case, and CaseParty instances.
        self.case_data = case_dict
        self.case_data['plaintiff'] = plaintiffs
        self.case_data['case_number'] = case_number
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
