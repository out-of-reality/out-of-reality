import logging

import matplotlib.pyplot as plt
from mpld3 import plugins

_logger = logging.getLogger(__name__)


def build_comparison_figure(chart_data, fullscreen=False):
    if not chart_data:
        return None

    num_angle_tags = len(chart_data)
    figsize = (18, 5 * num_angle_tags) if fullscreen else (10, 3 * num_angle_tags)

    fig, axes_subplots = plt.subplots(
        nrows=num_angle_tags, ncols=1, figsize=figsize, sharex=True, squeeze=False
    )
    flat_axes = [ax for sublist in axes_subplots for ax in sublist]
    cmap_sessions = plt.get_cmap("viridis")
    any_data_plotted = False

    for i, subplot_data in enumerate(chart_data):
        ax = flat_axes[i]
        ax.set_title(subplot_data.get("title", ""), fontsize=12)
        ax.set_ylabel("Angle (°)", fontsize=10)
        ax.grid(True, linestyle="--", alpha=0.7)
        if i == len(chart_data) - 1:
            ax.set_xlabel("Time (s)", fontsize=12)

        has_data_in_subplot = False
        series_list = subplot_data.get("series", [])
        for j, series in enumerate(series_list):
            if not series.get("y"):
                continue

            has_data_in_subplot = True
            color = cmap_sessions(
                j / (len(series_list) - 1) if len(series_list) > 1 else 0.5
            )

            ax.plot(
                series["x"],
                series["y"],
                label=series["label"],
                color=color,
                linewidth=2,
            )
            points = ax.scatter(series["x"], series["y"], s=10, alpha=0)

            labels = [
                f"{t:.2f} s, {a:.1f}°"
                for t, a in zip(series["x"], series["y"], strict=False)
            ]
            tooltip = plugins.PointLabelTooltip(points, labels=labels)
            plugins.connect(fig, tooltip)

        if has_data_in_subplot:
            any_data_plotted = True
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                legend_loc = "upper right"
                bbox_to_anchor = None
                if len(handles) > 3:
                    legend_loc = "center left"
                    bbox_to_anchor = (1.01, 0.5)
                ax.legend(
                    loc=legend_loc,
                    bbox_to_anchor=bbox_to_anchor,
                    fontsize=8 if bbox_to_anchor else 9,
                )
        else:
            ax.text(
                0.5,
                0.5,
                "No data available for this angle.",
                ha="center",
                va="center",
                transform=ax.transAxes,
                fontsize=10,
            )

    if not any_data_plotted:
        plt.close(fig)
        return None

    try:
        rect_right = 0.85 if len(chart_data[0].get("series", [])) > 3 else 0.95
        fig.tight_layout(rect=[0, 0.03, rect_right, 0.92])
    except (ValueError, UserWarning) as e:
        _logger.warning(
            f"Could not apply tight_layout to comparison chart: {e}", exc_info=True
        )

    return fig
