"""
The :mod:`replot` module is a (sane) Python plotting module, abstracting on top
of Matplotlib.
"""
import collections
import shutil

import matplotlib.pyplot as plt
import numpy as np
import seaborn.apionly as sns

from replot import adaptive_sampling
from replot import exceptions as exc


__VERSION__ = "0.0.1"


class Figure():
    """
    The main class from :mod:`replot`, representing a figure. Can be used \
            directly or in a ``with`` statement.
    """
    def __init__(self,
                 xlabel="", ylabel="", title="",
                 palette="hls", max_colors=10,
                 legend=None):
        """
        Build a :class:`Figure` object.

        :param xlabel: Label for the X axis (optional).
        :param ylabel: Label for the Z axis (optional).
        :param title: Title of the figure (optional).
        :param palette: Color palette to use (optional). Defaults to a safe \
                palette with compatibility with colorblindness and black and \
                white printing.
        :type palette: Either a palette name (``str``) or a built palette.
        :param max_colors: Number of colors to use in the palette (optional). \
                Defaults to 10.
        :param legend: Whether to use a legend or not (optional). Defaults to \
                no legend, except if labels are found on provided plots. \
                ``False`` to disable completely. ``None`` for default \
                behavior. A string indicating position (:mod:`matplotlib` \
                format) to put a legend. ``True`` is a synonym for ``best`` \
                position.
        """
        # Set default values for attributes
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.title = title
        self.palette = palette
        self.max_colors = max_colors
        self.legend = legend
        self.plots = collections.defaultdict(list)  # keys are groups

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.show()

    def show(self):
        """
        Actually render and show the :class:`Figure` object.
        """
        # Use custom matplotlib context
        with mpl_custom_rc_context():
            # Tweak matplotlib to use seaborn
            sns.set()
            # Plot using specified color palette
            with sns.color_palette(palette=self.palette,
                                   n_colors=self.max_colors):
                # Create figure
                figure, axes = plt.subplots()
                # Add plots
                for group_ in self.plots:
                    for plot_ in self.plots[group_]:
                        tmp_plots = axes.plot(*(plot_[0]), **(plot_[1]))
                        # Do not clip line at the axes boundaries to prevent
                        # extremas from being cropped.
                        for tmp_plot in tmp_plots:
                            tmp_plot.set_clip_on(False)
                # Set properties
                axes.set_xlabel(self.xlabel)
                axes.set_ylabel(self.ylabel)
                axes.set_title(self.title)
                self._legend(axes)
                # Draw figure
                figure.show()
            # Do not forget to restore matplotlib state, in order not to
            # interfere with it.
            sns.reset_orig()

    def plot(self, *args, **kwargs):
        """
        Plot something on the :class:`Figure` object.

        .. note:: This function expects ``args`` and ``kwargs`` to support
        every possible case. You can either pass it (see examples):

            - A single argument, being a series of points or a function.
            - Two series of points representing X values and Y values \
                    (standard :mod:`matplotlib` behavior).
            - Two arguments being a function and a list of points at which \
                    it should be evaluated (X values).
            - Two arguments being a function and an interval represented by \
                    a tuple of its bounds.

        .. note:: ``kwargs`` arguments are passed to \
                    ``matplotlib.pyplot.plot``.

        .. note:: You can use some :mod:`replot` specific keyword arguments:

            - ``group`` which defines permits to group plots together, in \
                    subplots (one unicode character maximum).

        >>> with replot.figure() as fig: fig.plot(np.sin, (-1, 1))
        >>> with replot.figure() as fig: fig.plot(np.sin, [-1, -0.9, …, 1])
        >>> with replot.figure() as fig: fig.plot([1, 2, 3], [4, 5, 6])
        >>> with replot.figure() as fig: fig.plot([1, 2, 3],
                                                  [4, 5, 6], linewidth=2.0)
        >>> with replot.figure() as fig: fig.plot([1, 2, 3],
                                                  [4, 5, 6], group="a")
        """
        if len(args) == 0:
            raise exc.InvalidParameterError(
                "You should pass at least one argument to this function.")

        # Extra custom kwargs (the ones from replot but not matplotlib) from
        # kwargs
        kwargs, custom_kwargs = _handle_custom_plot_arguments(kwargs)

        if hasattr(args[0], "__call__"):
            # We want to plot a function
            plot_ = _plot_function(args[0], *(args[1:]), **kwargs)
        else:
            # Else, it is a point series, and we just have to store it for
            # later plotting.
            plot_ = (args, kwargs)

        # Add the plot to the correct group
        if "group" in custom_kwargs:
            self.plots[custom_kwargs["group"]].append(plot_)
        else:
            self.plots["default"].append(plot_)

        # Automatically set the legend if label is found
        # (only do it if legend is not explicitly suppressed)
        if "label" in kwargs and self.legend is None:
            self.legend = True

    def _legend(self, axes):
        """
        Helper function to handle ``legend`` attribute. It places the legend \
                correctly depending on attributes and required plots.

        :param axes: The :mod:`matplotlib` axes to put the legend on.
        """
        # If no legend is required, just pass
        if self.legend is None or self.legend is False:
            return

        if self.legend is True:
            # If there should be a legend, but no location provided, put it at
            # best location.
            location = "best"
        else:
            location = self.legend
        # Create aliases for "upper" / "top" and "lower" / "bottom"
        location.replace("top ", "upper ")
        location.replace("bottom ", "lower ")
        # Avoid warning if no labels were given for plots
        nb_labelled_plots = sum(["label" in plt[1] for plt in self.plots])
        if nb_labelled_plots > 0:
            # Add legend
            axes.legend(loc=location)


