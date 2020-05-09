import base64
import os
import re
from io import StringIO

import json5
import requests
from arxiv2bib import arxiv2bib_dict, is_valid
from flask import abort
from googlesearch import search

from bibtex import \
    BibTeX  # use local patched version instead of citeproc.source.bibtex
from util import build_source_preview, build_author_source_preview, clean_doi, get_all_subclasses, \
    get_raw_bitbucket_url, get_webpage_text, author_name_as_dict, find_or_empty_string, strip_new_lines, get_bibtex_url, \
    extract_bibtex


def step_configs():
    configs = {}
    subclasses = get_all_subclasses(Step)
    for step_class in subclasses:
        if step_class.step_intro:
            configs[step_class.__name__] = step_class.config_dict()
    return configs


class NoChildrenException(Exception):
    pass


def get_subject(class_name):
    name_lower = class_name.lower()
    if "userinput" in name_lower:
        return "user input"
    if "readmefile" in name_lower:
        return "README file"
    if "citationfile" in name_lower:
        return "CITATION file"
    if "descriptionfile" in name_lower:
        return "R DESCRIPTION file"
    if "codemetafile" in name_lower:
        return "CodeMeta file"
    if "arxiv" in name_lower:
        return "ArXiv page"
    if "codemetaresponse" in name_lower:
        return "CodeMeta JSON data"
    if "crossref" in name_lower:
        return "DOI API response"
    if "bibtex" in name_lower:
        return "BibTeX"
    if "citentry" in name_lower:
        return "R CITATION format"
    if "githubrepo" in name_lower:
        return "GitHub repository main page"
    if "bitbucketrepo" in name_lower:
        return "Bitbucket repository main page"
    if "githubapi" in name_lower:
        return "GitHub repository API response"
    if "cran" in name_lower:
        return "R CRAN package webpage"
    if "pypi" in name_lower:
        return "Python PyPI package webpage"
    if "webpage" in name_lower:
        return "webpage"
    if "relation" in name_lower:
        return "cite-as relation header"
    return None


class Step(object):
    step_links = None
    step_intro = ""
    step_more = ""

    @classmethod
    def config_dict(cls):
        resp = {
            "name": cls.__name__,
            "step_links": cls.step_links,
            "step_intro": cls.step_intro,
            "step_more": cls.step_more,
            "subject": get_subject(cls.__name__)
        }
        return resp

    def __init__(self):
        self.remaining_children = self.starting_children
        # print "in init for {} with starting children {}, remaining children {}".format(
        #     self, self.starting_children, self.remaining_children)
        self.url = None
        self.content_url = None
        self.additional_content_url = None
        self.content = None
        self.parent = None
        self.source_preview = {
            'title': None
        }
        self.original_url = None

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
        child_obj.parent = self
        child_obj.set_content_url(self.content_url)
        child_obj.set_content(self.content)

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
        if "arxiv" in name_lower:
            return "arXiv ID"
        if "userinput" in name_lower:
            return None
        if "bibtex" in name_lower:
            return None
        if "citentry" in name_lower:
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

    def to_dict(self):
        ret = {
            "content_url": self.content_url,
            "additional_content_url": self.additional_content_url,
            "has_content": bool(self.content),
            "name": self.get_name(),
            "host": self.host,
            "found_via_proxy_type": self.found_via_proxy_type,
            "subject": get_subject(self.get_name()),
            "parent_step_name": self.parent.__class__.__name__,
            "parent_subject": get_subject(self.parent.__class__.__name__),
            "source_preview": self.source_preview,
            "original_url": self.original_url
        }
        return ret

    def __repr__(self):
        return "<{}>".format(self.__class__.__name__)


