import requests
import re
from HTMLParser import HTMLParser
from citeproc.source.json import CiteProcJSON
from citeproc import CitationStylesStyle, CitationStylesBibliography
from citeproc import formatter
from citeproc import Citation, CitationItem

def get_readme(github_base_url):

    # use this later
    # url = "https://github.com/{}/{}".format(
    #     owner,
    #     repo_name
    # )

    url = github_base_url
    r = requests.get(url)
    p = re.compile(
        ur'<article class="markdown-body entry-content" itemprop="text">(.+?)</article>',
        re.MULTILINE | re.DOTALL
    )
    try:
        result = re.findall(p, r.text)[0]
    except IndexError:
        result = None
    return result



def format_citation_from_metadata(data):
    for k, v in data.iteritems():
        if k=="author":
            author_list = []
            for name_dict in v:
                new_name_dict = {}
                for name_k, name_v in name_dict.iteritems():
                    if name_k == "literal":
                        new_name_dict["family"] = name_v
                    else:
                        new_name_dict[name_k] = name_v
                author_list.append(new_name_dict)
            data["author"] = author_list

    data["id"] = "ITEM-1"
    bib_source = CiteProcJSON([data])
    bib_style = CitationStylesStyle('harvard1', validate=False)
    bibliography = CitationStylesBibliography(bib_style, bib_source, formatter.html)
    citation = Citation([CitationItem('ITEM-1')])
    bibliography.register(citation)
    citation_text = u"".join(bibliography.bibliography()[0])

    html_parser = HTMLParser()
    citation_text = html_parser.unescape(u"".join(bibliography.bibliography()[0]))

    print "bib: \n{}".format(citation_text)
    return citation_text


class Software(object):
    def __init__(self):
        self.url = None
        self.doi = None
        self.metadata = {}
        self.citation = ""

    @property
    def readme_page(self):
        return self.url

    @property
    def best_citation(self):
        return "hi"

    def find_doi(self):
        if self.doi:
            return
        if self.url and "github.com" in self.url:
            readme = get_readme(self.url)
            if not readme:
                raise NotFoundException("No GitHub README found")
            if "zenodo" in readme:
                try:
                    text = readme.lower()
                    self.doi = re.findall("://zenodo.org/badge/doi/(.+?).svg", text, re.MULTILINE)[0]
                except IndexError:
                    pass

    @property
    def doi_url(self):
        if self.doi:
            return u"http://doi.org/{}".format(self.doi)

    def set_metadata(self):
        if not self.doi_url:
            return
        headers = {'Accept': 'application/rdf+xml;q=0.5, application/vnd.citationstyles.csl+json;q=1.0'}
        r = requests.get(self.doi_url, headers=headers)
        self.metadata = r.json()

    def set_citation(self):
        self.find_doi()
        self.set_metadata()
        self.citation = format_citation_from_metadata(self.metadata)


    def __repr__(self):
        return u"<Software ({})>".format(self.url)

    def to_dict(self):
        response = {
            "url": self.url,
            "doi": self.doi,
            "citation": self.citation,
            "metadata": self.metadata
        }
        return response
