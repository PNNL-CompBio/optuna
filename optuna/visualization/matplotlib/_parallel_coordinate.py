from collections import defaultdict
from typing import DefaultDict
from typing import List
from typing import Optional

import numpy as np

from optuna.logging import get_logger
from optuna.study import Study
from optuna.trial import TrialState
from optuna.visualization.matplotlib._matplotlib_imports import _imports

if _imports.is_successful():
    from optuna.visualization.matplotlib._matplotlib_imports import Axes
    from optuna.visualization.matplotlib._matplotlib_imports import LineCollection
    from optuna.visualization.matplotlib._matplotlib_imports import plt

_logger = get_logger(__name__)


def plot_parallel_coordinate(study: Study, params: Optional[List[str]] = None) -> Axes:
    """Plot the high-dimentional parameter relationships in a study with Matplotlib.

    Note that, If a parameter contains missing values, a trial with missing values is not plotted.

    Example:

        The following code snippet shows how to plot the high-dimentional parameter relationships.

        .. testcode::

            import optuna

            def objective(trial):
                x = trial.suggest_uniform('x', -100, 100)
                y = trial.suggest_categorical('y', [-1, 0, 1])
                return x ** 2 + y

            study = optuna.create_study()
            study.optimize(objective, n_trials=10)

            optuna.visualization.matplotlib.plot_parallel_coordinate(study, params=['x', 'y'])

    Args:
        study:
            A :class:`~optuna.study.Study` object whose trials are plotted for their objective
            values.
        params:
            Parameter list to visualize. The default is all parameters.

    Returns:
        A :class:`matplotlib.axes.Axes` object.
    """

    _imports.check()
    return _get_parallel_coordinate_plot(study, params)


def _get_parallel_coordinate_plot(study: Study, params: Optional[List[str]] = None) -> Axes:

    # Set up the graph style.
    fig, ax = plt.subplots()
    cmap = plt.get_cmap("Blues")
    ax.set_title("Parallel Coordinate Plot")
    ax.spines["top"].set_visible(False)
    ax.spines["bottom"].set_visible(False)

    # Prepare data for plotting.
    trials = [trial for trial in study.trials if trial.state == TrialState.COMPLETE]

    if len(trials) == 0:
        _logger.warning("Your study does not have any completed trials.")
        return Axes

    all_params = {p_name for t in trials for p_name in t.params.keys()}
    if params is not None:
        for input_p_name in params:
            if input_p_name not in all_params:
                raise ValueError("Parameter {} does not exist in your study.".format(input_p_name))
        all_params = set(params)
    sorted_params = sorted(list(all_params))

    obj_org = [t.value for t in trials]
    obj_min = min(obj_org)
    obj_max = max(obj_org)
    obj_w = obj_max - obj_min  # type: ignore
    dims_obj_base = [[o] for o in obj_org]

    cat_param_names = []
    cat_param_values = []
    cat_param_ticks = []
    for p_name in sorted_params:
        values = []
        for t in trials:
            if p_name in t.params:
                values.append(t.params[p_name])
        try:
            tuple(map(float, values))
        except (TypeError, ValueError):
            vocab = defaultdict(lambda: len(vocab))  # type: DefaultDict[str, int]
            values = [vocab[v] for v in values]
            cat_param_names.append(p_name)
            vocab_item_sorted = sorted(vocab.items(), key=lambda x: x[1])
            cat_param_values.append([v[0] for v in vocab_item_sorted])
            cat_param_ticks.append([v[1] for v in vocab_item_sorted])

        p_min = min(values)
        p_max = max(values)
        p_w = p_max - p_min
        for i, v in enumerate(values):
            dims_obj_base[i].append((v - p_min) / p_w * obj_w + obj_min)

    param_values = []
    var_names = ["Objective Value"]
    for param_name in sorted_params:
        param_values_trials = []
        for t in trials:
            if param_name in t.params:
                param_values_trials.append(t.params[param_name])
        var_names.append(param_name if len(param_name) < 20 else "{}...".format(param_name[:17]))
        param_values.append(param_values_trials)

    # Draw multiple line plots and axes.
    # https://stackoverflow.com/a/50029441
    ax.set_xlim(0, len(sorted_params))
    ax.set_ylim(obj_min, obj_max)
    xs = [range(0, len(sorted_params) + 1) for i in range(len(dims_obj_base))]
    segments = [np.column_stack([x, y]) for x, y in zip(xs, dims_obj_base)]
    lc = LineCollection(segments, cmap=cmap)
    lc.set_array(np.asarray([t.value for t in trials] + [0]))
    axcb = fig.colorbar(lc, pad=0.1)
    axcb.set_label("Objective Value")
    plt.xticks(range(0, len(sorted_params) + 1), var_names, rotation=330)

    for i, p_name in enumerate(sorted_params):
        ax2 = ax.twinx()
        ax2.set_ylim(min(param_values[i]), max(param_values[i]))
        ax2.spines["top"].set_visible(False)
        ax2.spines["bottom"].set_visible(False)
        ax2.get_xaxis().set_visible(False)
        ax2.plot([1] * len(param_values[i]), param_values[i], visible=False)
        ax2.spines["right"].set_position(("axes", (i + 1) / len(sorted_params)))
        if p_name in cat_param_names:
            idx = cat_param_names.index(p_name)
            tick_pos = cat_param_ticks[idx]
            tick_labels = cat_param_values[idx]
            ax2.set_yticks(tick_pos)
            ax2.set_yticklabels(tick_labels)

    ax.add_collection(lc)

    return ax