class MetadataStep(Step):
    @property
    def is_metadata(self):
        return True


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
            WebpageStep
        ]

    def set_content(self, input):
        url = self.clean_input(input)
        if "github" in url or "cran" in url.lower():
            self.content = url
        elif "readthedocs" in url:
            self.content = get_webpage_text(self.get_citation_html_file(url))
        elif "vhub" in url:
            self.content = get_webpage_text(url)
        elif url.startswith("http"):
            self.content = get_webpage_text(url)
        else:
            self.content = url

    def set_content_url(self, input):
        cleaned = self.clean_input(input)
        if cleaned.startswith("10."):
            cleaned = "http://doi.org/{}".format(cleaned)
        if cleaned.startswith("arxiv"):
            id = cleaned.split(":", 1)[1]
            cleaned = "http://arxiv.org/abs/{}".format(id)
        if cleaned.startswith("ftp://"):
            abort(404)
        if "readthedocs" in cleaned:
            cleaned = self.get_citation_html_file(cleaned)
        self.content_url = cleaned

    def clean_input(self, input):
        # doi
        if input.startswith("10."):
            return input

        # web page
        if input.startswith(("http://", "https://")):
            return input

        # arvix
        if input.lower().startswith("arxiv"):
            return input.lower()

        # arvix ID only, like 1812.02329
        r = re.compile('\d{4}.\d{5}')
        if r.match(input.lower()):
            return "arxiv:" + input.lower()

        # add http to try as a web page, then see if it returns an error
        if '.' in input:
            url = "http://{}".format(input)
        else:
            url = None

        try:
            response = requests.get(url, timeout=2)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            pass
        else:
            return url

        # google search
        # check if input is PMID
        if len(input) == 8 and input.isdigit():
            query = input
        else:
            query = '{} software citation'.format(input)
        for url in search(query, stop=1):
            return url

    @staticmethod
    def get_citation_html_file(url):
        # check for citation.html file
        r = requests.get(url + 'citation.html', timeout=2)
        if r.status_code == 200:
            return url + 'citation.html'
        u = requests.get(url + 'en/stable/citation.html', timeout=2)
        if u.status_code == 200:
            return url + 'en/stable/citation.html'
        else:
            return url


class WebpageMetadataStep(MetadataStep):
    def set_content(self, input):
        self.content = {}
        input = strip_new_lines(input)
        title = find_or_empty_string("<title.*?>(.+?)</title>", input)
        if not title:
            title = find_or_empty_string("<h1>(.+?)</h1>", input)
        if not title:
            title = find_or_empty_string("<h2>(.+?)</h2>", input)
        self.content["type"] = "misc"
        self.content["title"] = title.lstrip(" ").rstrip(" ")
        self.content["URL"] = self.content_url
        self.source_preview["title"] = build_source_preview(self.content_url, input, 'title', title)


class WebpageStep(Step):
    step_intro = "Software projects often have a project webpage."
    step_more = "This project webpage often includes attribution information like an associated DOI, GitHub repository, and/or project title."

    @property
    def starting_children(self):
        return [
            RelationHeaderStep,
            GithubRepoStep,
            BitbucketRepoStep,
            CrossrefResponseStep,
            BibtexStep,
            WebpageMetadataStep
        ]

    def set_content(self, input):
        if not input:
            self.content = get_webpage_text(self.content_url)
        else:
            self.content = input

    def set_content_url(self, input):
        self.content_url = input


