# coding: utf-8
import re
from tinydb import TinyDB  #, Query

#  This is for ipython interactive
def breakpoint(condition=True):
    '''
    in ipython:
    - breakpoint() <= break always
    - breakpoint(False) <= never break
    - breakpoint(condition) <= break if True
    '''
    # import here, to limit the imported names
    # to this function's namespace
    from sys import _getframe
    from IPython.terminal import debugger
    if condition:
        debugger.set_trace(_getframe().f_back)
        return debugger

# load parsed notes into something to search for:
db = TinyDB('Keep.json')
table = db.table('notes')
#- this doesn't work as I'd want
# res = table.search(Note.title.any(['Summit']))
#- so this is to make search look through all note text

## make it a python form, so we can use it
# get rid of db.Element cruft (e.g. record numbering):
# - might as well make it a generator, for memory skimpiness
notes = (dict(n) for n in table)


def findnotes( myre, notes, fields=set() ):
    # test: pass this as a parameter
    myre = r'[Ss]ummit'
    pat = re.compile(myre)
    # return this
    found = []
    for note in notes:
        this_note = False
        # breakpoint(False)
        for k,v in note.items():
            # empty fields == search all fields
            if not fields or k in fields:
                if isinstance(v, list):
                    for i in v:
                        if pat.findall(i):
                            this_note = True
                            break
                else:
                    if pat.findall(v):
                        this_note = True
                if this_note:
                    found.append(note)
                    break

    return found

