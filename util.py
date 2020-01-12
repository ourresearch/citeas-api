import bisect
import collections
import datetime
import logging
import math
import os
import re
import time
import unicodedata
import urlparse
from cgi import escape

import heroku
import requests
import sqlalchemy
from nameparser import HumanName
from unidecode import unidecode


class NoDoiException(Exception):
    pass


# from http://stackoverflow.com/a/3233356/596939
def update_recursive_sum(d, u):
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = update_recursive_sum(d.get(k, {}), v)
            d[k] = r
        else:
            if k in d:
                d[k] += u[k]
            else:
                d[k] = u[k]
    return d


# returns dict with values that are proportion of all values
def as_proportion(my_dict):
    if not my_dict:
        return {}
    total = sum(my_dict.values())
    resp = {}
    for k, v in my_dict.iteritems():
        resp[k] = round(float(v)/total, 2)
    return resp


def calculate_percentile(refset, value):
    if value is None:  # distinguish between that and zero
        return None

    matching_index = bisect.bisect_left(refset, value)
    percentile = float(matching_index) / len(refset)
    # print u"percentile for {} is {}".format(value, percentile)

    return percentile


def clean_html(raw_html):
  cleanr = re.compile(u'<.*?>')
  cleantext = re.sub(cleanr, u'', raw_html)
  return cleantext


# good for deduping strings.  warning: output removes spaces so isn't readable.
def normalize(text):
    response = text.lower()
    response = unidecode(unicode(response))
    response = clean_html(response)  # has to be before remove_punctuation
    response = remove_punctuation(response)
    response = re.sub(u"\s+", u"", response)
    for stop_word in ["a", "an", "the"]:
        response = response.replace(stop_word, "")
    return response


def remove_punctuation(input_string):
    # from http://stackoverflow.com/questions/265960/best-way-to-strip-punctuation-from-a-string-in-python
    no_punc = input_string
    if input_string:
        no_punc = u"".join(e for e in input_string if (e.isalnum() or e.isspace()))
    return no_punc


# from http://stackoverflow.com/a/11066579/596939
def replace_punctuation(text, sub):
    punctutation_cats = set(['Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po'])
    chars = []
    for my_char in text:
        if unicodedata.category(my_char) in punctutation_cats:
            chars.append(sub)
        else:
            chars.append(my_char)
    return u"".join(chars)


# from http://stackoverflow.com/a/22238613/596939
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError ("Type not serializable")


def conversational_number(number):
    words = {
        "1.0": "one",
        "2.0": "two",
        "3.0": "three",
        "4.0": "four",
        "5.0": "five",
        "6.0": "six",
        "7.0": "seven",
        "8.0": "eight",
        "9.0": "nine",
    }

    if number < 1:
        return round(number, 2)

    elif number < 1000:
        return int(math.floor(number))

    elif number < 1000000:
        divided = number / 1000.0
        unit = "thousand"

    else:
        divided = number / 1000000.0
        unit = "million"

    short_number = '{}'.format(round(divided, 2))[:-1]
    if short_number in words:
        short_number = words[short_number]

    return short_number + " " + unit


def safe_commit(db):
    try:
        db.session.commit()
        return True
    except (KeyboardInterrupt, SystemExit):
        # let these ones through, don't save anything to db
        raise
    except sqlalchemy.exc.DataError:
        db.session.rollback()
        print u"sqlalchemy.exc.DataError on commit.  rolling back."
    except Exception:
        db.session.rollback()
        print u"generic exception in commit.  rolling back."
        logging.exception("commit error")
    return False


def is_doi_url(url):
    # test urls at https://regex101.com/r/yX5cK0/2
    p = re.compile("https?:\/\/(?:dx.)?doi.org\/(.*)")
    matches = re.findall(p, url)
    if len(matches) > 0:
        return True
    return False


def clean_doi(dirty_doi, code_meta_exists=False):
    if not dirty_doi:
        raise NoDoiException("There's no DOI at all.")

    dirty_doi = remove_nonprinting_characters(dirty_doi)
    dirty_doi = dirty_doi.strip()

    # test cases for this regex are at https://regex101.com/r/zS4hA0/1
    p = re.compile(ur'.*?(10.+)')

    matches = re.findall(p, dirty_doi)
    if len(matches) == 0 and code_meta_exists is True:
        return None
    elif len(matches) == 0:
        raise NoDoiException("There's no valid DOI.")

    match = matches[0]

    try:
        resp = unicode(match, "utf-8")  # unicode is valid in dois
    except (TypeError, UnicodeDecodeError):
        resp = match

    # remove any url fragments
    if u"#" in resp:
        resp = resp.split(u"#")[0]

    return resp


