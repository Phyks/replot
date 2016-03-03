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
    automatically (or `save`d) upon leaving the `with` context.

    <dt>Plot functions</dt>
    <dd>Ever got annoyed by the fact that `matplotlib` can only plot point
    series and not evaluate a function _à la_ Mathematica? This module let
    you do things like `plot(sin, (-10, 10))` to plot a sine function between
    -10 and 10, using adaptive sampling.

    <dt>Order of call of methods is no longer important</dt>
    <dd>When calling a method from `matplotlib`, it is directly applied to the
    figure, and not deferred to the final render call. Then, if calling
    `matplotlib.pyplot.legend()` **before** having actually `plot`ted
    anything, it will fail. This is not the case with this module, as it
    abstracts on top of `matplotlib` and do the actual render only when the
    figure is to be `show`n. Even after having called the `show` method, you
    can still change everything in your figure!</dd>

    <dt>Does not interfere with `matplotlib`</dt>
    <dd>You can still use the default `matplotlib` if you want, as
    `matplotlib` state and parameters are not directly affected by this
    module, contrary to what `seaborn` do when you import it for
    instance.</dd>

    <dt>Useful aliases</dt>
    <dd>You think `loc="top left"` is easier to remember than `loc="upper
    left"` in a `matplotlib.pyplot.legend()` call? No worry, this module
    aliases it for you! (same for "bottom" with respect to "lower")</dd>

    <dt>Automatic legend</dt>
    <dd>If any of your plots contains a `label` keyword, a legend will be
    added automatically on your graph (you can still explicitly tell it not to
    add a legend by setting the `legend` attribute to `False`).</dd>

    <dt>Use `LaTeX` rendering in `matplotlib`, if available.</dt>
    <dd>If `replot` finds `LaTeX` installed on your machine, it will overload
    `matplotlib` settings to use `LaTeX` rendering.</dd>

    <dt>Handle subplots more easily</dt>
    <dd>**TODO**</dd>

    <dt>"Gridify"</dt>
    <dd>**TODO**</dd>
</dl>


## Examples

A more up to date doc is still to be written, but you can have a look at the
`Examples.ipynb` [Jupyter](https://github.com/jupyter/notebook/) notebook for
examples, which should cover most of the use cases.


## License

This Python module is released under MIT license. Feel free to contribute and
reuse. For more details, see `LICENSE.txt` file.


## Thanks

* [Matplotlib](http://matplotlib.org/) for their really good backend (but
  not for their terrible API)
* [Seaborn](https://github.com/mwaskom/seaborn) and
  [prettyplotlib](http://blog.olgabotvinnik.com/prettyplotlib/) which gave me
  the original idea.
* [This code](http://central.scipy.org/item/53/1/adaptive-sampling-of-1d-functions)
  from scipy central for a base code for adaptive sampling.