def plot(data, **kwargs):
    """
    Helper function to make one-liner plots. Typical use case is:

    >>> replot.plot([range(10),
                     (np.sin, (-5, 5)),
                     (lambda x: np.sin(x) + 4, (-10, 10), {"linewidth": 10}),
                     (lambda x: np.sin(x) - 4, (-10, 10), {"linewidth": 10}),
                     ([-i for i in range(5)], {"linewidth": 10})],
                    xlabel="some x label",
                    ylabel="some y label",
                    title="A title for the figure",
                    legend="best",
                    palette=replot.sns.color_palette("husl", 2))
    """
    # Init new figure
    figure = Figure(**kwargs)
    # data is a list of plotting commands
    for plot_ in data:
        # If we provide a tuple, handle it
        if isinstance(plot_, tuple):
            args = ()
            kwargs = {}
            # First case, only two items provided
            if len(plot_) == 2:
                # Parse args and kwargs according to type of items
                if isinstance(plot_[1], tuple):
                    args = (plot_[1],)
                elif isinstance(plot_[1], dict):
                    kwargs = plot_[1]
            # Second case, at least 3 items provided
            elif len(plot_) > 2:
                # Then, args and kwargs are well defined
                args = (plot_[1],)
                kwargs = plot_[2]
            # Pass the correct argument to plot function
            figure.plot(plot_[0], *args, **kwargs)
        else:
            figure.plot(plot_)
    figure.show()


def mpl_custom_rc_context():
    """
    Overload ``matplotlib.rcParams`` to enable advanced features if \
            available. In particular, use LaTeX if available.

    :returns: A ``matplotlib.rc_context`` object to use in a ``with`` \
            statement.
    """
    custom_rc = {}
    # Add LaTeX in rc if available
    if(shutil.which("latex") is not None and
       shutil.which("gs") is not None and
       shutil.which("dvipng") is not None):
        # LateX dependencies are all available
        custom_rc["text.usetex"] = True
        custom_rc["text.latex.unicode"] = True
    return plt.rc_context(rc=custom_rc)


def _handle_custom_plot_arguments(kwargs):
    """
    This method handles custom keyword arguments from plot in \
            :mod:`replot` which are not in :mod:`matplotlib` function.

    :param kwargs: A dictionary of keyword arguments to handle.
    :return: A tuple of :mod:`matplotlib` compatible keyword arguments \
            and of extra :mod:`replot` keyword arguments, both returned \
            as ``dict``.
    """
    custom_kwargs = {}
    # Handle "group" argument
    if "group" in kwargs:
        if len(kwargs["group"]) > 1:
            raise exc.InvalidParameterError(
                "Group name cannot be longer than one unicode character.")
        custom_kwargs["group"] = kwargs["group"]
        del kwargs["group"]
        return (kwargs, custom_kwargs)


def _plot_function(data, *args, **kwargs):
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
