import re

import requests
import requests_cache

from steps.core import MetadataStep, Step
from steps.utils import clean_doi, find_or_empty_string, get_webpage_text


class CrossrefResponseStep(Step):
    step_links = [("What is a DOI?", "https://project-thor.readme.io/docs/what-is-a-doi"), ("DOI metadata", "https://project-thor.readme.io/docs/accessing-doi-metadata")]
    step_intro = "A Digital Object Identifier (DOI) is a persistent identifier commonly used to uniquely identify scholarly papers, and increasingly used to identify datasets, software, and other research outputs."
    step_more = "A DOI is associated with all information needed to properly attribute it, including authors, title, and date of publication."

    @property
    def starting_children(self):
        return [
            CrossrefResponseMetadataStep
        ]

    def strip_junk_from_end_of_doi(self, doi):
        doi = re.sub("\s+", "", doi)
        if '">' in doi:
            doi = doi.split('">')[0]
        if "</a>" in doi:
            doi = doi.split("</a>")[0]
        doi = doi.strip(",")  # has to be first, because comma would be last item on line
        doi = doi.strip(".")  # has to be near first, because period would be last item on line
        doi = doi.strip("'")
        doi = doi.strip('"')
        doi = doi.strip("}")
        doi = clean_doi(doi).lower()
        return doi

    def extract_doi(self, text):
        if text.startswith('https://zenodo.org/record/'):
            text = get_webpage_text(text)

        badge_doi_1 = find_or_empty_string("://zenodo.org/badge/doi/(.+?).svg", text)
        if badge_doi_1:
            return self.strip_junk_from_end_of_doi(badge_doi_1)
        badge_doi_2 = find_or_empty_string("zenodo.org/badge/latestdoi/\d+", text)
        if badge_doi_2:
            text = get_webpage_text('https://' + badge_doi_2)
        zenodo_doi = find_or_empty_string("10\.5281\/zenodo\.\d+", text)
        if zenodo_doi:
            return self.strip_junk_from_end_of_doi(zenodo_doi)

        if '<html>' in text:
            text = re.sub('<[^<]+?>', '', text)  # strip html tags before searching for dois
        possible_dois = re.findall("10.\d{4,9}\/[-._;()/:A-Za-z0-9+]+", text, re.IGNORECASE|re.MULTILINE)
        for doi in possible_dois:
            if "10.5063/schema/codemeta-2.0" not in doi.lower():
                print("HERE I AM", doi)
                return self.strip_junk_from_end_of_doi(doi)

    def set_content(self, input):
        self.set_content_url(input)
        doi_url = self.content_url
        if not doi_url:
            return
        try:
            with requests_cache.disabled():
                headers = {'Accept': 'application/vnd.citationstyles.csl+json'}
                r = requests.get(doi_url, headers=headers)
                self.content = r.json()
                self.content["URL"] = doi_url
        except Exception:
            print("no doi metadata found for {}".format(doi_url))

    def set_content_url(self, input):
        has_doi = False
        if input.startswith("10."):
            has_doi = True
        elif self.content_url:
            if self.content_url.startswith("http") and "doi.org/10." in self.content_url:
                has_doi = True
                return
        elif input.startswith("http") and "doi.org/10." in input:
            has_doi = True
        else:
            # needs to be refactored at some point
            doi = self.extract_doi(input)
            if doi:
                input = doi
                has_doi = True
            elif input.startswith("http") and 'github.com' in input:
                # find zenodo badges in github repositories
                content = get_webpage_text(input)
                doi = self.extract_doi(content)
                if doi:
                    input = doi
                    has_doi = True

        if not has_doi:
            return

        try:
            doi = clean_doi(input)
        except Exception:
            print("no doi found for {}".format(input))
            return

        doi_url = "https://doi.org/{}".format(doi)
        self.content_url = doi_url


class CrossrefResponseMetadataStep(MetadataStep):
    def set_content(self, input):
        self.content = input