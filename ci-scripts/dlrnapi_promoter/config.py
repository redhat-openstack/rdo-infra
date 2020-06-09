"""
This file contains classes and function to build a configuration object that
can be passed to all the functions in the workfloww
"""
import copy
import logging
import os
import pprint

from jinja2 import Template
from jinja2.nativetypes import native_concat
from collections import OrderedDict

try:
    from urllib import urlparse
except ImportError:
    import urlparse


class ConfigError(Exception):
    pass


class ConfigCore(object):

    _log = logging.getLogger("promoter")

    def __init__(self, layers_list):
        """
        Initializes the layers in a ordered dict
        :param layers_list: the list of layers in the configuration,
        high priority first. The list cannot be changed.
        """
        self._layers = OrderedDict()
        for layer_name in layers_list:
            self._layers[layer_name] = {}
        self._log.debug("Config object configured with layers: %s",
                        ", ".join(layers_list))

    def _dump(self):
        pprint.pprint(self._layers)

    def _fill_layer_settings(self, layer_name, settings):
        """
        Allow access to the _layers data structure
        :param layer_name: The layer name to fill
        :param settings: A dict with the settings for the layer
        :return: None
        """
        self._layers[layer_name] = settings

    def _construct_value(self, attribute_name):
        """
        Generates the constructor name from the attribute name, and tries to
        call it.
        :param attribute_name: The name of the attribute whose value needs
        construction
        :return: The generated value if the constructor exists. raises
        AttributeError in case of any error
        """
        constructor_name = "_constructor_{}".format(attribute_name)
        try:
            constructor = self.__getattribute__(constructor_name)
        except AttributeError:
            self._log.error("No constructor for attribute %s", attribute_name)
            raise AttributeError

        self._log.debug("Running constructor for attribute %s",
                        attribute_name)
        try:
            return constructor()
        except Exception as exc:
            self._log.error("The constructor for attribute %s generated an "
                            "error, no value can be constructed")
            self._log.exception(exc)
            raise AttributeError

    def _search_layers(self, attribute_name):
        """
        Performs the simple search for the attribute name, on all layers,
        highest priority to lowest priority
        :param attribute_name: The name of the attribute to search
        :return: The value of the attribute or AttributeError if not found
        """
        for source_name, source in self.__getattribute__('_layers').items():
            try:
                value = source[attribute_name]
                self._log.debug("Getting attribute %s from layer '%s' ",
                                attribute_name, source_name)
                break
            except KeyError:
                self._log.debug("Attribute %s not found in layers",
                                attribute_name)

        try:
            return value
        except UnboundLocalError:
            raise AttributeError

    def _filter(self, attribute_name, value):
        """
        Generates the filter name from the attribute name and tried to call
        it with the value as parameter
        :param attribute_name: THe name of the attribute whose value need
        filtering
        :param value: The value of the attribute
        :return: The filtered value of the attribute or AttributeError if the
        filter fails
        """
        filter_name = "_filter_{}".format(attribute_name)
        try:
            filter_method = self.__getattribute__(filter_name)
        except AttributeError:
            return value

        self._log.debug("Running filter for attribute %s",
                        attribute_name)
        try:
            return filter_method(value)
        except Exception as exc:
            self._log.error("The filter for attribute %s generated an "
                            "error, no value can be constructed")
            self._log.exception(exc)
            raise AttributeError

    def _get_value(self, attribute_name):
        """
        High level method to drive the extraction/creation of a value from
        the attribute name.
        :param attribute_name: The name of the attribute whose value we want
        to know
        :return: The value or AttributeError if no value can be found or
        constructed
        """
        try:
            return self._search_layers(attribute_name)
        except AttributeError:
            try:
                return self._construct_value(attribute_name)
            except AttributeError:
                self._log.error("No attribute %s in config", attribute_name)
                raise AttributeError("No setting '{}' found"
                                     "".format(attribute_name))

    def _render(self, value):
        """
        Renders a string value that may contain a jinja template.
        :param value: The string with the possible template
        :return: The rendered string if it's a template, value otherwise
        """
        template = Template(value)
        # We can't call template.render directly in our case, as the render
        # will try to build a static dict from this object, and the dict will
        # be empty as we have no static values.
        # So we use low level API, passing shared=True and locals=False to
        # the context for the same reason as above.
        value = native_concat(template.root_render_func(
            template.new_context(vars=self, shared=True, locals=None)))

        # native concat returns int for string that contains only numbers
        # so we force to return a string
        return str(value)

    def __getattr__(self, attribute_name):
        """
        Drives any attribute access to the configuration. All
        config.attribute start generation here.
        The method tries to get a value then filters it and renders it when
        found
        :param attribute_name:
        :return: The value of the attribute or AttributeError if no value is
        available with any mean possible
        """
        value = self._get_value(attribute_name)
        value = self._filter(attribute_name, value)

        if isinstance(value, str):
            return self._render(value)
        else:
            return value

    def __getitem__(self, attribute_name):
        """
        config[item] is the same as config.item.
        This method is needed for templating, as jinja2 expects
        the data structure the act like a dict
        :param attribute_name:
        :return: The value of the attribute
        """
        return self.__getattr__(attribute_name)

    def __contains__(self, attribute_name):
        """
        This method is needed for templating, as jinja2 expects
        the data structure the act like a dict
        :param attribute_name: The name of the attribute to check
        :return: A bool, true if name is in config, false otherwise
        """
        try:
            self._get_value(attribute_name)
            return True
        except AttributeError:
            return False


