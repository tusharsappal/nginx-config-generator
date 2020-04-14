# Nice to have features
# TODO :- Add capability to load from a URI
# TODO:- Add docopt functionality to the code , to run as CLI

import logging

import yaml

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from nginx.nginx import Conf, Upstream, Key, Server, Location


def is_list_empty(list):
    if not list:
        return True
    else:
        return False


class NginxConfigGenerator:
    cidr_filter_list = []
    cidr_allow_all_list = []
    default_catch_all_map = {}
    data = None

    def __init__(self, data):
        self.data = data

    def build_ip_filters(self):
        if is_list_empty(self.data['ipfilter']['myfilter']) is False:
            for item in self.data['ipfilter']['myfilter']:
                self.cidr_filter_list.append(item)
        else:
            logger.warning(
                "my filter field is empty in the given input file , rules for the same will not be created in "
                "Nginx configuration")

    def build_allow_all_ip_list(self):
        if is_list_empty(self.data['ipfilter']['allowall']) is False:
            for item in self.data['ipfilter']['allowall']:
                self.cidr_allow_all_list.append(item)
        else:
            logger.warning(
                'allow all field is empty in the given input file , rules for the same will not be created in '
                'the Nginx configuration ')

    def build_default_catch_all_map(self):
        self.default_catch_all_map = self.data['catchall']

    @staticmethod
    def build_upstream_conf(env=None, runtime_port=None, upstream_default_host=None):

        logger.info('Building the upstream configuration for env: {}'.format(env))
        upstream_conf = Upstream(env,
                                 Key('server', upstream_default_host + ':' + str(runtime_port)))
        return upstream_conf

    def build_server_conf(self, is_default=False, env=None, server_name_list=[], location_config=None,
                          default_config_identifier=None, default_port=None, default_root_directory=None):
        server_conf = Server()

        if is_default is False:
            logger.info("Building the server section for {}".format(env))
            for server in server_name_list:
                server_conf.add(
                    Key(
                        'server_name', server
                    )
                )
            server_conf.add(
                Key('listen', '[::]:' + str(
                    self.default_catch_all_map[default_config_identifier]['port']) + 'default_server ipv6only=on'),
                Key('listen',
                    '0.0.0.0:' + str(self.default_catch_all_map[default_config_identifier]['port']) + 'default_server'))

            for key in location_config:
                loc = Location(key)
                loc.add(Key('proxy_pass', 'http://' + env)),

                if location_config[key]['ipfilter'] == 'myfilter':
                    for cidr in self.cidr_filter_list:
                        loc.add(Key('allow', cidr))
                elif location_config[key]['ipfilter'] == 'allowall':
                    for cidr in self.cidr_allow_all_list:
                        loc.add(Key('allow', cidr))
                loc.add(Key('deny', 'all'))

                server_conf.add(loc)

        elif is_default is True:
            server_conf.add(
                Key('listen', '[::]:' + str(default_port) + 'default_server ipv6only=on'),
                Key('listen', '0.0.0.0:' + str(default_port) + 'default_server'),
                Key('root', default_root_directory)
            )
            if not server_name_list:
                server_conf.add(
                    Key('server_name', '_')
                )

            loc = Location(next(iter(location_config)))
            key = str(next(iter(location_config)))
            for k, v in location_config[key].items():
                loc.add(Key(k, v))

            server_conf.add(loc)

        return server_conf


if __name__ == "__main__":

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)

    logger.addHandler(stream_handler)

    try:
        with open(r"./resources/sample_input.yaml") as file:
            logger.info("Parsing the provided yaml configuration")
            data = yaml.load(file, Loader=yaml.FullLoader)
    except Exception as ex:
        logger.error("An exception of type '{0}' occurred.".format(type(ex).__name__))
        exit(1)

    logger.info("Initializing the Nginx Config Generator")

    ng = NginxConfigGenerator(data)

    logger.info("Initializing the  IP Filters from provided yaml files")
    ng.build_ip_filters()

    logger.info("Initializing the allowed IP CIDR List")
    ng.build_allow_all_ip_list()

    logger.info("Initializing the default catch all configuration")
    ng.build_default_catch_all_map()

    c = Conf()

    # Building Default server configuration
    default_path_map = {
        '/': {
            'return': '503'
        }
    }
    logger.info("Using default path as {}".format(default_path_map))

    default_root_dir = "/var/www"
    logger.info("Using the default root dir path as {}".format(default_root_dir))

    upstream_default_host = "127.0.0.1"
    logger.info("Using the upstream section for default host")

    server_name_list = []

    runtime_port = data['catchall']['default']['port']
    logger.info("Using the Runtime port value as {}".format(runtime_port))

    logger.info('Building the default server section for the Nginx configuration with '
                'location config as {} , default port as {} and default root directory as {}'.
                format(default_path_map, runtime_port, default_root_dir))
    c.add(ng.build_server_conf(is_default=True, server_name_list=server_name_list, location_config=default_path_map,
                               default_port=runtime_port, default_root_directory=default_root_dir))

    for item in data['app'].keys():
        runtime_port = data['app'][item]['runtime_port']
        fdqn_list = data['app'][item]['fqdn']
        path_map = data['app'][item]['path_based_access_restriction']
        catch_all_config_identifier = data['app'][item]['catchall']

        c.add(ng.build_upstream_conf(env=item, runtime_port=runtime_port, upstream_default_host=upstream_default_host))
        c.add(ng.build_server_conf(is_default=False, env=item, server_name_list=fdqn_list,
                                   location_config=path_map,
                                   default_config_identifier=catch_all_config_identifier))

    logger.info(''.join(c.as_strings))
