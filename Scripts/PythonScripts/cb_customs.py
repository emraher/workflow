import re
import requests
import titlecase

# I doubt if we need to go above ten
words_to_numerals =\
    {
        'first': '1',
        'second': '2',
        'third': '3',
        'fourth': '4',
        'fifth': '5',
        'sixth': '6',
        'seventh': '7',
        'eighth': '8',
        'ninth': '9',
        'tenth': '10'
    }

# Lower case for the sake of comparison
english_identifiers =\
    {
        'american',
        'australian',
        'british',
        'canadian',
        'english',
        'newzealand',
        'ukenglish',
        'usenglish'
    }

journals_needing_article =\
    {
        'Journal of Philosophy',
        'Philosophical Quarterly',
        'Philosophical Review'
    }


def remove_outer_braces(s):
    """
    str -> str
    Remove the outermost braces from a string if it has no other braces.
    (This is a first pass at getting rid of unnecessarily protected
    biblatex fields. I would like to also strip where there are just
    internal braces as in '{This {is} a test}')
    >>> remove_outer_braces('{This is a test}')
    'This is a test'
    >>> remove_outer_braces('This is a test')
    'This is a test'
    >>> remove_outer_braces('{This} is a test')
    '{This} is a test'
    """
    if re.search('^{[^{}]*}$', s):
        s = s[1:-1]
    return s


def full_range(s):
    """ str -> str
    Take a string representing a Biblatex page range (e.g. '100--45').
    Return a string where all the units of the end are filled in.
    The range will be marked with two hyphens.
    >>> full_range('100--115')
    '100-115'
    >>> full_range('100-1000')
    '100-1000'
    >>> full_range('100-15')
    '100-115'
    >>> full_range('100-5')
    '100-105'
    """
    parts = re.split('-+', s)
    if len(parts[1]) < len(parts[0]):
        difference = len(parts[0]) - len(parts[1])
        parts[1] = parts[0][:difference] + parts[1]
    return '-'.join(parts)


def remove_resolver(doi):
    """
    str -> str
    Remove the 'http://dx.doi.org/' at the start of DOIs
    retrieved from the Crossref API.
    >>> remove_resolver('http://dx.doi.org/10.1080/00455091.2013.871111')
    '10.1080/00455091.2013.871111'
    >>> remove_resolver('10.1080/00455091.2013.871111')
    '10.1080/00455091.2013.871111'
    """
    return re.sub('http://dx.doi.org/', '', doi)


def title_name(name):
    """
    str -> str
    Take a name and return it in title case, leaving 'and' alone.
    >>> title_name('hodgson, thomas')
    'Hodgson, Thomas'
    >>> title_name('hodgson, thomas and CHOMSKY, NOAM')
    'Hodgson, Thomas and Chomsky, Noam'
    """
    name =\
        ' '.join(
            [x.title() if not re.match('and', x) else x for x in name.split()]
        )
    return name


def braces(s):
    """
    str -> str
    Take a string and enclose it in braces ('{', '}'),
    unless it already has them.
    >>> braces('foo')
    '{foo}'
    >>> braces('{foo}')
    '{foo}'
    """
    if not s.startswith('{'):
        s = '{' + s
    if not s.endswith('}'):
        s = s + '}'
    return s


def remove_series(record):
    """
    Remove Series fields.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if "series" in record:
        del record["series"]
    return record


def philpapers(record):
    """
    Put the PhilPapers ID in a field.

    This function assumes that the ID for the records is a PhilPapers ID.

    :param record: the record.
    :type record: dict
    :ret
    """
    if re.search('-', record["ID"]):
        # Split into a list at hyphens
        segments = re.split('-', record["ID"])
        # Check whether we have an ID of the form 'FOOBAR-1'
        if re.fullmatch('\d+', segments[-1]):
            ppid = '{}-{}'.format(
                segments[-2],
                segments[-1]
            )
        else:
            ppid = segments[-1]
        record["philpapers"] = ppid
    return record


def subtitles(record):
    """
    Put subtitles in.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if "journaltitle" in record and re.search(':', record["journaltitle"]):
        m = re.search(':', record["journaltitle"])
        title = record["journaltitle"][:m.start()].strip()
        subtitle = record["journaltitle"][m.end():].strip()
        record["journaltitle"] = title
        record["journalsubtitle"] = subtitle
    if "title" in record and re.search(':', record["title"]):
        m = re.search(':', record["title"])
        title = record["title"][:m.start()].strip()
        subtitle = record["title"][m.end():].strip()
        record["title"] = title
        record["subtitle"] = subtitle
    return record


