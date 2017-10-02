import requests
import re
import os
import datetime
from nameparser import HumanName

from util import clean_doi

class NoChildrenException(Exception):
    pass

def get_webpage_text(url):
    try:
        r = requests.get(url)
    except Exception:
        # print u"exception getting the webpage {}".format(url)
        return
    return r.text

def author_name_as_dict(literal_name):
    if len(literal_name.split(" ")) > 1:
        name_dict = HumanName(literal_name).as_dict()
        response_dict = {
            "family": name_dict["last"],
            "given": name_dict["first"],
            "suffix": name_dict["suffix"]
        }
    else:
        response_dict = {"family": literal_name}

    return response_dict

def find_or_empty_string(pattern, text):
    try:
        response = re.findall(pattern, text, re.IGNORECASE)[0]
    except IndexError:
        response = ""
    return response

class Step(object):
    def __init__(self):
        self.remaining_children = self.starting_children
        # print "in init for {} with starting children {}, remaining children {}".format(
        #     self, self.starting_children, self.remaining_children)
        self.url = None
        self.content_url = None
        self.content = None
        self.more_info = None

    @property
    def starting_children(self):
        return []

    # overridden for MetadataStep
    @property
    def is_metadata(self):
        return False

    def get_child(self):
        if not self.content:
            # print "no content"
            raise NoChildrenException

        if len(self.remaining_children) == 0:
            # print "no remaining_children"
            raise NoChildrenException

        child_class = self.remaining_children.pop(0)
        child_obj = child_class()
        child_obj.set_content_url(self.content_url)
        child_obj.set_content(self.content)

        return child_obj


    def get_name(self):
        return self.__class__.__name__

    def set_content(self, input):
        self.content = input

    def set_content_url(self, input):
        self.content_url = input

    def to_dict(self):
        ret = {
            "content_url": self.content_url,
            "has_content": bool(self.content),
            "name": self.get_name(),
            "more_info": self.more_info
        }
        return ret

    def __repr__(self):
        return u"<{}>".format(self.__class__.__name__)


class MetadataStep(Step):
    @property
    def is_metadata(self):
        return True



class WebpageMetadataStep(MetadataStep):

    def set_content(self, input):
        self.content = {}

        matches = re.findall(u"<h1>(.+?)</h1>", input)
        if matches:
            title = matches[0]
        else:
            title = input

        self.content["type"] = "misc"
        self.content["title"] = title



class WebpageStep(Step):
    @property
    def starting_children(self):
        return [
            WebpageMetadataStep
        ]

    def set_content(self, input):
        self.content = get_webpage_text(input)





class CrossrefResponseMetadataStep(MetadataStep):
    def set_content(self, input):
        self.content = input


class CrossrefResponseStep(Step):
    @property
    def starting_children(self):
        return [
            CrossrefResponseMetadataStep
        ]

    def set_content(self, input):
        try:
            doi = clean_doi(input)
            doi_url = u"https://doi.org/{}".format(doi)
            headers = {'Accept': 'application/vnd.citationstyles.csl+json'}
            print "doi_url", doi_url
            r = requests.get(doi_url, headers=headers)
            self.content = r.json()
        except Exception:
            print u"no doi metadata found for {}".format(input)
            pass

    def set_content_url(self, input):
        try:
            doi = clean_doi(input)
        except Exception:
            print u"no doi found for {}".format(input)
            return

        doi_url = u"http://doi.org/{}".format(doi)
        self.content_url = doi_url


class GithubApiResponseMetadataStep(MetadataStep):
    def set_content(self, input_dict):
        metadata_dict = {}
        metadata_dict["title"] = input_dict["repo"].get("name", input_dict["repo"]["url"])
        metadata_dict["author"] = [author_name_as_dict(input_dict["user"]["name"])]
        metadata_dict["publisher"] = "GitHub repository"
        metadata_dict["URL"] = input_dict["repo"]["url"]
        metadata_dict["issued"] = {"date-parts": [[input_dict["repo"]["created_at"][0:4]]]}
        metadata_dict["type"] = "software"

        self.content = metadata_dict

