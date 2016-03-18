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


class InvalidFigure(BaseException):
    """
    Exception raised when a figure is invalid and cannot be shown.
    """
    pass