def add_definite_to_journaltitles(record):
    """
    Add a definite article ('the') to titles from a specified list.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if "journaltitle" in record:
        if record["journaltitle"] in journals_needing_article:
            record["journaltitle"] = 'The ' + record["journaltitle"]
    return record


def remove_pages_from_books_and_collections(record):
    """
    Remove the 'pages' field from records with ENTRYTYPE 'incollection' or 'inbook'.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if record["ENTRYTYPE"] == "incollection" or record["ENTRYTYPE"] == "inbook":
        if "pages" in record:
            del record["pages"]
    return record


def active_quotes(record):
    """
    Replace LaTeX quotes with unicode quotes,
    defined as active characters by csquotes.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    # The regexes must be done like this to avoid balance problems
    # Match one or two '`', one or two ''', one '"', or one '“'
    # preceded by space or the start of a string
    for field in record:
        record[field] = re.sub(
            '(?:(?<=\s)|(?<=^))((`|\'){1,2}|\"|“)(?=\w)',
            '‘',
            record[field]
        )
    # Match one or two ''', one '"', or one '”'
    # followed by space or the end of a string
    for field in record:
        record[field] = re.sub(
            '(?<=\w)(\'{1,2}|\"|”)(?:(?=\s)|(?=$))',
            '’',
            record[field]
        )
    return record


def remove_protection(record):
    """
    Remove unnecessary protection.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if "title" in record:
        record["title"] = remove_outer_braces(record["title"])
    if "subtitle" in record:
        record["subtitle"] = remove_outer_braces(record["subtitle"])
    return record


def citeulike(record):
    """
    Remove CiteULike's special fields.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if "citeulike-article-id" in record:
        del record["citeulike-article-id"]
    if "priority" in record:
        del record["priority"]
    if "posted-at" in record:
        del record["posted-at"]
    return record


def empty_fields(record):
    """
    Remove empty fields.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    list_of_empty_fields = []
    for field in record:
        if record[field] == '':
            list_of_empty_fields.append(field)
    for field in list_of_empty_fields:
        del record[field]
    return record


def biblatex_page_ranges(record):
    if "pages" in record:
        # Get rid of p., pp. etc.
        record["pages"] = re.sub('[Pp]{1,2}\\.?', '', record["pages"]).strip()
        # If this is a range remove truncation and normalise it to two hyphens,
        # if not, complain
        if re.search('^\d+-+\d+$', record["pages"]):
            record["pages"] = record["pages"] = full_range(
                record["pages"]
            )
            # The function returns a single hyphen range,
            # so do the normalisation afterwards
            record["pages"] = re.sub('-+', '--', record["pages"])

        else:
            print(
                "The 'Pages' field for record {} isn't a valid biblatex range.".format(
                    record["ID"]
                )
            )
    return record


def non_page_hyphens(record):
    """
    Replace numbers of hyphens != 2 with 2.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if "volume" in record:
        record["volume"] = re.sub('-+', '--', record["volume"])
    if "number" in record:
        record["number"] = re.sub('-+', '--', record["number"])
    return record


def dashes(record):
    """
    Replace en and em dashes with hyphens.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    for field in record:
        record[field] = re.sub('–', '--', record[field])
        record[field] = re.sub('—', '---', record[field])
    return record


