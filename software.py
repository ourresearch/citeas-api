from citation import get_bib_source_from_dict, citations, reference_manager_exports
from steps.user_input import UserInputStep
from steps.exceptions import NoChildrenException


class Software(object):
    def __init__(self, user_supplied_id):
        self.user_supplied_id = user_supplied_id
        self.completed_steps = []

    def find_metadata(self):
        my_step = UserInputStep()
        my_step.set_content_url(self.user_supplied_id)
        my_step.set_content(self.user_supplied_id)
        self.completed_steps.append(my_step)

        cursor = 0
        while not self.completed_steps[-1].is_metadata:
            current_step = self.completed_steps[cursor]

            try:
                next_step = current_step.get_child()
                self.completed_steps.append(next_step)
                cursor = len(self.completed_steps) - 1
            except NoChildrenException:
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
        if metadata_step.content.get("issued"):
            try:
                year = metadata_step.content["issued"]["date-parts"][0][0]
            except IndexError:
                year = ""
            metadata_step.content["year"] = year

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
        return next(
            (i["citation"] for i in citations if i["style_shortname"] == "harvard1"),
            None,
        )

    def to_dict(self):
        bibtex_metadata = get_bib_source_from_dict(self.metadata)

        ret = {
            "url": self.display_url,
            "name": self.name,
            "citations": citations(bibtex_metadata),
            "exports": reference_manager_exports(self.metadata),
            "metadata": self.metadata,
            "provenance": self.get_provenance(),
        }
        return ret
