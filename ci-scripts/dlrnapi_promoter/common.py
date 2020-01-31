"""
This file contains general functions and classes
"""


class PromotionError(Exception):
    pass


def str2bool(value):
    """
    Converts a string with a boolean value into a proper boolean
    mostly useful for variables coming from ini parser
    """
    if value in ['yes', 'true', 'True', 'on', '1']:
        return True
    return False

# TODO(gcerami) move setup-logging here so it can be used in tests too
