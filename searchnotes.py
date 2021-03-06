# coding: utf-8
import re
import yaml
from tinydb import TinyDB, Query


# load parsed notes into something to search for:
# TinyDB passes all but "storage" arguments on to json.dump(),
#  so we're using indent here to "pretty-print" the output
#  so that git versioning works;
db = TinyDB('keep-db/Keep.json', indent=2)
dbnotes = db.table('notes')
dbarchive = db.table('archived')
# - this doesn't work as I'd want
#   res = table.search(Note.title.any(['Summit']))
# - so this is to make search look through all note text

# This is not necessary anymore, but is left here for
#  examples of forms you can sent to findnotes(),
#  which will taks a string, or tuple w/ re-string/re-flags
#  and either a table, or a list, or a generator for the
#  list of notes (thus you can narrow searches)
## make it a python form, so we can use it
# get rid of db.Element cruft (e.g. record numbering):
# - could make it a generator, for memory skimpiness
#   but that is ill-suited to interactive use

notes = [dict(n) for n in dbnotes]
# example:
myre = (r'summit', re.I)


def findnotes(myre, notes, fields=set(), inversion="!"):
    '''
    myre:  regular expression to search for;
           can be search-string, or tuple w/ (string, RE-flags, such as re.I)
           note: you can also pass RE-flags at stort of string (e.g.: "(?i)this")
           See 'special characters' under
           https://docs.python.org/3/library/re.html#regular-expression-syntax;
           note: special to this function:  re starting with "!" will cause
           a search negation (like grep -v);
    notes: a generator or list of notes, or a list of tinydb table.Elements
    fields: fields to search (searches all if empty)
    inversion: set alternate lead string to signify search inversion;
               this is stripped before re-compile.
    '''
    from types import GeneratorType

    # check for search inversion:
    flags = []
    if isinstance(myre, (list,tuple)):
        myre, *flags = myre

    inv = myre.startswith(inversion)
    if inv:
        myre = myre[len(inversion):]

    pat = re.compile(myre, *flags)

    found = []   # return this
    # make this the form of a list list if needed:
    form_of_list = lambda v: v if isinstance(v, (list, GeneratorType)) \
                        else (dict(i) for i in v)
    for note in form_of_list(notes):
        this_note = False
        # breakpoint(False)
        for k,v in note.items():
            # empty fields == search all fields
            if not fields or k in fields:
                if isinstance(v, list):
                    for s in v:
                        if pat.findall(s):
                            this_note = True
                            break
                else:
                    if pat.findall(v):
                        this_note = True
                # on positive search, stop w/ any find:
                if not inv and this_note is True:
                    found.append(note)
                    break
        # w/ inv search, check all note items, then:
        if inv and this_note is False:
            found.append(note)

    return found


def savefind(note_list, file_name, mode="w", start=0,
             fields=('heading','content','title')):
    '''
    note_list: list of found notes (dicts, not db.Elements);

    file_name: name to write yaml to (ending up to you);

    mode: "w" by default, but can use "a" if you want to add;

    start: if you write, "a", each note indexed from "1",
           so pass the last index currently in the file (or
           len of last list (or sum of lists) you wrote);
        TODO: I could keep the count and update it... maybe;

    fields: note fields to stringify (combine to one multi-line
            string);
    '''
    for note in note_list:
        for k in note.keys():
            # stringify these fields for exporting
            #  to writing projects
            if k in fields:
                note[k] = "\n".join(note[k])

    # index the note with numeric strings: for easier reading
    # - use: string_range(start=0, len(note_list), width)
    # - will return strings from "1" to len(note_list)
    # replaces this: (str(i+start) for i in range(1,len(note_list)+1)),
    #
    # To get a semblance of "numberic ordering" in the numeric strings,
    #  we'll make them uniform width, zero padded
    list_len = len(note_list)
    w = len(str(list_len+start))
    string_range = lambda start,stop,w: (f'{i+start:0{w}}' for i in range(1,stop+1))

    inotes = dict(zip(string_range(start,list_len,w), note_list))
    with open(file_name, mode) as f:
        yaml.dump(inotes, f, default_flow_style=False)


# announce for the interactive user, what's what:
def intro(notes=notes, myre=myre):
    msg = f"""
    Intro:
    {len(notes)} notes available as variable: 'notes'

    example search-term available:  myre: ('summit', re.I)

    use findnotes() and savefind(); help() for more info;

    tinyDB tables available: dbnotes, dbarchive
    tinyDB Query() is imported, if you want to create
       a db, instead of a text search.
       e.g: Note = Query()
            dbnotes.search(Note.labels == "['golang']" ...)
            See http://tinydb.readthedocs.io/en/latest/usage.html#queries

    To show this message again:  intro()
    """
    print(msg)


intro()

