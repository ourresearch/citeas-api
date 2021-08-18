import re

from flask import abort
from googlesearch import get_random_user_agent, search
import requests
import validators

from steps.arxiv import ArxivResponseStep
from steps.bitbucket import BitbucketRepoStep
from steps.cran import CranLibraryStep
from steps.core import Step
from steps.crossref import CrossrefResponseStep
from steps.github import GithubRepoStep
from steps.pypi import PypiLibraryStep
from steps.webpage import WebpageStep


class UserInputStep(Step):
    @property
    def starting_children(self):
        return [
            CrossrefResponseStep,
            ArxivResponseStep,
            GithubRepoStep,
            BitbucketRepoStep,
            CranLibraryStep,
            PypiLibraryStep,
            WebpageStep,
        ]

    def set_content_url(self, input):
        url = self.build_starting_url(input)
        if url.startswith("ftp://"):
            abort(404)
        if "readthedocs" in url:
            url = self.get_citation_html_file(url)
        self.content_url = url

    def set_content(self, input):
        if self.content_url.startswith("http://arxiv"):
            self.content = self.content_url.replace("http://", "").replace(
                ".org/abs/", ":"
            )
        else:
            self.content = self.content_url

    def build_starting_url(self, input):
        # doi
        if input.startswith("10."):
            url = "http://doi.org/{}".format(input)

        # web page
        elif input.startswith(("http://", "https://")):
            url = input

        # url in string
        elif re.search("(?P<url>https?://[^\s]+)", input):
            url = re.search("(?P<url>https?://[^\s]+)", input).group("url")

        # arxiv
        elif input.lower().startswith("arxiv"):
            id = input.split(":", 1)[1]
            url = "http://arxiv.org/abs/{}".format(id)

        # arvix ID only, like 1812.02329
        elif self.is_arxiv_id(input):
            url = "http://arxiv.org/abs/{}".format(input)

        # add http to see if it is a valid URL
        elif self.is_valid_url(input):
            url = "http://{}".format(input)

        else:
            # google search
            url = self.google_search(input)
            self.key_word = input
        return url

    @staticmethod
    def is_arxiv_id(input):
        r = re.compile("\d{4}.\d{5}")
        if r.match(input.lower()):
            return True

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

    @staticmethod
    def is_valid_url(input):
        url = "http://{}".format(input)
        if validators.url(url):
            try:
                r = requests.get(url, timeout=1)
                if r.status_code == requests.codes.ok:
                    return True
            except:
                return False

    @staticmethod
    def get_citation_html_file(url):
        # citation paths
        citation_opt_1 = "citation.html"
        citation_opt_2 = "reference/citing.html"

        # format url
        if url.endswith("en/stable") or url.endswith("en/latest"):
            citation_urls = [url + "/" + citation_opt_1, url + "/" + citation_opt_2]
        elif url.endswith("en/stable/") or url.endswith("en/latest/"):
            citation_urls = [url + citation_opt_1, url + citation_opt_2]
        elif url.endswith("/"):
            citation_urls = [
                url + "en/stable/" + citation_opt_1,
                url + "en/stable/" + citation_opt_2,
            ]
        else:
            citation_urls = [
                url + "en/stable/" + citation_opt_1,
                url + "en/stable/" + citation_opt_2,
            ]

        # check if citation exists
        try:
            for citation_url in citation_urls:
                r = requests.get(citation_url, timeout=2)
                if r.status_code == 200:
                    return citation_url
            return url
        except requests.exceptions.RequestException:
            return url
