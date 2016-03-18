"""
Grid layout functions.
"""
import math


def optimal(nb_items):
    """
    (Naive) attempt to find an optimal grid layout for N elements.

    :param nb_items: The number of square elements to put on the grid.
    :returns: A tuple ``(height, width)`` containing the number of rows and \
            the number of cols of the resulting grid.

    >>> _optimal(2)
    (1, 2)

    >>> _optimal(3)
    (1, 3)

    >>> _optimal(4)
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