def pick_best_url(urls):
    if not urls:
        return None

    #get a backup
    response = urls[0]

    # now go through and pick the best one
    for url in urls:
        # doi if available
        if "doi.org" in url:
            response = url

        # anything else if what we currently have is bogus
        if response == "http://www.ncbi.nlm.nih.gov/pmc/articles/PMC":
            response = url

    return response


def date_as_iso_utc(datetime_object):
    if datetime_object is None:
        return None

    date_string = u"{}{}".format(datetime_object, "+00:00")
    return date_string


def dict_from_dir(obj, keys_to_ignore=None, keys_to_show="all"):

    if keys_to_ignore is None:
        keys_to_ignore = []
    elif isinstance(keys_to_ignore, basestring):
        keys_to_ignore = [keys_to_ignore]

    ret = {}

    if keys_to_show != "all":
        for key in keys_to_show:
            ret[key] = getattr(obj, key)

        return ret

    for k in dir(obj):
        value = getattr(obj, k)

        if k.startswith("_"):
            pass
        elif k in keys_to_ignore:
            pass
        # hide sqlalchemy stuff
        elif k in ["query", "query_class", "metadata"]:
            pass
        elif callable(value):
            pass
        else:
            try:
                # convert datetime objects...generally this will fail becase
                # most things aren't datetime object.
                ret[k] = time.mktime(value.timetuple())
            except AttributeError:
                ret[k] = value
    return ret


def median(my_list):
    """
    Find the median of a list of ints

    from https://stackoverflow.com/questions/24101524/finding-median-of-list-in-python/24101655#comment37177662_24101655
    """
    my_list = sorted(my_list)
    if len(my_list) < 1:
            return None
    if len(my_list) %2 == 1:
            return my_list[((len(my_list)+1)/2)-1]
    if len(my_list) %2 == 0:
            return float(sum(my_list[(len(my_list)/2)-1:(len(my_list)/2)+1]))/2.0


def underscore_to_camelcase(value):
    words = value.split("_")
    capitalized_words = []
    for word in words:
        capitalized_words.append(word.capitalize())

    return "".join(capitalized_words)


