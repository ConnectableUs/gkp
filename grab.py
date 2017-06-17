#!/usr/bin/env python

import vcr
import requests
from hashlib import sha1
from bs4 import BeautifulSoup

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

    return soup.body


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
    import os
    from tinydb import TinyDB
    
    db = TinyDB('Keep.json')
    table = db.table('notes')
    
    hbreak = lambda i: i.name in ('br',)
    for root, dirs, files in os.walk('./Takeout/Keep/'):
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
                elif hbreak(i) or i.strip():  # TODO - multi-nls? i.strip()?
                    # every entry a list;
                    note_dict[key].append('\n' if hbreak(i) else i)
                    # insert tag collection here:
                    # if key not in ('heading', 'labels'):
                    #     pat.finall(i.text)
                    #     ... use sets, and set update (union) to avoid dup-tags
                # next element    
                i = i.next
            # save the note_dict into a storage - list, or db;
            table.insert(note_dict)
    db.close()

                
