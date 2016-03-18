"""
Various helper functions for plotting.
"""


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
