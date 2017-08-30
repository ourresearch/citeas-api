import requests
import re
import os
import json
from io import StringIO
from HTMLParser import HTMLParser
from citeproc.source.json import CiteProcJSON
from enhanced_citation_style import EnhancedCitationStyle
from enhanced_citation_style import get_style_name
from citeproc import CitationStylesBibliography
from citeproc import formatter
from citeproc import Citation
from citeproc import CitationItem

from bibtex import BibTeX  # use local patched version instead of citeproc.source.bibtex
from nameparser import HumanName


class NotFoundException(Exception):
    pass

def get_nonempty_contents(filename_list, github_base_url):
    for filename in filename_list:
        url = u"{}/raw/master/{}".format(github_base_url, filename)
        print "looking for filename", url
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.text
    return None

def get_concatenation(filename_list, github_base_url):
    response = ""
    for filename in filename_list:
        url = u"{}/raw/master/{}".format(github_base_url, filename)
        print u"getting {}".format(url)
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            response += u"\n{}".format(r.text)
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


def get_readme_and_citation_concat(github_base_url):
    readme = None
    readme = get_concatenation(["README", "README.md", "CITATION", "CITATION.md"], github_base_url)
    return readme


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

def get_bib_source_from_dict(data):
    data["id"] = "ITEM-1"
    id = "ITEM-1"

    if "author" in data:
        author_list = []
        for name_dict in data["author"]:
            new_name_dict = {}
            for name_k, name_v in name_dict.iteritems():
                if name_k == "literal":
                    new_name_dict = author_name_as_dict(name_v)
                else:
                    new_name_dict[name_k] = name_v
            author_list.append(new_name_dict)
        data["author"] = author_list

    if not "type" in data:
        data["type"] = "misc"

    for k, val in data.iteritems():
        if k in ["title", "container-title"]:
            num_upper = sum([1 for c in val if c.isupper()])
            if num_upper > 0.75*len(val):
                data[k] = val.title()

    if "bibtex" in data:
        del data["bibtex"]

    bib_source = CiteProcJSON([data])

    return bib_source



def find_zenodo_doi(text):
    if text and "zenodo" in text:
        try:
            text = text.lower()
            return re.findall("://zenodo.org/badge/doi/(.+?).svg", text, re.MULTILINE)[0]
        except IndexError:
            pass
    return None



