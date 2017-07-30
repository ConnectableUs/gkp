#!/usr/bin/env python
from os import path
import sys

import json

if len(sys.argv) > 1:
    print("usage:\n\t{} < your_json_file > your_prettified_json_file".format(
            path.basename(sys.argv[0])))
    sys.exit(1)

json.dump(json.load(sys.stdin), sys.stdout, indent=2)
