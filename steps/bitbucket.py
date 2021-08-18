import re

from steps.bibtex import BibtexStep
from steps.citation import CitationFileStep
from steps.codemeta import CodemetaResponseStep
from steps.core import Step
from steps.crossref import CrossrefResponseStep
from steps.utils import find_or_empty_string, get_raw_bitbucket_url, get_webpage_text


class BitbucketRepoStep(Step):
    step_links = [("Bitbucket home page", "https://bitbucket.com/")]
    step_intro = "Bitbucket is a web-based software version control repository hosting service."
    step_more = "Attribution information is often included in software source code, which can be inspected for software projects that have posted their code on Bitbucket."

    @property
    def starting_children(self):
        return [
            BitbucketCodemetaFileStep,
            BitbucketCitationFileStep,
            BitbucketReadmeFileStep,
            BitbucketDescriptionFileStep
            ]

    def set_content(self, input):
        if "bitbucket.org" not in input:
            return
        if input.startswith("http"):
            url = "/".join(input.split("/", 5)[0:5])
            url = url + '/src'
        else:
            url = find_or_empty_string('"(https?:\/\/bitbucket.org\/\w+\/\w+/?)"', input)
            if not url:
                return
            else:
                url = "/".join(url.split("/")[0:5])
                url = url + '/src'

        self.content = get_webpage_text(url)
        self.content_url = url

    def set_content_url(self, input):
        # set in set_content
        pass


class BitbucketReadmeFileStep(Step):
    step_links = [("README description", "https://confluence.atlassian.com/bitbucket/readme-content-221449772.html")]
    step_intro = "A README file contains information about other files in a directory or archive of computer software."
    step_more = "README files often contain requests for attribution."

    @property
    def starting_children(self):
        return [
            CrossrefResponseStep,
            BibtexStep
        ]

    def set_content(self, bitbucket_main_page_text):
        matches = re.findall('href=\"(.*\/readme.*?\?.*)\"', bitbucket_main_page_text, re.IGNORECASE)
        if matches:
            filename_part = matches[0]
            filename = get_raw_bitbucket_url(filename_part)

            self.content = get_webpage_text(filename)
            self.content_url = filename

    def set_content_url(self, input):
        # in this case set_content does it, because it knows the url
        pass


class BitbucketCodemetaFileStep(Step):
    step_links = [("CodeMeta user guide", "https://codemeta.github.io/user-guide/")]
    step_intro = "CodeMeta is a new standard for the exchange of software metadata across repositories and organizations."
    step_more = "The CodeMeta standard has many contributors spanning research, education, and engineering domains."

    @property
    def starting_children(self):
        return [
            CrossrefResponseStep,
            CodemetaResponseStep
        ]

    def set_content(self, bitbucket_main_page_text):
        matches = re.findall('href=\"(.*\/codemeta\.json.*?\?.*)\"', bitbucket_main_page_text, re.IGNORECASE)
        if matches:
            filename_part = matches[0]
            filename = get_raw_bitbucket_url(filename_part)

            self.content = get_webpage_text(filename)
            self.content_url = filename

    def set_content_url(self, input):
        # in this case set_content does it, because it knows the url
        pass


class BitbucketCitationFileStep(CitationFileStep):
    def set_content(self, bitbucket_main_page_text):
        matches = re.findall('href=\"(.*\/citation.*?)\"', bitbucket_main_page_text, re.IGNORECASE)

        if matches:
            filename_part = matches[0]
            filename = get_raw_bitbucket_url(filename_part)

            self.content = get_webpage_text(filename)
            self.content_url = filename


class BitbucketDescriptionFileStep(CitationFileStep):
    def set_content(self, bitbucket_main_page_text):
        matches = re.findall('href=\"(.*\/description.*?)\"', bitbucket_main_page_text, re.IGNORECASE)

        if matches:
            filename_part = matches[0]
            filename = get_raw_bitbucket_url(filename_part)

            self.content = get_webpage_text(filename)
            self.content_url = filename