class GithubApiResponseStep(Step):
    @property
    def starting_children(self):
        return [
            GithubApiResponseMetadataStep
            # GithubCitationFileStep,
            # GithubReadmeFileStep,
            # GithubApiResponseStep
        ]

    def get_github_token_tuple(self):
        tokens_str = os.environ["GITHUB_TOKENS"]
        tokens = [t.split(":") for t in tokens_str.split(",")]
        (login, token) = tokens[0]
        return (login, token)

    def set_content(self, input):
        github_url = self.content_url

        if not github_url:
            return
        if not "github.com" in github_url:
            return

        self.content = {}
        h = {"User-Agent": "CiteAs"}
        (login, token) = self.get_github_token_tuple()

        repo_api_url = github_url.replace("github.com/", "api.github.com/repos/")
        r = requests.get(repo_api_url, auth=(login, token), headers=h)
        self.content["repo"] = r.json()

        user_api_url = "https://api.github.com/users/{}".format(self.content["repo"]["owner"]["login"])
        r = requests.get(user_api_url, auth=(login, token), headers=h)
        self.content["user"] = r.json()

        self.content_url = repo_api_url





class GithubRepoStep(Step):
    @property
    def starting_children(self):
        return [
                GithubDescriptionFileStep,
                # GithubCitationFileStep,
                # GithubReadmeFileStep,
                GithubApiResponseStep
            ]

    def set_content(self, input):
        if not "github.com" in input:
            return
        url = "/".join(input.split("/", 5)[0:5])
        self.content = get_webpage_text(url)
        self.content_url = url

    def set_content_url(self, input):
        # set in set_content
        pass






class GithubDescriptionMetadataStep(MetadataStep):
    def set_content(self, text):
        bibtex = None
        metadata_dict = {}

        package = find_or_empty_string(ur"Package: (.*)", text)
        title = find_or_empty_string(ur"Title: (.*)", text)
        metadata_dict["title"] = u"{}: {}".format(package, title)
        person_list = re.findall(ur"person\((.*)\)", text)
        authors = []
        for person in person_list:
            section = person.replace('"', '').split(",")
            name = section[0]
            last_name = section[1].strip()
            if not last_name.startswith("role"):
                name += u" {}".format(last_name)
            authors.append(author_name_as_dict(name))
        metadata_dict["author"] = authors
        metadata_dict["year"] = datetime.datetime.utcnow().isoformat()[0:4]
        version = find_or_empty_string(ur"Version: (.*)", text)
        metadata_dict["note"] = u"R package version {}".format(version)
        metadata_dict["container-title"] = metadata_dict["note"]
        metadata_dict["URL"] = u"https://CRAN.R-project.org/package={}".format(package)
        metadata_dict["type"] = "Manual"
        self.content = metadata_dict


class GithubDescriptionFileStep(Step):
    @property
    def starting_children(self):
        return [
            GithubDescriptionMetadataStep
        ]

    def set_content(self, github_main_page_text):
        description_filename = None
        matches = re.findall(u"href=\"(.*blob/master/description.*?)\"", github_main_page_text, re.IGNORECASE)
        if matches:
            filename_part = matches[0]
            filename_part = filename_part.replace("/blob", "")
            description_filename = u"https://raw.githubusercontent.com{}".format(filename_part)

        self.content = get_webpage_text(description_filename)
        self.content_url = description_filename

    def set_content_url(self, input):
        # in this case set_content does it, because it knows the url
        pass


class UserInputStep(Step):
    @property
    def starting_children(self):
        return [
            CrossrefResponseStep,
            GithubRepoStep,
            WebpageStep
        ]

    def set_content(self, input):
        self.content = input

    def set_content_url(self, input):
        self.content_url = input
