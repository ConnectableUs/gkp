## versioning json results of keep scans

See if .gitattributes can usefully manage
inydb files, which are json files with no superfluous
newlines whatsoever.

A test might be to observe `git diffs` between one
test repo with the json file thus modified:

```
sed 's/}/\n}\n' < Keep.json > test1/Keep.json
```

with a [.gitignore](https://git-scm.com/docs/gitattributes) based repo:

```
*.json  eol='}'
```

Two things to check here:

- how `git diff` compares on the two repositories;
- how tinydb handles the files of both;


