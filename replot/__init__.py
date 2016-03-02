"""
The :mod:`replot` module is a (sane) Python plotting module, abstracting on top
of Matplotlib.
"""
import matplotlib.pyplot as plt
import numpy as np
import seaborn.apionly as sns

from replot import exceptions as exc


__VERSION__ = "0.0.1"

# Constants
DEFAULT_NB_SAMPLES = 1000
DEFAULT_X_INTERVAL = np.linspace(-10, 10,
                                 DEFAULT_NB_SAMPLES)


# TODO: Remove it, this is interfering with matplotlib
plt.rcParams['figure.figsize'] = (10.0, 8.0)  # Larger figures by default
plt.rcParams['text.usetex'] = True  # Use LaTeX rendering


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
        self.plots = []

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.show()

    def show(self):
        """
        Actually render and show the :class:`Figure` object.
        """
        # Tweak matplotlib to use seaborn
        sns.set()
        # Plot using specified color palette
        with sns.color_palette(palette=self.palette, n_colors=self.max_colors):
            # Create figure
            figure, axes = plt.subplots()
            # Add plots
            for plot_ in self.plots:
                tmp_plots = axes.plot(*(plot_[0]), **(plot_[1]))
                # Do not clip line at the axes boundaries to prevent extremas
                # from being cropped.
                for tmp_plot in tmp_plots:
                    tmp_plot.set_clip_on(False)
            # Set properties
            axes.set_xlabel(self.xlabel)
            axes.set_ylabel(self.ylabel)
            axes.set_title(self.title)
            self._legend(axes)
            # Draw figure
            figure.show()
        # Do not forget to restore matplotlib state, in order not to interfere
        # with it.
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

        .. note:: ``kwargs`` arguments are directly passed to \
                    ``matplotlib.pyplot.plot``.

        >>> with replot.figure() as fig: fig.plot(np.sin)
        >>> with replot.figure() as fig: fig.plot(np.sin, (-1, 1))
        >>> with replot.figure() as fig: fig.plot(np.sin, [-1, -0.9, …, 1])
        >>> with replot.figure() as fig: fig.plot([1, 2, 3], [4, 5, 6])
        >>> with replot.figure() as fig: fig.plot([1, 2, 3],
                                                  [4, 5, 6], linewidth=2.0)
        """
        if len(args) == 0:
            raise exc.InvalidParameterError(
                "You should pass at least one argument to this function.")

        if hasattr(args[0], "__call__"):
            # We want to plot a function
            self._plot_function(args[0], *(args[1:]), **kwargs)
        else:
            # Else, it is a point series, and we just have to store it for
            # later plotting.
            self.plots.append((args, kwargs))

        # Automatically set the legend if label is found
        # (only do it if legend is not explicitly suppressed)
        if "label" in kwargs and self.legend is None:
            self.legend = True

    def _plot_function(self, data, *args, **kwargs):
        """
        Helper function to handle plotting of unevaluated functions (trying \
                to evaluate it nicely and rendering the plot).

        :param data: The function to plot.

        .. seealso:: The documentation of the ``replot.Figure.plot`` method.

        .. note:: ``args`` is used to handle the interval or point series on \
                which the function should be evaluated. ``kwargs`` are passed \
                directly to ``matplotlib.pyplot.plot`.
        """
        # TODO: Better default interval and so on, adaptive plotting
        if len(args) == 0:
            # No interval specified, using default one
            x_values = DEFAULT_X_INTERVAL
        elif isinstance(args[0], (list, np.ndarray)):
            # List of points specified
            x_values = args[0]
        elif isinstance(args[0], tuple):
            # Interval specified, generate a list of points
            x_values = np.linspace(args[0][0], args[0][1],
                                   DEFAULT_NB_SAMPLES)
        else:
            raise exc.InvalidParameterError(
                "Second parameter in plot command should be a tuple " +
                "specifying plotting interval.")
        y_values = [data(i) for i in x_values]
        self.plots.append(((x_values, y_values) + args[1:], kwargs))

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
                     np.cos,
                     (lambda x: np.sin(x) + 4, (-10, 10), {"linewidth": 10}),
                     (lambda x: np.sin(x) - 4, {"linewidth": 10}),
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
