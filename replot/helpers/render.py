"""
Various helper functions for plotting.
"""
import numpy as np


def set_axis_property(group_, setter, value, default_setter=None):
    """
    Set a property on an axis at render time.

    :param group_: The subplot for this axis.
    :param setter: The setter to use to set the axis property.
    :param value: The value for the property, either a value or a dict with \
            group as key.
    :param default_setter: Default setter to call if ``value`` is a dict but \
            has no key for the given subplot.
    :returns: None.
    """
    if isinstance(value, dict):
        try:
            if value[group_] is not None:
                setter(value[group_])
        except KeyError:
            # No entry for this axis in the dict, use default argument
            if default_setter is not None:
                default_setter()
    else:
        if value is not None:
            setter(value)


def linewidth_from_data_units(linewidth, axis, reference='y'):
    """
    Convert a linewidth in data units to linewidth in points.

    Parameters
    ----------
    linewidth: float
        Linewidth in data units of the respective reference-axis
    axis: matplotlib axis
        The axis which is used to extract the relevant transformation
        data (data limits and size must not change afterwards)
    reference: string
        The axis that is taken as a reference for the data width.
        Possible values: 'x' and 'y'. Defaults to 'y'.

    Returns
    -------
    linewidth: float
        Linewidth in points

    From https://stackoverflow.com/questions/19394505/matplotlib-expand-the-line-with-specified-width-in-data-unit.
    """
    fig = axis.get_figure()
    if reference == 'x':
        length = fig.bbox_inches.width * axis.get_position().width
        value_range = np.diff(axis.get_xlim())
    elif reference == 'y':
        length = fig.bbox_inches.height * axis.get_position().height
        value_range = np.diff(axis.get_ylim())
    # Convert length to points
    length *= 72  # Inches to points is a fixed conversion in matplotlib
    # Scale linewidth to value range
    return linewidth * (length / value_range)


def data_units_from_points(points, axis, reference='y'):
    """
    Convert points to data units on the given axis.

    Parameters
    ----------
    points: float
        Value in points to convert.
    axis: matplotlib axis
        The axis which is used to extract the relevant transformation
        data (data limits and size must not change afterwards)
    reference: string
        The axis that is taken as a reference for the data width.
        Possible values: 'x' and 'y'. Defaults to 'y'.

    Returns
    -------
    points: float
        Converted value.
    """
    fig = axis.get_figure()

    if reference == 'x':
        length = fig.bbox_inches.width * axis.get_position().width
        value_range = np.diff(axis.get_xlim())
    elif reference == 'y':
        length = fig.bbox_inches.height * axis.get_position().height
        value_range = np.diff(axis.get_ylim())
    # Convert length to points
    length *= 72  # Inches to points is a fixed conversion in matplotlib
    # Scale linewidth to value range
    return points / (length / value_range)
