import re
from dataclasses import dataclass

from public_digital.dataclasses.base_dataclasses import CaseParty

# Compile regular expressions for garnishment and employer patterns
GARNISHMENT_PATTERN = re.compile(r'garnishment|personal earnings', re.IGNORECASE)
EMPLOYER_PATTERN = re.compile(r'see jr\.(.+)', re.IGNORECASE)

# Regular expression pattern to match different formats of "served" status
SERVE_STATUS_PATTERN = re.compile(
    r'(?i)(Signed Receipt for Certified Mail Returned and Filed|PROCESS SERVER RETURN:\s+RESIDENTIAL SERVICE|PROCESS SERVER RETURN:\s+PERSONAL SERVICE|PROCESS SERVER RETURN:\s+SUBSTITUTE SERVICE)'

)

# Regular expression pattern to match different date formats
SERVE_STATUS_DATE_PATTERN = re.compile(
    r'(?:((\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4}))|'
    r'(\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
    r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\b (\d{1,2}), (\d{4})))',
    re.IGNORECASE
)

# Regular expression pattern to match different judgment-related phrases
JUDGMENT_PATTERNS = re.compile(r'(?i)judg.*(award|grant|render)')

# Regular expression pattern to match different dismissal-related phrases
DISMISSED_PATTERN = re.compile(r'\bdismissed(?:,)?\s+(?:with|without|w/o|for)\b', re.IGNORECASE)

# Regular expression pattern to match different date formats
HEARING_DATE_PATTERN = re.compile(r'(?i)(set for|continued to)')

# Add bankruptcy_pattern to search for the word "bankruptcy" in the description
BANKRUPTCY_PATTERN = re.compile(r'\bbankruptcy\b', re.IGNORECASE)

# mapping for case_type field
COURT_CASE_TYPES_MAP = {
    '': 'Other',
    'administrative appeals': 'Other',
    'professional tort': 'Contract / Debt',
    'other torts': 'Contract / Debt',
    'product liability': 'Contract / Debt',
    'foreclosures-cv': 'Foreclosure',
    'foreclosure': 'Foreclosure',
    'workers compensation': 'Other',
    'termination awa': 'Other',
    'other civil': 'Contract / Debt',
    'foreclosure-cv': 'Contract / Debt',
    'other civil-dp': 'Domestic',
    'other civil-cv': 'Contract / Debt',
    'cert. qualification employment': 'Other'
} 

@dataclass
class CustomCaseParty(CaseParty):
    garnishment_answer: None = None
    answer_date: None = None
    last_pay_date: None = None
    agreement_date: None = None


    
