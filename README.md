Replot
======


This repo is an attempt for a better API to plot graphs with
[Matplotlib](http://matplotlib.org/) in Python.

## Features

These are the current features. I will extend the module whenever I feel the
need to introduce new functions and methods. Please let me know about any bad
design in the API, or required feature!

<dl>
    <dt>Saner default plots</dt>
    <dd>Matplotlib plots are quite ugly by default, colors are not really
    suited for optimal black and white print, or ease reading for colorblind
    people. This module imports and makes use of
    [Seaborn](https://github.com/mwaskom/seaborn) for saner default params.</dd>

    <dt>Support `with` statement</dt>
    <dd>Ever got tired of having to start any figure with a call to
    `matplotlib.pyplot.subplots()`? This module abstracts it using `with`
    statement. New figures are defined by a `with` statement, and are `show`n
    automatically upon leaving the `with` context.

    <dt>Plot functions</dt>
    <dd>Ever got annoyed by the fact that `matplotlib` can only plot point
    series and not evaluate a function _à la_ Mathematica? This module let
    you do things like `plot(sin, (-10, 10))` to plot a sine function between
    -10 and 10.

    <dt>Order of call of methods is no longer important</dt>
    <dd>When calling a method from `matplotlib`, it is directly applied to the
    figure, and not deferred to the final render call. Then, if calling
    `matplotlib.pyplot.legend()` **before** having actually `plot`ted
    anything, it will fail. This is not the case with this module, as it
    abstracts on top of `matplotlib` and do the actual render only when the
    figure is to be `show`n. Even after having called the `show` method, you
    can still change everything in your figure!</dd>
</dl>


## Examples

A more up to date doc is still to be written, but you can have a look at the
`Examples.ipynb` [Jupyter](https://github.com/jupyter/notebook/) notebook for
examples.


## License

MIT license.
