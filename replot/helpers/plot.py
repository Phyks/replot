"""
Various helper functions for plotting.
"""
import numpy as np

from replot import adaptive_sampling
from replot import exceptions as exc


def plot_function(data, *args, **kwargs):
    """
    Helper function to handle plotting of unevaluated functions (trying \
            to evaluate it nicely and rendering the plot).

    :param data: The function to plot.
    :returns: A tuple of ``(args, kwargs)`` representing the plot.

    .. seealso:: The documentation of the ``replot.Figure.plot`` method.

    .. note:: ``args`` is used to handle the interval or point series on \
            which the function should be evaluated. ``kwargs`` are passed \
            directly to ``matplotlib.pyplot.plot`.
    """
    if len(args) == 0:
        # If no interval specified, raise an issue
        raise exc.InvalidParameterError(
            "You should pass a plotting interval to the plot command.")
    elif isinstance(args[0], tuple):
        # Interval specified, use it and adaptive plotting
        x_values, y_values = adaptive_sampling.sample_function(
            data,
            args[0],
            tol=1e-3)
    elif isinstance(args[0], (list, np.ndarray)):
        # List of points specified, use them and compute values of the
        # function
        x_values = args[0]
        y_values = [data(i) for i in x_values]
    else:
        raise exc.InvalidParameterError(
            "Second parameter in plot command should be a tuple " +
            "specifying plotting interval.")
    return ((x_values, y_values) + args[1:], kwargs)
