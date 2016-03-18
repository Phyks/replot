"""
Palette handling functions.
"""
import cycler
import palettable


def default(n):
    """
    Default palette is a CubeHelix perceptual rainbow palette with length the
    number of plots.

    :param n: The number of colors in the palette.
    :returns: The palette as a list of colors (as RGB tuples).
    """
    return palettable.cubehelix.Cubehelix.make(
        start_hue=240., end_hue=-300., min_sat=1., max_sat=2.5,
        min_light=0.3, max_light=0.8, gamma=.9, n=n).mpl_colors


def build_cycler_palette(palette, n):
    """
    Build a cycler palette for the selected subplot.

    :param n: number of colors in the palette.
    :returns: a cycler object for the palette.
    """
    if hasattr(palette, "__call__"):
        return cycler.cycler("color", palette(n))
    else:
        return cycler.cycler("color", palette)
