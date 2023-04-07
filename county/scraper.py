from public_digital.spiders import BaseScraper as pd
from typing import Generator


class CaseScraper(pd.CaseScraperBase):

    name = 'lorain_scraper'

    def start_requests(self) -> pd.Request:
        """START REQUEST FUNCTION FOR SCRAPY"""
        self.error_count = 0
        yield pd.Request(
            url=self.base_url,
            callback=self.landing_page,
            dont_filter=True,
            meta={
            'case_number_int_repr':self.start_case, 
            'initial': True
            }
        )

    @pd.return_soup
    def landing_page(self, soup: pd.BeautifulSoup) -> Generator[pd.Request, None, None]:
        """LANDING PAGE REQUEST"""

        
        if 'An exception has occured: System.IndexOutOfRangeException: There is no row at position 0.' in soup.text and not soup.response.meta.get('initial'):
            self.error_count += 1
            if self.error_count > 20:
                print('failure')
            
        self.error_count = 0
        case_number = soup.response.meta.get('case_number_int_repr')
  
        # YIELDS CASE DETAILS REQUEST
        yield pd.Request(
            pd.urljoin(self.base_url,
            f'Docket.aspx?CaseID={case_number+1}'),
            callback=self.landing_page,
            meta={
            'case_number_int_repr': case_number+1, 
            'initial': False
            }
        )

        if not soup.response.meta.get('initial'):
        
            yield pd.CaseItem(
                case_number=soup.response.meta['case_number_int_repr'],
                soup=soup,
                link=soup.response.url,
                county=self.county
            )
