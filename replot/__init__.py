"""
The :mod:`replot` module is a (sane) Python plotting module, abstracting on top
of Matplotlib.
"""
import collections
import math
import os
import shutil

import matplotlib as mpl
# Use "agg" backend automatically if no display is available.
try:
    os.environ["DISPLAY"]
except KeyError:
    mpl.use("agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn.apionly as sns

from replot import adaptive_sampling
from replot import exceptions as exc
from replot import grid_parser
from replot import tools


__VERSION__ = "0.0.1"

# Constants
_DEFAULT_GROUP = "_"


class Figure():
    """
    The main class from :mod:`replot`, representing a figure. Can be used \
            directly or in a ``with`` statement.
    """
    def __init__(self,
                 xlabel="", ylabel="", title="",
                 palette="hls", max_colors=10,
                 legend=None, savepath=None, grid=None):
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
        :param savepath: A path to save the image to (optional). If set, \
                the image will be saved on exiting a `with` statement.
        :param grid: A dict containing the width and height of the grid, and \
                a description of the grid as a list of subplots. Each subplot \
                is a tuple of \
                ``((y_position, x_position), symbol, (rowspan, colspan))``. \
                No check for grid validity is being made. You can set it to \
                ``False`` to disable it completely.

        .. note:: If you use group plotting, ``xlabel``, ``ylabel`` and \
                ``legend`` will be set uniformly for every subplot. If you \
                wish to set different properties for every subplots, you \
                should pass a dict for these properties, keys being the \
                group symbols and values being the value for each subplot.
        """
        # Set default values for attributes
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.title = title
        self.palette = palette
        self.max_colors = max_colors
        self.legend = legend
        self.plots = collections.defaultdict(list)  # keys are groups
        self.grid = grid
        self.savepath = savepath

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        # Do not render the figure if an exception was raised
        if exception_type is None:
            if self.savepath is not None:
                self.save()
            else:
                self.show()

    def save(self, *args, **kwargs):
        """
        Render and save the figure. Also show the figure if possible.

        .. note:: Signature is the same as the one from \
                ``matplotlib.pyplot.savefig``. You should refer to its \
                documentation for lengthy details.

        .. note:: Typical use is:
            >>> with replot.Figure() as figure: figure.save("SOME_FILENAME")

        .. note:: If a ``savepath`` has been provided to the :class:`Figure` \
                object, you can call ``figure.save()`` without argument and \
                this path will be used.
        """
        if len(args) == 0 and self.savepath is not None:
            args = (self.savepath,)

        figure = self._render()
        figure.savefig(*args, **kwargs)

    def show(self):
        """
        Render and show the :class:`Figure` object.
        """
        figure = self._render()
        figure.show()

    def set_grid(self, grid_description=None, auto=False):
        """
        Apply a grid layout on the figure (subplots). Subplots are based on \
                defined groups (see ``group`` keyword to \
                ``replot.Figure.plot``).

        :param grid_description: A list of rows. Each row is a string \
                containing the groups to display (can be seen as ASCII art).
        :param auto: Whether the grid should be guessed automatically from \
                groups or not (optional). Can be a boolean or a dict having \
                the possible ``height`` (int), ``width`` (int) and  \
                ``ignore_groups`` (boolean) fields to force the height or \
                width of the resulting grid, or force every plot to go in \
                a separate subplot, regardless of its group.

        .. note:: Groups are a single unicode character. If a group does not \
                contain any plot, the resulting subplot will simply be empty.

        .. note:: Note that if you do not include the default group in the \
                grid description, it will not be shown.

        >>> with replot.Figure() as fig: fig.set_grid(["AAA",
                                                       "BBC"
                                                       "DEC"])
        """
        # Handle auto gridifying
        if auto is not False:
            if isinstance(auto, dict):
                self._set_auto_grid(**auto)
            else:
                self._set_auto_grid()
            return

        # Default parameters
        if grid_description is None:
            grid_description = []
        elif grid_description is False:
            # Disable the grid and return
            self.grid = False
            return

        # Check that grid is not empty
        if len(grid_description) == 0:
            raise exc.InvalidParameterError("Grid cannot be an empty list.")
        # Check that all rows have the same number of elements
        for row in grid_description:
            if len(row) != len(grid_description[0]):
                raise exc.InvalidParameterError(
                    "All rows must have the same number of elements.")
        # Parse the ASCII art grid
        parsed_grid = grid_parser.parse_ascii(grid_description)
        if parsed_grid is None:
            # If grid is not valid, raise an exception
            raise exc.InvalidParameterError(
                "Invalid grid provided. You did not use rectangular areas " +
                "for each group.")
        # Set the grid
        self.grid = parsed_grid

    def _set_auto_grid(self, height=None, width=None, ignore_groups=False):
        """
        Apply an automatic grid on the figure, trying to fit best to the \
                number of plots.

        .. note:: This method must be called after all the plots \
                have been added to the figure, or the grid will miss some \
                groups.

        .. note:: The grid will be filled by the groups in lexicographic \
                order. Unassigned plots go to the last subplot.

        :param height: An optional ``height`` for the grid.
        :param width: An optional ``height`` for the grid.
        :param ignore_groups: By default, ``gridify`` will use groups to \
                organize plots in different subplots. If you want to put \
                every plot in a different subplot, without dealing with \
                groups, you can set this to ``True``.
        """
        if ignore_groups:
            # If we want to ignore groups, we will start by creating a new
            # group for every existing plot
            existing_plots = []
            for group_ in self.plots:
                existing_plots.extend(self.plots[group_])
            self.plots = collections.defaultdict(list,
                                                 {chr(i): [existing_plots[i]]
                                                  for i in
                                                  range(len(existing_plots))})

        # Find the optimal layout
        nb_groups = len(self.plots)
        if height is None and width is not None:
            height = math.ceil(nb_groups / width)
        elif width is None and height is not None:
            width = math.ceil(nb_groups / height)
        else:
            height, width = _optimal_grid(nb_groups)

        # Apply the layout
        groups = sorted([k
                         for k in self.plots.keys()
                         if k != _DEFAULT_GROUP and len(self.plots[k]) > 0])
        if len(self.plots[_DEFAULT_GROUP]) > 0:
            # Handle default group separately
            groups.append(_DEFAULT_GROUP)
        grid_description = ["".join(batch)
                            for batch in tools.batch(groups, width)]
        self.set_grid(grid_description)

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

            - ``group`` which permits to group plots together, in \
                    subplots (one unicode character maximum). ``group`` \
                    keyword will not affect the render unless you state \
                    :mod:`replot` to use subplots. Note that ``_`` is a \
                    reserved group name which cannot be used.

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

        # Extract custom kwargs (the ones from replot but not matplotlib) from
        # kwargs
        if kwargs is not None:
            kwargs, custom_kwargs = _handle_custom_plot_arguments(kwargs)
        else:
            custom_kwargs = {}

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
            self.plots[_DEFAULT_GROUP].append(plot_)

        # Automatically set the legend if label is found
        # (only do it if legend is not explicitly suppressed)
        if "label" in kwargs and self.legend is None:
            self.legend = True

    def _legend(self, axe, overload_legend=None):
        """
        Helper function to handle ``legend`` attribute. It places the legend \
                correctly depending on attributes and required plots.

        :param axe: The :mod:`matplotlib` axe to put the legend on.
        :param overload_legend: An optional legend specification to use \
                instead of the ``legend`` attribute.
        """
        if overload_legend is None:
            overload_legend = self.legend

        # If no legend is required, just pass
        if overload_legend is None or overload_legend is False:
            return

        if overload_legend is True:
            # If there should be a legend, but no location provided, put it at
            # best location.
            location = "best"
        else:
            location = overload_legend
        # Create aliases for "upper" / "top" and "lower" / "bottom"
        location.replace("top ", "upper ")
        location.replace("bottom ", "lower ")
        # Avoid warning if no labels were given for plots
        nb_labelled_plots = sum(["label" in plt[1]
                                 for group in self.plots.values()
                                 for plt in group])
        if nb_labelled_plots > 0:
            # Add legend
            axe.legend(loc=location)

    def _grid(self):
        """
        Create subplots according to the grid description.

        :returns: A tuple containing the figure object as first element, and \
                a dict mapping the symbols of the groups to matplotlib axes \
                as second element.
        """
        if self.grid is False:
            # If grid is disabled, we plot every group in the same sublot.
            axes = {}
            figure, axe = plt.subplots()
            for subplot in self.plots:
                axes[subplot] = axe
            return figure, axes
        elif self.grid is None:
            # If no grid is provided, create an auto grid for the figure.
            self._set_auto_grid()

        # Axes is a dict associating symbols to matplotlib axes
        axes = {}
        figure = plt.figure()
        # Build all the axes
        grid_size = (self.grid["height"], self.grid["width"])
        for subplot in self.grid["grid"]:
            position, symbol, (rowspan, colspan) = subplot
            axes[symbol] = plt.subplot2grid(grid_size,
                                            position,
                                            colspan=colspan,
                                            rowspan=rowspan)
        if _DEFAULT_GROUP not in axes:
            # Set the default group axe to None if it is not in the grid
            axes[_DEFAULT_GROUP] = None
        return figure, axes

    def _set_axes_properties(self, axe, group_):
        # Set xlabel
        if isinstance(self.xlabel, dict):
            try:
                axe.set_xlabel(self.xlabel[group_])
            except KeyError:
                # No entry for this axe in the dict, pass it
                pass
        else:
            axe.set_xlabel(self.xlabel)
        # Set ylabel
        if isinstance(self.ylabel, dict):
            try:
                axe.set_ylabel(self.ylabel[group_])
            except KeyError:
                # No entry for this axe in the dict, pass it
                pass
        else:
            axe.set_ylabel(self.ylabel)
        # Set title
        if isinstance(self.title, dict):
            try:
                axe.set_ylabel(self.title[group_])
            except KeyError:
                # No entry for this axe in the dict, pass it
                pass
        else:
            axe.set_title(self.title)
        # Set legend
        if isinstance(self.legend, dict):
            try:
                self._legend(axe, overload_legend=self.legend[group_])
            except KeyError:
                # No entry for this axe in the dict, use default argument
                # That is put a legend except if no plots on this axe.
                self._legend(axe, overload_legend=True)
        else:
            self._legend(axe)

    def _render(self):
        """
        Actually render the figure.

        :returns: A :mod:`matplotlib` figure.
        """
        figure = None
        # Use custom matplotlib context
        with mpl_custom_rc_context():
            # Tweak matplotlib to use seaborn
            sns.set()
            # Plot using specified color palette
            with sns.color_palette(palette=self.palette,
                                   n_colors=self.max_colors):
                # Create figure
                figure, axes = self._grid()
                # Add plots
                for group_ in self.plots:
                    # Get the axe corresponding to current group
                    try:
                        axe = axes[group_]
                    except KeyError:
                        # If not found, plot in the default group
                        axe = axes[_DEFAULT_GROUP]
                    # Skip this plot if the axe is None
                    if axe is None:
                        continue
                    # Plot
                    for plot_ in self.plots[group_]:
                        tmp_plots = axe.plot(*(plot_[0]), **(plot_[1]))
                        # Do not clip line at the axes boundaries to prevent
                        # extremas from being cropped.
                        for tmp_plot in tmp_plots:
                            tmp_plot.set_clip_on(False)
                    # Set ax properties
                    self._set_axes_properties(axe, group_)
            # Do not forget to restore matplotlib state, in order not to
            # interfere with it.
            sns.reset_orig()
        return figure


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
        elif kwargs["group"] == _DEFAULT_GROUP:
            raise exc.InvalidParameterError(
                "'%s' is a reserved group name." % (_DEFAULT_GROUP,))
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


def _optimal_grid(nb_items):
    """
    (Naive) attempt to find an optimal grid layout for N elements.

    :param nb_items: The number of square elements to put on the grid.
    :returns: A tuple ``(height, width)`` containing the number of rows and \
            the number of cols of the resulting grid.

    >>> _optimal_grid(2)
    (1, 2)

    >>> _optimal_grid(3)
    (1, 3)

    >>> _optimal_grid(4)
    (2, 2)
    """
    # Compute first possibility
    height1 = math.floor(math.sqrt(nb_items))
    width1 = math.ceil(nb_items / height1)

    # Compute second possibility
    width2 = math.ceil(math.sqrt(nb_items))
    height2 = math.ceil(nb_items / width2)

    # Minimize the product of height and width
    if height1 * width1 < height2 * width2:
        height, width = height1, width1
    else:
        height, width = height2, width2

    return (height, width)
