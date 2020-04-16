# Nice to have features
# Add capability to load input from a URI
# Add markdown file describing the project features

import argparse
import logging

import yaml

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from nginx.nginx import Conf, Upstream, Key, Server, Location, dump


def is_list_empty(list):
    """
    Checks if the list data structure passed is empty or not
    :param list: List to be checked
    :return: True if list is empty else False
    """
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
        """
        Initialize object.
        :param data: Parsed yaml data as dict
        """
        self.data = data

    def build_ip_filters(self):
        """
        Builds the filtered CIDR IP list to allow connections from
        :return: None
        """
        if is_list_empty(self.data['ipfilter']['myfilter']) is False:
            for item in self.data['ipfilter']['myfilter']:
                self.cidr_filter_list.append(item)
        else:
            logger.warning(
                "my filter field is empty in the given input file , rules for the same will not be created in "
                "Nginx configuration")

    def build_allow_all_ip_list(self):
        """
        Builds the CIDR IP List for allowing connections from universe
        :return: None
        """
        if is_list_empty(self.data['ipfilter']['allowall']) is False:
            for item in self.data['ipfilter']['allowall']:
                self.cidr_allow_all_list.append(item)
        else:
            logger.warning(
                'allow all field is empty in the given input file , rules for the same will not be created in '
                'the Nginx configuration ')

    def build_default_catch_all_map(self):
        """
        Builds the map for catchall configurations
        :return: None
        """
        self.default_catch_all_map = self.data['catchall']

    @staticmethod
    def build_upstream_conf(env=None, runtime_port=None, upstream_default_host=None):
        """
        Builds the upstream section configuration for the env passed
        :param env: env being acceptance , prodcution etc
        :param runtime_port: port on which the virtual host for env listens on being served by same Nginx host
        :param upstream_default_host:
        :return: Upstream configuration Object to be added to the overall generated Nginx Configuration
        """

        logger.info('Building the upstream configuration for env: {}'.format(env))
        upstream_conf = Upstream(env,
                                 Key('server', upstream_default_host + ':' + str(runtime_port)))
        return upstream_conf

    def build_server_conf(self, is_default=False, env=None, server_name_list=[], location_config=None,
                          default_config_identifier=None, default_port=None, default_root_directory=None):
        """
        Builds the Nginx server section configuration for the env passed
        :param is_default: is passed as True , will build the config for default server ( env )
        :param env: env being acceptance , production etc
        :param server_name_list: Virtual Server Host entry serving the traffic for the env passed
        :param location_config: Build configuration for different path's being served by the env passed
        :param default_config_identifier: Builds the listen construct for the default catchall runtime port
        :param default_port: Default port value to build default server configuration, applicable only when is_default entry is set to True
        :param default_root_directory: Default path for the default server configuration , applicable only when is_default is set to True
        :return: Server Configuration Object to be added to overall generated Nginx Configuration.
        """
        server_conf = Server()

        if is_default is False:
            logger.info("Building the server section for {}".format(env))
            if server_name_list:
                for server in server_name_list:
                    server_conf.add(
                        Key(
                            'server_name', server
                        )
                    )
            else:
                logger.warning("Server Name for env {} are not set".format(env))
            server_conf.add(
                Key('listen', '[::]:' + str(
                    self.default_catch_all_map[default_config_identifier]['port']) + 'default_server ipv6only=on'),
                Key('listen',
                    '0.0.0.0:' + str(self.default_catch_all_map[default_config_identifier]['port']) + 'default_server'))

            if location_config:
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
            else:
                logger.warning("Location is/are not specified for the env:{}".format(env))

        elif is_default is True:
            if str(default_port) is None or len(str(default_port)) == 0:
                logger.warning("Default port not set, Nginx config for default host might now work properly !!")
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
    """
    The Starting block for the program
    """
    parser = argparse.ArgumentParser(description='Script to generate Nginx Configuration')
    parser.add_argument("--input", required=True, help="Location of the input.yaml file to process", type=str)
    parser.add_argument("--output", required=False,
                        help="Location where the output nginx donfig would be dumped "
                             "(this includes the output file name as well",
                        type=str)

    args = parser.parse_args()

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)

    logger.addHandler(stream_handler)

    logger.info("Reading Yaml file from location {}".format(args.input))

    if not args.output:
        logger.warning("Output location not specified , will be storing the generated nginx under resources folder")
    else:
        logger.info(
            "Output location specified as {}, will be used to store the generate Nginx file".format(args.output))

    try:
        with open(args.input, "r") as file:
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

    file_handler = None
    output_path = None
    if args.output:
        output_path = args.output
        file_handler = open(args.output, "w")
    else:
        output_path = "./resources/generated_nginx.conf"
        file_handler = open(output_path, "w")

    # Writing the Nginx configuration to the location specified
    dump(c, file_handler)

    logger.info('Generated Nginx Configuration is present location {}'.format(output_path))
