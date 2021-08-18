from googlesearch import get_random_user_agent, search

from steps.arxiv import ArxivResponseStep
from steps.bitbucket import BitbucketRepoStep
from steps.cran import CranLibraryStep
from steps.core import Step
from steps.github import GithubRepoStep
from steps.pypi import PypiLibraryStep
from steps.webpage import WebpageStep


class GoogleStep(Step):
    step_intro = "Use Google to find the software citation."
    step_more = "This project webpage often includes attribution information like an associated DOI, GitHub repository, and/or project title."

    @property
    def starting_children(self):
        return [
            ArxivResponseStep,
            GithubRepoStep,
            BitbucketRepoStep,
            CranLibraryStep,
            PypiLibraryStep,
            WebpageStep,
        ]

    def set_content_url(self, input):
        if "http" in input:
            return None
        self.content_url = self.google_search(input)

    def set_content(self, input):
        self.content = self.content_url

    @staticmethod
    def google_search(input):
        random_user_agent = get_random_user_agent()
        # check if input is PMID
        if len(input) == 8 and input.isdigit():
            query = input
        elif "scipy" in input:
            query = "scipy citation"
        else:
            query = "{} software citation".format(input)

        for url in search(query, stop=3, user_agent=random_user_agent):
            if "citebay.com" not in url and not url.endswith(".pdf"):
                return url