def remove_keyword(record):
    """
    Remove Keywords fields.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if "keywords" in record:
        del record["keywords"]
    if "keyword" in record:
        del record["keyword"]
    return record


def strip_doi(record):
    """
    Strip resolvers from DOI fields.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if "doi" in record:
        record["doi"] = remove_resolver(record["doi"])
    return record


def get_doi(record):
    """
    Get DOIs for articles from the CrossRef API.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if record["ENTRYTYPE"] == "article" and "doi" not in record:
        # Build a search term for the API
        query = ''
        # Build a query
        # The API doesn't like spaces or exotic characters
        if "title" in record:
            query += re.sub('\W+', '+', record["title"])
            if "author" in record:
                query += '+' + re.sub('\W+', '+', record["author"])
        # I need to make sure a query has been built
        if query:
            payload = {
                'query': query,
                'rows': '1',
                'sort': 'score',
                'order': 'desc'
            }
            # We might not have an internet connection
            # Catch the exception that will raise
            r = requests.get(
                'http://api.crossref.org/works',
                params=payload
            )
            print(
                'I got status code {} from the CrossRef API for record {}.'.format(
                    r.status_code,
                    record["ID"]
                )
            )
            # Proceed if the status code was a good one
            try:
                if r.status_code == requests.codes.ok:
                    # The result is JSON text
                    # Items is a list in order of match score, it will have a DOI in it
                    # Catch exception raised by any sort of problem with the response
                    try:
                        doi = r.json()['message']['items'][0]['DOI']
                        record["doi"] = doi
                    except (IndexError, KeyError):
                        print("I couldn't find a DOI in the JSON for record {}.".format(
                            record["ID"]
                            )
                        )
            # This deals with errors caused by encoding problems,
            # which are fixed anyway by having the conversion
            # to unicode done before authors are dealt with
            except UnicodeEncodeError:
                print(
                    "I couldn't get a DOI. A character in record {} wasn't encoded in a way the CrossRef API understands.".format(
                        record["ID"]
                    )
                )
    return record


def titlecase_name(record):
    """
    Put authors and editors into title case.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if "author" in record:
        record["author"] = title_name(record["author"])
    if "editor" in record:
        record["editor"] = title_name(record["editor"])
    return record


def publisher(record):
    """
    Protect 'and' in publisher field with braces around the field.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if "publisher" in record:
        if re.search('and', record["publisher"]):
            record["publisher"] = braces(record["publisher"])
    return record


def edition(record):
    """
    Put "Edition" in a nice format.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if "edition" in record:
        if record["edition"].lower().strip() in words_to_numerals:
            record["edition"] =\
                words_to_numerals[record["edition"].lower().strip()]
        elif re.search('\d+(st|nd|rd|th)', record["edition"].lower().strip()):
            record["edition"] =\
                re.sub('(st|nd|rd|th)', '', record["edition"].lower().strip())
    return record


def journaltitle(record):
    """
    Change "Journal" to "Journaltitle".

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if "journal" in record:
        record["journaltitle"] = record["journal"]
        del record["journal"]
    return record


def case_title(record):
    """
    Put titles in titlecase for English records.
    Depends on the 'titlecase' module
    https://pypi.python.org/pypi/titlecase/

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if "language" not in record or record["language"] in english_identifiers:
        if "title" in record:
            record["title"] = titlecase.titlecase(record["title"])
        if "subtitle" in record:
            record["subtitle"] = titlecase.titlecase(record["subtitle"])
        if "booktitle" in record:
            record["booktitle"] = titlecase.titlecase(record["booktitle"])
    return record


def join_author_editor(record):
    """
    Convert authors and/or editors as lists of strings
    to strings joined by "and".

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if "author" in record:
        record["author"] = " and ".join(record["author"])
    if "editor" in record:
        record["editor"] = " and ".join([d['name'] for d in record["editor"]])
    return record


def booktitle(record):
    """
    Add 'Booktitle' field identical to 'Title' field for book entries.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if record["ENTRYTYPE"] == "book":
        if "title" in record:
            record["booktitle"] = record["title"]
    return record


