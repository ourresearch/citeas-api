from steps.exceptions import NoChildrenException
from steps.utils import get_all_subclasses, get_subject


class Step(object):
    step_links = None
    step_intro = ""
    step_more = ""

    @classmethod
    def config_dict(cls):
        resp = {
            "name": cls.__name__,
            "step_links": cls.step_links,
            "step_intro": cls.step_intro,
            "step_more": cls.step_more,
            "subject": get_subject(cls.__name__)
        }
        return resp

    def __init__(self):
        self.remaining_children = self.starting_children
        self.url = None
        self.content_url = None
        self.additional_content_url = None
        self.content = None
        self.parent = None
        self.key_word = None
        self.source_preview = {
            'title': None
        }
        self.original_url = None

    @property
    def starting_children(self):
        return []

    # overridden for MetadataStep
    @property
    def is_metadata(self):
        return False

    def get_child(self):
        if not self.content:
            # print "no content"
            raise NoChildrenException

        if len(self.remaining_children) == 0:
            # print "no remaining_children"
            raise NoChildrenException

        child_class = self.remaining_children.pop(0)
        child_obj = child_class()
        child_obj.parent = self
        child_obj.set_content_url(self.content_url)
        child_obj.set_content(self.content)

        return child_obj

    def get_name(self):
        return self.__class__.__name__

    def set_content(self, input):
        self.content = input

    def set_content_url(self, input):
        self.content_url = input

    @property
    def found_via_proxy_type(self):
        name_lower = self.get_name().lower()
        if "metadata" in name_lower:
            return None
        if "codemeta" in name_lower:
            return None
        if "crossref" in name_lower:
            return "doi"
        if "arxiv" in name_lower:
            return "arXiv ID"
        if "userinput" in name_lower:
            return None
        if "bibtex" in name_lower:
            return None
        if "citentry" in name_lower:
            return None
        return "link"

    @property
    def host(self):
        name_lower = self.get_name().lower()
        if name_lower.startswith("github"):
            return "github"
        if name_lower.startswith("crossref"):
            return "crossref"
        if name_lower.startswith("webpage"):
            return "webpage"
        if name_lower.startswith("cran"):
            return "cran"
        if name_lower.startswith("pypi"):
            return "pypi"
        return None

    def to_dict(self):
        ret = {
            "content_url": self.content_url,
            "additional_content_url": self.additional_content_url,
            "has_content": bool(self.content),
            "name": self.get_name(),
            "host": self.host,
            "found_via_proxy_type": self.found_via_proxy_type,
            "subject": get_subject(self.get_name()),
            "parent_step_name": self.parent.__class__.__name__,
            "parent_subject": get_subject(self.parent.__class__.__name__),
            "source_preview": self.source_preview,
            "original_url": self.original_url,
            "key_word": self.key_word
        }
        return ret

    def __repr__(self):
        return "<{}>".format(self.__class__.__name__)


class MetadataStep(Step):
    @property
    def is_metadata(self):
        return True


def step_configs():
    configs = {}
    subclasses = get_all_subclasses(Step)
    for step_class in subclasses:
        if step_class.step_intro:
            configs[step_class.__name__] = step_class.config_dict()
    return configs







