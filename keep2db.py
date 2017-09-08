#!/usr/bin/env python

#import vcr
import os
import re
# from hashlib import sha1
from bs4 import BeautifulSoup
from tinydb import TinyDB, Query
from tinydb.operations import delete

import magic  # pip import python-magic

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
    Note = Query()

    # grab default table
    # ... except this doesn't work the I expect:
    # ... default_table doesn't do squat in opening the db
    notes = db.table(notes_name)
    archives = db.table(archives_name)

    # TODO: parameterize the path name (I think no default - force passing one)
    W = 0  # print width
    for root, dirs, files in os.walk(walk_path):
        for filename in files:
            # we're printing filename progress on one line;
            # - use the max filename width,
            #   with at least 3*'.' on each side of filename
            W = max(W, len(filename)+6)
            print(f'{filename:.^{W}}', end='\r')
            # check for type of file - can have image files from keep:
            fn = os.path.join(root,filename)
            f_type = magic.from_file(fn, mime=True)
            # OLD:   if soup is None:
            # TODO:
            # if 'image' in f_type:
                #  need to do _something_ with image files,
                #   which can be in keep-output
            if 'xml' not in f_type:
                print(f'{fn} does not appear to be an html file;')
                continue

            soup = grab(fn, file=True)
            # for Takeout, this seems to work:
            note = soup.next
            assert len(note['class'])>0 and note['class'][0] == 'note', \
                   f'{filename} does not appear to be a note!'

            # turns out "filename" selection is too random;  they could
            #   have made a "key" but... not in their radar;
            # NO! =>  note_dict = {'filename': filename}
            note_dict = {}
            key = 'unknown'
            # set ensures no dup tags per note

            # embbeded image from a twitter link caused trouble;
            #  - don't need to worry about it, as it's just a
            #    preview, but leaving this in for any future glitch;
            #  - it took a while for this one to crop up.
            '''
            if filename.startswith('Our experience'):
                import pdb; pdb.set_trace()
            '''

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
                elif hbreak(i) or ( isinstance(i, str) and i.strip() ):
                    # every entry a list;
                    ## BUG: TODO:  this is breaking / replicating w/ the update
                    ##    paradigm;  need to fix this before using...
                    ##  TODO:  ??? maybe not "get" existing, until after we've
                    ##    completed this, and then just "diff" the lists?
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
                elif not isinstance(i, str):  # empty strings skipped above;
                    # unexpected element - skipping; warning:
                    print(f'>>> unexpected element {i.name} in {filename}; skipping;')
                    #print(f'   >>> {i}')
                # next element
                i = i.next
            # save the note_dict into a storage - list, or db;

            if 'tags' in note_dict:
                # sets are not JSON serializable:
                note_dict['tags'] = list(note_dict['tags'])
                # to avoid order-related changes to this table element:
                note_dict['tags'].sort()

            # after parsing a file, see if there's an
            #   existing item to update
            #   (not before - it doesn't work)

            # if already in a table, then note which one
            note_table = None  # default
            # TODO:  here, filename can not be part of DB;
            #
            #  We have to approach identifying elements in a differnt
            #  way.  It seems the following are perhaps the most
            #  identifying (in decreasing order, with notes):
            #  ---- if these exist, consider them matching even tho title can change
            #  - 'title'    ; doesn't always exist
            #  - 'heading'  ; a timestamp, but almost useless,
            #               ; as it's possible to have 300 of same!!!
            #  ---- a mojority match on these is probably most can hope for:
            #  - 'labels'
            #  - 'tags'
            #  - 'content'
            #  ---- this is probably the limit of reasonable tests
            #  - 'attachments'
            #  - 'bullet'    ; usually empty, or checklist checked
            #  - 'text'      ; appears to be text to go w/ bullet
            #  - 'listitem'  ; not sure what these are

            # Keep drilling down until we find one Element:
            if 'title' in note_dict:
                this_query = (Note.title == note_dict['title'])
            if 'heading' in note_dict:
                this_query = this_query & (Note.heading == note_dict['heading'])

            iter=0
            nomatch = 0

            while True:
                iter += 1
                n = notes.count(this_query)
                m = archives.count(this_query)
                print(f'notes matched: {n}, archiveds matched: {m}')

                if n == 0 and m == 0:
                    note_table = None
                    break
                elif n == 1:
                    # found note to update
                    note_table = notes
                    note_elem = notes.get(this_query)
                    break
                elif m == 1:
                    # found archive to update
                    note_elem = archives.get(this_query)
                    note_table = archives
                    break
                elif n > 0 and m == 0:  # most likely case
                    # need to narrow from notes  # probably need to check for containment
                    if iter == 1:
                        if 'labels' in note_dict:
                            this_query = this_query & (Note.labels == note_dict['labels'])
                        # iterate; then
                        if 'tags' in note_dict:
                            this_query = this_query & (Note.tags == note_dict['tags'])
                    elif iter == 2:
                        if 'content' in note_dict:
                            this_query = this_query & (Note.content.all(note_dict['content']))
                    else:
                        nomatch += 1
                        break

                #elif n == 0 and m > 0:  # less likely case
                #    # need to narrow from archives
                #    pass
                else:  # unlikely case of found in both tables
                    # need to narrow from both
                    # put in a pdb trigger here, for development:
                    import pdb
                    pdb.set_trace()


            # TODO: delete this block:
            '''
            if notes.contains(Note.filename == filename):
                # Note: if multiple Elements w/ filename, this
                #  silently gets only a possibly random one:
                note_elem = notes.get(Note.filename == filename)
                note_table = notes
            elif archives.contains(Note.filename == filename):
                note_elem = archives.get(Note.filename == filename)
                note_table = archives
            '''

            def n_update(table_, old_, new_):
                ''' table_: the tinydb table (or db)
                    old_:   the existing element
                    new_:   a dict containing new content

                Before calling n_update():
                    Fetch existing db element, if there is one;
                    if it exists, then call n_update()
                Then:
                    - compare old & new records
                    - if different, call n_update(), which:
                        - take a set difference of the keys;
                        - if keys dropped, delete them
                        - update rest of eid w/ new record
                '''

                # database element and dict will compare ok:
                # update only if changed:
                if old_ != new_:
                    table_.update(new_, eids=[old_.eid])
                    # check for dropped keys; delete as necessary
                    for i in set(old_) - set(new_):
                        table_.update(delete(i), eids=[old_.eid])


            # If possible, update, else insert these.
            if 'archived' in note_dict:
                if note_table is archives:
                    n_update(archives, note_elem, note_dict)
                else:
                    archives.insert(note_dict)
                    if note_table is notes:
                        # element moving between tables
                        notes.remove(eids=[note_elem.eid])
            else:
                if note_table is notes:
                    n_update(notes, note_elem, note_dict)
                else:  # note_table is None:
                    notes.insert(note_dict)

    # add a newline, as filenames are just progress-spit on one line, above:
    print(f"\n{len(notes)} notes...")
    print(f"{len(archives)} archived notes...")
    print(f"{nomatch} over-matched note updates...")
    db.close()
