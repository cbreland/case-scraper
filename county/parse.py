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

# -------------------------------------------------------------------------------------

    #
    # (STEP 1) THE FOLLOWING STEPS ARE BASED ON GETTING CASE AND PARTY DATA FROM DOCKET ENTRIES
    #
    # Create a dictionary of initial case data as key, value pairs
    # In the following data structure
    """
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

# -------------------------------------------------------------------------------------

    #
    # (STEP 2)
    #
    # Create a list of dictionaries containing the docket entry data as key, value pairs
    # In the following data structure
    """
    docket_dicts
        entry: str
        date_time: datestring format '01/01/1900 
        unique_id: int
    """
    docket_dicts = parse_docket_entries(soup)

# -------------------------------------------------------------------------------------

    #
    # (STEP 3)
    #
    # Create a list of dictionaries with defendant data as key, value pairs
    # In the following data structure
    """
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

# -------------------------------------------------------------------------------------

    #
    # (STEP 4)
    #
    # Create a dictionary with defendant and plaintiff data as key, value pairs
    # from parsing the docket entries
    #
    # Return a tuple with each dictionary included
    # In the following data structure
    """
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

    # Parse CaseParty and Case fields from docket
    case_docket_data, case_party_docket_data = parse_docket_fields(
        docket_dicts, case_dict, plaintiffs, case_number
    )

# -------------------------------------------------------------------------------------

    #
    # STEPS (5 - 8) PACKAGING DATA INTO DATACLASSES
    #

    #
    # (STEP 5)
    #
    # Create a list of CaseDocket objects
    dockets = [
        CaseDocket(**docket_entry)
        for docket_entry in docket_dicts
    ]

# -------------------------------------------------------------------------------------

    #
    # (STEP 6)
    #
    # Create a Case object
    case = Case(**case_docket_data)

# -------------------------------------------------------------------------------------

    #
    # (STEP 7)
    #
    # Create a list of CaseParty objects with dictionaries that were created
    # Also add the list of CaseDockets as a dictionary.
    case_parties = [
        CaseParty(
            **case_party_docket_data,
            **defendant_dict,
            docket_entries=dockets
        )
        for defendant_dict in defendant_dicts
    ]

# -------------------------------------------------------------------------------------

    #
    # (STEP 8)
    #
    # Create BaseCasePacked object with the list of Case and list of CaseParty objects
    return PackedCase(case, case_parties)
