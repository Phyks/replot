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
    people. This module defines a clean default colorscheme to solve it.</dd>

    <dt>Support <code>with</code> statement</dt>
    <dd>Ever got tired of having to start any figure with a call to
    <code>matplotlib.pyplot.subplots()</code>? This module abstracts it using
    <code>with</code> statement. New figures are defined by a
    <code>with</code> statement, and are <code>show</code>n automatically (or
    <code>save</code>d) upon leaving the <code>with</code> context.

    <dt>Plot functions</dt>
    <dd>Ever got annoyed by the fact that <code>matplotlib</code> can only
    plot point series and not evaluate a function <em>à la</em> Mathematica?
    This module let you do things like <code>plot(sin, (-10, 10))</code> to
    plot a sine function between -10 and 10, using adaptive sampling.

    <dt>Order of call of methods is no longer important</dt>
    <dd>When calling a method from <code>matplotlib</code>, it is directly
    applied to the figure, and not deferred to the final render call. Then, if
    calling <code>matplotlib.pyplot.legend()</code> <strong>before</strong>
    having actually <code>plot</code>ted anything, it will fail. This is not
    the case with this module, as it abstracts on top of
    <code>matplotlib</code> and do the actual render only when the figure is
    to be <code>show</code>n. Even after having called the <code>show</code>
    method, you can still change everything in your figure!</dd>

    <dt>Does not interfere with <code>matplotlib</code></dt>
    <dd>You can still use the default <code>matplotlib</code> if you want, as
    <code>matplotlib</code> state and parameters are not directly affected by
    this module, contrary to what <code>seaborn</code> do when you import it
    for instance.</dd>

    <dt>Useful aliases</dt>
    <dd>You think <code>loc="top left"</code> is easier to remember than
    <code>loc="upper left"</code> in a <code>matplotlib.pyplot.legend()</code>
    call? No worry, this module aliases it for you! (same for "bottom" with
    respect to "lower")</dd>

    <dt>Automatic legend</dt>
    <dd>If any of your plots contains a <code>label</code> keyword, a legend
    will be added automatically on your graph (you can still explicitly tell
    it not to add a legend by setting the <code>legend</code> attribute to
    <code>False</code>).</dd>

    <dt>Use <code>LaTeX</code> rendering in <code>matplotlib</code>, if
    available.</dt>
    <dd>If <code>replot</code> finds <code>LaTeX</code> installed on your
    machine, it will overload <code>matplotlib</code> settings to use
    <code>LaTeX</code> rendering.</dd>

    <dt>Handle subplots more easily</dt>
    <dd>Have you ever struggled with <code>matplotlib</code> to define a subplot
    grid and arrange your plot? <code>replot</code> lets you describe your
    grid visually using ascii art!</dd>

    <dt>"Gridify"</dt>
    <dd>You have some plots that you would like to arrange into a grid, to
    compare them easily, but you do not want to waste time setting up a grid
    and placing your plots at the correct place? <code>replot</code> handles
    it for you out of the box!</dd>

    <dt>Easy plotting in log scale</dt>
    <dd><code>replot</code> defines <code>logplot</code> and
    <code>loglogplot</code> shortcuts functions to plot in <em>log</em> scale
    or <em>loglog</em> scale.</dd>
</dl>


## Examples

A more up to date doc is still to be written, but you can have a look at the
<a href="https://github.com/Phyks/replot/blob/master/Examples.ipynb">`Examples.ipynb`</a>
[Jupyter](https://github.com/jupyter/notebook/) notebook for
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
