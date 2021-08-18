import requests

from steps.core import MetadataStep, Step
from steps.crossref import CrossrefResponseStep
from steps.utils import get_webpage_text


class RelationHeaderStep(Step):
    step_links = [("What is a cite-as link relation?", "https://tools.ietf.org/html/rfc8574")]
    step_intro = "A cite-as link relation header is a special header meant to direct the user to a citation resource."

    @property
    def starting_children(self):
        return [
            CrossrefResponseStep
        ]

    def set_content(self, input):
        if self.content_url.startswith(("http://", "https://")):
            relation_link = self.check_for_rel_cite_as_header(self.content_url)
            if relation_link:
                self.content_url = relation_link
                if 'doi.org' in relation_link:
                    self.content = 'found'
                else:
                    return get_webpage_text(relation_link)

    def check_for_rel_cite_as_header(self, input):
        r = requests.get(input)

        cite_as_links = []
        if 'link' in r.headers:
            header_links = requests.utils.parse_header_links(r.headers['link'])
            for link in header_links:
                if 'rel' in link and link['rel'] == 'cite-as':
                    cite_as_links.append(link)

            if cite_as_links:
                doi_links = [link for link in cite_as_links if 'doi.org' in link['url']]
            else:
                doi_links = None

            # try to find doi links first
            if doi_links:
                self.original_url = input
                return doi_links[0]['url']
            elif cite_as_links:
                self.original_url = input
                return cite_as_links[0]['url']
            else:
                return input


class RelationResponseMetadataStep(MetadataStep):
    def set_content(self, input):
        self.content = input