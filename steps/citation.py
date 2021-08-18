from steps.bibtex import BibtexStep
from steps.citentry import CitentryStep
from steps.crossref import CrossrefResponseStep
from steps.core import Step


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
