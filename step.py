import requests
import re
import os
import json
import datetime
from io import StringIO
from nameparser import HumanName
from bibtex import BibTeX  # use local patched version instead of citeproc.source.bibtex

from util import clean_doi

def step_configs():
    configs = {}
    for step_class in Step.__subclasses__():
        configs[step_class.__name__] = step_class.config_dict()
    return configs


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
        response = re.findall(pattern, text, re.IGNORECASE|re.MULTILINE)[0]
    except IndexError:
        response = ""
    return response

def get_bibtex_url(text):
    if not text:
        return None
    try:
        result = re.findall(u'(http"?\'?[^"\']*data_type=BIBTEX[^"\']*)', text, re.MULTILINE | re.DOTALL)[0]
    except IndexError:
        result = None
    return result

def extract_bibtex(text):
    if not text:
        return None
    try:
        result = re.findall(ur"(@.+{.+})", text, re.MULTILINE | re.DOTALL)[0]
    except IndexError:
        result = None
    return result


class Step(object):
    step_links = None
    step_intro = "This is an intro sentence."
    step_more = "This sentence has more information."

    @classmethod
    def config_dict(cls):
        resp = {
            "name": cls.__name__,
            "step_links": [cls.step_links],
            "step_intro": cls.step_intro,
            "step_more": cls.step_more
        }
        return resp


    def __init__(self):
        self.remaining_children = self.starting_children
        # print "in init for {} with starting children {}, remaining children {}".format(
        #     self, self.starting_children, self.remaining_children)
        self.url = None
        self.content_url = None
        self.content = None
        self.parent = None

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
        child_obj.parent = self

        return child_obj


    def get_name(self):
        return self.__class__.__name__

    def set_content(self, input):
        self.content = input

    def set_content_url(self, input):
        self.content_url = input

    @property
    def found_via_proxy_type(self):
        name_lower = self.get_name().lower()
        if "metadata" in name_lower:
            return None
        if "codemeta" in name_lower:
            return None
        if "crossref" in name_lower:
            return "doi"
        if "userinput" in name_lower:
            return None
        if "bibtex" in name_lower:
            return None
        return "link"


    @property
    def host(self):
        name_lower = self.get_name().lower()
        if name_lower.startswith("github"):
            return "github"
        if name_lower.startswith("crossref"):
            return "crossref"
        if name_lower.startswith("webpage"):
            return "webpage"
        if name_lower.startswith("cran"):
            return "cran"
        if name_lower.startswith("pypi"):
            return "pypi"
        return None

    def get_subject(self, class_name):
        name_lower = class_name.lower()
        if "userinput" in name_lower:
            return "user input"
        if "readmefile" in name_lower:
            return "README file"
        if "citationfile" in name_lower:
            return "R CITATION file"
        if "descriptionfile" in name_lower:
            return "R DESCRIPTION file"
        if "codemetafile" in name_lower:
            return "CODEMETA file"
        if "codemetaresponse" in name_lower:
            return "CODEMETA JSON data"
        if "crossref" in name_lower:
            return "DOI API response"
        if "bibtex" in name_lower:
            return "BibTeX"
        if "githubrepo" in name_lower:
            return "GitHub repository main page"
        if "githubapi" in name_lower:
            return "GitHub repository API response"
        if "cran" in name_lower:
            return "R CRAN package webpage"
        if "pypi" in name_lower:
            return "Python PyPI package webpage"
        if "webpage" in name_lower:
            return "webpage"
        return None

    def to_dict(self):
        ret = {
            "content_url": self.content_url,
            "has_content": bool(self.content),
            "name": self.get_name(),
            "more_info_url": self.step_links,
            "host": self.host,
            "found_via_proxy_type": self.found_via_proxy_type,
            "subject": self.get_subject(self.get_name()),
            "parent_step_name": self.parent.__class__.__name__,
            "parent_subject": self.get_subject(self.parent.__class__.__name__),
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
        title = find_or_empty_string(u"<h1>(.+?)</h1>", input)
        if not title:
            title = find_or_empty_string(u"<title>(.+?)</title>", input)
        if not title:
            title = find_or_empty_string(u"<h2>(.+?)</h2>", input)
        self.content["type"] = "misc"
        self.content["title"] = title
        self.content["URL"] = self.content_url


class WebpageStep(Step):
    @property
    def starting_children(self):
        return [
            GithubRepoStep,
            CrossrefResponseStep,
            BibtexStep,
            WebpageMetadataStep
        ]

    def set_content(self, input):
        self.content = get_webpage_text(input)

    def set_content_url(self, input):
        self.content_url = input



class PypiLibraryStep(Step):
    step_links = "https://pypi.python.org/pypi"
    @property
    def starting_children(self):
        return [
            GithubRepoStep,
            CrossrefResponseStep,
            BibtexStep
        ]

    def set_content(self, input):
        self.set_content_url(input)
        if self.content_url:
            page = get_webpage_text(self.content_url)
            # get rid of the header because it has pypi specific stuff, not stuff about the library
            # makes it hard to get github links out for the library
            # see for example https://pypi.python.org/pypi/executor
            if '<div id="content-body">' in page:
                page = page.split('<div id="content-body">')[1]
            self.content = page

    def set_content_url(self, input):
        if not input.startswith("http"):
            return

        if "pypi.python.org/pypi" in input or "readthedocs.org" in input:
            self.content_url = input


class CranLibraryStep(Step):
    step_links = "https://cran.r-project.org/"

    @property
    def starting_children(self):
        return [
            GithubRepoStep,
            CrossrefResponseStep,
            BibtexStep
        ]

    def set_content(self, input):
        if self.content_url:
            self.content = get_webpage_text(self.content_url)

    def set_content_url(self, input):
        # print "set_content_url", input
        if input and u"cran.r-project.org/web/packages" in input:
            package_name = find_or_empty_string(u"cran.r-project.org/web/packages/(.*)/?", input)
            if package_name:
                package_name = package_name.split("/")[0]
                self.content_url = u"https://cran.r-project.org/web/packages/{}".format(package_name)



class CrossrefResponseMetadataStep(MetadataStep):
    def set_content(self, input):
        self.content = input


class CrossrefResponseStep(Step):
    step_links = "https://project-thor.readme.io/docs/what-is-a-doi"

    @property
    def starting_children(self):
        return [
            CrossrefResponseMetadataStep
        ]

    def get_zenodo_doi(self, input):
        badge_doi = find_or_empty_string("://zenodo.org/badge/doi/(.+?).svg", input)
        if badge_doi:
            return badge_doi
        zenodo_doi = find_or_empty_string("doi.org/(10.5281/zenodo\.\d+)", input)
        if zenodo_doi:
            return zenodo_doi

    def set_content(self, input):
        self.set_content_url(input)
        doi_url = self.content_url
        if not doi_url:
            return
        try:
            headers = {'Accept': 'application/vnd.citationstyles.csl+json'}
            r = requests.get(doi_url, headers=headers)
            self.content = r.json()
            self.content["URL"] = doi_url
        except Exception:
            print u"no doi metadata found for {}".format(doi_url)
            pass

    def set_content_url(self, input):
        has_doi = False
        if input.startswith("10."):
            has_doi = True
        elif input.startswith("http") and "doi.org/10." in input:
            has_doi = True
        elif self.get_zenodo_doi(input):
            input = self.get_zenodo_doi(input)
            has_doi = True

        # print "has_doi", has_doi, input[0:10]

        if not has_doi:
            return

        try:
            doi = clean_doi(input)
        except Exception:
            print u"no doi found for {}".format(input)
            return

        doi_url = u"https://doi.org/{}".format(doi)
        self.content_url = doi_url


class CodemetaResponseMetadataStep(MetadataStep):
    def set_content(self, input_dict):
        print self.content
        self.content = input_dict


class CodemetaResponseStep(Step):
    step_links = "https://codemeta.github.io/user-guide/"

    @property
    def starting_children(self):
        return [
            CodemetaResponseMetadataStep
        ]


    def set_content(self, input):
        data = json.loads(input)
        self.content = {}
        self.content["doi"] = clean_doi(data["identifier"])
        if self.content["doi"]:
            doi_url = u"https://doi.org/{}".format(self.content["doi"])
            self.content["URL"] = doi_url
        else:
            self.content["URL"] = data["codeRepository"]
        self.content["title"] = data["title"]
        self.content["author"] = []
        if "agents" in data:
            if isinstance(data["agents"], dict):
                agents = [data["agents"]]
            else:
                agents = data["agents"]
            for agent in agents:
                self.content["author"].append(author_name_as_dict(data["agents"]["name"]))
        if "dateCreated" in data:
            self.content["issued"] = {"date-parts": [[data["dateCreated"][0:4]]]}

        self.content["publisher"] = "DataCite"

        self.content["type"] = "software"

        self.content["repo"] = data["codeRepository"]
        print self.content


class GithubApiResponseMetadataStep(MetadataStep):
    def set_content(self, input_dict):
        metadata_dict = {}
        metadata_dict["title"] = input_dict["repo"].get("name", input_dict["repo"]["html_url"])
        metadata_dict["author"] = [author_name_as_dict(input_dict["user"]["name"])]
        metadata_dict["publisher"] = "GitHub repository"
        metadata_dict["URL"] = input_dict["repo"]["html_url"]
        metadata_dict["issued"] = {"date-parts": [[input_dict["repo"]["created_at"][0:4]]]}
        metadata_dict["type"] = "software"

        self.content = metadata_dict

class GithubApiResponseStep(Step):
    step_links = "https://developer.github.com/v3/repos/#get"

    @property
    def starting_children(self):
        return [
            GithubApiResponseMetadataStep
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
        # print "repo_api_url", repo_api_url
        r = requests.get(repo_api_url, auth=(login, token), headers=h)
        self.content["repo"] = r.json()

        user_api_url = "https://api.github.com/users/{}".format(self.content["repo"]["owner"]["login"])
        # print "user_api_url", user_api_url
        r = requests.get(user_api_url, auth=(login, token), headers=h)
        self.content["user"] = r.json()

        self.content_url = repo_api_url





class GithubRepoStep(Step):
    step_links = "http://github.com/"

    @property
    def starting_children(self):
        return [
                GithubCodemetaFileStep,
                GithubCitationFileStep,
                GithubReadmeFileStep,
                GithubDescriptionFileStep,
                GithubApiResponseStep
            ]

    def set_content(self, input):
        if not "github.com" in input:
            return
        if input.startswith("http"):
            url = "/".join(input.split("/", 5)[0:5])
        else:
            url = find_or_empty_string('\"(https?://github.com/.+?)\"', input)
            url = url.replace("/issues", "")
            url = url.replace("/new", "")
            if not url:
                return

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
    step_links = "http://r-pkgs.had.co.nz/description.html"

    @property
    def starting_children(self):
        return [
            GithubDescriptionMetadataStep
        ]

    def set_content(self, github_main_page_text):
        matches = re.findall(u"href=\"(.*blob/master/description.*?)\"", github_main_page_text, re.IGNORECASE)
        if matches:
            filename_part = matches[0]
            filename_part = filename_part.replace("/blob", "")
            filename = u"https://raw.githubusercontent.com{}".format(filename_part)
            self.content = get_webpage_text(filename)
            self.content_url = filename

    def set_content_url(self, input):
        # in this case set_content does it, because it knows the url
        pass

class GithubCitationFileStep(Step):
    step_links = "http://r-pkgs.had.co.nz/inst.html#inst-citation"

    @property
    def starting_children(self):
        return [
            CrossrefResponseStep,
            BibtexStep
        ]

    def set_content(self, github_main_page_text):
        matches = re.findall(u"href=\"(.*blob/master/citation.*?)\"", github_main_page_text, re.IGNORECASE)
        if matches:
            filename_part = matches[0]
            filename_part = filename_part.replace("/blob", "")
            filename = u"https://raw.githubusercontent.com{}".format(filename_part)
            self.content = get_webpage_text(filename)
            self.content_url = filename

    def set_content_url(self, input):
        # in this case set_content does it, because it knows the url
        pass


class BibtexMetadataStep(MetadataStep):
    def set_content(self, bibtex):
        bibtext_string = u"{}".format(bibtex)
        bibtext_string.replace("-", "-")
        bib_dict = BibTeX(StringIO(bibtext_string))

        id = bib_dict.keys()[0]

        if "month" in bib_dict[id]:
            del bib_dict[id]["month"]

        metadata_dict = {}
        # print "bib_dict[id].keys()", bib_dict[id].keys()
        # print "bib_dict[id].values()", bib_dict[id].values()

        for (k, v) in bib_dict[id].items():
                # print k, v
                try:
                    # if k in ["volume", "year", "type", "title", "author", "eid", "doi", "container-title", "adsnote", "eprint", "page"]:
                    # print v.values()
                    if k in ["booktitle", "address", "volume", "year", "type", "title", "author", "eid", "doi", "container-title", "adsnote", "eprint"]:
                        metadata_dict[k] = v
                    pass
                except Exception:
                    print "ERROR on ", k, v
                    pass
        # metadata_dict = dict(bib_dict[id].items())
        metadata_dict["bibtex"] = bibtex
        if hasattr(bib_dict[id], "year") and bib_dict[id]["year"]:
            metadata_dict["issued"] = {"date-parts": [[bib_dict[id]["year"]]]}
        self.content = metadata_dict



class BibtexStep(Step):
    step_links = "https://verbosus.com/bibtex-style-examples.html"

    @property
    def starting_children(self):
        return [
            BibtexMetadataStep
        ]

    def set_content(self, input):
        if not u"@" in input:
            return
        bibtex = extract_bibtex(input)
        if bibtex:
            self.content = bibtex
        else:
            my_bibtex_url = get_bibtex_url(input)
            if my_bibtex_url:
                r = requests.get(my_bibtex_url)
                self.content = extract_bibtex(r.text)
                # self.content_url = my_bibtex_url


class GithubCodemetaFileStep(Step):
    step_links = "https://codemeta.github.io/user-guide/"

    @property
    def starting_children(self):
        return [
            CodemetaResponseStep
        ]

    def set_content(self, github_main_page_text):
        matches = re.findall(u"href=\"(.*blob/master/codemeta.json)\"", github_main_page_text, re.IGNORECASE)
        if matches:
            filename_part = matches[0]
            filename_part = filename_part.replace("/blob", "")
            filename = u"https://raw.githubusercontent.com{}".format(filename_part)
            self.content = get_webpage_text(filename)
            self.content_url = filename

    def set_content_url(self, input):
        # in this case set_content does it, because it knows the url
        pass


class GithubReadmeFileStep(Step):
    step_links = "https://help.github.com/articles/about-readmes/"

    @property
    def starting_children(self):
        return [
            CrossrefResponseStep
        ]

    def set_content(self, github_main_page_text):
        matches = re.findall(u"href=\"(.*blob/master/readme.*?)\"", github_main_page_text, re.IGNORECASE)
        if matches:
            filename_part = matches[0]
            filename_part = filename_part.replace("/blob", "")
            filename = u"https://raw.githubusercontent.com{}".format(filename_part)
            self.content = get_webpage_text(filename)
            self.content_url = filename

    def set_content_url(self, input):
        # in this case set_content does it, because it knows the url
        pass


class UserInputStep(Step):
    @property
    def starting_children(self):
        return [
            CrossrefResponseStep,
            GithubRepoStep,
            CranLibraryStep,
            PypiLibraryStep,
            WebpageStep
        ]

    def set_content(self, input):
        self.content = input

    def set_content_url(self, input):
        self.content_url = input
