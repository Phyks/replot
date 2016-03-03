"""
This file contains various utility functions.
"""
from itertools import islice, chain


def batch(iterable, size):
    """
    Get items from a sequence a batch at a time.

    .. note:

        Adapted from
        https://code.activestate.com/recipes/303279-getting-items-in-batches/.


    .. note:

        All batches must be exhausted immediately.

    :params iterable: An iterable to get batches from.
    :params size: Size of the batches.
    :returns: A new batch of the given size at each time.

    >>> [list(i) for i in batch([1, 2, 3, 4, 5], 2)]
    [[1, 2], [3, 4], [5]]
    """
    item = iter(iterable)
    while True:
        batch_iterator = islice(item, size)
        try:
            yield chain([next(batch_iterator)], batch_iterator)
        except StopIteration:
            return
