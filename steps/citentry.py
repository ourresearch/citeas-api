import re

from steps.core import MetadataStep, Step
from steps.utils import author_name_as_dict, find_or_empty_string


class CitentryStep(Step):
    step_links = [
        (
            "CitEntry example",
            "https://github.com/tidyverse/ggplot2/blob/master/inst/CITATION",
        )
    ]
    step_intro = (
        "CitEntry is a format for sharing reference information in CITATION files."
    )
    step_more = "CITATION files are used often in R."

    @property
    def starting_children(self):
        return [CitentryMetadataStep]

    def set_content(self, input):
        if "citEntry(" not in input:
            return

        input = input.replace("\n", "")
        # want this below to be greedy
        matches = re.findall("citEntry\((.*)\)", input, re.IGNORECASE | re.MULTILINE)
        if matches:
            self.content = matches[0]


class CitentryMetadataStep(MetadataStep):
    def set_content(self, citentry_content):
        self.content = {
            "title": find_or_empty_string('title\s*=\s*"(.*?)"', citentry_content),
            "URL": find_or_empty_string('url\s*=\s*"(.*?)"', citentry_content),
            "volume": find_or_empty_string('volume\s*=\s*"(.*?)"', citentry_content),
            "number": find_or_empty_string('number\s*=\s*"(.*?)"', citentry_content),
            "pages": find_or_empty_string('pages\s*=\s*"(.*?)"', citentry_content),
            "publisher": find_or_empty_string(
                'publisher\s*=\s*"(.*?)"', citentry_content
            ),
            "isbn": find_or_empty_string('isbn\s*=\s*"(.*?)"', citentry_content),
            "container-title": find_or_empty_string(
                'journal\s*=\s*"(.*?)"', citentry_content
            ),
            "year": find_or_empty_string('year\s*=\s*"(.*?)"', citentry_content),
        }

        if self.content["year"]:
            self.content["issued"] = {"date-parts": [[self.content["year"]]]}
        self.content["type"] = find_or_empty_string(
            'entry\s*=\s*"(.*?)"', citentry_content
        )

        self.content["author"] = []
        first_author = find_or_empty_string('author\s*=.*?"(.*?)"', citentry_content)
        if first_author:
            self.content["author"].append(author_name_as_dict(first_author))
