import re

from arxiv2bib import arxiv2bib_dict, is_valid

from steps.core import MetadataStep, Step
from steps.utils import author_name_as_dict


class ArxivResponseStep(Step):
    step_links = [("What is arXiv?", "https://arxiv.org/help/general")]
    step_intro = "ArXiv is a website that hosts research articles."
    step_more = "An arXiv paper is associated with all information needed to properly attribute it, including authors, title, and date of publication."

    @property
    def starting_children(self):
        return [
            ArxivMetadataStep
        ]

    def set_content(self, input):
        arxiv_id = self.extract_arxiv(input)
        if arxiv_id:
            self.set_content_url(arxiv_id)
            input = arxiv_id

        try:
            input = input.split(":", 1)[1].lower()
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
        if self.extract_arxiv(input):
            print('found arxiv')
            return self.extract_arxiv(input)

        if input.startswith("http://arxiv:"):
            arxiv_id = input.split(":", 1)[1]
            self.content_url = "https://arxiv.org/abs/{}".format(arxiv_id)

    def extract_arxiv(self, text):
        possible_arxiv_ids = re.findall("arXiv:\d{4}.\d{4,5}", text, re.IGNORECASE|re.MULTILINE)
        for arxiv_id in possible_arxiv_ids:
            return arxiv_id


class ArxivMetadataStep(MetadataStep):
    def set_content(self, input_dict):
        print(self.content)
        self.content = input_dict