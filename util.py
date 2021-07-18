from html import escape
import re
import unicodedata
import urllib.parse

from nameparser import HumanName
import requests


class NoDoiException(Exception):
    pass


def clean_html(raw_html):
    cleanr = re.compile("<.*?>")
    cleantext = re.sub(cleanr, "", raw_html)
    return cleantext


def clean_doi(dirty_doi, code_meta_exists=False):
    if not dirty_doi:
        raise NoDoiException("There's no DOI at all.")

    dirty_doi = remove_nonprinting_characters(dirty_doi)
    dirty_doi = dirty_doi.strip()

    # test cases for this regex are at https://regex101.com/r/zS4hA0/1
    p = re.compile(r".*?(10.+)")

    matches = re.findall(p, dirty_doi)
    if len(matches) == 0 and code_meta_exists is True:
        return None
    elif len(matches) == 0:
        raise NoDoiException("There's no valid DOI.")

    match = matches[0]

    try:
        resp = str(match, "utf-8")  # unicode is valid in dois
    except (TypeError, UnicodeDecodeError):
        resp = match

    # remove any url fragments
    if "#" in resp:
        resp = resp.split("#")[0]

    return resp


# from http://farmdev.com/talks/unicode/
def to_unicode_or_bust(obj, encoding="utf-8"):
    if isinstance(obj, str):
        if not isinstance(obj, str):
            obj = str(obj, encoding)
    return obj


def remove_nonprinting_characters(input, encoding="utf-8"):
    input_was_unicode = True
    if isinstance(input, str):
        if not isinstance(input, str):
            input_was_unicode = False

    unicode_input = to_unicode_or_bust(input)

    # see http://www.fileformat.info/info/unicode/category/index.htm
    char_classes_to_remove = ["C", "M", "Z"]

    response = "".join(
        c
        for c in unicode_input
        if unicodedata.category(c)[0] not in char_classes_to_remove
    )

    if not input_was_unicode:
        response = response.encode(encoding)

    return response


def get_raw_bitbucket_url(url):
    s = url.split("/")
    raw_url = "https://bitbucket.org/{}/{}/raw/{}".format(s[1], s[2], "/".join(s[4:]))
    if raw_url.endswith("?at=default"):
        raw_url = raw_url[:-11]
    return raw_url


def get_all_subclasses(cls):
    all_subclasses = []

    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses


def build_source_preview(url, source_text, citation_part, citation_content):
    result = header(citation_part, url)
    source_text = escape(source_text)
    citation_content = escape(citation_content)
    source_text = trim_source_text(citation_content, source_text)
    source_text = source_text.replace(
        citation_content, '<span class="highlight">' + citation_content + "</span>", 1
    )
    result += "<br>" + source_text
    return result


def build_author_source_preview(url, source_text, citation_part, author_list):
    result = header(citation_part, url)
    source_text = trim_source_text(author_list[0]["family"], source_text)
    for author in author_list:
        if "given" in author:
            source_text = source_text.replace(
                author["given"],
                '<span class="highlight">' + author["given"] + "</span>",
                1,
            )
        if "family" in author:
            source_text = source_text.replace(
                author["family"],
                '<span class="highlight">' + author["family"] + "</span>",
                1,
            )
    result += "<br>" + source_text
    return result


def trim_source_text(citation_content, source_text):
    characters_to_display = 500
    location_index = source_text.index(citation_content)
    start = (
        0
        if location_index < characters_to_display
        else location_index - characters_to_display
    )
    source_text = source_text[start : location_index + characters_to_display]
    source_text = source_text.replace("\n", "<br />").replace("'", "")
    return source_text


def header(citation_part, url):
    return "<i>Snapshot of {} data found at {}.</i>".format(citation_part, url)


def get_hops(url):
    redirect_re = re.compile("<meta[^>]*?url=(.*?)[\"']", re.IGNORECASE)
    hops = []
    while url:
        if url in hops:
            url = None
        else:
            hops.insert(0, url)
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/50.0.2661.102 Safari/537.36"
            }
            r = requests.get(url, headers=headers)
            if r.url != url:
                hops.insert(0, r.url)
            # check for redirect meta tag
            match = redirect_re.search(r.text)
            if match:
                url = urllib.parse.urljoin(url, match.groups()[0].strip())
            else:
                url = None
    return hops


def get_webpage_text(starting_url):
    hops = get_hops(starting_url)
    try:
        url = hops[0]
        r = requests.get(url)
    except Exception:
        return
    return r.text


def author_name_as_dict(literal_name):
    if not literal_name:
        return {"family": ""}

    if len(literal_name.split(" ")) > 1:
        name_dict = HumanName(literal_name).as_dict()
        response_dict = {
            "family": name_dict["last"],
            "given": name_dict["first"],
            "suffix": name_dict["suffix"],
        }
    else:
        response_dict = {"family": literal_name}

    return response_dict


def find_or_empty_string(pattern, text):
    try:
        response = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)[0]
    except IndexError:
        response = ""
    return response


def strip_new_lines(text):
    return text.replace("\n", " ").replace("\r", "")


def get_bibtex_url(text):
    if not text:
        return None
    try:
        result = re.findall(
            "(http\"?'?[^\"']*data_type=BIBTEX[^\"']*)", text, re.MULTILINE | re.DOTALL
        )[0]
    except IndexError:
        result = None

    # vhub bibtex pattern
    try:
        result = re.findall(
            "(\/resources\/.*\/citation\?citationFormat=bibtex.*no_html=1&.*rev=\d*)",
            text,
            re.MULTILINE,
        )[0]
        result = "https://vhub.org" + result
    except IndexError:
        result = None

    return result


def extract_bibtex(text):
    valid_entry_types = [
        "article",
        "book",
        "booklet",
        "conference",
        "inbook",
        "incollection",
        "inproceedings",
        "manual",
        "mastersthesis",
        "misc",
        "phdthesis",
        "proceedings",
        "techreport",
        "unpublished",
    ]
    if not text:
        return None
    try:
        entry_type = re.findall(r"(@\w+-?\w+)", text, re.MULTILINE | re.DOTALL)[0]
        if entry_type[1:] not in valid_entry_types:
            return None
        result = re.findall(r"@\w+-?\w+{.*}", text, re.MULTILINE | re.DOTALL)[0]
    except IndexError:
        result = None
    return result