class Software(object):
    def __init__(self):
        self.url = None
        self.doi = None
        self.metadata = {}
        self.bib_source = None
        self.bibtex = None
        self.github_api_raw = None
        self.github_user_api_raw = None
        self.provenance = []
        self.citation_style = "harvard1"


    @property
    def doi_url(self):
        if self.doi:
            return u"http://doi.org/{}".format(self.doi)
        return None

    @property
    def display_url(self):
        if self.url:
            return self.url
        if self.doi_url:
            return self.doi_url
        return None


    @property
    def has_github_url(self):
        return self.url and "github.com" in self.url

    @property
    def owner_login(self):
        if not self.has_github_url:
            return
        if not self.github_api_raw:
            self.set_github_api_raw()
        return self.github_api_raw["owner"]["login"]

    @property
    def owner_name(self):
        if not self.has_github_url:
            return
        if not self.github_user_api_raw:
            self.set_github_user_api_raw()
        return self.github_user_api_raw["name"]

    @property
    def repo_name(self):
        if not self.has_github_url:
            return
        if not self.github_api_raw:
            self.set_github_api_raw()
        return self.github_api_raw["name"]

    @property
    def year(self):
        if not self.has_github_url:
            return
        if not self.github_api_raw:
            self.set_github_api_raw()
        return self.github_api_raw["created_at"][0:4]


    def find_doi(self):
        if self.doi:
            return
        if self.has_github_url:
            self.provenance.append("looked for zenodo doi in github readme and citation files")
            self.doi = find_zenodo_doi(get_readme_and_citation_concat(self.url))
            if self.doi:
                self.provenance.append("... found doi.")
            else:
                self.provenance.append("... didn't find it")

    def find_citeas_request_in_github_repo(self):
        request_text = None
        if self.has_github_url:
            request_text = get_readme_and_citation_concat(self.url)
            return extract_bibtex(request_text)
        return None

    def get_github_token_tuple(self):
        tokens_str = os.environ["GITHUB_TOKENS"]
        tokens = [t.split(":") for t in tokens_str.split(",")]
        (login, token) = tokens[0]
        return (login, token)

    def set_github_api_raw(self):
        if not self.has_github_url:
            return
        api_url = self.url.replace("github.com/", "api.github.com/repos/")
        h = {"User-Agent": "CiteAs"}
        (login, token) = self.get_github_token_tuple()
        r = requests.get(api_url, auth=(login, token), headers=h)
        self.github_api_raw = r.json()

    def set_github_user_api_raw(self):
        if not self.has_github_url:
            return
        api_url = "https://api.github.com/users/{}".format(self.owner_login)
        h = {"User-Agent": "CiteAs"}
        (login, token) = self.get_github_token_tuple()
        r = requests.get(api_url, auth=(login, token), headers=h)
        self.github_user_api_raw = r.json()

    def set_metadata_from_homepage(self):
        bibtex = None
        r = requests.get(self.url)
        homepage_text = r.text
        bibtex = extract_bibtex(homepage_text)
        if not bibtex:
            if get_bibtex_url(homepage_text):
                r = requests.get(get_bibtex_url(homepage_text))
                self.bibtex = extract_bibtex(r.text)

    def set_metadata(self):
        if self.doi_url:
            print u"calling self.set_metadata_from_doi()"
            self.set_metadata_from_doi()

        elif self.has_github_url:
            self.bibtex = self.find_citeas_request_in_github_repo()
            if not self.bibtex:
                print u"calling self.set_metadata_from_github_biblio()"
                self.set_metadata_from_github_biblio()

        elif self.url:
            self.set_metadata_from_homepage()

        if self.bibtex:
            print u"calling self.set_metadata_from_bibtex()"
            self.set_metadata_from_bibtex(self.bibtex)
            if self.doi_url:
                print u"calling self.set_metadata_from_doi()"
                self.set_metadata_from_doi()

        if not self.metadata:
            self.metadata = {}
            self.metadata["type"] = "misc"
            self.metadata["URL"] = self.url


    def set_metadata_from_bibtex(self, bibtex):
        bibtext_string = u"{}".format(bibtex)
        bibtext_string.replace("-", "-")
        bib_dict = BibTeX(StringIO(bibtext_string))
        id = bib_dict.keys()[0]

        if "month" in bib_dict[id]:
            del bib_dict[id]["month"]

        self.metadata = dict(bib_dict[id].items())
        self.metadata["bibtex"] = bibtex
        if self.year:
            self.metadata["issued"] = {"date-parts": [[self.year]]}
        if "doi" in self.metadata:
            print "self.metadata[doi]", self.metadata["doi"]
            self.doi = list(self.metadata["doi"])[0]


    def set_metadata_from_doi(self):
        headers = {'Accept': 'application/vnd.citationstyles.csl+json'}
        r = requests.get(self.doi_url, headers=headers)
        self.metadata = r.json()


    def set_metadata_from_github_biblio(self):
        self.metadata = {}
        self.metadata["title"] = self.repo_name
        self.metadata["author"] = [author_name_as_dict(self.owner_name)]
        self.metadata["publisher"] = "GitHub repository"
        self.metadata["URL"] = self.url
        self.metadata["issued"] = {"date-parts": [[self.year]]}
        self.metadata["type"] = "software"


    def set_bib_source(self):
        self.find_doi()
        self.set_metadata()
        self.bib_source = get_bib_source_from_dict(self.metadata)

    @property
    def citation(self):
        return self.display_citation(self.citation_style)

    @property
    def citation_plain(self):
        return self.display_citation(self.citation_style, formatter=formatter.plain)

    def display_citation(self, bib_stylename, formatter=formatter.html):
        # valid style names: plos, apa, pnas, nature, bmj, harvard1
        # full list is here: https://github.com/citation-style-language/styles

        bib_style = EnhancedCitationStyle(bib_stylename)
        bibliography = CitationStylesBibliography(bib_style, self.bib_source, formatter) #could be formatter.html
        id = "ITEM-1"
        citation = Citation([CitationItem(id)])
        bibliography.register(citation)

        try:
            citation_parts = u"".join(bibliography.bibliography()[0])
            citation_text = u"".join(citation_parts)
        except Exception:
            print "Error parsing bibliography, so no bibliography for now"
            citation_text = str(self.bib_source["bibtex"])

        html_parser = HTMLParser()
        citation_text = html_parser.unescape(citation_text)

        return citation_text

    @property
    def citation_styles(self):
        response = []
        # full list of possible citation formats is here: https://github.com/citation-style-language/styles
        for bib_stylename in ["plos", "apa", "pnas", "nature", "bmj", "harvard1", "modern-language-association-with-url"]:
            citation_style_object = {
                "style_shortname": bib_stylename,
                "citation": self.display_citation(bib_stylename),
                "style_fullname": get_style_name(bib_stylename)
            }
            response.append(citation_style_object)
        return response

    def __repr__(self):
        return u"<Software ({})>".format(self.url)

    def to_dict(self):
        response = {
            "url": self.display_url,
            "doi": self.doi,
            "citation": self.citation_styles,
            "metadata": self.metadata,
            "provenance": self.provenance
        }
        return response



