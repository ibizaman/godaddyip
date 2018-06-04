"""
Maintains A and CNAME records in Godaddy.
"""
import argparse
import json
import signal
from pathlib import Path
from time import sleep

import requests
import yaml


DEFAULT_CONFIG_FILES = [
    Path(p)
    for p in ["/etc/godaddyip/godaddyip.yaml",
              Path.home() / ".config/godaddyip/godaddyip.yaml",
              "./config/godaddyip.yaml"]]

IPIFY_URL = "https://api.ipify.org?format=json"

GODADDY_URL = "https://api.godaddy.com/v1"
GODADDY_URL_RECORD = GODADDY_URL + "/domains/{domain}/records/{type}/{name}"
GODADDY_HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Authorization': 'sso-key {key}:{secret}'
}


class Config:
    def __init__(self, config_file):
        self._config = {}

        self.parse_config(config_file)

    def __getitem__(self, key):
        return self._config[key]

    def set_arecord(self, value):
        self._config['arecord'] = value

    def set_key(self, value):
        self._config['key'] = value

    def set_secret(self, value):
        self._config['secret'] = value

    def set_domain(self, value):
        self._config['domain'] = value

    def add_cname(self, value):
        self._config['cnames'].add(value)

    def del_cname(self, value):
        if 'cnames' not in self._config:
            return

        try:
            self._config['cnames'].remove(value)
        except KeyError:
            pass

    def parse_config(self, config_file):
        self._config = {}

        if not config_file.is_file():
            return

        self._config = yaml.load(config_file.read_text()) or {}
        self._config['cnames'] = set(self._config.get('cnames', []))

    def dump_config(self, config_file):
        config = dict(self._config)
        config['cnames'] = list(config.get('cnames', []))
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(yaml.dump(config, default_flow_style=False))


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.set_defaults(func=None)
    command_parser = parser.add_subparsers()

    parser_conf = command_parser.add_parser('configure', help='Modify configuration file.')
    parser_conf.set_defaults(func=configure)
    parser_conf.add_argument(
        'config_file',
        type=Path,
        help='Location of the config file to modify.'
    )
    conf_action_parser = parser_conf.add_subparsers()

    parser_conf_arecord = conf_action_parser.add_parser('arecord', help='Update A record.')
    parser_conf_arecord.set_defaults(action='set_arecord')
    parser_conf_arecord.add_argument('value')

    parser_conf_key = conf_action_parser.add_parser('key', help='Update godaddy key.')
    parser_conf_key.set_defaults(action='set_key')
    parser_conf_key.add_argument('value')

    parser_conf_secret = conf_action_parser.add_parser('secret', help='Update godaddy secret.')
    parser_conf_secret.set_defaults(action='set_secret')
    parser_conf_secret.add_argument('value')

    parser_conf_domain = conf_action_parser.add_parser('domain', help='Update godaddy domain.')
    parser_conf_domain.set_defaults(action='set_domain')
    parser_conf_domain.add_argument('value')

    parser_conf_add = conf_action_parser.add_parser('add-cname', help='Add or replace CNAME record.')
    parser_conf_add.set_defaults(action='add_cname')
    parser_conf_add.add_argument('value')

    parser_conf_del = conf_action_parser.add_parser('del-cname', help='Remove CNAME record.')
    parser_conf_del.set_defaults(action='del_cname')
    parser_conf_del.add_argument('value')

    parser_run = command_parser.add_parser('run', help='Run script.')
    parser_run.set_defaults(func=run)
    parser_run.add_argument(
        '--config_files',
        type=lambda v: [Path(p) for p in v.split(',')],
        default=','.join(str(p) for p in DEFAULT_CONFIG_FILES),
        help="Location of config files, last one found takes precendence, defaults to {}.".format(
            ', '.join(str(p) for p in DEFAULT_CONFIG_FILES)))
    parser_run.add_argument(
        '--tmp_folder',
        type=Path,
        default=Path('/tmp/godaddyip/'),
        help="Folder where temporary files are located")

    args = vars(parser.parse_args())
    if args['func']:
        args['func'](**args)


def configure(config_file, action, value, **_kwargs):
    config = Config(config_file)

    getattr(config, action)(value)

    config.dump_config(config_file)


def run(config_files, tmp_folder, **_kwargs):
    config = Config(find_config(config_files))

    def sigusr1_handler(_signum, _stack):
        config.parse_config(find_config(config_files))
        print('Reloaded configuration file.')
        
    signal.signal(signal.SIGUSR1, sigusr1_handler)

    while True:
        try:
            maintain_records(config, tmp_folder)
            print('Sleeping for 5 minutes.')
            sleep(300)
        except KeyboardInterrupt:
            return


def find_config(config_files):
    for config_file in reversed(config_files):
        if config_file.is_file():
            return config_file

    raise RuntimeError("No configuration found on given paths.")


def maintain_records(config, tmp_folder):
    headers = GODADDY_HEADERS
    headers['Authorization'] = headers['Authorization'].format(key=config['key'], secret=config['secret'])

    ip = current_ip_ipify()
    update_arecord(tmp_folder, headers, config['domain'], config['arecord'], ip)

    for cname in config['cnames']:
        update_cname(tmp_folder, headers, config['domain'], cname, config['arecord'])


def update_arecord(tmp_folder, headers, domain, arecord, ip):
    print('Updating A record {}.'.format(arecord))

    if previous_value(tmp_folder, 'arecord') == ip:
        print('Same ip as previous one, nothing to do.')
        return True

    url = GODADDY_URL_RECORD.format(domain=domain, type='A', name=arecord)

    r = requests.put(url, headers=headers, data=json.dumps([{'data': ip}]))
    if r.status_code != 200:
        print('Could not update A record {}:'.format(arecord))
        print(r.text)
        return False

    store_value(tmp_folder, 'arecord', ip)
    return True


def update_cname(tmp_folder, headers, domain, cname, alias):
    print('Updating CNAME record {}.'.format(cname))

    if previous_value(tmp_folder, cname) == alias:
        print('Same alias as previous one, nothing to do.')
        return True

    full_cname = cname + '.' + alias
    full_alias = alias + '.' + domain

    url = GODADDY_URL_RECORD.format(domain=domain, type='CNAME', name=full_cname)

    r = requests.put(url, headers=headers, data=json.dumps([{'data': full_alias}]))
    if r.status_code != 200:
        print('Could not update CNAME record {}:'.format(cname))
        print(r.text)
        return False

    store_value(tmp_folder, cname, alias)
    return True


def current_ip_ipify():
    r = requests.get(IPIFY_URL)
    r.raise_for_status()
    return r.json()['ip']


def previous_value(tmp_folder, name):
    file = tmp_folder / name
    if not file.is_file():
        return None
    return file.read_text()


def store_value(tmp_folder, name, value):
    tmp_folder.mkdir(parents=True, exist_ok=True)
    (tmp_folder / name).write_text(value)


if __name__ == '__main__':
    main()
