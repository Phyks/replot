"""
The :mod:`replot` module is an attempt at an easier API to plot graphs using
Matplotlib.
"""
from replot.figure import Figure

__all__ = ["plot", "Figure"]


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