class PypiLibraryStep(Step):
    step_links = [("PyPI home page", "https://pypi.python.org/pypi")]
    step_intro = "The Python Package Index (PyPI) is a repository of software for the Python programming language."
    step_more = "A project's PyPI repository page often lists useful attribution information."

    @property
    def starting_children(self):
        return [
            GithubRepoStep,
            BitbucketRepoStep,
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
    step_links = [("CRAN home page", "https://cran.r-project.org/")]
    step_intro = "The Comprehensive R Archive Network (CRAN) is a repository of software for the R programming language."
    step_more = "A project's CRAN repository page often lists useful attribution information."

    @property
    def starting_children(self):
        return [
            CranCitationFileStep,
            CranDescriptionFileStep,
            GithubRepoStep,
            BitbucketRepoStep,
            CrossrefResponseStep,
            BibtexStep
        ]

    def set_content(self, input):
        if self.content_url:
            self.content = get_webpage_text(self.content_url)

    def set_content_url(self, input):
        # print "set_content_url", input
        if input and "cran.r-project.org/web/packages" in input:
            package_name = find_or_empty_string("cran.r-project.org/web/packages/(\w+\.?\w+)/?", input)
            self.content_url = "https://cran.r-project.org/web/packages/{}".format(package_name)
        elif input and  "cran.r-project.org/package=" in input.lower():
            package_name = find_or_empty_string("cran.r-project.org/package=(.*)/?", input)
            package_name = package_name.split("/")[0]
            self.content_url = "https://cran.r-project.org/web/packages/{}".format(package_name)


class CrossrefResponseMetadataStep(MetadataStep):
    def set_content(self, input):
        self.content = input


class CrossrefResponseStep(Step):
    step_links = [("What is a DOI?", "https://project-thor.readme.io/docs/what-is-a-doi"), ("DOI metadata", "https://project-thor.readme.io/docs/accessing-doi-metadata")]
    step_intro = "A Digital Object Identifier (DOI) is a persistent identifier commonly used to uniquely identify scholarly papers, and increasingly used to identify datasets, software, and other research outputs."
    step_more = "A DOI is associated with all information needed to properly attribute it, including authors, title, and date of publication."

    @property
    def starting_children(self):
        return [
            CrossrefResponseMetadataStep
        ]

    def strip_junk_from_end_of_doi(self, doi):
        doi = re.sub("\s+", "", doi)
        if '">' in doi:
            doi = doi.split('">')[0]
        if "</a>" in doi:
            doi = doi.split("</a>")[0]
        doi = doi.strip(",")  # has to be first, because comma would be last item on line
        doi = doi.strip(".")  # has to be near first, because period would be last item on line
        doi = doi.strip("'")
        doi = doi.strip('"')
        doi = doi.strip("}")
        doi = clean_doi(doi).lower()
        return doi

    def extract_doi(self, text):
        if text.startswith('https://zenodo.org/record/'):
            text = get_webpage_text(text)

        badge_doi = find_or_empty_string("://zenodo.org/badge/doi/(.+?).svg", text)
        if badge_doi:
            return self.strip_junk_from_end_of_doi(badge_doi)
        zenodo_doi = find_or_empty_string("10.5281/zenodo\.\d+", text)
        if zenodo_doi:
            return self.strip_junk_from_end_of_doi(zenodo_doi)

        possible_dois = re.findall("10.\d{4,9}/[-._;()/:A-Z0-9+]+", text, re.IGNORECASE|re.MULTILINE)
        for doi in possible_dois:
            if "10.5063/schema/codemeta-2.0" in doi.lower():
                pass
            else:
                print("HERE I AM", doi)
                return self.strip_junk_from_end_of_doi(doi)

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
            print("no doi metadata found for {}".format(doi_url))
            pass

    def set_content_url(self, input):
        has_doi = False
        if input.startswith("10."):
            has_doi = True
        elif self.content_url:
            if self.content_url.startswith("http") and "doi.org/10." in self.content_url:
                has_doi = True
                return
        elif input.startswith("http") and "doi.org/10." in input:
            has_doi = True
        elif self.extract_doi(input):
            has_doi = True

        if not has_doi:
            return

        input = self.extract_doi(input)

        # print "has_doi", has_doi, input[0:10]

        try:
            doi = clean_doi(input)
        except Exception:
            print("no doi found for {}".format(input))
            return

        doi_url = "https://doi.org/{}".format(doi)
        self.content_url = doi_url


class ArxivResponseStep(Step):
    step_links = [("What is arXiv?", "https://arxiv.org/help/general")]
    step_intro = "ArXiv is a website that hosts research articles."
    step_more = "An arXiv paper is associated with all information needed to properly attribute it, including authors, title, and date of publication."

    @property
    def starting_children(self):
        return [
            ArxivMetadataStep
        ]

    def set_content(self, full_input):
        try:
            input = full_input.split(":", 1)[1].lower()
        except IndexError:
            return

        if not is_valid(input):
            return

        response = arxiv2bib_dict([input])
        my_reference = response[input]
        self.content = {}
        try:
            self.content["title"] = re.sub("\s+", " ", my_reference.title)
            self.content["URL"] = my_reference.url
            self.content["container-title"] = "arXiv"
            self.content["year"] = my_reference.year
            self.content["eprint"] = my_reference.id
            self.content["issued"] = {"date-parts": [[my_reference.year]]}
        except AttributeError:
            pass

        self.content["type"] = "article"

        self.content["author"] = []
        for author in my_reference.authors:
            self.content["author"].append(author_name_as_dict(author))

    def set_content_url(self, input):
        if input.startswith("arxiv:"):
            arxiv_id = input.split(":", 1)[1]
            self.content_url = "https://arxiv.org/abs/{}".format(arxiv_id)


class ArxivMetadataStep(MetadataStep):
    def set_content(self, input_dict):
        print(self.content)
        self.content = input_dict


class CodemetaResponseMetadataStep(MetadataStep):
    def set_content(self, input_dict):
        self.content = input_dict


class CodemetaResponseStep(Step):
    step_links = [("CodeMeta user guide", "https://codemeta.github.io/user-guide/")]
    step_intro = "CodeMeta is a new standard for the exchange of software metadata across repositories and organizations."
    step_more = "The CodeMeta standard has many contributors spanning research, education, and engineering domains."

    @property
    def starting_children(self):
        return [
            CodemetaResponseMetadataStep
        ]

    def set_content(self, input):
        data = json5.loads(input)
        if "citation" in data:
            data = data["citation"]
        if data:
            code_meta_exists = True
        self.content = {}

        if data.get("id"):
            self.content["doi"] = find_or_empty_string("zenodo\.org\/record\/(\d+)", data["id"])
        elif data.get("identifier"):
            self.content["doi"] = clean_doi(data["identifier"], code_meta_exists)
        else:
            self.content["doi"] = None

        if self.content["doi"]:
            doi_url = "https://doi.org/{}".format(self.content["doi"])
            self.content["URL"] = doi_url
        else:
            if "codeRepository" in data:
                self.content["URL"] = data["codeRepository"]
                self.content["repo"] = data["codeRepository"]
            elif "url" in data:
                self.content["URL"] = data["url"]
                self.content["repo"] = data["url"]

        if "name" in data:
            self.content["title"] = data["name"]

        if "title" in data:
            self.content["title"] = data["title"]

        self.content["author"] = []
        if "author" in data:
            if type(data["author"]) is dict:
                author = data["author"]
                self.content["author"].append(
                    author_name_as_dict('{} {}'.format(author["givenName"], author["familyName"])))
            elif type(data["author"]) is list:
                authors = data["author"]
                for author in authors:
                    try:
                        self.content["author"].append(
                            author_name_as_dict('{} {}'.format(author["givenName"], author["familyName"])))
                    except UnicodeEncodeError:
                        continue

        if "agents" in data:
            if isinstance(data["agents"], dict):
                agents = [data["agents"]]
            else:
                agents = data["agents"]
            for agent in agents:
                self.content["author"].append(author_name_as_dict(data["agents"]["name"]))

        if "dateCreated" in data:
            self.content["issued"] = {"date-parts": [[data["dateCreated"][0:4]]]}

        if "version" in data:
            self.content["version"] = data["version"]

        self.content["type"] = "software"


class GithubApiResponseMetadataStep(MetadataStep):
    def set_content(self, input_dict):
        metadata_dict = {}
        if "gist.github.com" in input_dict["repo"]["html_url"]:
            for key, value in input_dict["repo"]["files"].items():
                file_name = key
            metadata_dict["title"] = file_name
        else:
            metadata_dict["title"] = input_dict["repo"].get("name", input_dict["repo"]["html_url"])
        metadata_dict["author"] = [author_name_as_dict(input_dict["user"]["name"])]
        metadata_dict["publisher"] = "GitHub repository"
        metadata_dict["URL"] = input_dict["repo"]["html_url"]
        year = [[input_dict["repo"]["created_at"][0:4]]]
        metadata_dict["issued"] = {"date-parts": year}
        metadata_dict["year"] = year
        metadata_dict["type"] = "software"

        self.content = metadata_dict


class GithubApiResponseStep(Step):
    step_links = [("GITHUB API docs", "https://developer.github.com/v3/repos/#get")]
    step_intro = "GitHub is a Web-based software version control repository hosting service."
    step_more = "GitHub's API can be used to find metadata about software projects, like the project's authors, title, and created date."

    @property
    def starting_children(self):
        return [
            GithubApiResponseMetadataStep
        ]

    def set_content(self, input):
        github_url = self.content_url

        if not github_url:
            return
        if "github.com" not in github_url:
            return

        self.content = {}
        h = {"User-Agent": "CiteAs"}
        (login, token) = self.get_github_token_tuple()
        repo_api_url = self.get_repo_api_url(github_url)

        r_repo = requests.get(repo_api_url, auth=(login, token), headers=h)
        r_repo = r_repo.json()

        try:
            user_api_url = "https://api.github.com/users/{}".format(r_repo["owner"]["login"])
        except (KeyError, TypeError):
            print("bad github request")
            return

        r_login = requests.get(user_api_url, auth=(login, token), headers=h)
        self.content["repo"] = r_repo
        self.content["user"] = r_login.json()
        self.content_url = repo_api_url
        self.additional_content_url = {'url': user_api_url, 'description': 'author source'}

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
            gist_id = find_or_empty_string("gist.github.com\/\w+\/(\w+|\d+)", repo_api_url)
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


class GithubRepoStep(Step):
    step_links = [("GitHub home page", "http://github.com/")]
    step_intro = "GitHub is a Web-based software version control repository hosting service."
    step_more = "Attribution information is often included in software source code, which can be inspected for software projects that have posted their code on GitHub."

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
            if 'sphinx' and 'theme' in url or url.endswith('.zip'):
                url = None
            if not url:
                return

        self.content = get_webpage_text(url)
        self.content_url = url

    def set_content_url(self, input):
        # set in set_content
        pass


class DescriptionMetadataStep(MetadataStep):
    def set_content(self, text):
        metadata_dict = {}

        package = find_or_empty_string(r"Package: (.*)", text)
        title = find_or_empty_string(r"Title: (.*)", text)
        self.source_preview["title"] = build_source_preview(self.content_url, text, 'title', title)
        metadata_dict["title"] = "{}: {}".format(package, title)

        metadata_dict["author"] = self.find_authors(text)
        self.source_preview["author"] = build_author_source_preview(self.content_url, text, 'author', metadata_dict["author"])

        version = find_or_empty_string(r"Version: (.*)", text)
        metadata_dict["note"] = "R package version {}".format(version)
        metadata_dict["container-title"] = metadata_dict["note"]

        published_date = find_or_empty_string(r"Date/Publication: (.*)", text)
        if published_date:
            year = published_date[0:4]
            metadata_dict["year"] = year
            metadata_dict["issued"] = {"date-parts": [[year]]}
            self.source_preview["year"] = build_source_preview(self.content_url, text, 'year', published_date)

        metadata_dict["URL"] = "https://CRAN.R-project.org/package={}".format(package)
        metadata_dict["type"] = "Manual"
        self.content = metadata_dict

    def find_authors(self, text):
        authors = self.find_authors_method_1(text)
        if not authors:
            authors = self.find_authors_method_2(text)
        return authors

    @staticmethod
    def find_authors_method_1(text):
        person_list = []
        given_names = re.findall("given\s?=\s?\"(.*?)\"", text)
        family_names = re.findall("family\s?=\s?\"(.*?)\"", text)
        for given_name, family_name in zip(given_names, family_names):
            person_list.append(family_name + ", " + given_name)
        if not person_list:
            person_list = re.findall("person\(\n?(.*)", text)
        role_list = re.findall("role(.*)\)", text)
        authors = []
        if role_list:
            for person, roles in zip(person_list, role_list):
                # parse name
                section = person.replace('"', '').split(",")
                name = section[0]
                last_name = section[1].strip()
                if not last_name.startswith("role"):
                    name += " {}".format(last_name)

                # parse roles
                roles = re.findall('"([^"]*)"', roles)

                # if author ('aut') or creator ('cre') then add to author list
                if 'aut' in roles or 'cre' in roles:
                    authors.append(author_name_as_dict(name))
        else:
            for person in person_list:
                section = person.replace('"', '').split(",")
                name = section[0]
                last_name = section[1].strip()
                name += " {}".format(last_name)
                authors.append(author_name_as_dict(name))
        return authors

    @staticmethod
    def find_authors_method_2(text):
        # format 'Author: Krzysztof Byrski [aut, cre], Przemyslaw Spurek [ctb]'
        authors = []
        raw_authors = find_or_empty_string("Author: (.*)", text)
        roles = re.findall("\[\w+,?\s?\w+\,?\s?\w+]", raw_authors)
        if roles:
            for role in roles:
                raw_authors = raw_authors.replace(role, '')

        names = raw_authors.split(',')
        if roles:
            for name, role in zip(names, roles):
                if 'aut' in role or 'cre' in role:
                    name = name.split('<')[0].strip() # remove email addresses
                    authors.append(author_name_as_dict(name))
        else:
            for name in names:
                name = name.split('<')[0].strip()  # remove email addresses
                authors.append(author_name_as_dict(name))
        return authors


class DescriptionFileStep(Step):
    step_links = [("R DESCRIPTION file specifications", "http://r-pkgs.had.co.nz/description.html")]
    step_intro = "Software written in R often includes a source file called 'DESCRIPTION' that specifies the project's title and authors."
    step_more = "The DESCRIPTION file can be parsed to extract this attribution information."

    @property
    def starting_children(self):
        return [
            DescriptionMetadataStep
        ]

    def set_content_url(self, input):
        self.parent_content_url = input


class CranDescriptionFileStep(DescriptionFileStep):
    def set_content(self, input):
        filename = self.parent_content_url + '/DESCRIPTION'
        page = get_webpage_text(filename)

        self.content = page
        self.content_url = filename


class GithubDescriptionFileStep(DescriptionFileStep):
    def set_content(self, github_main_page_text):
        matches = re.findall("href=\"(.*blob/.*/description.*?)\"", github_main_page_text, re.IGNORECASE)
        if matches:
            filename_part = matches[0]
            filename_part = filename_part.replace("/blob", "")
            filename = "https://raw.githubusercontent.com{}".format(filename_part)
            self.content = get_webpage_text(filename)
            self.content_url = filename


class CitationFileStep(Step):
    step_links = [
        ("CITATION file introduction", "https://www.software.ac.uk/blog/2013-09-02-encouraging-citation-software-introducing-citation-files"),
        ("CITATION file specifications for R", "http://r-pkgs.had.co.nz/inst.html#inst-citation")
        ]
    step_intro = "Software sometimes includes a plain text file called 'CITATION' that specifies the project's title and authors, particularly software written in R."
    step_more = "The CITATION file can be parsed to extract this attribution information."

    @property
    def starting_children(self):
        if self.host == 'cran':
            return [
                BibtexStep,
                CrossrefResponseStep,
                CitentryStep
            ]
        else:
            return [
                CrossrefResponseStep,
                CitentryStep,
                BibtexStep
            ]

    def set_content_url(self, input):
        # in this case set_content does it, because it knows the url
        self.parent_content_url = input


class CranCitationFileStep(CitationFileStep):
    def set_content(self, cran_main_page_text):
        cran_citation_url = self.parent_content_url + '/citation.html'
        r = requests.get(cran_citation_url)

        if r.status_code == 200:
            self.content = r.text
            self.content_url = cran_citation_url


class GithubCitationFileStep(CitationFileStep):
    step_links = [("Citation File Format (CFF)", "https://citation-file-format.github.io/")]
    step_intro = "Software repositories sometimes includes a plain text citation file named 'CITATION' or 'CITATION.cff' " \
                 "that includes the author, software title, and other additional information."
    step_more = "The CITATION file can be parsed to extract this attribution information."

    def set_content(self, github_main_page_text):
        matches = re.findall("href=\"(.*blob/.*/citation.*?)\"", github_main_page_text, re.IGNORECASE)
        if not matches:
            matches = re.findall("href=\"(.*/inst)\"", github_main_page_text, re.IGNORECASE)
            if matches:
                inst_url = "http://github.com{}".format(matches[0])
                r = requests.get(inst_url)
                inst_page_text = r.text
                matches = re.findall("href=\"(.*blob/.*/citation.*?)\"", inst_page_text, re.IGNORECASE)

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
        api_url = 'https://api.github.com/repos{}/contents/CITATION?ref=master'.format(repo_path)
        r = requests.get(api_url)
        if r.status_code != 200:
            return None
        api_resp = r.json()
        encoded_content = api_resp.get('content')
        decoded_content = base64.b64decode(encoded_content).decode('utf-8')
        return decoded_content


class BibtexMetadataStep(MetadataStep):
    def set_content(self, bibtex):
        bibtext_string = "{}".format(bibtex)
        # bibtext_string = bibtext_string.replace("-", "-")
        bibtext_string = bibtext_string.replace("journal = {", "container-title = {")
        bib_dict = BibTeX(StringIO(bibtext_string))

        id = list(bib_dict.keys())[0]

        if "month" in bib_dict[id]:
            del bib_dict[id]["month"]

        metadata_dict = {}
        # print "bib_dict[id].keys()", bib_dict[id].keys()
        # print "bib_dict[id].values()", bib_dict[id].values()

        for (k, v) in list(bib_dict[id].items()):
                # print k, v
                try:
                    # if k in ["volume", "year", "type", "title", "author", "eid", "doi", "container-title", "adsnote", "eprint", "page"]:
                    # print v.values()
                    # if k in ["booktitle", "address", "volume", "year", "type", "title", "author", "eid", "doi", "container-title", "adsnote", "eprint"]:
                    if k in ["url", "note", "journal", "booktitle", "address", "volume", "issue", "number", "type", "title", "eid", "container-title", "adsnote", "eprint", "pages", "author", "year"]:
                        metadata_dict[k] = v
                except Exception:
                    print("ERROR on ", k, v)
                    pass
        # metadata_dict = dict(bib_dict[id].items())
        metadata_dict["bibtex"] = bibtex

        # uppercase and include doi
        doi = bib_dict[id].get("doi")
        if doi and doi.strip():
            metadata_dict["DOI"] = bib_dict[id]["doi"]
            metadata_dict["url"] = "http://doi.org/{}".format(bib_dict[id]["doi"])

        # clean it up to get rid of {} around it, etc
        year_raw = str(metadata_dict['year'])
        year_matches = re.findall('(\d{4})', year_raw)
        if year_matches:
            year = int(year_matches[0])
            metadata_dict["issued"] = {"date-parts": [[str(year)]]}
            metadata_dict["year"] = str(year)

        if "note" in metadata_dict:
            metadata_dict["container-title"] = metadata_dict["note"]

        if "url" in metadata_dict:
            metadata_dict["URL"] = metadata_dict["url"]
        metadata_dict["type"] = "Manual"

        self.content = metadata_dict


class BibtexStep(Step):
    step_links = [("BibTeX examples", "https://verbosus.com/bibtex-style-examples.html")]
    step_intro = "BibTeX is a format for sharing reference information."
    step_more = "BibTeX evolved from LaTeX and is frequently used in the physics and math communities."

    @property
    def starting_children(self):
        return [
            BibtexMetadataStep
        ]

    def set_content(self, input):
        # if u"@font-face" in input:
        #     return
        bibtex = extract_bibtex(input)
        if bibtex:
            self.content = bibtex
        else:
            my_bibtex_url = get_bibtex_url(input)
            if my_bibtex_url:
                r = requests.get(my_bibtex_url)
                if my_bibtex_url.startswith('https://vhub.org'):
                    self.content = r.text
                    self.content_url = my_bibtex_url.replace('amp;', '')
                else:
                    self.content = extract_bibtex(r.text)


class CitentryStep(Step):
    step_links = [("CitEntry example", "https://github.com/tidyverse/ggplot2/blob/master/inst/CITATION")]
    step_intro = "CitEntry is a format for sharing reference information in CITATION files."
    step_more = "CITATION files are used often in R."

    @property
    def starting_children(self):
        return [
            CitentryMetadataStep
        ]

    def set_content(self, input):
        if not "citEntry(" in input:
            return

        input = input.replace("\n", "")
        # want this below to be greedy
        matches = re.findall("citEntry\((.*)\)", input, re.IGNORECASE | re.MULTILINE)
        if matches:
            self.content = matches[0]


class CitentryMetadataStep(MetadataStep):
    def set_content(self, citentry_content):
        self.content = {}
        self.content["title"] = find_or_empty_string("title\s*=\s*\"(.*?)\"", citentry_content)
        self.content["URL"] = find_or_empty_string("url\s*=\s*\"(.*?)\"", citentry_content)
        self.content["volume"] = find_or_empty_string("volume\s*=\s*\"(.*?)\"", citentry_content)
        self.content["number"] = find_or_empty_string("number\s*=\s*\"(.*?)\"", citentry_content)
        self.content["pages"] = find_or_empty_string("pages\s*=\s*\"(.*?)\"", citentry_content)
        self.content["publisher"] = find_or_empty_string("publisher\s*=\s*\"(.*?)\"", citentry_content)
        self.content["isbn"] = find_or_empty_string("isbn\s*=\s*\"(.*?)\"", citentry_content)
        self.content["container-title"] = find_or_empty_string("journal\s*=\s*\"(.*?)\"", citentry_content)

        self.content["year"] = find_or_empty_string("year\s*=\s*\"(.*?)\"", citentry_content)
        if self.content["year"]:
            self.content["issued"] = {"date-parts": [[self.content["year"]]]}
        self.content["type"] = find_or_empty_string("entry\s*=\s*\"(.*?)\"", citentry_content)

        self.content["author"] = []
        first_author = find_or_empty_string("author\s*=.*?\"(.*?)\"", citentry_content)
        if first_author:
            self.content["author"].append(author_name_as_dict(first_author))


class GithubCodemetaFileStep(Step):
    step_links = [("CodeMeta user guide", "https://codemeta.github.io/user-guide/")]
    step_intro = "CodeMeta is a new standard for the exchange of software metadata across repositories and organizations."
    step_more = "The CodeMeta standard has many contributors spanning research, education, and engineering domains."

    @property
    def starting_children(self):
        return [
            CrossrefResponseStep,
            CodemetaResponseStep
        ]

    def set_content(self, github_main_page_text):
        matches = re.findall("href=\"(.*blob/.*/codemeta.json)\"", github_main_page_text, re.IGNORECASE)
        if matches:
            filename_part = matches[0]
            filename_part = filename_part.replace("/blob", "")
            filename = "https://raw.githubusercontent.com{}".format(filename_part)
            self.content = get_webpage_text(filename)
            self.content_url = filename

        # get content from description

    def set_content_url(self, input):
        # in this case set_content does it, because it knows the url
        pass


class GithubReadmeFileStep(Step):
    step_links = [("README description", "https://help.github.com/articles/about-readmes/")]
    step_intro = "A README file contains information about other files in a directory or archive of computer software."
    step_more = "README files often contain requests for attribution."

    @property
    def starting_children(self):
        return [
            CrossrefResponseStep
        ]

    def set_content(self, github_main_page_text):
        matches = re.findall("href=\"(.*blob/.*/readme.*?)\"", github_main_page_text, re.IGNORECASE)
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
        dependencies = find_or_empty_string('# Dependencies #(.+)#?.+#?', readme_text)
        readme_text = readme_text.replace(dependencies, '')
        return readme_text


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
        if not "bitbucket.org" in input:
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
        found_match = False
        matches = re.findall('href=\"(.*\/citation.*?)\"', bitbucket_main_page_text, re.IGNORECASE)

        if matches:
            filename_part = matches[0]
            filename = get_raw_bitbucket_url(filename_part)

            self.content = get_webpage_text(filename)
            self.content_url = filename


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


class BitbucketDescriptionFileStep(CitationFileStep):
    def set_content(self, bitbucket_main_page_text):
        found_match = False
        matches = re.findall('href=\"(.*\/description.*?)\"', bitbucket_main_page_text, re.IGNORECASE)

        if matches:
            filename_part = matches[0]
            filename = get_raw_bitbucket_url(filename_part)

            self.content = get_webpage_text(filename)
            self.content_url = filename


class RelationResponseMetadataStep(MetadataStep):
    def set_content(self, input):
        self.content = input


class RelationHeaderStep(Step):
    step_links = [("What is a cite-as link relation?", "https://tools.ietf.org/html/rfc8574")]
    step_intro = "A cite-as link relation header is a special header meant to direct the user to a citation resource."

    @property
    def starting_children(self):
        return [
            CrossrefResponseStep
        ]

    def set_content(self, input):
        if self.content_url.startswith(("http://", "https://")):
            relation_link = self.check_for_rel_cite_as_header(self.content_url)
            if relation_link:
                self.content_url = relation_link
                if 'doi.org' in relation_link:
                    self.content = 'found'
                else:
                    return get_webpage_text(relation_link)

    def check_for_rel_cite_as_header(self, input):
        r = requests.get(input)

        if 'link' in r.headers:
            header_links = requests.utils.parse_header_links(r.headers['link'])
            cite_as_links = [link for link in header_links if link['rel'] == 'cite-as']

            if cite_as_links:
                doi_links = [link for link in cite_as_links if 'doi.org' in link['url']]
            else:
                doi_links = None

            # try to find doi links first
            if doi_links:
                self.original_url = input
                return doi_links[0]['url']
            elif cite_as_links:
                self.original_url = input
                return cite_as_links[0]['url']
            else:
                return input