from io import StringIO
import re

import requests

from bibtex import \
    BibTeX  # use local patched version instead of citeproc.source.bibtex
from steps.core import MetadataStep, Step
from steps.utils import extract_bibtex, get_bibtex_url


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


class BibtexMetadataStep(MetadataStep):
    def set_content(self, bibtex):
        bibtext_string = "{}".format(bibtex)
        bibtext_string = bibtext_string.replace("journal = {", "container-title = {")
        bibtext_string = bibtext_string.replace("\\url", "url")
        bib_dict = BibTeX(StringIO(bibtext_string))

        id = list(bib_dict.keys())[0]

        if "month" in bib_dict[id]:
            del bib_dict[id]["month"]

        metadata_dict = {}

        for (k, v) in list(bib_dict[id].items()):
            try:
                if k in ["url", "note", "journal", "booktitle", "address", "volume", "issue", "number", "type", "title", "eid", "container-title", "adsnote", "eprint", "pages", "author", "year"]:
                    metadata_dict[k] = v
            except Exception:
                print("ERROR on ", k, v)
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