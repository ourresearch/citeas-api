from io import StringIO
from HTMLParser import HTMLParser
from citeproc.source.json import CiteProcJSON
from enhanced_citation_style import EnhancedCitationStyle
from enhanced_citation_style import get_style_name
from citeproc import CitationStylesBibliography
from citeproc import formatter
from citeproc import Citation
from citeproc import CitationItem

from step import UserInputStep
from step import NoChildrenException
from step import author_name_as_dict



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


def build_bibtex_author_list(authors):
    author_list = ''
    for i, author in enumerate(authors):
        if i > 0:
            author_list += ' and '

        if author.get("family"):
            author_list += author.get("family")

        if author.get("given"):
            author_list += ', ' + author.get("given")

    return author_list


def bibtex_pages_format(pages):
    return pages.replace('-', '--')


def get_bib_source_from_dict(data):

    data["id"] = "ITEM-1"
    id = "ITEM-1"

    if "author" in data:
        data["author"] = get_author_list(data["author"])

    if not "type" in data:
        data["type"] = "misc"

    for k, val in data.iteritems():
        if val and (k in ["title", "container-title"]):
            num_upper = sum([1 for c in val if c.isupper()])
            if num_upper > 0.75*len(val):
                data[k] = val.title()

    if "page" in data and data["page"]=="-":
        del data["page"]

    if "bibtex" in data:
        del data["bibtex"]

    bib_source = CiteProcJSON([data])

    return bib_source



def display_citation(bibtex_metadata, bib_stylename, formatter=formatter.html):
    # valid style names: plos, apa, pnas, nature, bmj, harvard1
    # full list is here: https://github.com/citation-style-language/styles

    bib_style = EnhancedCitationStyle(bib_stylename)
    bibliography = CitationStylesBibliography(bib_style, bibtex_metadata, formatter) #could be formatter.html
    id = "ITEM-1"
    citation = Citation([CitationItem(id)])
    bibliography.register(citation)

    citation_parts = u"".join(bibliography.bibliography()[0])
    citation_text = u"".join(citation_parts)

    html_parser = HTMLParser()
    citation_text = html_parser.unescape(citation_text)

    return citation_text


def citations(bibtex_metadata):
    response = []
    # full list of possible citation formats is here: https://github.com/citation-style-language/styles
    for bib_stylename in ["apa", "harvard1", "nature", "modern-language-association-with-url", "chicago-author-date", "vancouver"]:
        citation_style_object = {
            "style_shortname": bib_stylename,
            "citation": display_citation(bibtex_metadata, bib_stylename),
            "style_fullname": get_style_name(bib_stylename)
        }
        response.append(citation_style_object)
    return response


