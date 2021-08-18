import base64
import os
import re

import requests

from steps.citation import CitationFileStep
from steps.codemeta import CodemetaResponseStep
from steps.core import MetadataStep, Step
from steps.crossref import CrossrefResponseStep
from steps.description import DescriptionFileStep
from steps.utils import (
    author_name_as_dict,
    find_or_empty_string,
    get_webpage_text,
    strip_new_lines,
)


class GithubRepoStep(Step):
    step_links = [("GitHub home page", "http://github.com/")]
    step_intro = (
        "GitHub is a Web-based software version control repository hosting service."
    )
    step_more = "Attribution information is often included in software source code, which can be inspected for software projects that have posted their code on GitHub."

    @property
    def starting_children(self):
        return [
            CrossrefResponseStep,
            GithubCodemetaFileStep,
            GithubCitationFileStep,
            GithubReadmeFileStep,
            GithubDescriptionFileStep,
            GithubApiResponseStep,
        ]

    def set_content(self, input):
        if not "github.com" in input:
            return
        if input.startswith("http"):
            url = "/".join(input.split("/", 5)[0:5])
        else:
            url = find_or_empty_string('"(https?://github.com/.+?)"', input)
            url = url.replace("/issues", "")
            url = url.replace("/new", "")
            if "sphinx" and "theme" in url or url.endswith(".zip"):
                url = None
            if not url:
                return

        if self.is_organization(url):
            pinned_url = self.get_pinned_url(url)
            if pinned_url:
                self.content = get_webpage_text(pinned_url)
                self.content_url = pinned_url
                return

        self.content = get_webpage_text(url)
        self.content_url = url

    def set_content_url(self, input):
        # set in set_content
        pass

    @staticmethod
    def is_organization(url):
        url = url.replace("http://", "")
        url = url.replace("https://", "")
        return len(url.split("/")) == 2

    def get_pinned_url(self, url):
        text = get_webpage_text(url)
        pinned_area = find_or_empty_string("PINNED_REPO.*\s*<span", text)
        pinned_url = find_or_empty_string('href="(\/\w+\/\w+)"', pinned_area)
        if pinned_url:
            pinned_url = "https://github.com" + pinned_url
        return pinned_url


class GithubApiResponseStep(Step):
    step_links = [("GITHUB API docs", "https://developer.github.com/v3/repos/#get")]
    step_intro = (
        "GitHub is a Web-based software version control repository hosting service."
    )
    step_more = "GitHub's API can be used to find metadata about software projects, like the project's authors, title, and created date."

    @property
    def starting_children(self):
        return [GithubApiResponseMetadataStep]

    def set_content(self, input):
        github_url = self.content_url

        if not github_url:
            return
        if github_url.endswith("github.com") or "github.com" not in github_url:
            return

        self.content = {}
        h = {"User-Agent": "CiteAs"}
        (login, token) = self.get_github_token_tuple()
        repo_api_url = self.get_repo_api_url(github_url)

        r_repo = requests.get(repo_api_url, auth=(login, token), headers=h)
        r_repo = r_repo.json()

        try:
            user_api_url = "https://api.github.com/users/{}".format(
                r_repo["owner"]["login"]
            )
        except (KeyError, TypeError):
            print("bad github request")
            return

        r_login = requests.get(user_api_url, auth=(login, token), headers=h)
        self.content["repo"] = r_repo
        self.content["user"] = r_login.json()
        self.content_url = repo_api_url
        self.additional_content_url = {
            "url": user_api_url,
            "description": "author source",
        }

    @staticmethod
    def get_repo_api_url(github_url):
        # remove /wiki
        repo_api_url = github_url.replace("/wiki", "")
        # strip trailing /
        if repo_api_url.endswith("/"):
            repo_api_url = repo_api_url[:-1]
        # remove www
        repo_api_url = repo_api_url.replace("http://www.", "http://")
        repo_api_url = repo_api_url.replace("https://www.", "https://")
        # switch to API URL
        if "gist.github.com" in repo_api_url:
            gist_id = find_or_empty_string(
                "gist.github.com\/\w+\/(\w+|\d+)", repo_api_url
            )
            repo_api_url = "https://api.github.com/gists/{}".format(gist_id)
        else:
            repo_api_url = repo_api_url.replace("github.com/", "api.github.com/repos/")
        return repo_api_url

    @staticmethod
    def get_github_token_tuple():
        tokens_str = os.environ["GITHUB_TOKENS"]
        tokens = [t.split(":") for t in tokens_str.split(",")]
        (login, token) = tokens[0]
        return login, token


