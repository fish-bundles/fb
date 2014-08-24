#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from os.path import expanduser

from cliff.command import Command

from fish_bundles.cli.lock import Lock


def update_init_file():
    lock = Lock.load()

    configurations = []

    for bundle in lock.bundles:
        cfg = lock.get_config_path(bundle)
        if cfg is not None:
            bundle_path = lock.get_bundle_path(bundle)
            configurations.append('    set -gx __fish_bundles_bundle_root_path %s' % bundle_path)
            configurations.append('    . %s' % cfg)

    with open(expanduser('~/.config/fish/functions/fish_bundles_init.fish'), 'w') as fish_init:
        fish_init.write('''
function fish_bundles_init --description="Initializes fish bundle paths and configurations"
    set -ex __fish_bundles_list
    . ~/.config/fish/bundles/functions_path.fish
%s
    set -ex __fish_bundles_bundle_root_path
end
'''.strip() % ("\n".join(configurations)))


class Init(Command):
    "Initializes fish-bundles."

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        update_init_file()
