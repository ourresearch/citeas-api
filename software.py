import requests
import datetime
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


def get_github_path(filename, github_base_url):
    return u"{}/raw/master/{}".format(github_base_url, filename)

def get_github_file_contents(filename, github_base_url):
    response = ""
    url = get_github_path(filename, github_base_url)
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


def find_or_empty_string(pattern, text):
    try:
        response = re.findall(pattern, text)[0]
    except IndexError:
        response = ""
    return response



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

def get_author_list(data_author):
    author_list = []
    for name_dict in data_author:
        new_name_dict = {}
        for name_k, name_v in name_dict.iteritems():
            if name_k == "literal":
                new_name_dict = author_name_as_dict(name_v)
            else:
                new_name_dict[name_k] = name_v
        author_list.append(new_name_dict)
    return author_list


def get_bib_source_from_dict(data):
    data["id"] = "ITEM-1"
    id = "ITEM-1"

    if "author" in data:
        data["author"] = get_author_list(data["author"])

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





class ProvenanceStep(object):
    def __init__(self, source_type="", location="", success=None, context=""):
        self.source_type = source_type
        self.location = location
        self.success = success
        self.context = context
        self.timestamp = datetime.datetime.utcnow()


    def __repr__(self):
        return u"<ProvenanceStep ({})>".format(self.display)

    @property
    def looking_for_pronoun(self):
        if not self.source_type:
            return ""
        if self.source_type.endswith("s"):
            return "them"
        return "it"

    def to_dict(self):
        response = {
            "location": self.location,
            "source_type": self.source_type,
            "context": self.context
        }
        return response

    def display(self):
        if not self.success:
            return None

        response = u""
        if self.source_type:
            response += u"Looked for {}".format(self.source_type)

        if self.location:
            if self.location.startswith("http"):
                response += u" at {}".format(self.location)
            else:
                response += u" in {}".format(self.location)

        if self.success == True:
            response += u". Found {}!".format(self.looking_for_pronoun)
        elif self.success == False:
            response += u". Didn't find {}.".format(self.looking_for_pronoun)
        else:
            response += "."

        return response


class LastProvenanceStep(ProvenanceStep):
    def __init__(self):
        self.looking_for = None
        self.place_looking = None
        self.success = None

    def display(self):
        return u"Finished!"

class ProvenanceChain(object):
    def __init__(self):
        self.list = []

    def append(self, obj):
        self.list.append(obj)

    def display(self):
        return [obj.to_dict() for obj in self.list if obj.success]
        # return [obj.display() for obj in self.list if obj.success]





