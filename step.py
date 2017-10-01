import requests
import re


class NoChildrenException(Exception):
    pass




class Step(object):
    def __init__(self):
        self.children = []
        self.url = None
        self.content = None
        self.more_info = None


    def get_child(self):
        if not self.content:
            raise NoChildrenException

        if not self.children:
            raise NoChildrenException

        child_obj = self.children.pop()
        child_obj.set_content(self.content)
        return child_obj


    def get_name(self):
        return self.__class__.__name__

    def set_content(self, input):
        pass


    def to_dict(self):
        ret = {
            "url": self.url,
            "has_content": bool(self.content),
            "name": self.get_name(),
            "more_info": self.more_info
        }
        return ret









class UserInputStep(Step):
    def __init__(self):
        self.children = [
            # children here
        ]
        super(self.__class__, self).__init__()




class GithubRepoStep(Step):
    def __init__(self):
        self.children = [
            GithubDescriptionFileStep(),
            GithubCitationFileStep(),
            GithubReadmeFileStep()
            # metadataStep here later
        ]
        super(self.__class__, self).__init__()



class GithubDescriptionFileStep(Step):
    pass


class GithubCitationFileStep(Step):
    pass


class GithubReadmeFileStep(Step):
    pass


