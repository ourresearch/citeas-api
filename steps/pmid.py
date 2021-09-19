import re
from steps.arxiv import ArxivResponseStep
from steps.bibtex import BibtexStep
from steps.bitbucket import BitbucketRepoStep
from steps.crossref import CrossrefResponseStep
from steps.github import GithubRepoStep
from steps.core import MetadataStep, Step
from steps.utils import get_webpage_text


class PMIDStep(Step):
    step_links = [
        ("What is a PMID?", "https://en.wikipedia.org/wiki/PubMed#PubMed_identifier")
    ]
    step_intro = "A PMID (PubMed identifier or PubMed unique identifier) is a unique integer value, starting at 1, assigned to each PubMed record."
    step_more = ""

    @property
    def starting_children(self):
        return [
            CrossrefResponseStep,
            ArxivResponseStep,
            GithubRepoStep,
            BitbucketRepoStep,
            BibtexStep
        ]

    def set_content(self, input):
        pubmed_url_1 = re.findall(
            "www.ncbi.nlm.nih.gov\/pubmed\/\d{8}", input, re.IGNORECASE | re.MULTILINE
        )
        pubmed_url_2 = re.findall(
            "pubmed.ncbi.nlm.nih.gov\/\d{8}", input, re.IGNORECASE | re.MULTILINE
        )
        pubmed_url_3 = re.findall(
            "PMC\d{7}", input, re.IGNORECASE | re.MULTILINE
        )
        pubmed_url = None
        if pubmed_url_1:
            pubmed_url = pubmed_url_1[0]
        elif pubmed_url_2:
            pubmed_url = pubmed_url_2[0]
        elif pubmed_url_3:
            pubmed_url = f"pubmed.ncbi.nlm.nih.gov/{pubmed_url_3[0]}"

        if pubmed_url:
            self.content_url = f"https://{pubmed_url}"
            self.content = get_webpage_text(self.content_url)