class Software(object):
    def __init__(self):
        self.url = None
        self.doi = None
        self.metadata = {}
        self.bib_source = None
        self.bibtex = None
        self.github_api_raw = None
        self.github_user_api_raw = None
        self.provenance_chain = ProvenanceChain()
        self.citation_style = "harvard1"
        self.request_url = None



    @property
    def name(self):
        if self.metadata and self.metadata.get("title", None):
            return self.metadata.get("title", None)
        return self.url

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
    def base_library_url(self):
        if u"cran.r-project.org/web/packages" in self.url:
            package_name = re.find(u"cran.r-project.org/web/packages/(.*)/?", self.url, re.IGNORECASE)
            if package_name:
                return u"http://cran.r-project.org/web/packages/{}".format(package_name)
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
            if not self.metadata:
                return
            else:
                return self.metadata["issued"]["date-parts"][0][0]
        if not self.github_api_raw:
            self.set_github_api_raw()
        return self.github_api_raw["created_at"][0:4]


    def find_doi(self):
        if self.doi:
            self.provenance_chain.append(ProvenanceStep("request parameters", self.request_url, True, "DOI"))
            return
        else:
            self.provenance_chain.append(ProvenanceStep("request parameters", self.request_url, False, "DOI"))

        if self.has_github_url:
            self.provenance_chain.append(ProvenanceStep("request parameters", self.request_url, True, "GitHub URL"))

            for filename in ["README", "README.md", "CITATION", "CITATION.md"]:
                text = get_github_file_contents(filename, self.url)
                self.doi = find_zenodo_doi(text)
                if self.doi:
                    self.provenance_chain.append(
                        ProvenanceStep("DOI found", get_github_path(filename, self.url), True, u"GitHub {} file".format(filename)))
                    return
                else:
                    self.provenance_chain.append(
                        ProvenanceStep("DOI found", get_github_path(filename, self.url), False, u"GitHub {} file".format(filename)))

        else:
            self.provenance_chain.append(ProvenanceStep("request parameters", self.request_url, False, "GitHub URL"))


    def set_metadata_from_github(self):
        self.bibtex = self.find_bibtex_request_in_github_repo()
        if not self.bibtex:
            print u"calling self.set_metadata_from_description_file()"
            self.set_metadata_from_description_file()
        if not self.bibtex and not self.metadata:
            print u"calling self.set_metadata_from_github_biblio()"
            self.set_metadata_from_github_biblio()

    def find_bibtex_request_in_github_repo(self):
        bibtex = None
        if self.has_github_url:
            for filename in ["README", "README.md", "CITATION", "CITATION.md"]:
                text = get_github_file_contents(filename, self.url)
                bibtex = extract_bibtex(text)
                if bibtex:
                    self.provenance_chain.append(
                        ProvenanceStep("bibtex metadata", get_github_path(filename, self.url), True, u"GitHub {} file".format(filename)))
                    return bibtex
                else:
                    self.provenance_chain.append(
                        ProvenanceStep("bibtex metadata", get_github_path(filename, self.url), False, u"GitHub {} file".format(filename)))

        return None

    @property
    def authors(self):
        if self.metadata and self.metadata.get("author", None):
            return self.metadata["author"]
        return {}

    def set_metadata_from_description_file(self):
        bibtex = None
        if self.has_github_url:
            text = get_github_file_contents("DESCRIPTION", self.url)

        package = find_or_empty_string(ur"Package: (.*)", text)
        title = find_or_empty_string(ur"Title: (.*)", text)
        self.metadata["title"] = u"{}: {}".format(package, title)
        person_list = re.findall(ur"person\((.*)\)", text)
        authors = []
        for person in person_list:
            section = person.replace('"', '').split(",")
            name = section[0]
            last_name = section[1].strip()
            if not last_name.startswith("role"):
                name += u" {}".format(last_name)
            authors.append(author_name_as_dict(name))
        self.metadata["author"] = authors
        self.metadata["year"] = datetime.datetime.utcnow().isoformat()[0:4]
        version = find_or_empty_string(ur"Version: (.*)", text)
        self.metadata["note"] = u"R package version {}".format(version)
        self.metadata["container-title"] = self.metadata["note"]
        self.metadata["URL"] = u"https://CRAN.R-project.org/package={}".format(package)
        self.metadata["type"] = "Manual"

        self.provenance_chain.append(
            ProvenanceStep("DESCRIPTION metadata", get_github_path("DESCRIPTION", self.url), True, u"GitHub DESCRIPTION file"))


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
        if bibtex:
            self.provenance_chain.append(ProvenanceStep(u"bibtex", self.url, True))
            self.bibtex = bibtex
        else:
            self.provenance_chain.append(ProvenanceStep(u"bibtex", self.url, False))
            my_bibtex_url = get_bibtex_url(homepage_text)
            if my_bibtex_url:
                self.provenance_chain.append(ProvenanceStep(u"Project webpage", self.url, True, "BibTex citation request"))
                r = requests.get(my_bibtex_url)
                self.bibtex = extract_bibtex(r.text)
                if self.bibtex:
                    self.provenance_chain.append(ProvenanceStep(u"bibtex", my_bibtex_url, True, "BibTex citation request"))
                else:
                    self.provenance_chain.append(ProvenanceStep(u"bibtex", my_bibtex_url, False, "BibTex citation request"))



    def set_metadata(self):
        if self.doi_url:
            print u"calling self.set_metadata_from_doi()"
            self.set_metadata_from_doi()

        elif self.has_github_url:
            self.set_metadata_from_github()

        elif self.url:
            self.set_metadata_from_homepage()

        if self.bibtex:
            print u"calling self.set_metadata_from_bibtex()"
            self.set_metadata_from_bibtex(self.bibtex)
            if self.doi_url:
                print u"calling self.set_metadata_from_doi()"
                self.set_metadata_from_doi()

        if not self.metadata:
            self.provenance_chain.append(ProvenanceStep(u"citation details", "webpage default", None))
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
        if hasattr(bib_dict[id], "year") and bib_dict[id]["year"]:
            self.metadata["issued"] = {"date-parts": [[bib_dict[id]["year"]]]}

        if "doi" in self.metadata:
            self.doi = list(self.metadata["doi"])[0]
            self.provenance_chain.append(ProvenanceStep("Bibtex", "url goes here", True, "DOI in bibtex"))
        else:
            self.provenance_chain.append(ProvenanceStep("Bibtex", "Bibtex metadata", False))

        print "*******"
        print self.metadata

    def set_metadata_from_doi(self):
        headers = {'Accept': 'application/vnd.citationstyles.csl+json'}
        r = requests.get(self.doi_url, headers=headers)
        self.metadata = r.json()
        self.provenance_chain.append(ProvenanceStep("DOI metadata", self.doi_url, True, "DOI API"))

    def set_metadata_from_github_biblio(self):
        self.metadata = {}
        self.metadata["title"] = self.repo_name
        self.metadata["author"] = [author_name_as_dict(self.owner_name)]
        self.metadata["publisher"] = "GitHub repository"
        self.metadata["URL"] = self.url
        # self.metadata["issued"] = {"date-parts": [[self.year]]}
        self.metadata["type"] = "software"
        self.provenance_chain.append(ProvenanceStep("GitHub", self.url, True, "GitHub repository metadata"))

    def find_citation(self):
        self.find_doi()
        self.set_metadata()
        self.bib_source = get_bib_source_from_dict(self.metadata)
        self.provenance_chain.append(LastProvenanceStep())

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
        for bib_stylename in ["apa", "harvard1", "nature", "modern-language-association-with-url", "chicago-author-date", "vancouver"]:
            citation_style_object = {
                "style_shortname": bib_stylename,
                "citation": self.display_citation(bib_stylename),
                "style_fullname": get_style_name(bib_stylename)
            }
            response.append(citation_style_object)
        return response

    def export(self, export_type):
        if export_type == "csv":
            items = self.metadata.items()
            header_row = u",".join([name for (name, value) in items])
            value_row = u",".join([str(value) for (name, value) in items])
            response = u"{}\n{}".format(header_row, value_row)
            return response
        elif export_type == "ris":
            response_list = []
            response_list.append(("T1", self.metadata.get("title", "")))
            response_list.append(("JO", self.metadata.get("container-title", "")))
            response_list.append(("VL", self.metadata.get("volume", "")))
            response_list.append(("IS", self.metadata.get("issue", "")))
            response_list.append(("SP", self.metadata.get("page", "")))
            response_list.append(("V1", self.year))
            response_list.append(("PB", self.metadata.get("publisher", "")))
            if self.genre == "article-journal":
                response_list.append(("TY", "JOUR"))
            for author in self.authors:
                response_list.append(("A1", u", ".join([author["family"], author.get("given", "")])))
            response = u"\n".join(u"{} {}".format(k, v) for (k, v) in response_list)
            return response
        elif export_type == "enw":
            response_list = []
            response_list.append(("%T", self.metadata.get("title", "")))
            response_list.append(("%J", self.metadata.get("container-title", "")))
            response_list.append(("%V", self.metadata.get("volume", "")))
            response_list.append(("%N", self.metadata.get("issue", "")))
            response_list.append(("%P", self.metadata.get("page", "")))
            response_list.append(("%D", self.year))
            response_list.append(("%I", self.metadata.get("publisher", "")))
            if self.genre == "article-journal":
                response_list.append(("0%", "Journal Article"))
            for author in self.authors:
                response_list.append(("%A", u", ".join([author["family"], author.get("given", "")])))
            response = u"\n".join(u"{} {}".format(k, v) for (k, v) in response_list)
            return response
        elif export_type == "bibtex":
            return """@article{piwowar2007sharing,
              title={Sharing detailed research data is associated with increased citation rate},
              author={Piwowar, Heather A and Day, Roger S and Fridsma, Douglas B},
              journal={PloS one},
              volume={2},
              number={3},
              pages={e308},
              year={2007},
              publisher={Public Library of Science}
            }
            """
        return None

    @property
    def exports(self):
        response = []
        for export_name in ["csv", "enw", "ris", "bibtex"]:
            export_object = {
                "export_name": export_name,
                "export": self.export(export_name)
            }
            response.append(export_object)
        return response

    @property
    def genre(self):
        response = "article-journal"
        if self.metadata:
            metadata_type = self.metadata.get("type", None)
            if metadata_type:
                response = metadata_type
        return response


    def __repr__(self):
        return u"<Software ({})>".format(self.url)

    def to_dict(self):
        response = {
            "url": self.display_url,
            "name": self.name,
            "doi": self.doi,
            "citations": self.citation_styles,
            "exports": self.exports,
            "metadata": self.metadata,
            "provenance": self.provenance_chain.display()
        }
        return response



