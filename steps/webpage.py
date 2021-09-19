from steps.arxiv import ArxivResponseStep
from steps.bibtex import BibtexStep
from steps.bitbucket import BitbucketRepoStep
from steps.core import MetadataStep, Step
from steps.crossref import CrossrefResponseStep
from steps.github import GithubRepoStep
from steps.pmid import PMIDStep
from steps.relation_header import RelationHeaderStep
from steps.utils import (
    build_source_preview,
    find_or_empty_string,
    get_webpage_text,
    strip_new_lines,
)


class WebpageStep(Step):
    step_intro = "Software projects often have a project webpage."
    step_more = "This project webpage often includes attribution information like an associated DOI, GitHub repository, and/or project title."

    @property
    def starting_children(self):
        return [
            RelationHeaderStep,
            CrossrefResponseStep,
            PMIDStep,
            ArxivResponseStep,
            GithubRepoStep,
            BitbucketRepoStep,
            BibtexStep,
            WebpageMetadataStep,
        ]

    def set_content(self, input):
        self.content = get_webpage_text(self.content_url)

    def set_content_url(self, input):
        self.content_url = input


class WebpageMetadataStep(MetadataStep):
    def set_content(self, input):
        self.content = {}
        input = strip_new_lines(input)
        title = find_or_empty_string("<title.*?>(.+?)</title>", input)
        if not title:
            title = find_or_empty_string("<h1>(.+?)</h1>", input)
        if not title:
            title = find_or_empty_string("<h2>(.+?)</h2>", input)
        self.content["type"] = "misc"
        self.content["title"] = title.lstrip(" ").rstrip(" ")
        self.content["URL"] = self.content_url
        self.source_preview["title"] = build_source_preview(
            self.content_url, input, "title", title
        )
