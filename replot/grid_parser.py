"""
This module implements functions to easily translate an ASCII art matrix into
subplots commands, to create subplots easily.

Thanks to Laurent Dardelet for writing this code.
"""
import numpy as np


def parse_ascii(M):
    """
    Parse an ASCII art grid into subplots commands.

    :param M: A list of strings, each string representing a row.
    :returns: A dict containing the width and height of the grid, and a \
            description of the grid as a list of subplots. Each subplot is a \
            tuple of \
            ``((y_position, x_position), symbol, (rowspan, colspan))``. \
            Returns ``None`` if the matrix could not be parsed.

    .. note:: This function expects ``M`` to represent a valid rectangular \
            matrix.

    .. note:: Position starts from 0 and origin is the top left corner.

    >>> parse_ascii(["AAA",
                     "BBC",
                     "DEC"]
    {
      "width": 3,
      "height": 3,
      "grid": [
        ((0, 0), "A", (1, 3)),
        ((1, 0), "B", (1, 2)),
        ((1, 2), "C", (2, 1))
        ((2, 0), "D", (1, 1)),
        ((2, 1), "E", (1, 1)),
      ]
    }
    """
    # Get the dimensions of the matrix
    height, width = len(M), len(M[0])

    # Store the list of found symbols
    symbols_found = []
    # Keep track of the elements which have already been assigned to a zone
    elements_done = np.zeros([height, width])
    # List of the output subplots commands
    subplot_list = []

    # Iterate through M, starting from top left corner
    # Going from left to right and from top to bottom
    for n_x in range(width):
        for n_y in range(height):
            if elements_done[n_y, n_x] == 0:
                # If this location in the matrix has never been assigned to so
                # far, it is the current symbol we'll try to match with its
                # neighbours.
                current_symbol = M[n_y][n_x]
                if current_symbol in symbols_found:
                    return None
                else:
                    # By default, subplot is of size (1, 1)
                    colspan = 1
                    rowspan = 1
                    # Keep track of the current symbol as having already been
                    # seen
                    symbols_found.append(current_symbol)

                    # Look at neighbouring positions, to find the limits of a
                    # possible subplot
                    # Start looking by increasing X coordinate
                    for n_x_tmp in range(n_x + 1, width):
                        if M[n_y][n_x_tmp] == current_symbol:
                            colspan += 1
                    # Then, do the same by increasing Y coordinate
                    for n_y_tmp in range(n_y + 1, height):
                        if M[n_y_tmp][n_x] == current_symbol:
                            rowspan += 1

                    # We have found an area with the current symbol. Check that
                    # it is a rectangle containing only the current symbol.
                    is_valid_rectangle = _check_rect(n_x, n_y,
                                                     colspan, rowspan,
                                                     current_symbol,
                                                     M)
                    if is_valid_rectangle:
                        # Mark all these elements as processed
                        _set_as_done(n_x, n_y, colspan, rowspan, elements_done)
                        # And store the associated subplot command
                        subplot_list.append(
                            ((n_y, n_x),
                             current_symbol,
                             (rowspan, colspan)))
                    else:
                        return None
    return {"width": width,
            "height": height,
            "grid": subplot_list}



def _check_rect(n_x, n_y, dx, dy, symbol, M):
    """
    Check that for a rectangle defined by two of its sides, every element \
            within it is the same.

    .. note:: This method is called once the main script has reached the \
            limits of a rectangle.

    :param n_x: Starting position of the rectangle (top left corner abscissa).
    :param n_y: Starting position of the rectangle (top left corner ordonate).
    :param dx: Width of the rectangle.
    :param dy: Height of the rectangle.
    :param symbol: Symbol which should be in the rectangle.
    :param M: Input matrix, as a list of strings.
    :returns: Boolean indicated whether the rectangle is correct or not.
    """
    for x in range(dx):
        for y in range(dy):
            if M[n_y + y][n_x + x] != symbol:
                return False
    return True


def _set_as_done(n_x, n_y, dx, dy, elements_done):
    """
    Mark some elements as having been processed, to keep track of them.

    :param n_x: Starting position of the rectangle (top left corner abscissa).
    :param n_y: Starting position of the rectangle (top left corner ordonate).
    :param dx: Width of the rectangle.
    :param dy: Height of the rectangle.
    :param elements_done: A matrix of the same shape as the input matrix, \
            updated in place.
    """
    for x in range(dx):
        for y in range(dy):
            elements_done[n_y+y, n_x+x] = 1
