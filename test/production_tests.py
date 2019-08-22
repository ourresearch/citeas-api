import logging
import random
import re
import requests


def main():
    """
    Retrieve a random resource and run it against the production CiteAs API.
    """
    random_resource = random.choice([
        random_cran_package(),
        random_doi(),
        random_github_url(),
        random_hacker_news_link(),
        random_software_keyword()
    ])
    logging.info(get_citeas_apa_citation(random_resource))


def get_citeas_apa_citation(resource):
    """
    Returns a dict with a resource and generated CiteAs citation in APA format.
    """
    r = requests.get('https://api.citeas.org/product/' + resource)
    citation = r.json()['citations'][0]['citation']
    return {resource: citation}


def random_cran_package():
    """
    Returns a random cran package URL.
    """
    r = requests.get('https://cran.r-project.org/web/packages/available_packages_by_name.html')
    packages = re.findall('/web/packages/(\w+.?\w+)/index.html', r.text, re.DOTALL)
    url_formats = ['CRAN.R-project.org/package={}', 'https://cran.r-project.org/web/packages/{}/index.html']
    return random.choice(url_formats).format(random.choice(packages))


def random_doi():
    """
    Returns a random DOI.
    """
    r = requests.get('https://api.crossref.org/works?sample=1')
    return r.json()['message']['items'][0]['DOI']


def random_github_url():
    """
    Returns a random URL from GitHub's trending repositories page.
    """
    r = requests.get('https://github-trending-api.now.sh/')
    trending_repos = [repo['url'] for repo in r.json()]
    return random.choice(trending_repos)


def random_hacker_news_link():
    """
    Returns a random Hacker News link from the front page stories.
    """
    r = requests.get('http://hn.algolia.com/api/v1/search?tags=front_page')
    stories = r.json()['hits']
    story_links = [story['url'] for story in stories]
    return random.choice(story_links)


def random_software_keyword():
    """
    Returns a keyword based on the top GitHub projects written in a random programming language.
    """
    programming_language = random.choice(['java', 'javascript', 'go', 'python', 'r'])
    r = requests.get(
        'https://api.github.com/search/repositories?q=language:{}&sort=stars&order=desc'.format(programming_language)
    )
    projects = r.json()['items']
    keywords = [project['name'] for project in projects]
    return random.choice(keywords)


if __name__ == "__main__":
    main()
