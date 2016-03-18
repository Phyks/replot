"""
The :mod:`replot` module is a (sane) Python plotting module, abstracting on top
of Matplotlib.
"""
import collections
import math
import os
import shutil

import cycler
import matplotlib as mpl
# Use "agg" backend automatically if no display is available.
try:
    os.environ["DISPLAY"]
except KeyError:
    mpl.use("agg")
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import palettable

from replot import adaptive_sampling
from replot import exceptions as exc
from replot import grid_parser
from replot import tools


__VERSION__ = "0.0.1"

#############
# CONSTANTS #
#############
_DEFAULT_GROUP = "_"


# Default palette is husl palette with length 10 color cycle
def _default_palette(n):
    """
    Default palette is a CubeHelix perceptual rainbow palette with length the
    number of plots.

    :param n: The number of colors in the palette.
    :returns: The palette as a list of colors (as RGB tuples).
    """
    return palettable.cubehelix.Cubehelix.make(
        start_hue=240., end_hue=-300., min_sat=1., max_sat=2.5,
        min_light=0.3, max_light=0.8, gamma=.9, n=n).mpl_colors


class Figure():
    """
    The main class from :mod:`replot`, representing a figure. Can be used \
            directly or in a ``with`` statement.
    """
    def __init__(self,
                 xlabel="", ylabel="", title="",
                 xrange=None, yrange=None,
                 palette=_default_palette,
                 legend=None, savepath=None, grid=None,
                 custom_mpl_rc=None):
        """
        Build a :class:`Figure` object.

        :param xlabel: Label for the X axis (optional).
        :param ylabel: Label for the Z axis (optional).
        :param title: Title of the figure (optional).
        :param xrange: Range of the X axis (optional), as a tuple \
                representing the interval.
        :param yrange: Range of the Y axis (optional), as a tuple \
                representing the interval.
        :param palette: Color palette to use (optional). Defaults to a safe \
                palette with compatibility with colorblindness and black and \
                white printing.
        :type palette: Either a list of colors (as RGB tuples) or a function \
                to call with number of plots as parameter and which returns a \
                list of colors (as RGB tuples). You can also pass a Seaborn \
                palette directly, or use a Palettable Palette.mpl_colors.
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
        :param custom_mpl_rc: An optional dict to overload some \
                :mod:`matplotlib` rc params.

        .. note:: If you use group plotting, ``xlabel``, ``ylabel``, \
                ``legend``, ``xrange``, ``yrange`` and ``zrange``  will be \
                set uniformly for every subplot. If you wish to set \
                different properties for every subplots, you \
                should pass a dict for these properties, keys being the \
                group symbols and values being the value for each subplot.
        """
        # Set default values for attributes
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.title = title
        self.xrange = xrange
        self.yrange = yrange
        self.palette = palette
        self.legend = legend
        self.plots = collections.defaultdict(list)  # keys are groups
        self.grid = grid
        self.savepath = savepath
        self.custom_mpl_rc = None
        # Working attributes
        self.figure = None
        self.axes = None
        self.animation = {"type": False,
                          "args": (), "kwargs": {},
                          "persist": []}

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

        self.render()
        if self.figure is not None:
            self.figure.savefig(*args, **kwargs)
        else:
            raise exc.InvalidFigure("Invalid figure.")

    def show(self):
        """
        Render and show the :class:`Figure` object.
        """
        self.render()
        if self.figure is not None:
            self.figure.show()
        else:
            raise exc.InvalidFigure("Invalid figure.")

    def set_grid(self, grid_description=None,
                 height=None, width=None, ignore_groups=False,
                 auto=False):
        """
        Apply a grid layout on the figure (subplots). Subplots are based on \
                defined groups (see ``group`` keyword to \
                ``replot.Figure.plot``).

        :param grid_description: A list of rows. Each row is a string \
                containing the groups to display (can be seen as ASCII art). \
                Can be a single string in case of a single row.
        :param height: An optional ``height`` for the grid, implies \
                ``auto=True``.
        :param width: An optional ``height`` for the grid, implies \
                ``auto=True``.
        :param ignore_groups: (optional, implies ``auto=True``) By default, \
                ``set_grid`` will use groups to organize plots in different \
                subplots. If you want to put every plot in a different \
                subplot, regardless of their groups, you can set this \
                to ``True``.
        :param auto: Whether the grid should be guessed automatically from \
                groups or not (optional).

        .. note:: Groups are a single unicode character. If a group does not \
                contain any plot, the resulting subplot will simply be empty.

        .. note:: Note that if you do not include the default group in the \
                grid description, it will not be shown.

        >>> with replot.Figure() as fig: fig.set_grid(["AAA",
                                                       "BBC"
                                                       "DEC"])
        """
        # Handle auto gridifying
        if auto or height is not None or width is not None or ignore_groups:
            self._set_auto_grid(height, width, ignore_groups)
            return

        # Default parameters
        if grid_description is None:
            grid_description = []
        elif grid_description is False:
            # Disable the grid and return
            self.grid = False
            return
        elif isinstance(grid_description, str):
            # If a single string is provided, enclose it in a list.
            grid_description = [grid_description]

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
        :param ignore_groups: By default, ``set_grid`` will use groups to \
                organize plots in different subplots. If you want to put \
                every plot in a different subplot, regardless of their \
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
            - ``line`` which can be set to ``True``/``False`` to plot \
                    broken lines or discrete data series.
            - ``logscale`` which can be either ``log`` or ``loglog`` to use \
                    such scales.
            - ``orthonormal`` (boolean) to force axis to be orthonormal.
            - ``xlim`` and ``ylim`` which are tuples of intervals on the \
                    x and y axis.
            - ``invert`` (boolean) invert X and Y axis on the plot. Invert \
                    the axes labels as well.
            - ``rotate`` (angle in degrees) rotate the plot by the angle in \
                    degrees. Leave the labels untouched.
            - ``frame`` to specify a frame on which the plot should appear \
                    when calling ``animate`` afterwards. Default behavior is \
                    to increase the frame number between each plots. Frame \
                    count starts at 0.

        .. note:: Note that this API call considers list of tuples as \
                list of (x, y) coordinates to plot, contrary to standard \
                matplotlib API which considers it is two different plots.

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
            if hasattr(args[0], "__iter__"):
                try:
                    # If we pass it a list of tuples, consider it as a list of
                    # (x, y) coordinates contrary to the standard matplotlib
                    # behavior
                    x_list, y_list = zip(*args[0])
                    args = (list(x_list),
                            list(y_list)) + args[1:]
                except (TypeError, StopIteration, AssertionError):
                    pass
            plot_ = (args, kwargs)

        # Keep track of the custom kwargs
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
                new_X_list.append(
                    np.cos(custom_kwargs["rotate"]) * x +
                    np.sin(custom_kwargs["rotate"]) * y)
                new_Y_list.append(
                    -np.sin(custom_kwargs["rotate"]) * x +
                    np.cos(custom_kwargs["rotate"]) * y)
            plot_ = (
                (new_X_list, new_Y_list) + plot_[0][2:],
                plot_[1], plot_[2])

        # Add the plot to the correct group
        if "group" in custom_kwargs:
            group_ = custom_kwargs["group"]
        else:
            group_ = _DEFAULT_GROUP
        self.plots[group_].append(plot_)

        # Automatically set the legend if label is found
        # (only do it if legend is not explicitly suppressed)
        if "label" in kwargs and self.legend is None:
            self.legend = True

    def logplot(self, *args, **kwargs):
        """
        Plot something on the :class:`Figure` object, in log scale.

        .. note:: See :func:`replot.Figure.plot` for the full documentation.

        >>> with replot.figure() as fig: fig.logplot(np.log, (-1, 1))
        """
        kwargs["logscale"] = "log"
        self.plot(*args, **kwargs)

    def loglogplot(self, *args, **kwargs):
        """
        Plot something on the :class:`Figure` object, in log-log scale.

        .. note:: See :func:`replot.Figure.plot` for the full documentation.

        >>> with replot.figure() as fig: fig.logplot(np.log, (-1, 1))
        """
        kwargs["logscale"] = "loglog"
        self.plot(*args, **kwargs)

    def animate(self, *args, **kwargs):
        """
        Create an animation.

        You can either:
            - pass it a function TODO
            - use it directly without arguments to create an animation from \
                    the previously plot commands.
        """
        # TODO
        self.animation["type"] = "gif"
        self.animation["args"] = args
        self.animation["kwargs"] = kwargs

    def _legend(self, axis, overload_legend=None):
        """
        Helper function to handle ``legend`` attribute. It places the legend \
                correctly depending on attributes and required plots.

        :param axis: The :mod:`matplotlib` axis to put the legend on.
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
            axis.legend(loc=location)

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
            figure, axis = plt.subplots()
            # Set the palette for the subplot
            axis.set_prop_cycle(
                self._build_cycler_palette(sum([len(i)
                                                for i in self.plots.values()]))
            )
            # Set the axis for every subplot
            for subplot in self.plots:
                axes[subplot] = axis

            # Set attributes
            self.figure = figure
            self.axes = axes
            # Return
            return
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
            # Set the palette for the subplot
            axes[symbol].set_prop_cycle(
                self._build_cycler_palette(len(self.plots[symbol])))
        if _DEFAULT_GROUP not in axes:
            # Set the default group axis to None if it is not in the grid
            axes[_DEFAULT_GROUP] = None

        # Set attributes
        self.figure = figure
        self.axes = axes

    def _set_axes_properties(self, axis, group_):
        is_inverted_axis = len(
            [i
             for i in self.plots[group_]
             if "invert" in i[2] and i[2]["invert"]]
        ) > 0
        # Set xlabel
        if isinstance(self.xlabel, dict):
            try:
                if is_inverted_axis:
                    # Handle axis inversion
                    axis.set_ylabel(self.xlabel[group_])
                else:
                    axis.set_xlabel(self.xlabel[group_])
            except KeyError:
                # No entry for this axis in the dict, pass it
                pass
        else:
            if is_inverted_axis:
                # Handle axis inversion
                axis.set_ylabel(self.xlabel)
            else:
                axis.set_xlabel(self.xlabel)
        # Set ylabel
        if isinstance(self.ylabel, dict):
            try:
                if is_inverted_axis:
                    # Handle axis inversion
                    axis.set_xlabel(self.ylabel[group_])
                else:
                    axis.set_ylabel(self.ylabel[group_])
            except KeyError:
                # No entry for this axis in the dict, pass it
                pass
        else:
            if is_inverted_axis:
                # Handle axis inversion
                axis.set_xlabel(self.ylabel)
            else:
                axis.set_ylabel(self.ylabel)
        # Set title
        if isinstance(self.title, dict):
            try:
                axis.set_ylabel(self.title[group_])
            except KeyError:
                # No entry for this axis in the dict, pass it
                pass
        else:
            axis.set_title(self.title)
        # Set legend
        if isinstance(self.legend, dict):
            try:
                self._legend(axis, overload_legend=self.legend[group_])
            except KeyError:
                # No entry for this axis in the dict, use default argument
                # That is put a legend except if no plots on this axis.
                self._legend(axis, overload_legend=True)
        else:
            self._legend(axis)
        # Set xrange
        if isinstance(self.xrange, dict):
            try:
                if self.xrange[group_] is not None:
                    axis.set_xlim(*self.xrange[group_])
            except KeyError:
                # No entry for this axis in the dict, pass it
                pass
        else:
            if self.xrange is not None:
                axis.set_xlim(*self.xrange)
        # Set yrange
        if isinstance(self.yrange, dict):
            try:
                if self.yrange[group_] is not None:
                    axis.set_ylim(*self.yrange[group_])
            except KeyError:
                # No entry for this axis in the dict, pass it
                pass
        else:
            if self.yrange is not None:
                axis.set_ylim(*self.yrange)

    def _build_cycler_palette(self, n):
        """
        Build a cycler palette for the selected subplot.

        :param n: number of colors in the palette.
        :returns: a cycler object for the palette.
        """
        if hasattr(self.palette, "__call__"):
            return cycler.cycler("color", self.palette(n))
        else:
            return cycler.cycler("color", self.palette)

    def render(self):
        """
        Actually render the figure.

        :returns: A :mod:`matplotlib` figure.
        """
        # Use custom matplotlib context
        with mpl_custom_rc_context(rc=self.custom_mpl_rc):
            if self.figure is None or self.axes is None:
                # Create figure if necessary
                self._grid()

            if self.animation["type"] is False:
                self._render_no_animation()
            elif self.animation["type"] == "gif":
                self._render_gif_animation()
            elif self.animation["type"] == "animation":
                # TODO
                return None
            else:
                return None
        self.figure.tight_layout(pad=1)

    def _render_gif_animation(self):
        """
        Handle the render of a GIF-like animation, cycling through the plots.

        :returns: A :mod:`matplotlib` figure.
        """
        # Init
        # TODO
        self.axes[_DEFAULT_GROUP].set_xlim((-2, 2))
        self.axes[_DEFAULT_GROUP].set_ylim((-2, 2))
        line, = self.axes[_DEFAULT_GROUP].plot([], [])
        # Define an animation function (closure)
        def animate(i):
            # TODO
            x = np.linspace(0, 2, 1000)
            y = np.sin(2 * np.pi * (x - 0.01 * i))
            line.set_data(x, y)
            return line,
        # Set default kwargs
        default_args = (self.figure, animate)
        default_kwargs = {
            "frames": 200,
            "interval": 20,
            "blit": True,
        }
        # Update with overloaded arguments
        default_args = default_args + self.animation["args"]
        default_kwargs.update(self.animation["kwargs"])
        # Keep track of animation object, as it has to persist
        self.animation["persist"] = [
            animation.FuncAnimation(*default_args, **default_kwargs)]
        return self.figure

    def _render_no_animation(self):
        """
        Handle the render of the figure when no animation is used.

        :returns: A :mod:`matplotlib` figure.
        """
        # Add plots
        for group_ in self.plots:
            # Get the axis corresponding to current group
            try:
                axis = self.axes[group_]
            except KeyError:
                # If not found, plot in the default group
                axis = self.axes[_DEFAULT_GROUP]
            # Skip this plot if the axis is None
            if axis is None:
                continue
            # Plot
            for plot_ in self.plots[group_]:
                tmp_plots = axis.plot(*(plot_[0]), **(plot_[1]))
                # Handle custom kwargs at plotting time
                if "logscale" in plot_[2]:
                    if plot_[2]["logscale"] == "log":
                        axis.set_xscale("log")
                    elif plot_[2]["logscale"] == "loglog":
                        axis.set_xscale("log")
                        axis.set_yscale("log")
                if "orthonormal" in plot_[2] and plot_[2]["orthonormal"]:
                    axis.set_aspect("equal")
                if "xlim" in plot_[2]:
                    axis.set_xlim(*plot_[2]["xlim"])
                if "ylim" in plot_[2]:
                    axis.set_ylim(*plot_[2]["ylim"])
                # Do not clip line at the axes boundaries to prevent
                # extremas from being cropped.
                for tmp_plot in tmp_plots:
                    tmp_plot.set_clip_on(False)
            # Set ax properties
            self._set_axes_properties(axis, group_)
        return self.figure


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
                    palette=seaborn.color_palette("husl", 2))
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


def _mpl_custom_rc_scaling():
    """
    Scale the elements of the figure to get a better rendering.

    Settings borrowed from
    [Seaborn](https://github.com/mwaskom/seaborn/blob/master/seaborn/rcmod.py#L344).

    :returns: a :mod:`matplotlib` ``rcParams``-like dict.
    """
    rc_params = {
        "figure.figsize": np.array([8, 5.5]),
        # Set misc font sizes
        "font.size": 12,
        "axes.labelsize": 11,
        "axes.titlesize": 12,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        # Set misc linewidth
        "grid.linewidth": 1,
        "lines.linewidth": 1.75,
        "patch.linewidth": .3,
        "lines.markersize": 7,
        "lines.markeredgewidth": 1.75,
        # Disable ticks
        "xtick.major.width": 0,
        "ytick.major.width": 0,
        "xtick.minor.width": 0,
        "ytick.minor.width": 0,
        # Set ticks padding
        "xtick.major.pad": 7,
        "ytick.major.pad": 7,
    }
    return rc_params


def _mpl_custom_rc_axes_style():
    """
    Set the style of the plot and the axes. Things like set a grid etc.

    Settings borrowed from
    [Seaborn](https://github.com/mwaskom/seaborn/blob/master/seaborn/rcmod.py#L344).

    :returns: a :mod:`matplotlib` ``rcParams``-like dict.
    """
    # Use dark gray instead of black for better readability on screen
    dark_gray = ".15"
    rc_params = {
        # Colors
        "figure.facecolor": "white",
        "text.color": dark_gray,
        # Legend
        "legend.frameon": False,  # No frame around legend
        "legend.numpoints": 1,
        "legend.scatterpoints": 1,
        # Ticks
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.color": dark_gray,
        "ytick.color": dark_gray,
        "lines.solid_capstyle": "round",
        # Axes
        "axes.axisbelow": True,
        "axes.linewidth": 0,
        "axes.labelcolor": dark_gray,
        "axes.grid": True,
        "axes.facecolor": "EAEAF2",
        "axes.edgecolor": "white",
        # Grid
        "grid.linestyle": "-",
        "grid.color": "white",
        # Image
        "image.cmap": "Greys"
    }
    return rc_params


def mpl_custom_rc_context(rc=None):
    """
    Overload ``matplotlib.rcParams`` to enable advanced features if \
            available. In particular, use LaTeX if available.

    :param rc: An optional dict to overload some :mod:`matplotlib` rc params.
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
    # Use LaTeX default font family
    # See https://stackoverflow.com/questions/17958485/matplotlib-not-using-latex-font-while-text-usetex-true
    custom_rc["font.family"] = "serif"
    custom_rc["font.serif"] = "cm"
    # Scale everything
    custom_rc.update(_mpl_custom_rc_scaling())
    # Set axes style
    custom_rc.update(_mpl_custom_rc_axes_style())
    # Overload if necessary
    if rc is not None:
        custom_rc.update(rc)
    # Return a context object
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
    # Handle "line" argument
    if "line" in kwargs:
        if not kwargs["line"]:  # If should not draw lines, set kwargs for it
            kwargs["linestyle"] = "None"
            kwargs["marker"] = "x"
        del kwargs["line"]
    # Handle "logscale" argument
    if "logscale" in kwargs:
        custom_kwargs["logscale"] = kwargs["logscale"]
        del kwargs["logscale"]
    # Handle "orthonormal" argument
    if "orthonormal" in kwargs:
        custom_kwargs["orthonormal"] = kwargs["orthonormal"]
        del kwargs["orthonormal"]
    # Handle "xlim" argument
    if "xlim" in kwargs:
        custom_kwargs["xlim"] = kwargs["xlim"]
        del kwargs["xlim"]
    # Handle "ylim" argument
    if "ylim" in kwargs:
        custom_kwargs["ylim"] = kwargs["ylim"]
        del kwargs["ylim"]
    # Handle "invert" argument
    if "invert" in kwargs:
        custom_kwargs["invert"] = kwargs["invert"]
        del kwargs["invert"]
    # Handle "rotate" argument
    if "rotate" in kwargs:
        # Convert angle to radians
        custom_kwargs["rotate"] = kwargs["rotate"] * np.pi / 180
        del kwargs["rotate"]
    # Handle "frame" argument
    if "frame" in kwargs:
        custom_kwargs["frame"] = kwargs["frame"]
        del kwargs["frame"]
    else:
        custom_kwargs["frame"] = 0
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
