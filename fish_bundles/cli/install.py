#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from json import dumps
import sys
import shutil
from os import environ, makedirs
from os.path import join, dirname, exists, expanduser
import tempfile
from zipfile import ZipFile
from cStringIO import StringIO

from cliff.lister import Lister
import requests
from blessings import Terminal
from requests.exceptions import ConnectionError

from fish_bundles.cli.lock import Lock
from fish_bundles.cli.init import update_init_file


class Install(Lister):
    "Installs the configured bundles."

    log = logging.getLogger(__name__)

    def __init__(self, *args, **kw):
        super(Install, self).__init__(*args, **kw)
        self.term = Terminal()

    def get_parser(self, prog_name):
        parser = super(Install, self).get_parser(prog_name)
        parser.add_argument('--force', action='store_true',  default=False)
        return parser

    def get_dim(self, msg):
        return self.term.dim_yellow(msg)

    def get_error_message(self, message, details):
        return self.term.bold_red('\nError: %s\n\n%s%sError details: %s\n' % (
            message, self.term.normal, self.term.dim_white, details
        ))

    def show_warning(self, msg, extra_line=True):
        separator = "%s\n" % ('-' * len(msg))
        self.app.stdout.write(separator)
        self.app.stdout.write(self.term.bold_white_on_yellow(msg) + '\n')
        self.app.stdout.write(separator)
        if extra_line:
            self.app.stdout.write('\n')

    def take_action(self, parsed_args):
        if '__fish_bundles_list' not in environ:
            self.show_warning(
                'Warning: Could not find the "__fish_bundles_list" environment variable. '
                'Have you added any \'fish_bundle "bundle-name"\' entries in your config.fish file?\n'
            )

        self.ensure_user_token()

        bundles = environ.get('__fish_bundles_list', '')
        bundles = list(set(bundles.split(':')))
        bundles = ['fish-bundles/root-bundle-fish-bundle'] + [bundle for bundle in bundles if bundle]
        server = environ.get('__fish_bundles_host', 'http://bundles.fish/')
        bundle_path = environ.get('__fish_bundles_root', expanduser('~/.config/fish/bundles'))

        info = self.get_bundle_info(server, bundles)
        installed, lock = self.install(info, bundle_path, parsed_args.force)

        if not installed:
            self.app.stdout.write(self.term.bold_green(
                u'\n☺ YAY! All bundles are up-to-date. No new bundles were installed. ☺ \n'
            ))
        else:
            installed_bundles = ", ".join(
                [bundle[1] for bundle in installed]
            )
            self.app.stdout.write(self.term.bold_green(
                '\nSuccessfully installed %d bundles (%s)!\n\n%s%sUpdated Bundle Versions:\n' % (
                    len(installed),
                    installed_bundles,
                    self.term.normal,
                    self.term.bold_blue
                )
            ))

            update_init_file()

        result = []

        self.app.stdout.write(self.term.bold_blue(u'\nInstalled Bundles:\n'))
        for bundle in lock.bundles:
            author, repo = bundle['repo'].split('/')
            version = bundle['version']
            result.append((repo, version, author))

        return tuple((('bundle', 'version', 'author'),) + (result, ))

    def install(self, info, bundle_path, force):
        tmp_dir = tempfile.mkdtemp()
        installed_bundles = []
        lock = Lock.load()

        for bundle in info:
            if not force and lock.is_up_to_date(bundle):
                self.copy_bundle(bundle, to=tmp_dir)
                continue

            logging.info(self.get_dim('>>> Installing %s...' % bundle['repo']))
            self.unzip(bundle, to=tmp_dir)
            author, repo = bundle['repo'].split('/')
            logging.info(self.get_dim('>>> %s installed successfully.' % bundle['repo']))
            installed_bundles.append((author, repo, bundle['version']))
            lock.update_bundle(bundle)

        shutil.rmtree(bundle_path)
        shutil.copytree(tmp_dir, bundle_path)
        lock.reload()
        lock.save()

        return installed_bundles, lock

    def copy_bundle(self, bundle, to):
        bundle_path = environ.get('__fish_bundles_root', expanduser('~/.config/fish/bundles'))
        bundle_dir = join(bundle_path.rstrip('/'), bundle['repo'].lstrip('/'))
        to_dir = join(to.rstrip('/'), bundle['repo'].lstrip('/'))
        shutil.copytree(bundle_dir, to_dir)

    def is_allowed_path(self, path):
        return path.endswith('.fish')

    def unzip(self, bundle, to):
        data = requests.get(bundle['zip'])
        z = ZipFile(StringIO(data.content))

        files = z.filelist

        root = files[0].filename

        root_path = join(to.rstrip('/'), bundle['repo'].lstrip('/'))

        for zip_file in files[1:]:
            path = zip_file.filename.replace(root, '').lstrip('/')
            if not self.is_allowed_path(path):
                continue

            file_path = join(root_path.rstrip('/'), path)
            file_dir = dirname(file_path)
            if not exists(file_dir):
                makedirs(file_dir)

            with open(file_path, 'w') as writer:
                with z.open(zip_file) as reader:
                    writer.write(reader.read())

    def get_bundle_info(self, server, bundles):
        try:
            result = requests.get("%s/my-bundles" % server.rstrip('/'), params=dict(bundles=dumps(bundles)))
        except ConnectionError:
            err = sys.exc_info()[1]
            raise RuntimeError(self.get_error_message(
                'Could not process the bundles. fish-bundles server was not found or an error happened.',
                str(err)
            ))

        if result.status_code != 200:
            raise RuntimeError(self.get_error_message(
                'Could not process the bundles. fish-bundles server was not found or an error happened.',
                'status code - %s' % result.status_code
            ))

        data = result.json()

        if data['result'] != 'bundles-found':
            raise RuntimeError(self.get_error_message(
                'Could not process the bundles. %s' % data['error'],
                'status code - %s\n' % result.status_code
            ))

        return data['bundles']

    def ensure_user_token(self):
        token_path = environ.get('__fish_bundles_token_path', expanduser('~/.fbrc'))
        if not exists(token_path):
            # https://help.github.com/articles/creating-an-access-token-for-command-line-use
            self.show_warning(
                "We still can't find your authentication tokens for github. Your connectivity may be limited.",
                extra_line=False
            )
            self.app.stdout.write("==> Please verify the docs on how to configure it at http://github.com/whateverurl.\n\n")
