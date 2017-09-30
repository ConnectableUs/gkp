#!/bin/bash

# grab a new google keep archive:

# 1/ put it in a clean directory:

DEST=./Takeout

echo rm -rf $DEST/*
rm -rf $DEST/*

# unpack the latest archive

SRCD=my-google-data-downloads
SRC="$SRCD/$(ls -rt $SRCD | tail -1)"

echo tar xzf $SRC
tar xzf $SRC

# finally, make a new DB from this:


# make sure we're in venv; if not, make it so:
which python | fgrep env/keep/bin/python > /dev/null
if [ "$?" -ne "0" ]; then
    source env/keep/bin/activate
fi

python keep2db.py
