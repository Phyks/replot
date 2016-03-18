"""
Functions to set custom :mod:`matplotlib` parameters.
"""
import shutil

import numpy as np


def custom_rc(rc=None):
    """
    Overload ``matplotlib.rcParams`` to enable advanced features if \
            available. In particular, use LaTeX if available.

    :param rc: An optional dict to overload some :mod:`matplotlib` rc params.
    :returns: A ``matplotlib.rc_context`` object to use in a ``with`` \
            statement.
    """
    custom_rc_ = {}
    # Add LaTeX in rc if available
    if(shutil.which("latex") is not None and
       shutil.which("gs") is not None and
       shutil.which("dvipng") is not None):
        # LateX dependencies are all available
        custom_rc_["text.usetex"] = True
        custom_rc_["text.latex.unicode"] = True
    # Use LaTeX default font family
    # See https://stackoverflow.com/questions/17958485/matplotlib-not-using-latex-font-while-text-usetex-true
    custom_rc_["font.family"] = "serif"
    custom_rc_["font.serif"] = "cm"
    # Scale everything
    custom_rc_.update(_rc_scaling())
    # Set axes style
    custom_rc_.update(_rc_axes_style())
    # Overload if necessary
    if rc is not None:
        custom_rc_.update(rc)
    # Return a context object
    return custom_rc_


def _rc_scaling():
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


def _rc_axes_style():
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