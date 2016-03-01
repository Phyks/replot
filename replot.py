"""
* Saner default config.
* Matplotlib API methods have an immediate effect on the figure. We do not want
it, then we write a buffer on top of matplotlib API.
"""
import matplotlib.pyplot as plt
import numpy as np
import seaborn.apionly as sns


# TODO: Remove it, this is interfering with matplotlib
plt.rcParams['figure.figsize'] = (10.0, 8.0)  # Larger figures by default
plt.rcParams['text.usetex'] = True  # Use LaTeX rendering


class Figure():
    def __init__(self,
                 xlabel="", ylabel="", title="", palette="hls",
                 legend=None):
        # TODO: Constants
        self.max_colors = 10
        self.default_points_number = 1000
        self.default_x_interval = np.linspace(-10, 10,
                                              self.default_points_number)

        # Set default values for attributes
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.title = title
        self.palette = palette
        self.legend = legend
        self.plots = []

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.show()

    def show(self):
        """
        Actually render and show the figure.
        """
        # Tweak matplotlib to use seaborn
        sns.set()
        # Plot using specified color palette
        with sns.color_palette(self.palette, self.max_colors):
            # Create figure
            figure, axes = plt.subplots()
            # Add plots
            for plot in self.plots:
                axes.plot(*(plot[0]), **(plot[1]))
            # Set properties
            axes.set_xlabel(self.xlabel)
            axes.set_ylabel(self.ylabel)
            axes.set_title(self.title)
            if self.legend is not None and self.legend is not False:
                self._legend(axes, location=self.legend)
            # Draw figure
            figure.show()
        # Do not forget to restore matplotlib state, in order not to interfere
        # with it.
        sns.reset_orig()


    #def palette(self, palette):
    #    """
    #    """
    #    if isinstance(palette, str):
    #        self.current_palette = palette
    #        with seaborn.color_palette(self.current_palette, self.max_colors):
    #            # TODO
    #            pass

    def plot(self, data, *args, **kwargs):
        """
        Plot something on the figure.

        >>> plot(np.sin)
        >>> plot(np.sin, (-1, 1))
        >>> plot(np.sin, [-1, -0.9, …, 1])
        >>> plot([1, 2, 3], [4, 5, 6])
        """
        if hasattr(data, "__call__"):
            # We want to plot a function
            self._plot_function(data, *args, **kwargs)
        else:
            # Else, it is a point series, and we just have to store it for
            # later plotting.
            self.plots.append(((data,) + args, kwargs))

        # Automatically set the legend if label is found
        # (only do it if legend is not explicitly suppressed)
        if "label" in kwargs and self.legend is None:
            self.legend = True

    def _plot_function(self, data, *args, **kwargs):
        """
        """
        # TODO: Better default interval and so on
        if len(args) == 0:
            # No interval specified, using default one
            x_values = self.default_x_interval
        elif isinstance(args[0], (list, np.ndarray)):
            # List of points specified
            x_values = args[0]
        elif isinstance(args[0], tuple):
            # Interval specified, generate a list of points
            x_values = np.linspace(args[0][0], args[0][1],
                                   self.default_points_number)
        else:
            # TODO: Error
            assert False
        y_values = [data(i) for i in x_values]
        self.plots.append(((x_values, y_values) + args[1:], kwargs))

    def _legend(self, axes, location="best"):
        """
        """
        if location is True:
            # If there should be a legend, but no location provided, put it at
            # best location.
            location = "best"
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
    """
    figure = Figure(**kwargs)
    # TODO: Fix API, support every plot type
    for plt in data:
        figure.plot(plt)
    return figure
