"""
"""
import collections
import math
import os

import matplotlib as mpl
# Use "agg" backend automatically if no display is available.
try:
    os.environ["DISPLAY"]
except KeyError:
    mpl.use("agg")
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np

from replot import constants
from replot import exceptions as exc
from replot import tools
from replot.grid import layout
from replot.grid import parser as grid_parser
from replot.helpers import custom_kwargs as custom_kwargs_parser
from replot.helpers import custom_mpl
from replot.helpers import palette as rpalette
from replot.helpers import plot as plot_helpers
from replot.helpers import render as render_helpers


class Figure():
    """
    The main class from :mod:`replot`, representing a figure. Can be used \
            directly or in a ``with`` statement.
    """
    def __init__(self,
                 xlabel="", ylabel="", title="",
                 xrange=None, yrange=None,
                 palette=rpalette.default,
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
        self.custom_mpl_rc = custom_mpl_rc
        # Working attributes
        self.animation = {"type": False,
                          "args": (), "kwargs": {},
                          "persist": []}

    def __enter__(self):  # Allow use in a with statement
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

        .. note:: If a ``savepath`` has been provided to the :class:`Figure` \
                object, you can call ``figure.save()`` without argument and \
                this path will be used.

        >>> with replot.Figure() as figure: figure.save("SOME_FILENAME")
        >>> with replot.Figure(savepath="SOME_FILENAME") as figure: pass
        """
        if len(args) == 0 and self.savepath is not None:
            args = (self.savepath,)

        figure = self.render()
        if figure is not None:
            figure.savefig(*args, **kwargs)
        else:
            raise exc.InvalidFigure("Invalid figure.")

    def show(self):
        """
        Render and show the :class:`Figure` object.
        """
        figure = self.render()
        if figure is not None:
            figure.show()
        else:
            raise exc.InvalidFigure("Invalid figure.")

    def render(self):
        """
        Actually render the figure.

        :returns: A :mod:`matplotlib` figure object.
        """
        # Use custom matplotlib context
        with plt.rc_context(rc=custom_mpl.custom_rc(rc=self.custom_mpl_rc)):
            # Create figure if necessary
            figure, axes = self._render_grid()

            # Render depending on animation type
            if self.animation["type"] is False:
                self._render_no_animation(axes)
            elif self.animation["type"] == "gif":
                self._render_gif_animation(figure, axes)
            elif self.animation["type"] == "animation":
                # TODO
                return None
            else:
                return None
            # Use tight_layout to optimize layout, use custom padding
            figure.tight_layout(pad=1)  # TODO: Messes up animations
        return figure

    def set_grid(self, grid_description=None,
                 height=None, width=None, ignore_groups=False,
                 auto=None):
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
        :returns: None.

        .. note:: Groups are a single unicode character. If a group does not \
                contain any plot, the resulting subplot will simply be empty.

        .. note:: Note that if you do not include the default group in the \
                grid description, it will not be shown.

        >>> with replot.Figure() as fig: fig.set_grid(["AAA",
                                                       "BBC"
                                                       "DEC"])
        """
        # Handle incompatible arguments
        if((height is not None or width is not None or ignore_groups) and
           auto is False):
            raise exc.InvalidParameterError(
                "auto=False and height/width/ignore_groups arguments are " +
                "not compatible.")
        # Handle auto gridifying
        if auto is None:
            auto = False
        if auto or height is not None or width is not None or ignore_groups:
            self._set_auto_grid(height, width, ignore_groups)
            return

        if grid_description is False:
            # Disable the grid and return
            self.grid = False
            return
        elif isinstance(grid_description, str):
            # If a single string is provided, enclose it in a list.
            grid_description = [grid_description]
        # Check that grid is not empty
        if grid_description is None or len(grid_description) == 0:
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
                    x and y axis. You can also use the ``xrange`` / \
                    ``yrange`` aliases if you find them more convenient.
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
        kwargs, custom_kwargs = custom_kwargs_parser.parse(kwargs)

        if hasattr(args[0], "__call__"):
            # We want to plot a function
            plot_ = plot_helpers.plot_function(args[0], *(args[1:]), **kwargs)
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

        # Apply custom kwargs on plot_
        plot_ = custom_kwargs_parser.edit_plot_command(plot_, custom_kwargs)

        # Add the plot to the correct group
        if "group" in custom_kwargs:
            group_ = custom_kwargs["group"]
        else:
            group_ = constants.DEFAULT_GROUP
        self.plots[group_].append(plot_)

        # Automatically set the legend if label is found
        # (only do it if legend is not explicitly suppressed)
        if "label" in kwargs and self.legend is None:
            self.legend = True

    def logplot(self, *args, **kwargs):
        """
        Plot something on the :class:`Figure` object, in log scale.

        .. note:: See :func:`replot.Figure.plot` for the full documentation.

        .. note:: Side effect of this function is to set the axes to be in \
                log scale for the associated subplot.

        >>> with replot.figure() as fig: fig.logplot(np.log, (-1, 1))
        """
        kwargs["logscale"] = "log"
        self.plot(*args, **kwargs)

    def loglogplot(self, *args, **kwargs):
        """
        Plot something on the :class:`Figure` object, in log-log scale.

        .. note:: See :func:`replot.Figure.plot` for the full documentation.

        .. note:: Side effect of this function is to set the axes to be in \
                log scale for the associated subplot.

        >>> with replot.figure() as fig: fig.logplot(np.log, (-1, 1))
        """
        kwargs["logscale"] = "loglog"
        self.plot(*args, **kwargs)

    def animate(self, *args, **kwargs):
        """
        Create an animation.

        You can either:
            - use it directly without arguments to create an animation from \
                    the previously plot commands, cycling through the plots \
                    for each subplot.
            - TODO: Use an animation function.
        """
        self.animation["type"] = "gif"
        self.animation["args"] = args
        self.animation["kwargs"] = kwargs

    ###################
    # Private methods #
    ###################
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
            height, width = layout.optimal(nb_groups)

        # Apply the layout
        groups = sorted([k
                         for k in self.plots.keys()
                         if k != constants.DEFAULT_GROUP and
                         len(self.plots[k]) > 0])
        if len(self.plots[constants.DEFAULT_GROUP]) > 0:
            # Handle default group separately
            groups.append(constants.DEFAULT_GROUP)
        grid_description = ["".join(batch)
                            for batch in tools.batch(groups, width)]
        self.set_grid(grid_description)

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

    def _render_grid(self):
        """
        Helper method to create figure and axes with \
                subplots according to the grid description.

        :returns: A tuple containing the figure object as first element, and \
                a dict mapping the symbols of the groups to matplotlib axes \
                as second element.
        """
        # If no grid is provided, create an auto grid for the figure.
        if self.grid is None:
            self._set_auto_grid()

        # Axes is a dict associating symbols to matplotlib axes
        axes = {}
        figure = plt.figure()
        # Build all the axes
        if self.grid is not False:
            grid_size = (self.grid["height"], self.grid["width"])
            for subplot in self.grid["grid"]:
                position, symbol, (rowspan, colspan) = subplot
                axes[symbol] = plt.subplot2grid(grid_size,
                                                position,
                                                colspan=colspan,
                                                rowspan=rowspan)
                # Set the palette for the subplot
                axes[symbol].set_prop_cycle(
                    rpalette.build_cycler_palette(self.palette,
                                                  len(self.plots[symbol])))
            if constants.DEFAULT_GROUP not in axes:
                # Set the default group axis to None if it is not in the grid
                axes[constants.DEFAULT_GROUP] = None
        else:
            axis = plt.subplot2grid((1, 1), (0, 0))
            # Set the palette for the subplot
            axis.set_prop_cycle(
                rpalette.build_cycler_palette(
                    self.palette,
                    sum([len(i) for i in self.plots.values()]))
            )
            # Set the axis for every subplot
            for subplot in self.plots:
                axes[subplot] = axis
        return (figure, axes)

    def _set_axes_properties(self, axis, group_):
        """
        Set the various properties on the axes.

        :param axis: A :mod:`matplotlib` axis.
        :param group_: The group of plots to use to get the properties to set.
        :returns: None.
        """
        # Handle "invert" kwarg
        is_inverted_axis = (len(
            [i
             for i in self.plots[group_]
             if "invert" in i[2] and i[2]["invert"]]
        ) > 0)
        if is_inverted_axis:
            set_xlabel = axis.set_ylabel
            set_ylabel = axis.set_xlabel
        else:
            set_xlabel = axis.set_xlabel
            set_ylabel = axis.set_ylabel
        # Set xlabel and ylabel
        render_helpers.set_axis_property(group_, set_xlabel, self.xlabel)
        render_helpers.set_axis_property(group_, set_ylabel, self.ylabel)
        # Set title
        render_helpers.set_axis_property(group_, axis.set_title, self.title)
        # Set legend
        render_helpers.set_axis_property(
            group_,
            lambda v: self._legend(axis, overload_legend=v),
            self.legend,
            lambda: self._legend(axis, overload_legend=True)
        )
        # Set xrange / yrange
        render_helpers.set_axis_property(group_, axis.set_xlim, self.xrange)
        render_helpers.set_axis_property(group_, axis.set_ylim, self.yrange)
        # Note: Extend axes limits to have the full plot, even with large
        # linewidths. This is necessary as we do not clip lines.
        maximum_linewidth = max(
            max([plt[1].get("lw", 0) for plt in self.plots[group_]]),
            max([plt[1].get("linewidth", 0) for plt in self.plots[group_]])
        )
        if maximum_linewidth > 0:
            # Only extend axes limits if linewidths is larger than the default
            # one.
            ticks_position = {  # Dump ticks position to restore them afterwards
                "x": (axis.xaxis.get_majorticklocs(),
                      axis.xaxis.get_minorticklocs()),
                "y": (axis.yaxis.get_majorticklocs(),
                      axis.yaxis.get_minorticklocs())
            }
            # Set xrange
            extra_xrange = render_helpers.data_units_from_points(
                maximum_linewidth,
                axis,
                reference="x")
            xrange = (axis.get_xlim()[0] - extra_xrange / 2,
                      axis.get_xlim()[1] + extra_xrange / 2)
            render_helpers.set_axis_property(group_, axis.set_xlim, xrange)
            # Set yrange
            extra_yrange = render_helpers.data_units_from_points(
                maximum_linewidth,
                axis,
                reference="y")
            yrange = (axis.get_ylim()[0] - extra_yrange / 2,
                      axis.get_ylim()[1] + extra_yrange / 2)
            render_helpers.set_axis_property(group_, axis.set_ylim, yrange)
            # Restore ticks
            axis.xaxis.set_ticks(ticks_position["x"][0], minor=False)
            axis.xaxis.set_ticks(ticks_position["x"][1], minor=True)
            axis.yaxis.set_ticks(ticks_position["y"][0], minor=False)
            axis.yaxis.set_ticks(ticks_position["y"][1], minor=True)


    def _render_gif_animation(self, figure, axes):
        """
        Handle the render of a GIF-like animation, cycling through the plots.

        :param figure: A :mod:`matplotlib` figure.
        :param axes: A dict mapping the symbols of the groups to matplotlib \
                axes as second element.
        """
        # Init
        # TODO
        axes[constants.DEFAULT_GROUP].set_xlim((-2, 2))
        axes[constants.DEFAULT_GROUP].set_ylim((-2, 2))
        line, = axes[constants.DEFAULT_GROUP].plot([], [])
        # Define an animation function (closure)
        def animate(i):
            # TODO
            x = np.linspace(0, 2, 1000)
            y = np.sin(2 * np.pi * (x - 0.01 * i))
            line.set_data(x, y)
            return line,
        # Set default kwargs
        args = (figure, animate)
        kwargs = constants.DEFAULT_ANIMATION_KWARGS
        # Update with overloaded arguments
        args += self.animation["args"]
        kwargs.update(self.animation["kwargs"])
        # Keep track of animation object, as it has to persist
        self.animation["persist"] = [
            animation.FuncAnimation(*args, **kwargs)]

    def _render_no_animation(self, axes):
        """
        Handle the render of the figure when no animation is used.

        :param axes: A dict mapping the symbols of the groups to matplotlib \
                axes as second element.
        """
        # Add plots
        for group_ in self.plots:
            # Get the axis corresponding to current group
            try:
                axis = axes[group_]
            except KeyError:
                # If not found, plot in the default group
                axis = axes[constants.DEFAULT_GROUP]
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
