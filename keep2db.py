#!/usr/bin/env python

#import vcr
import os
import re
import requests
# from hashlib import sha1
from bs4 import BeautifulSoup
from tinydb import TinyDB, Query

def grab(html, file=False,  update=False, dev=None):
    '''
    grab a url and save it locally w/ vcr;
    html - either url or filename
    file - if true, loads a text html from file
           and renders the remaining options inactive;
    update = True; use vcrpy record_mode "all",
          to update the cassette; only valid
          if file=False; -- makes no sense for this use,
          since repo is all local; OBSOLETE
    dev - develop: save an uncompressed text
          copy if results, with the url, to
          the text file named in 'dev' argument.
    '''
    # I'll try to "be smart" about this; let's see how it works:
    file_name = html.lower()
    if not file and not file_name.startswith(('http://','https://')):
        file = True
    if file:
        with open(html) as f:
            soup = BeautifulSoup(f.read(), "html.parser")
    # for current use, this is really only for file-based parsing;
    else:
        print("Error: vcr not supported")
        exit(1)

    # if you want to test a bit more:
    if dev:  # save this, so you can develop a script
        with open(dev, 'w') as f:
            f.write(html+'\n\n')
            f.write(soup.__repr__()+'\n')

    return soup.body


# TODO:
# - I want to make this both TinyDB active
#   (it's nice to just load from the json into a REPL
#    but do I really need TinyDB for that?)
# - And pony.orm (since it does JSON types on backends which
#   doesn't support it - e.g. sqllite), with flask-ponywoosh query/search
#   (I think sqlalchemy w/ postgres, and flask-appbuilder might have
#    worked, but seemed more to learn to get it going)
# - I might possibly eventually also get this working with
#   some version of Redis, possibly thru the walrus query stuff,
#   which also supports the golang storage w/ redis api;
# - I probably want some functions to keep this all in one place;
# - I may (?) also want to checkout google-api to access directly,
#   eventually;
##
# But here's the thing:  with "searchnotes", this is fully useful
#  in a ipython repl - for search and save out to a yaml.  So the
#  above TODOs may not be of any real merit.  We'll see.

if __name__ == "__main__":
    # DEV:
    # TODO: parameterize the db filename, but keep a default:
    # TODO: as it stands now, wonder if tinydb is of any utility;
    # MAYBE: parameterize default_table, but leave it a default:
    db_name = 'keep-db/Keep.json'
    notes_name = 'notes'
    archives_name = 'archives'
    walk_path = './Takeout/Keep/'
    newlines = '\n'  # only want to strip newlines from output
    ## instead, use explicit char ranges, and add '-', so
    #    hyphenated tags are caught as one (e.g. 'speak-self')
    #tag_pat = re.compile(r'(#\w+)')
    tag_pat = re.compile(r'(#[a-zA-Z0-9_-]+)')
    hbreak = lambda i: i.name in ('br',)

    # TinyDB passes all but "storage" arguments on to json.dump(),
    #  so we're using indent here to "pretty-print" the output
    #  so that git versioning of the db's works;
    db = TinyDB(db_name, indent=2)
    # grab default table
    # ... except this doesn't work the I expect:
    # ... default_table doesn't do squat in opening the db
    notes = db.table(notes_name)
    archives = db.table(archives_name)

    # TODO: parameterize the path name (I think no default - force passing one)
    for root, dirs, files in os.walk(walk_path):
        for filename in files:
            print(f'{filename}...')
            soup = grab(os.path.join(root,filename), file=True)
            if soup is None:
                print(f'{os.path.join(root, filename)} does not appear to be an html file;')
                continue
            # for Takeout, this seems to work:
            note = soup.next
            assert len(note['class'])>0 and note['class'][0] == 'note', \
                   f'{filename} does not appear to be a note!'

            note_dict = {}
            key = 'unknown'
            i = note.next
            while i:
                # process here
                # if not isinstance(i, str) and not hbreak(i):
                if i.name in ('div', 'span',):
                    key = i['class'][0]
                    # I think I'll special-case this for now:
                    if key == 'label':
                        key = 'labels'
                    if key not in note_dict:
                        note_dict[key] = []
                # save no empty lines, unless an explicit <br/>:
                elif hbreak(i) or i.strip():
                    # every entry a list;
                    note_dict[key].append('' if hbreak(i) else i.strip(newlines))
                    ## tag collection: we're in a string, so do it here
                    # places to skip looking for hashtags
                    # - don't search empty strings, <brk/>, or
                    #   the things which are timestamps, or already tag-like
                    if i and not hbreak(i) \
                       and key not in ('archive','heading','labels'):
                        assert isinstance(i, str), \
                            f"i: [{i}] is type {type(i)}; str needed"
                        tags = tag_pat.findall(i)
                        if tags:
                            # set ensures no dup tags per note
                            if 'tags' not in note_dict:
                                note_dict['tags'] = set()
                            note_dict['tags'].update(tags)

                # next element
                i = i.next
            # save the note_dict into a storage - list, or db;
            if 'tags' in note_dict:
                # sets are not JSON serializable:
                note_dict['tags'] = list(note_dict['tags'])
            if 'archived' in note_dict:
                archives.insert(note_dict)
            else:
                notes.insert(note_dict)

    print(f"{len(notes)} notes...")
    print(f"{len(archives)} archived notes...")
    db.close()

