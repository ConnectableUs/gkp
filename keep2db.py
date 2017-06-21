#!/usr/bin/env python

#import vcr
import requests
from hashlib import sha1
from bs4 import BeautifulSoup
import os
from tinydb import TinyDB, Query
from tinydb.database import Table as dbTable
'''
OBSOLETE:
from yamlstorage import YAMLStorage
'''

# by default, this is for grabbing twitter threads,
#  which are otherwise impossible to print!
def grab(html, file=False,  update=False, dev=None):
    '''
    grab a url and save it locally w/ vcr;
    html - either url or filename
    file - if true, loads a text html from file
           and renders the remaining options inactive;
    update = True; use vcrpy record_mode "all",
          to update the cassette; only valid
          if file=False;
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
    else:
        print("Error: vcr not supported")
        exit(1)
        '''
        vcr_settings = {
            'cassette_library_dir': 'vcr_cassettes'
        }
        if update:
            vcr_settings.update({'record_mode':'all'})
        my_vcr = vcr.VCR(**vcr_settings)

        # need bytestring for hashlib routines;
        burl = sha1(bytearray(html, 'utf8'))
        # name the vcr saved file w/ hexdigest of url
        hd = burl.hexdigest()  # for yaml filename
        with my_vcr.use_cassette(f'{hd}.yaml'):
            soup = BeautifulSoup(requests.get(html).text, "html.parser")

        # if you want to test a bit more:
        if dev:  # save this, so you can develop a script
            with open(dev, 'w') as f:
                f.write(html+'\n\n')
                f.write(soup.__repr__()+'\n')
        '''

    return soup.body


"""
OBSOLETE:
## USE commandline tool json2yaml instead (much faster, simpler)
def save2yaml(search_results, file_name, default_table='google_keep'):
    # TinyDB Query search results return a list of Elements
    with TinyDB(file_name, default_table=default_table, storage=YAMLStorage) as db:
        notes = db.table(default_table)
        json2yaml(search_results, notes)
        # on exit, this should write and close the output YAML db;


## USE commandline tool json2yaml instead (much faster, simpler)
def json2yaml(jtab, ytab,
              stripset={'archived','title','content','heading'} ):
    '''
    jtab:  either a TinyDB table, or search result (list of db Elements)
    ytab:  the receiving (probably empty) dbTable of a YAMLStorage type
           (nothing enforces this, so this is really just a table-copy)
    TinyDB:
        json tables are about 500x faster loading,
           so useful for querying;
        yaml talbes in block style are conducive
           to browsing w/ an editor, looking, inspection

    Use this to create a yaml.
    - create a TinyDB table instance you want to convert from;
    - create a TinyDB yaml table instance you want to convert to;
      (suggest a clean file, or at least a clean table)

    - if you care to strip() strings in any of the note entries,
      pass a set or tuple of keys to strip (str or list of str's);
      a useful default is included, but - after seeing these in yaml,
      I now strip these at soup parsing;

    RETURNS:
        nothing: if succeeded, you should close the TinyDBs as appropriate

    E.g.:
        >>> db2 = TinyDB("foo.yaml", storage=YAMLStorage)
        >>> ytab = db2.table('keep_notes')
        >>> json2yaml(jtab, ytab)  # adds to the yaml DB file
    '''
    # if you look over the jtab.all() generator,
    #   tinyDB will just save a single item, after iterating
    #   over them all;  will need to look into this later;
    #   - it might just be something I need to update in
    #     class YAMLStorage
    notes = jtab.all() if isinstance(jtab, dbTable) else jtab
    if stripset:
        for note in notes:
            for i in stripset:
                # if we want to remove whitespace from this group:
                if i in note:
                    d = note[i]
                    if isinstance(d, list):
                        # use enumerate to change
                        #  the original list, which is a ref
                        for k,v in enumerate(d):
                            d[k] = v.strip()
                    else:
                        d = d.strip()

    #remove any dbElement cruft, let new indecies be created:
    ytab.insert_multiple([dict(i) for i in notes])
"""



# TODO:
# - I want to make this both TinyDB active
#   (it's too nice to just load from the json into a REPL)
# - And pony.orm (since it does JSON types on backends which
#   doen't support it - e.g. sqllite), with flask-ponywoosh query/search
#   (I think sqlalchemy w/ postgres, and flask-appbuilder might have
#    worked, but seemed more to learn to get it going)
# - I might possibly eventually also get this working with
#   some version of Redis, possibly thru the walrus query stuff,
#   which also supports the golang storage w/ redis api;
# - I probably want some functions to keep this all in one place;
# - I may (?) also want to checkout google-api to access directly,
#   eventually;
if __name__ == "__main__":
    #DEV:
    '''
    --- ok, this works for a single Keep record; now:
    TODO:
        - loop through every file in the Keep directory;
        - store to TinyDB
          >>> from tinydb import TinyDB, Query
          inserting each note should work fine.
          >>> db = TinyDB('filename.json')
          at each "note" (Keep file) read, insert:
          >>> db.insert(note_dict)
          its saved as you go, so simple as:
          >>> db.close()
        - add processing and separately saving hashtags
          >>> pat = re.compile(r'(#\w+)')
          >>> pat.findall(some_string)  # returns list of tags
    '''

    # TODO: parameterize the db filename, but keep a default:
    # MAYBE: parameterize default_table, but leave it a default:
    db_name = 'Keep.json'
    default_table = 'notes'
    walk_path = './Takeout/Keep/'
    newlines = '\n'  # only want to strip newlines from output
    tag_pat = re.compile(r'(#\w+)')
    hbreak = lambda i: i.name in ('br',)

    db = TinyDB(db_name, default_table=default_table)  # could just set default_table here;
    # grab default table
    table = db.table()

    # TODO: parameterize the path name (I think no default - force passing one)
    for root, dirs, files in os.walk(walk_path):
        for filename in files:
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
                    if key not in ('archive', heading', 'labels'):
                        tags = tag_pat.findall(i)
                        if tags:
                            if 'tags' not in note_dict:
                                note_dict['tags'] = set()
                            note_dict['tags'].update(tags)

                # next element
                i = i.next
            # save the note_dict into a storage - list, or db;
            table.insert(note_dict)
    db.close()


