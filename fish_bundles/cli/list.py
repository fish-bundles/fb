#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from cliff.lister import Lister
from blessings import Terminal

from fish_bundles.cli.lock import Lock


class List(Lister):
    "Lists all installed bundles."

    log = logging.getLogger(__name__)

    def __init__(self, *args, **kw):
        super(List, self).__init__(*args, **kw)
        self.term = Terminal()

    def take_action(self, parsed_args):
        lock = Lock.load()
        result = []

        self.app.stdout.write(self.term.bold_blue(u'\nInstalled Bundles:\n'))
        for bundle in lock.bundles:
            author, repo = bundle['repo'].split('/')
            version = bundle['version']
            result.append((repo, version, author))

        return tuple((('bundle', 'version', 'author'),) + (result, ))
