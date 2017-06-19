import os
import yaml
from tinydb import Storage


# reading in for json of ~2k items: 12ms
# reading in for yaml of ~2k items: 6s
# --- so use this for readable/inspectable instance,
# --- not for regular data searches


def touch(fname, times=None, create_dirs=False):
    if create_dirs:
        base_dir = os.path.dirname(fname)
        if base_dir and not os.path.exists(base_dir):
            os.makedirs(base_dir)
    with open(fname, 'a'):
        os.utime(fname, times)


class YAMLStorage(Storage):
    def __init__(self, filename, create_dirs=True, default_flow_style=False, **kwargs):  # (1)
        # create tile is not exists
        touch(filename, create_dirs=create_dirs)
        self.kwargs = kwargs
        self._flow = default_flow_style
        self._handle = open(filename, 'r+')

    def close(self):  # (4)
        self._handle.close()

    def read(self):
        f = self._handle
        f.seek(0, os.SEEK_END)
        size = f.tell()

        if not size:  # empty file
            return None
        else:
            f.seek(0)
            try:
                data = yaml.safe_load(f.read())  # (2)
                return data
            except yaml.YAMLError:
                return None  # (3)

    def write(self, data):
        f = self._handle
        f.seek(0)
        yaml.dump(data, f, default_flow_style=self._flow,
                  **self.kwargs)
        f.flush()
        f.truncate()
