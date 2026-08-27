import math

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager


def pick_preferred_font() -> str:
    preferred = [
        "Microsoft YaHei",
        "Microsoft JhengHei",
        "PingFang SC",
        "Noto Sans CJK SC",
        "SimHei",
        "Source Han Sans SC",
    ]
    installed = {f.name for f in font_manager.fontManager.ttflist}
    for name in preferred:
        if name in installed:
            return name
    return "DejaVu Sans"

def configure_typography() -> None:
    font_name = pick_preferred_font()
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = [font_name]
    plt.rcParams["axes.unicode_minus"] = False

def draw_radar(ax, name: str, labels, values, score_max=10):
    ax.clear()
    # 旋转为顶部起始、顺时针，视觉上更“正”
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    labels_closed = labels + [labels[0]]
    values_closed = values + [values[0]]

    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles_closed = angles + [angles[0]]

    r_max = max(score_max, max(values) if values else score_max)

    ax.set_facecolor("#F8FCFF")

    # 多边形网格（替代圆环网格）
    ring_levels = np.linspace(r_max / 5, r_max, 5).tolist()
    for level in ring_levels:
        ax.plot(
            angles_closed,
            [level] * len(labels_closed),
            color="#8EC7E8",
            linewidth=1.0,
            alpha=0.55 if level < r_max else 0.75,
            zorder=1,
        )
    for angle in angles:
        ax.plot([angle, angle], [0, r_max], color="#8EC7E8", linewidth=1.0, alpha=0.5, zorder=1)

    # 5分参考线（红色虚线）
    base_values = [min(5.0, r_max)] * len(labels_closed)
    ax.plot(angles_closed, base_values, linestyle="--", linewidth=1.7, color="#C62828", alpha=0.9, zorder=2)

    # 主数据
    ax.plot(angles_closed, values_closed, linewidth=2.8, color="#10A7A5", zorder=4)
    ax.fill(angles_closed, values_closed, alpha=0.25, color="#8BD8D6", zorder=3)
    ax.scatter(angles, values, s=165, facecolor="#FFFFFF", edgecolor="#10A7A5", linewidth=2.2, zorder=5)

    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=12, fontweight="medium")
    for txt in ax.get_xticklabels():
        txt.set_picker(8)

    tick_values = np.linspace(0, r_max, 5)
    ax.set_ylim(0, r_max)
    ax.set_yticks(tick_values)
    ax.set_yticklabels([])
    ax.set_rlabel_position(18)
    ax.tick_params(axis="x", pad=16)

    ax.grid(False)
    ax.spines["polar"].set_visible(False)

    ax.set_title(f"{name} 能力雷达图（V6）", fontsize=17, fontweight="semibold", pad=14, color="#0A6FAE")

    for angle, value in zip(angles, values):
        is_outer = value >= r_max * 0.88
        radial_shift = -r_max * 0.08 if is_outer else r_max * 0.07
        label_r = min(max(value + radial_shift, r_max * 0.18), r_max * 0.92)

        # 切向偏移，避免标签压在节点圆点和折线上
        tangent_x = -math.sin(angle) * 8
        tangent_y = math.cos(angle) * 8
        ax.annotate(
            f"{value:.1f}",
            xy=(angle, label_r),
            xytext=(tangent_x, tangent_y),
            textcoords="offset points",
            ha="center",
            va="center",
            fontsize=12,
            fontweight="medium",
            color="#0B6EA8",
            bbox={
                "boxstyle": "round,pad=0.2",
                "facecolor": "#FFFFFF",
                "edgecolor": "#9FD5EE",
                "linewidth": 0.8,
                "alpha": 0.95,
            },
            zorder=6,
        )

    return ax.get_xticklabels()