class PromoterConfig(ConfigCore):
    """

    """

    def __init__(self, default_settings=None, file_settings=None,
                 cli_settings=None, experimental_settings=None):
        """

        :param default_settings:
        :param file_settings:
        :param cli_settings:
        :param experimental_settings:
        """
        super(PromoterConfig, self).__init__(['cli', 'file', 'default',
                                              'experimental'])
        if cli_settings is None:
            cli_settings = {}
        if file_settings is None:
            file_settings = {}
        if default_settings is None:
            default_settings = {}
        if experimental_settings is None:
            experimental_settings = {}
        self._layers["cli"] = cli_settings
        self._layers['file'] = file_settings
        self._layers['default'] = default_settings
        self._layers['experimental'] = experimental_settings
        self._log.debug("Initialized")

    # Constructors

    def _constructor_dlrnauth_password(self):
        """

        :return:
        """
        return os.environ.get('DLRNAPI_PASSWORD', None)

    def _constructor_qcow_server(self):
        """

        :return:
        """
        return self['overcloud_images']['qcow_servers'][
            self.default_qcow_server]

    def _constructor_api_url(self):
        """
        API url is the wild west of exceptions.
        :return: The api_url
        """
        host = self['dlrn_api_host']
        port = self['dlrn_api_port']
        scheme = self['dlrn_api_scheme']
        distro = self['distro_name']
        version = self['distro_version']
        release = self['release']
        url_port = None
        endpoint = None

        distro_endpoint = distro

        if version == '8':
            distro_endpoint += version
        release_endpoint = release
        if release == "master":
            release_endpoint = "master-uc"
        if distro_endpoint is not None and release_endpoint is not None:
            endpoint = "api-{}-{}".format(distro_endpoint,
                                          release_endpoint)
        if port is None or (scheme == "http" and port == 443) \
                or (scheme == "https" and
                    port == 443):
            url_port = ""
        else:
            url_port = ":{}".format(port)

        if not host and not port:
            url_hostport = ""
        else:
            url_hostport = "{}{}".format(host, url_port)

        url_elements = [None] * 6
        url_elements[0] = scheme
        url_elements[1] = url_hostport
        url_elements[2] = endpoint
        url = urlparse.urlunparse(url_elements)

        if url is None:
            self._log.error("No valid API url found")
        else:
            self._log.debug("Assigning api_url %s", url)
        return url

    # filters

    def _filter_allowed_clients(self, allowed_clients):
        if isinstance(allowed_clients, str):
            return allowed_clients.split(',')
        else:
            return allowed_clients

    def _filter_distro_name(self, distro_name):
        if isinstance(distro_name, str):
            return distro_name.lower()
        else:
            return None

    def _filter_promotions(self, promotions):
        if isinstance(promotions, dict):
            _promotions = copy.deepcopy(promotions)
            for target_name, info in promotions.items():
                if 'criteria' in info and not isinstance(info['criteria'], set):
                    info['criteria'] = set(info['criteria'])
            return _promotions
        else:
            return promotions


