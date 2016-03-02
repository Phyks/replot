"""
TODO
"""


class BaseException(Exception):
    """
    Base exception for all replot exceptions.
    """
    pass


class InvalidParameterError(BaseException):
    """
    Exception raised when an invalid parameter is provided.
    """
    pass