class GithubCodemetaFileStep(Step):
    step_links = [("CodeMeta user guide", "https://codemeta.github.io/user-guide/")]
    step_intro = "CodeMeta is a new standard for the exchange of software metadata across repositories and organizations."
    step_more = "The CodeMeta standard has many contributors spanning research, education, and engineering domains."

    @property
    def starting_children(self):
        return [CrossrefResponseStep, CodemetaResponseStep]

    def set_content(self, github_main_page_text):
        matches = re.findall(
            'href="(.*blob/.*/codemeta.json)"', github_main_page_text, re.IGNORECASE
        )
        if matches:
            filename_part = matches[0]
            filename_part = filename_part.replace("/blob", "")
            filename = "https://raw.githubusercontent.com{}".format(filename_part)
            self.content = get_webpage_text(filename)
            self.content_url = filename

    def set_content_url(self, input):
        # in this case set_content does it, because it knows the url
        pass


class GithubReadmeFileStep(Step):
    step_links = [
        ("README description", "https://help.github.com/articles/about-readmes/")
    ]
    step_intro = "A README file contains information about other files in a directory or archive of computer software."
    step_more = "README files often contain requests for attribution."

    @property
    def starting_children(self):
        return [CrossrefResponseStep]

    def set_content(self, github_main_page_text):
        matches = re.findall(
            'href="(.*blob/.*/readme.*?)"', github_main_page_text, re.IGNORECASE
        )
        if matches:
            filename_part = matches[0]
            filename_part = filename_part.replace("/blob", "")
            filename_part = filename_part.replace("https://github.com", "")
            filename = "https://raw.githubusercontent.com{}".format(filename_part)
            readme_text = get_webpage_text(filename)
            self.content = self.strip_dependencies(readme_text)
            self.content_url = filename

    def set_content_url(self, input):
        # in this case set_content does it, because it knows the url
        pass

    @staticmethod
    def strip_dependencies(readme_text):
        readme_text = strip_new_lines(readme_text)
        dependencies = find_or_empty_string("# Dependencies #(.+)#?.+#?", readme_text)
        readme_text = readme_text.replace(dependencies, "")
        return readme_text


class GithubCitationFileStep(CitationFileStep):
    step_links = [
        ("Citation File Format (CFF)", "https://citation-file-format.github.io/")
    ]
    step_intro = (
        "Software repositories sometimes includes a plain text citation file named 'CITATION' or 'CITATION.cff' "
        "that includes the author, software title, and other additional information."
    )
    step_more = (
        "The CITATION file can be parsed to extract this attribution information."
    )

    def set_content(self, github_main_page_text):
        matches = re.findall(
            'href="(.*blob/.*/citation.*?)"', github_main_page_text, re.IGNORECASE
        )
        if not matches:
            matches = re.findall(
                'href="(.*/inst)"', github_main_page_text, re.IGNORECASE
            )
            if matches:
                inst_url = "http://github.com{}".format(matches[0])
                r = requests.get(inst_url)
                inst_page_text = r.text
                matches = re.findall(
                    'href="(.*blob/.*/citation.*?)"', inst_page_text, re.IGNORECASE
                )

        if matches:
            filename_part = matches[0]
            filename_part = filename_part.replace("/blob", "")
            filename_part = filename_part.replace("https://github.com", "")
            filename_part = filename_part.replace("http://github.com", "")
            filename = "https://raw.githubusercontent.com{}".format(filename_part)

            # check if symlink
            decoded_content = self.get_symlink_content(matches)

            if decoded_content:
                self.content = decoded_content
            else:
                self.content = get_webpage_text(filename)
            self.content_url = filename

    @staticmethod
    def get_symlink_content(matches):
        repo_path = matches[0].replace("/blob/master/CITATION", "")
        api_url = "https://api.github.com/repos{}/contents/CITATION?ref=master".format(
            repo_path
        )
        r = requests.get(api_url)
        if r.status_code != 200:
            return None
        api_resp = r.json()
        encoded_content = api_resp.get("content")
        decoded_content = base64.b64decode(encoded_content).decode("utf-8")
        return decoded_content


class GithubDescriptionFileStep(DescriptionFileStep):
    def set_content(self, github_main_page_text):
        matches = re.findall(
            'href="(.*blob/.*/description.*?)"', github_main_page_text, re.IGNORECASE
        )
        if matches:
            filename_part = matches[0]
            filename_part = filename_part.replace("/blob", "")
            filename = "https://raw.githubusercontent.com{}".format(filename_part)
            self.content = get_webpage_text(filename)
            self.content_url = filename


class GithubApiResponseMetadataStep(MetadataStep):
    def set_content(self, input_dict):
        metadata_dict = {}
        if "gist.github.com" in input_dict["repo"]["html_url"]:
            for key, value in input_dict["repo"]["files"].items():
                file_name = key
            metadata_dict["title"] = file_name
        else:
            metadata_dict["title"] = input_dict["repo"].get(
                "name", input_dict["repo"]["html_url"]
            )
        metadata_dict["author"] = [author_name_as_dict(input_dict["user"]["name"])]
        metadata_dict["publisher"] = "GitHub repository"
        metadata_dict["URL"] = input_dict["repo"]["html_url"]
        year = [[input_dict["repo"]["created_at"][0:4]]]
        metadata_dict["issued"] = {"date-parts": year}
        metadata_dict["year"] = year
        metadata_dict["type"] = "software"

        self.content = metadata_dict
