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
from requests.exceptions import ConnectionError
from blessings import Terminal


class Install(Lister):
    "Installs the configured bundles."

    log = logging.getLogger(__name__)

    def __init__(self, *args, **kw):
        super(Install, self).__init__(*args, **kw)
        self.term = Terminal()

    def get_error_message(self, message, details):
        return self.term.bold_red('\nError: %s\n\n%s%sError details: %s\n' % (
            message, self.term.normal, self.term.dim_white, details
        ))

    def show_warning(self, msg):
        separator = "%s\n" % ('-' * len(msg))
        self.app.stdout.write(separator)
        self.app.stdout.write(self.term.bold_white_on_yellow(msg))
        self.app.stdout.write(separator + '\n')

    def take_action(self, parsed_args):
        if '__fish_bundles_list' not in environ:
            self.show_warning(
                'Warning: Could not find the "__fish_bundles_list" environment variable. '
                'Have you added any \'fish_bundle "bundle-name"\' entries in your config.fish file?\n'
            )

        bundles = environ.get('__fish_bundles_list', '')
        bundles = list(set(bundles.split(':')))
        bundles = ['fish-bundles/root-bundle-fish-bundle'] + bundles
        server = environ.get('__fish_bundles_host', 'http://bundles.fish/')
        bundle_path = environ.get('__fish_bundles_root', expanduser('~/.config/fish/bundles'))

        info = self.get_bundle_info(server, bundles)
        installed = self.install(info, bundle_path)

        self.app.stdout.write(self.term.bold_green(
            '\nSuccessfully installed %d bundle(s)!\n\nUpdated Bundle Versions:\n' % len(installed)
        ))

        result = []

        for bundle in installed:
            author, repo, version = bundle
            result.append((repo, version, author))

        return tuple((('bundle', 'version', 'author'),) + (result, ))

    def install(self, info, bundle_path):
        tmp_dir = tempfile.mkdtemp()
        installed_bundles = []

        for bundle in info:
            logging.info('Installing %s...' % bundle['repo'])
            self.unzip(bundle['zip'], to=tmp_dir)
            author, repo = bundle['repo'].split('/')
            logging.info('%s installed successfully.' % bundle['repo'])
            installed_bundles.append((author, repo, bundle['version']))

        shutil.rmtree(bundle_path)
        shutil.copytree(tmp_dir, bundle_path)

        return installed_bundles

    def unzip(self, url, to):
        data = requests.get(url)
        z = ZipFile(StringIO(data.content))

        files = z.filelist

        root = files[0].filename

        for zip_file in files[1:]:
            path = zip_file.filename.replace(root, '').lstrip('/')
            if 'functions/' not in path or not path.endswith('.fish'):
                continue

            file_path = join(to.rstrip('/'), path)
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