class PromoterConfigFactory(object):
    """
    This class builds a singleton object to be passed to all the other
    functions in the workflow.
    The base class should be only used for testing as it just performs the
    basic loading.
    """

    defaults = {
        'release': 'master',
        'distro_name': 'centos',
        'distro_version': '7',
        'dlrnauth_username': 'ciuser',
        'promotions': None,
        'dry_run': "false",
        'manifest_push': "false",
        'target_registries_push': "true",
        'latest_hashes_count': '10',
        'allowed_clients': 'registries_client,qcow_client,dlrn_client',
        'log_level': "INFO",
        'log_file': None,
        "dlrn_api_host": "trunk.rdoproject.org",
        "containers_list_base_url": ("https://opendev.org/openstack/"
                                     "tripleo-common/raw/commit/"),
        "containers_list_path": "container-images/overcloud_containers.yaml.j2",
        "repo_url": "https://{{ dlrn_api_host }}/{{ distro }}-{{ release }}",
        'log_file': "~/promoter_logs/{{ distro }}_{{ distro }}.log",
        "distro": "{{ distro_name }}{{ distro_release }}"
    }

    log = logging.getLogger("promoter")

    def __init__(self, filters="all", validate="all"):
        """
        Initialize the config object loading from ini file
        :param config_path: the path to the configuration file to load
        :param validate: A comma separated list of checks for the config
        file
        """
        # Initial log setup
        setup_logging("promoter", logging.DEBUG)
        self.git_root = None
        self.script_root = None
        self.git_root, self.script_root = get_root_paths(self.log)
        self.log.debug("Git root %s", self.git_root)
        self.log.debug("Script root %s", self.git_root)

    def __call__(self, config_path, cli_settings=None, validate="all"):
        file_settings = self.load_file_settings(config_path)
        experimental_path = os.path.join(self.script_root,
                                         "promoter_defaults_experimental.yaml")
        experimental_settings = self.load_file_settings(experimental_path)

        config = PromoterConfig(default_settings=self.defaults,
                                file_settings=file_settings,
                                cli_settings=cli_settings,
                                experimental_settings=experimental_settings)

        if not self.validate(config, checks=validate):
            self.log.error("Error in configuration file %s", config_path)
            raise ConfigError

        return config

    def load_file_settings(self, config_path):
        """
        Loads configuration from a yaml file.
        :param config_path: the path to the config file
        :return: a dict with the configuration
        """

        self.log.debug("Config file passed: %s", config_path)
        if config_path is None:
            self.log.error("Config file passed can't be None")
            raise ConfigError
        # The path is either absolute ot it's relative to the code root
        if not os.path.isabs(config_path):
            config_path = os.path.join(self.script_root, "config",
                                       config_path)
        try:
            os.stat(config_path)
        except OSError:
            self.log.error("Configuration file not found")
            raise

        self.log.debug("Using config file %s", config_path)
        with open(config_path) as config_file:
            try:
                config = yaml.safe_load(config_file)
            except yaml.YAMLError as exc:
                self.log.error("Unable to load config file %s", config_path)
                self.log.exception(exc)
                raise ConfigError
        if not isinstance(config, dict):
            self.log.error("Config file %s does not contain valid data",
                           config_path)
            raise ConfigError

        return config

    def validate(self, config, checks="all"):
        """
        :param config: A PromoterConfig instance to check
        :param checks: a comma separated list of checks to perform
        :return: A boolean, True if the validation was successful,
        false otherwise
        """
        if not checks:
            return True

        conf_ok = True
        if checks == "all":
            checks = ["logs", "password", "promotions"]

        if 'logs' in checks:
            try:
                with open(config.log_file, "w"):
                    pass
            except (FileNotFoundError, PermissionError):
                self.log.error("Invalid log file %s", config.log_file)
                conf_ok = False
            try:
                getattr(logging, config.log_level)
            except AttributeError:
                self.log.error("Unrecognized log level: %s",
                               config['log_level'])
                conf_ok = False

        if "promotions" in checks:
            try:
                promotions = config.promotions
            except AttributeError:
                self.log.error("Missing promotions section")
                conf_ok = False

            if promotions is None:
                self.log.error("Missing promotions section")
                conf_ok = False
            elif not promotions:
                self.log.error("Promotions section is empty")
                conf_ok = False
            else:
                for target_name, info in promotions.items():
                    if 'criteria' not in info:
                        self.log.error("Missing criteria for target %s",
                                       target_name)
                        conf_ok = False
                    if 'criteria' in info and not info['criteria']:
                        self.log.error("Empty criteria for target %s",
                                       target_name)
                        conf_ok = False
                    if 'candidate_label' not in info:
                        self.log.error("Missing candidate label for target %s",
                                       target_name)
                        conf_ok = False

        if "password" in checks:
            if config.dlrnauth_password is None:
                self.log.error("No dlrnapi password found in env")
                conf_ok = False

        return conf_ok