def chunks(l, n):
    """
    Yield successive n-sized chunks from l.

    from http://stackoverflow.com/a/312464
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]


def page_query(q, page_size=1000):
    offset = 0
    while True:
        r = False
        print "util.page_query() retrieved {} things".format(page_query())
        for elem in q.limit(page_size).offset(offset):
            r = True
            yield elem
        offset += page_size
        if not r:
            break


def elapsed(since, round_places=2):
    return round(time.time() - since, round_places)


def truncate(str, max=100):
    if len(str) > max:
        return str[0:max] + u"..."
    else:
        return str


def str_to_bool(x):
    if x.lower() in ["true", "1", "yes"]:
        return True
    elif x.lower() in ["false", "0", "no"]:
        return False
    else:
        raise ValueError("This string can't be cast to a boolean.")


# from http://stackoverflow.com/a/20007730/226013
ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n/10%10!=1)*(n%10<4)*n%10::4])


#from http://farmdev.com/talks/unicode/
def to_unicode_or_bust(obj, encoding='utf-8'):
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj


def remove_nonprinting_characters(input, encoding='utf-8'):
    input_was_unicode = True
    if isinstance(input, basestring):
        if not isinstance(input, unicode):
            input_was_unicode = False

    unicode_input = to_unicode_or_bust(input)

    # see http://www.fileformat.info/info/unicode/category/index.htm
    char_classes_to_remove = ["C", "M", "Z"]

    response = u''.join(c for c in unicode_input if unicodedata.category(c)[0] not in char_classes_to_remove)

    if not input_was_unicode:
        response = response.encode(encoding)

    return response


# getting a "decoding Unicode is not supported" error in this function?
# might need to reinstall libaries as per
# http://stackoverflow.com/questions/17092849/flask-login-typeerror-decoding-unicode-is-not-supported
class HTTPMethodOverrideMiddleware(object):
    allowed_methods = frozenset([
        'GET',
        'HEAD',
        'POST',
        'DELETE',
        'PUT',
        'PATCH',
        'OPTIONS'
    ])
    bodyless_methods = frozenset(['GET', 'HEAD', 'OPTIONS', 'DELETE'])

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        method = environ.get('HTTP_X_HTTP_METHOD_OVERRIDE', '').upper()
        if method in self.allowed_methods:
            method = method.encode('ascii', 'replace')
            environ['REQUEST_METHOD'] = method
        if method in self.bodyless_methods:
            environ['CONTENT_LENGTH'] = '0'
        return self.app(environ, start_response)


def get_random_dois(n):
    url = u"http://api.crossref.org/works?filter=from-pub-date:2006-01-01&sample={}".format(n)
    r = requests.get(url)
    items = r.json()["message"]["items"]
    dois = [item["DOI"] for item in items]
    print dois


def restart_dyno(app_name, dyno_name):
    cloud = heroku.from_key(os.getenv("HEROKU_API_KEY"))
    app = cloud.apps[app_name]
    process = app.processes[dyno_name]
    process.restart()
    print u"restarted {} on {}!".format(dyno_name, app_name)


def get_raw_bitbucket_url(url):
    s = url.split('/')
    raw_url = u"https://bitbucket.org/{}/{}/raw/{}".format(s[1], s[2], '/'.join(s[4:]))
    if raw_url.endswith('?at=default'):
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
    source_text = source_text.replace(citation_content, '<span class="highlight">' + citation_content + '</span>', 1)
    result += '<br>' + source_text
    return result


def build_author_source_preview(url, source_text, citation_part, author_list):
    result = header(citation_part, url)
    source_text = trim_source_text(author_list[0]['family'], source_text)
    for author in author_list:
        if 'given' in author:
            source_text = source_text.replace(
                author['given'],
                '<span class="highlight">' + author['given'] + '</span>',
                1
            )
        if 'family' in author:
            source_text = source_text.replace(
                author['family'],
                '<span class="highlight">' + author['family'] + '</span>',
                1
            )
    result += '<br>' + source_text
    return result


def trim_source_text(citation_content, source_text):
    characters_to_display = 500
    location_index = source_text.index(citation_content)
    start = 0 if location_index < characters_to_display else location_index - characters_to_display
    source_text = source_text[start:location_index + characters_to_display]
    source_text = source_text.replace('\n', '<br />').replace('\'', '')
    return source_text


def header(citation_part, url):
    return '<i>Snapshot of {} data found at {}.</i>'.format(citation_part, url)


def get_hops(url):
    redirect_re = re.compile('<meta[^>]*?url=(.*?)["\']', re.IGNORECASE)
    hops = []
    while url:
        if url in hops:
            url = None
        else:
            hops.insert(0, url)
            r = requests.get(url)
            if r.url != url:
                hops.insert(0, r.url)
            # check for redirect meta tag
            match = redirect_re.search(r.text)
            if match:
                url = urlparse.urljoin(url, match.groups()[0].strip())
            else:
                url = None
    return hops


def get_webpage_text(starting_url):
    hops = get_hops(starting_url)
    try:
        url = hops[0]
        r = requests.get(url)
    except Exception:
        # print u"exception getting the webpage {}".format(url)
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
            "suffix": name_dict["suffix"]
        }
    else:
        response_dict = {"family": literal_name}

    return response_dict


def find_or_empty_string(pattern, text):
    try:
        response = re.findall(pattern, text, re.IGNORECASE|re.MULTILINE)[0]
    except IndexError:
        response = ""
    return response


def strip_new_lines(text):
    return text.replace("\n", " ").replace("\r", "")


def get_bibtex_url(text):
    if not text:
        return None
    try:
        result = re.findall(u'(http"?\'?[^"\']*data_type=BIBTEX[^"\']*)', text, re.MULTILINE | re.DOTALL)[0]
    except IndexError:
        result = None

    # vhub bibtex pattern
    try:
        result = re.findall(u'(\/resources\/.*\/citation\?citationFormat=bibtex.*no_html=1&.*rev=\d*)', text, re.MULTILINE)[0]
        result = 'https://vhub.org' + result
    except IndexError:
        result = None

    return result


def extract_bibtex(text):
    valid_entry_types = ['article', 'book', 'booklet', 'conference', 'inbook', 'incollection', \
                        'inproceedings', 'manual', 'mastersthesis', 'misc', 'phdthesis', 'proceedings', \
                         'techreport', 'unpublished']
    if not text:
        return None
    try:
        entry_type = re.findall(ur"(@\w+-?\w+)", text, re.MULTILINE | re.DOTALL)[0]
        myvar = entry_type[1:]
        if entry_type[1:] not in valid_entry_types:
            return None
        result = re.findall(ur"@\w+-?\w+{.*}", text, re.MULTILINE | re.DOTALL)[0]
    except IndexError:
        result = None
    return result