def export_contents(export_type, metadata_dict):
    if export_type == "csv":
        items = metadata_dict.items()
        header_row = u",".join([name for (name, value) in items])
        try:
            value_row = u",".join([str(value) for (name, value) in items])
        except UnicodeEncodeError:
            value_row = ""
        response = u"{}\n{}".format(header_row, value_row)
        return response
    elif export_type == "ris":
        response_list = []
        response_list.append(("TY", "JOUR"))
        response_list.append(("T1", metadata_dict.get("title", "")))
        response_list.append(("JO", metadata_dict.get("container-title", "")))
        response_list.append(("VL", metadata_dict.get("volume", "")))
        response_list.append(("IS", metadata_dict.get("issue", "")))
        response_list.append(("SP", metadata_dict.get("page", "")))
        response_list.append(("V1", metadata_dict.get("year", "")))
        response_list.append(("PB", metadata_dict.get("publisher", "")))
        for author in metadata_dict.get("author", []):
            response_list.append(("A1", u", ".join([author.get("family", ""), author.get("given", "")])))
        response = u"\n".join(u"{} - {}".format(k, v) for (k, v) in response_list)
        response += "\nER - "
        return response
    elif export_type == "enw":
        response_list = []
        response_list.append(("%T", metadata_dict.get("title", "")))
        response_list.append(("%J", metadata_dict.get("container-title", "")))
        response_list.append(("%V", metadata_dict.get("volume", "")))
        response_list.append(("%N", metadata_dict.get("issue", "")))
        response_list.append(("%P", metadata_dict.get("page", "")))
        response_list.append(("%D", metadata_dict.get("year", "")))
        response_list.append(("%I", metadata_dict.get("publisher", "")))
        response_list.append(("0%", "Journal Article"))
        for author in metadata_dict.get("author", []):
            response_list.append(("%A", u", ".join([author.get("family", ""), author.get("given", "")])))
        response = u"\n".join(u"{} {}".format(k, v) for (k, v) in response_list)
        return response
    elif export_type == "bibtex":
        if metadata_dict.get("type"):
            response = "@" + metadata_dict.get("type") + "{ITEM1, "
        else:
            response = "@article{ITEM1, "

        response_list = []

        response_list.append(("title", metadata_dict.get("title", "")))

        # handle book type differently
        if metadata_dict.get("type") == "book":
            response_list.append(("isbn", metadata_dict.get("isbn", "")))
        elif metadata_dict.get("type") == "software":
            response_list.append(("url", metadata_dict.get("URL", "")))
            response_list.append(("journal", metadata_dict.get("container-title", "")))
            response_list.append(("volume", metadata_dict.get("volume", "")))
            response_list.append(("number", metadata_dict.get("number", "")))
        else:
            response_list.append(("journal", metadata_dict.get("container-title", "")))
            response_list.append(("volume", metadata_dict.get("volume", "")))
            response_list.append(("number", metadata_dict.get("number", "")))

        response_list.append(("pages", bibtex_pages_format(metadata_dict.get("page", ""))))
        response_list.append(("year", metadata_dict.get("year", "")))
        response_list.append(("publisher", metadata_dict.get("publisher", "")))
        author_list = build_bibtex_author_list(metadata_dict.get("author", []))
        response_list.append(("author", author_list))

        response += u",\n".join(u"{}={{{}}}".format(k, v) for (k, v) in response_list)
        response += "}"

        return response

    return None


def reference_manager_exports(metadata_dict):
    response = []
    for export_name in ["csv", "enw", "ris", "bibtex"]:
        export_object = {
            "export_name": export_name,
            "export": export_contents(export_name, metadata_dict)
        }
        response.append(export_object)
    return response





class Software(object):
    def __init__(self, user_supplied_id):
        self.user_supplied_id = user_supplied_id
        self.completed_steps = []


    def find_metadata(self):
        my_step = UserInputStep()
        my_step.set_content(self.user_supplied_id)
        my_step.set_content_url(self.user_supplied_id)
        self.completed_steps.append(my_step)

        cursor = 0
        while not self.completed_steps[-1].is_metadata:
            current_step = self.completed_steps[cursor]

            # print "current_step:", current_step
            try:
                # print "before adding next step, self.completed_steps:", self.completed_steps
                next_step = current_step.get_child()
                self.completed_steps.append(next_step)
                # print "after adding next step, self.completed_steps:", self.completed_steps
                # set cursor to end of stack.
                cursor = len(self.completed_steps) - 1
            except NoChildrenException:
                # print "got NoChildrenException"
                cursor -= 1

    @property
    def name(self):
        if self.metadata and self.metadata.get("title", ""):
            response = self.metadata.get("title", "")
            if response.__class__.__name__ == "MixedString":
                return response.pop()
            else:
                return response
        return self.display_url


    @property
    def display_url(self):
        return self.completed_steps[0].content_url

    @property
    def metadata(self):
        metadata_step = self.completed_steps[-1]
        if metadata_step.content.get('issued'):
            try:
                year = metadata_step.content['issued']['date-parts'][0][0]
            except IndexError:
                year = ''
            metadata_step.content['year'] = year

        metadata_dict = metadata_step.content

        for step in reversed(self.completed_steps):
            if step.url and step.content:
                metadata_dict["URL"] = step.url
                break

        return metadata_dict


    def get_provenance(self):
        ret = [s.to_dict() for s in self.completed_steps]
        return ret

    @property
    def citation_plain(self):
        citations = self.to_dict()["citations"]
        return next((i["citation"] for i in citations if i["style_shortname"] == 'harvard1'), None)

    def to_dict(self):
        bibtex_metadata = get_bib_source_from_dict(self.metadata)

        ret = {
            "url": self.display_url,
            "name": self.name,
            "citations": citations(bibtex_metadata),
            "exports": reference_manager_exports(self.metadata),
            "metadata": self.metadata,
            "provenance": self.get_provenance()
        }
        return ret
