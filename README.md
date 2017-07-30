## versioning json results of keep scans

See if .gitattributes can usefully manage
inydb files, which are json files with no superfluous
newlines whatsoever.

A test might be to observe `git diffs` between one
test repo with the json file thus modified:

```
sed 's/}/\n}\n/g' < Keep.json > test1/Keep.json
```

with a [.gitattributes](https://git-scm.com/docs/gitattributes) based repo:

```
*.json  eol='}'
```

Two things to check here:

- how `git diff` compares on the two repositories;
- how tinydb handles the files of both;


Sat Jul 29 23:11:58 CDT 2017 >>

It turns out that [TinyDB](http://tinydb.readthedocs.io/en/latest/usage.html#storage-middleware)
passes all additional keyword arguments (other than 'storage') to json.dump().

I tried doing this separately in a modified file, but TinyDB() failed with this.
But letting TinyDB manage this kind of "pretty-print" output, it uses this
consistently, and things seem to work.

I've added the `indent=2` keyword to format json.dump(), and this seems to work fine.
It turns out the git-diff's are much cleaner when TinyDB is allowed to build up the
existing json file.
