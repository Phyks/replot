"""
Parse custom keyword arguments for ``plot`` command.
"""
import numpy as np

from replot import constants
from replot import exceptions as exc


def parse(kwargs):
    """
    This method handles custom keyword arguments from plot in \
            :mod:`replot` which are not in :mod:`matplotlib` function.

    :param kwargs: A dictionary of keyword arguments to handle.
    :return: A tuple of :mod:`matplotlib` compatible keyword arguments \
            and of extra :mod:`replot` keyword arguments, both returned \
            as ``kwargs`` ``dict``.
    """
    # Default values
    custom_kwargs = {
        "frame": 0
    }
    # Handle "group" argument
    if "group" in kwargs:
        if len(kwargs["group"]) > 1:
            raise exc.InvalidParameterError(
                "Group name cannot be longer than one unicode character.")
        elif kwargs["group"] == constants.DEFAULT_GROUP:
            raise exc.InvalidParameterError(
                "'%s' is a reserved group name." % (constants.DEFAULT_GROUP,))
        custom_kwargs["group"] = kwargs["group"]
        del kwargs["group"]
    # Handle "line" argument
    if "line" in kwargs:
        if not kwargs["line"]:  # If should not draw lines, set kwargs for it
            kwargs["linestyle"] = "None"
            kwargs["marker"] = "x"
        del kwargs["line"]
    # Handle "xrange" argument, alias for xlim
    if "xrange" in kwargs:
        kwargs["xlim"] = kwargs["xrange"]
    # Handle "yrange" argument, alias for xlim
    if "yrange" in kwargs:
        kwargs["ylim"] = kwargs["yrange"]

    # Handle other arguments
    custom_args = [
        "frame",
        "invert",
        "logscale",
        "orthonormal",
        "rotate",
        "xlim",
        "ylim"]
    for custom_arg in custom_args:
        if custom_arg in kwargs:
            custom_kwargs[custom_arg] = kwargs[custom_arg]
            del kwargs[custom_arg]

    return (kwargs, custom_kwargs)


def edit_plot_command(plot_, custom_kwargs):
    """
    Edit a plot_ command tuple to take into account custom kwargs, that is \
            append them to the plot_ command and edit the command accordingly \
            (for axes inversion for instance).

    :param plot_: a ``(args, kwargs)`` plot command.
    :param custom_kwargs: A dict of custom kwargs.
    :returns: a ``(args, kwargs, custom_kwargs)`` plot command.
    """
    # Keep track of custom_kwargs in plot_
    plot_ += (custom_kwargs,)

    # Handle inversion
    if "invert" in custom_kwargs and custom_kwargs["invert"]:
        # Invert X and Y data
        plot_ = (
            (plot_[0][1], plot_[0][0]) + plot_[0][2:],
            plot_[1], plot_[2])

    # Handle rotation
    if "rotate" in custom_kwargs:
        # Rotate X, Y data
        # TODO: Not clean
        new_X_list = []
        new_Y_list = []
        for x, y in zip(plot_[0][0], plot_[0][1]):
            angle = np.deg2rad(custom_kwargs["rotate"])
            new_X_list.append(
                np.cos(angle) * x +
                np.sin(angle) * y)
            new_Y_list.append(
                -np.sin(angle) * x +
                np.cos(angle) * y)
        plot_ = (
            (new_X_list, new_Y_list) + plot_[0][2:],
            plot_[1], plot_[2])

    return plot_
