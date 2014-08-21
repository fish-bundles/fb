#!/usr/bin/python
# -*- coding: utf-8 -*-


import logging
from os.path import expanduser

from cliff.command import Command


class Init(Command):
    "Initializes fish-bundles."

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        with open(expanduser('~/.config/fish/functions/fish_bundles_init.fish'), 'w') as fish_init:
            fish_init.write('''
function fish_bundles_init --description="Initializes fish bundle paths and configurations"
    set -ex __fish_bundles_list
    . ~/.config/fish/bundles/functions_path.fish
end
'''.strip())
