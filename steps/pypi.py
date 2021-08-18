from steps.bibtex import BibtexStep
from steps.bitbucket import BitbucketRepoStep
from steps.core import Step
from steps.crossref import CrossrefResponseStep
from steps.github import GithubRepoStep
from steps.utils import get_webpage_text


class PypiLibraryStep(Step):
    step_links = [("PyPI home page", "https://pypi.python.org/pypi")]
    step_intro = "The Python Package Index (PyPI) is a repository of software for the Python programming language."
    step_more = (
        "A project's PyPI repository page often lists useful attribution information."
    )

    @property
    def starting_children(self):
        return [GithubRepoStep, BitbucketRepoStep, CrossrefResponseStep, BibtexStep]

    def set_content(self, input):
        self.set_content_url(input)
        if self.content_url:
            page = get_webpage_text(self.content_url)
            # get rid of the header because it has pypi specific stuff, not stuff about the library
            # makes it hard to get github links out for the library
            # see for example https://pypi.python.org/pypi/executor
            if '<div id="content-body">' in page:
                page = page.split('<div id="content-body">')[1]
            self.content = page

    def set_content_url(self, input):
        if not input.startswith("http"):
            return

        if "pypi.python.org/pypi" in input or "readthedocs.org" in input:
            self.content_url = input
