#!/usr/bin/env python3

import argparse
import re
import shutil
import sys

import cb_customs

from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.customization import *


def fix_keys(l):
    """ list -> list
    Take a list that represents lines.
    Find lines which are the start of a bibtex entry without a key.
    Add dummy keys to those lines.
    Remove spaces from keys.
    >>> fix_keys(
        ['@book{foo bar,', '@article{', '    Author = {Thomas Hodgson}', '}']
    )
    ['@book{foobar,', '@article{Foo1,', '    Author = {Thomas Hodgson}', '}']
    """
    i = 1
    j = 0
    while j < len(l):
        if re.fullmatch('@\\w+\\s*{,{0,1}', l[j].strip()):
            l[j] = l[j][:l[j].find('{')+1] + 'Foo' + str(i) + ','
            i += 1
        elif re.match('@', l[j].strip()):
            # Find where the key starts
            start = re.search('{', l[j]).end()
            # Get rid of any non word characters
            key = re.sub('\W+', '', l[j][start:])
            # Put it back together; add a comma which will have been removed
            l[j] = l[j][:start] + key + ','
        j += 1
    return l


def customizations(record):
    """Use some functions delivered by the library

    :param record: a record
    :returns: -- customized record
    """
    # This needs to come before authors are dealt with
    # otherwise there are encoding problems
    record = convert_to_unicode(record)
    record = author(record)
    record = editor(record)
    # This is needed after `author` is called to allow writing
    record = cb_customs.join_author_editor(record)
    record = cb_customs.titlecase_name(record)
    record = cb_customs.remove_booktitle(record)
    record = cb_customs.language(record)
    record = cb_customs.case_title(record)
    record = cb_customs.journaltitle(record)
    # This should come after `journaltitle`is called
    record = cb_customs.add_definite_to_journaltitles(record)
    record = cb_customs.remove_pages_from_books_and_collections(record)
    record = cb_customs.non_page_hyphens(record)
    record = cb_customs.dashes(record)
    record = cb_customs.biblatex_page_ranges(record)
    record = cb_customs.remove_abstract(record)
    record = cb_customs.remove_ISBN(record)
    record = cb_customs.remove_ISSN(record)
    record = cb_customs.remove_epub(record)
    record = cb_customs.remove_copyright(record)
    record = cb_customs.remove_publisher(record)
    record = cb_customs.remove_link(record)
    record = cb_customs.escape_characters(record)
    record = cb_customs.remove_ampersand(record)
    record = cb_customs.jstor(record)
    record = cb_customs.citeulike(record)
    record = cb_customs.edition(record)
    record = cb_customs.multivolume(record)
    record = cb_customs.publisher(record)
    record = cb_customs.strip_doi(record)
    record = cb_customs.remove_keyword(record)
    record = cb_customs.empty_fields(record)
    record = cb_customs.remove_protection(record)
    record = cb_customs.active_quotes(record)
    record = cb_customs.subtitles(record)
    record = cb_customs.remove_series(record)
    if not args.nodoi:
        try:
            record = cb_customs.get_doi(record)
        # If there is a connection error stop trying to get DOIs
        except cb_customs.requests.exceptions.ConnectionError:
            if args.verbose:
                print(
                    "I couldn't connect to the CrossRef API. "
                    "Perhaps you are not connected to the internet?"
                )
            args.nodoi = True
    return record

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input',
        help='Path to the input file'
    )
    parser.add_argument(
        '--no-doi',
        dest='nodoi',
        action='store_true',
        help="Don't look for DOIs from CrossRef"
    )
    parser.add_argument(
        '--verbose',
        dest='verbose',
        action='store_true',
        help="Print messages"
    )
    args = parser.parse_args()
    if args.input:
        bib = args.input
        try:
            shutil.copy(bib, bib + '.backup')
            if args.verbose:
                print(
                    "I have made a backup of the orignal file at {}.backup"
                    .format(bib)
                )
            with open(bib, 'r', encoding='utf-8') as biblatex:
                content = biblatex.read()
        except FileNotFoundError:
            if args.verbose:
                print("I couldn't find the file {}.".format(bib))
            sys.exit()
    else:
        content = sys.stdin.read()
    # Find the start of the first record
    try:
        start = re.search('@', content).start()
    except AttributeError:
        if args.verbose:
            print("The file I was given didn't contain any records.")
        sys.exit()
    content = content[start:].split('\n')
    # Provide dummy citekeys
    content = fix_keys(content)
    fixed_content = '\n'.join(content)
    bibliography = BibTexParser(
        fixed_content,
        customization=customizations,
        ignore_nonstandard_types=False
        # Otherwise bibtexparser will complain if I give it a collection
    )
    output = BibTexWriter().write(bibliography)
    if args.input:
        with open(bib, 'w', encoding='utf-8') as biblatex:
            biblatex.write(output)
    else:
        sys.stdout.write(output)
