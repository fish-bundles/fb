#!/usr/bin/python
# -*- coding: utf-8 -*-

from json import dumps, loads
from os import makedirs, environ
from os.path import dirname, exists, expanduser, join

from semantic_version import Version


class Lock(object):
    def __init__(self, bundles):
        self.bundles = bundles

    @classmethod
    def get_default_path(cls):
        return environ.get('__fish_bundles_lock_file', expanduser('~/.config/fish/bundles.lock'))

    @classmethod
    def get_functions_path_file(cls):
        return environ.get('__fish_bundles_import_file', expanduser('~/.config/fish/bundles/functions_path.fish'))

    @property
    def bundles_path(self):
        return environ.get('__fish_bundles_root', expanduser('~/.config/fish/bundles'))

    def get_bundle_path(self, bundle):
        return join(self.bundles_path, bundle['repo'])

    def get_bundle_functions_path(self, bundle):
        return join(self.get_bundle_path(bundle), 'functions')

    def get_bundle_config_path(self, bundle):
        return join(self.get_bundle_path(bundle), 'config.fish')

    def get_config_path(self, bundle):
        config_path = self.get_bundle_config_path(bundle)
        if not exists(config_path):
            return None

        return config_path

    @classmethod
    def load(self, path=None):
        if path is None:
            path = Lock.get_default_path()

        if not exists(path):
            return Lock([])

        with open(path, 'r') as lock_file:
            content = lock_file.read()
            data = loads(content)
            return Lock(data)

    def save(self, path=None):
        if path is None:
            path = Lock.get_default_path()

        if not exists(dirname(path)):
            makedirs(dirname(path))

        data = dumps(self.bundles)
        with open(path, 'w') as lock_file:
            lock_file.write(data)

        self.update_function_paths()

    def update_function_paths(self):
        paths = []
        for bundle in self.bundles:
            functions_path = self.get_bundle_functions_path(bundle)
            paths.append("set -gx fish_function_path $fish_function_path %s\n" % functions_path)

        path = Lock.get_functions_path_file()
        with open(path, 'w') as import_file:
            for path in paths:
                import_file.write(path)

    def get_bundle(self, key):
        match = filter(lambda item: item['repo'] == key, self.bundles)
        if not match:
            return None

        return match[0]

    def reload(self):
        new_bundles = []
        for bundle in self.bundles:
            bundle_path = self.get_bundle_path(bundle)
            if exists(bundle_path):
                new_bundles.append(bundle)
        self.bundles = new_bundles

    def update_bundle(self, bundle):
        match = self.get_bundle(bundle['repo'])
        if match:
            self.bundles.remove(match)
        self.bundles.append(bundle)

    def is_up_to_date(self, bundle):
        key = bundle['repo']
        match = self.get_bundle(key)

        if not match:
            return False

        return Version(match['version']) >= Version(bundle['version'])
