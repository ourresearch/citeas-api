import requests

from steps.bibtex import BibtexStep
from steps.bitbucket import BitbucketRepoStep
from steps.citation import CitationFileStep
from steps.core import Step
from steps.crossref import CrossrefResponseStep
from steps.description import DescriptionFileStep
from steps.github import GithubRepoStep
from steps.pmid import PMIDStep
from steps.utils import find_or_empty_string, get_webpage_text


class CranLibraryStep(Step):
    step_links = [("CRAN home page", "https://cran.r-project.org/")]
    step_intro = "The Comprehensive R Archive Network (CRAN) is a repository of software for the R programming language."
    step_more = (
        "A project's CRAN repository page often lists useful attribution information."
    )

    @property
    def starting_children(self):
        return [
            CranCitationFileStep,
            CranDescriptionFileStep,
            GithubRepoStep,
            BitbucketRepoStep,
            CrossrefResponseStep,
            PMIDStep,
            BibtexStep,
        ]

    def set_content(self, input):
        if self.content_url:
            self.content = get_webpage_text(self.content_url)

    def set_content_url(self, input):
        if input and "cran.r-project.org/web/packages" in input:
            package_name = find_or_empty_string(
                "cran.r-project.org/web/packages/(\w+\.?\w+)/?", input
            )
            self.content_url = "https://cran.r-project.org/web/packages/{}".format(
                package_name
            )
        elif input and "cran.r-project.org/package=" in input.lower():
            package_name = find_or_empty_string(
                "cran.r-project.org/package=(.*)/?", input
            )
            package_name = package_name.split("/")[0]
            self.content_url = "https://cran.r-project.org/web/packages/{}".format(
                package_name
            )


class CranCitationFileStep(CitationFileStep):
    def set_content(self, cran_main_page_text):
        cran_citation_url = self.parent_content_url + "/citation.html"
        r = requests.get(cran_citation_url)

        if r.status_code == 200:
            self.content = r.text
            self.content_url = cran_citation_url


class CranDescriptionFileStep(DescriptionFileStep):
    def set_content(self, input):
        filename = self.parent_content_url + "/DESCRIPTION"
        page = get_webpage_text(filename)
        self.content = page
        self.content_url = filename
