"""
Defines Queue related exception types
"""


# pylint: disable=unnecessary-pass


class InvalidAWSCredentialException(Exception):
    """ raise when the aws credential given with env var is not valid """

    pass


class InvalidQueueException(Exception):
    """ raise when created a queues given invalid parameters """

    pass


class QueueNotInitializedException(Exception):
    """ raise when queues not fully initialized """

    pass
