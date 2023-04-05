from public_digital.spiders import BaseScraper as pd


class CaseScraper(pd.CaseScraperBase):

    name = 'lorain_scraper'

    def start_requests(self) -> pd.Request:
        """START REQUEST FUNCTION FOR SCRAPY"""

        yield pd.Request(
            url=self.base_url,
            callback=self.landing_page,
            dont_filter=True
        )

    @pd.return_soup
    def landing_page(self, soup: pd.BeautifulSoup):
        """LANDING PAGE REQUEST"""

        for current_case in range(self.arg_start, 
            self.arg_end if self.arg_end else 999999999):

            # YIELDS CASE DETAILS REQUEST
            yield pd.Request(
                pd.urljoin(self.base_url,
                f'Docket.aspx?CaseID={current_case}'),
                callback=self.case_details,
                meta={'case_number_int_repr': current_case}
            )

    @pd.return_soup
    def case_details(self, soup: pd.BeautifulSoup):
        """CASE DETAILS REQUEST"""

        yield pd.CaseItem(
            case_number=soup.response.meta['case_number_int_repr'],
            soup=soup,
            link=soup.response.url,
            county=self.county
        )
