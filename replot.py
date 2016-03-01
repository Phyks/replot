"""
* Saner default config.
* Matplotlib API methods have an immediate effect on the figure. We do not want
it, then we write a buffer on top of matplotlib API.
"""
import matplotlib.pyplot as plt
import numpy as np
import seaborn


plt.rcParams['figure.figsize'] = (10.0, 8.0)  # Larger figures by default
plt.rcParams['text.usetex'] = True  # Use LaTeX rendering


class Figure():
    def __init__(self,
                 xlabel="", ylabel="", title="", palette="hls",
                 legend=None):
        self.max_colors = 10
        self.default_points_number = 1000
        self.default_x_interval = np.linspace(-10, 10,
                                              self.default_points_number)

        self.xlabel = xlabel
        self.ylabel = ylabel
        self.title = title
        self.palette = palette
        # TODO: Legend should be automatic if labelled data is found
        self.legend = legend
        self.plots = []

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.show()

    def show(self):
        """
        """
        seaborn.set()
        with seaborn.color_palette(self.palette, self.max_colors):
            # Create figure
            figure, axes = plt.subplots()
            # Add plots
            for plot in self.plots:
                axes.plot(*(plot[0]), **(plot[1]))
            # Set properties
            axes.set_xlabel(self.xlabel)
            axes.set_ylabel(self.ylabel)
            axes.set_title(self.title)
            if self.legend is not None:
                self._legend(axes, location=self.legend)
            # Draw figure
            figure.show()
        seaborn.reset_orig()


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
            self._plot_function(data, *args, **kwargs)
        else:
            self.plots.append(((data,) + args, kwargs))

    def _plot_function(self, data, *args, **kwargs):
        """
        """
        # TODO: Better default interval and so on
        if len(args) == 0:
            # No interval specified, using default one
            x_values = self.default_x_interval
        elif isinstance(args[0], (list, np.ndarray)):
            x_values = args[0]
        elif isinstance(args[0], tuple):
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
        # If there should be a legend, but no location provided, put it at best
        # location
        if location is True:
            location = "best"
        location.replace("top ", "upper ")
        location.replace("bottom ", "lower ")
        axes.legend(loc=location)
