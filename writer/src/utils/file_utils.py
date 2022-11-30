import os
import logging
import logging.config
import yaml


def initialize_logging():
    """
    Initialize the logger once as the application starts up
    """
    logging_path = os.getenv('LOGGING_PATH', 'config/logging.yaml')
    if not os.path.exists(logging_path):
        raise ValueError(f"No logging yaml file under {logging_path}")
    with open(logging_path, 'rt') as f:
        config = yaml.safe_load(f.read())
    logging.config.dictConfig(config)


def initialize_properties():
    """
    Initialize yaml with properties
    """
    properties_path = os.getenv('PROPERTIES_PATH', 'config/application.yaml')
    if not os.path.exists(properties_path):
        raise ValueError(f"No properties yaml file under {properties_path}")
    with open(properties_path, 'rt') as properties_file:
        return yaml.safe_load(properties_file)


#def get_os_variable(name, default_value=None):
#    value = os.getenv(name, default_value)
#    if value is None:
#        raise ValueError(f"No value for a variable {name}")
#    return value

