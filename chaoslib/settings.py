# -*- coding: utf-8 -*-
import os
import os.path

from logzero import logger
import yaml

from chaoslib.types import Settings

__all__ = ["load_settings", "save_settings"]
CHAOSTOOLKIT_CONFIG_PATH = os.path.abspath(
    os.path.expanduser("~/.chaostoolkit/settings.yaml"))


def load_settings(settings_path: str = CHAOSTOOLKIT_CONFIG_PATH) -> Settings:
    """
    Load chaostoolkit settings as a mapping of key/values or return `None`
    when the file could not be found.
    """
    if not os.path.exists(settings_path):
        logger.debug("The Chaos Toolkit settings file could not be found at "
                     "'{c}'.".format(c=settings_path))
        return

    with open(settings_path) as f:
        try:
            return yaml.safe_load(f.read())
        except yaml.YAMLError as ye:
            logger.error("Failed parsing YAML settings: {}".format(str(ye)))


def save_settings(settings: Settings,
                  settings_path: str = CHAOSTOOLKIT_CONFIG_PATH):
    """
    Save chaostoolkit settings as a mapping of key/values, overwriting any file
    that may already be present.
    """
    settings_dir = os.path.dirname(settings_path)
    if not os.path.isdir(settings_dir):
        os.mkdir(settings_dir)

    with open(settings_path, 'w') as outfile:
        yaml.dump(settings, outfile, default_flow_style=False)