def remove_abstract(record):
    """
    Remove abstracts.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if "abstract" in record:
        del record["abstract"]
    return record


def remove_epub(record):
    """
    Remove epub field.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if "epub" in record:
        del record["issn"]
    return record


def remove_ISSN(record):
    """
    Remove ISSN.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if "issn" in record:
        del record["issn"]
    return record


def remove_ISBN(record):
    """
    Remove ISBNs.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if "isbn" in record:
        del record["isbn"]
    return record


def remove_copyright(record):
    """
    Remove copyright.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if "copyright" in record:
        del record["copyright"]
    return record


def language(record):
    """
    Remove listings as English.
    Make sure we have both language and langid.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if "language" in record:
        if record["language"].lower() in english_identifiers:
            del record["language"]
    if "language" in record:
        if "langid" not in record:
            record["langid"] = record["language"].lower()
        else:
            if record["language"] != record["langid"]:
                print(
                    "The 'Language' and 'Langid' fields for record {} don't match.".format(
                        record["ID"]
                    )
                )
    else:
        if "langid" in record:
            print(
                "There is a 'Langid' but no 'Language' field for record {} don't match.".format(
                    record["ID"]
                )
            )
    return record


def remove_publisher(record):
    """
    Remove publisher from articles.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if record["ENTRYTYPE"] == "article":
        if "publisher" in record:
            del record["publisher"]
    return record


def remove_link(record):
    """
    Remove links.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if "link" in record:
        del record["link"]
    return record


def remove_ampersand(record):
    """
    Convert ampersand ('&') to 'and'

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if "booktitle" in record:
        record["booktitle"] = re.sub('\\\\&', 'and', record["booktitle"])
    if "journaltitle" in record:
        record["journaltitle"] = re.sub('\\\\&', 'and', record["journaltitle"])
    if "subtitle" in record:
        record["subtitle"] = re.sub('\\\\&', 'and', record["subtitle"])
    if "title" in record:
        record["title"] = re.sub('\\\\&', 'and', record["title"])
    return record


def escape_characters(record):
    """
    Make sure that characters reserved by LaTeX are escaped.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    list_of_characters = ['&', '%', '_']
    for val in record:
        for c in list_of_characters:
            record[val] = re.sub(
                '(?<!\\\\){}'.format(c),
                '\{}'.format(c),
                record[val]
            )
    return record


def jstor(record):
    """
    Get rid of JSTOR's special fields.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if "jstor_articletype" in record:
        del record["jstor_articletype"]
    if "jstor_formatteddate" in record:
        del record["jstor_formatteddate"]
    if "jstor_issuetitle" in record:
        del record["jstor_issuetitle"]
    return record


def protect(s):
    """
    Str -> Str

    Helper function for `protect_capitalization`.
    Take a string and return a string where words containing capital letters
    (after the first word) are protected with braces.
    """
    needs_protection = re.findall('(?<=\s)\S*[A-Z]+\S*|(?<=:\s)\S+', s)
    for word in needs_protection:
        s = re.sub(word, '{{{}}}'.format(word), s)
    return s


def protect_capitalisation(record):
    """
    Protect capitalised words with braces.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if "title" in record:
        record["title"] = protect(record["title"])
    if "subtitle" in record:
        record["subtitle"] = protect(record["subtitle"])
    if "booktitle" in record:
        record["booktitle"] = protect(record["booktitle"])
    return record


def multivolume(record):
    """
    If a book or collection has a volume number,
    change its ENTRYTYPE to mvbook/mvcollection.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if record["ENTRYTYPE"] == "book":
        if "volume" in record:
            record["ENTRYTYPE"] = "mvbook"
    elif record["ENTRYTYPE"] == "collection":
        if "volume" in record:
            record["ENTRYTYPE"] = "mvcollection"
    return record


def remove_booktitle(record):
    """
    Remove 'booktitle' fields.

    :param record: the record.
    :type record: dict
    :returns: dict -- the modified record.
    """
    if "booktitle" in record:
        del record["booktitle"]
    return record
