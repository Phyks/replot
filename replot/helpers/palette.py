"""
Palette handling functions.
"""
import cycler
import palettable



COLORBREWER_Q10 = [
    "#1f78b4", "#33a02c", "#e31a1c", "#ff7f00", "#6a3d9a",
    "#a6cee3", "#b2df8a", "#fb9a99", "#fdbf6f", "#cab2d6"]
COLORBREWER_Q9 = [
    "#e41a1c", "#377eb8", "#4daf4a", "#984ea3",
    "#ff7f00", "#ffff33", "#a65628", "#f781bf", "#999999"]
TABLEAU_10 = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]


def cubehelix(n):
    """
    Builds a CubeHelix perceptual rainbow palette with length the
    number of plots.

    :param n: The number of colors in the palette.
    :returns: The palette as a list of colors (as RGB tuples).
    """
    return palettable.cubehelix.Cubehelix.make(
        start_hue=240., end_hue=-300., min_sat=1., max_sat=2.5,
        min_light=0.3, max_light=0.8, gamma=.9, n=n).mpl_colors


def build_cycler_palette(palette):
    """
    Build a cycler palette for the selected subplot.

    :param palette: A list of colors in a format understable by \
            matplotlib.
    :returns: a cycler object for the palette.
    """
    return cycler.cycler("color", palette)
