import json5

from steps.core import MetadataStep, Step
from steps.utils import author_name_as_dict, clean_doi, find_or_empty_string


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
