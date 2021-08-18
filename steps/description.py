import re

from steps.core import MetadataStep, Step
from steps.utils import (
    author_name_as_dict,
    build_author_source_preview,
    build_source_preview,
    find_or_empty_string,
)


class DescriptionFileStep(Step):
    step_links = [
        (
            "R DESCRIPTION file specifications",
            "http://r-pkgs.had.co.nz/description.html",
        )
    ]
    step_intro = "Software written in R often includes a source file called 'DESCRIPTION' that specifies the project's title and authors."
    step_more = (
        "The DESCRIPTION file can be parsed to extract this attribution information."
    )

    @property
    def starting_children(self):
        return [DescriptionMetadataStep]

    def set_content_url(self, input):
        self.parent_content_url = input


class DescriptionMetadataStep(MetadataStep):
    def set_content(self, text):
        metadata_dict = {}

        package = find_or_empty_string(r"Package: (.*)", text)
        title = find_or_empty_string(r"Title: (.*)", text)
        self.source_preview["title"] = build_source_preview(
            self.content_url, text, "title", title
        )
        metadata_dict["title"] = "{}: {}".format(package, title)

        metadata_dict["author"] = self.find_authors(text)
        if metadata_dict["author"] != "":
            self.source_preview["author"] = build_author_source_preview(
                self.content_url, text, "author", metadata_dict["author"]
            )

        version = find_or_empty_string(r"Version: (.*)", text)
        metadata_dict["note"] = "R package version {}".format(version)
        metadata_dict["container-title"] = metadata_dict["note"]

        published_date = find_or_empty_string(r"Date/Publication: (.*)", text)
        if published_date:
            year = published_date[0:4]
            metadata_dict["year"] = year
            metadata_dict["issued"] = {"date-parts": [[year]]}
            self.source_preview["year"] = build_source_preview(
                self.content_url, text, "year", published_date
            )

        metadata_dict["URL"] = "https://CRAN.R-project.org/package={}".format(package)
        metadata_dict["type"] = "Manual"
        self.content = metadata_dict

    def find_authors(self, text):
        try:
            authors = self.find_authors_method_1(text)
            if not authors:
                authors = self.find_authors_method_2(text)
        except IndexError:
            authors = ""
        return authors

    @staticmethod
    def find_authors_method_1(text):
        person_list = []
        given_names = re.findall('given\s?=\s?"(.*?)"', text)
        family_names = re.findall('family\s?=\s?"(.*?)"', text)
        for given_name, family_name in zip(given_names, family_names):
            person_list.append(family_name + ", " + given_name)
        if not person_list:
            person_list = re.findall("person\(\n?(.*)", text)
        role_list = re.findall("role(.*)\)", text)
        authors = []
        if role_list:
            for person, roles in zip(person_list, role_list):
                # parse name
                section = person.replace('"', "").split(",")
                name = section[0]
                last_name = section[1].strip()
                if not last_name.startswith("role"):
                    name += " {}".format(last_name)

                # parse roles
                roles = re.findall('"([^"]*)"', roles)

                # if author ('aut') or creator ('cre') then add to author list
                if "aut" in roles or "cre" in roles:
                    authors.append(author_name_as_dict(name))
        else:
            for person in person_list:
                section = person.replace('"', "").split(",")
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
                raw_authors = raw_authors.replace(role, "")

        names = raw_authors.split(",")
        if roles:
            for name, role in zip(names, roles):
                if "aut" in role or "cre" in role:
                    name = name.split("<")[0].strip()  # remove email addresses
                    authors.append(author_name_as_dict(name))
        else:
            for name in names:
                name = name.split("<")[0].strip()  # remove email addresses
                authors.append(author_name_as_dict(name))
        return authors
