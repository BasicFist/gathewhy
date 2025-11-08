"""GPU card widget for AI backend dashboard - REDESIGNED.

Modern GPU card with better visualization and readability.
"""

from __future__ import annotations

from textual.widgets import Static

from ..models import GPUOverview


class GPUCard(Static):
    """Displays GPU utilization summary with modern styling.

    Shows total VRAM usage, peak utilization percentage, and per-GPU breakdown
    with visual indicators and color coding. Gracefully handles systems without
    NVIDIA GPUs.

    Features:
        - Visual VRAM usage bars
        - Color-coded utilization
        - Icons for different metrics
        - Per-GPU breakdown
    """

    def update_overview(self, overview: GPUOverview) -> None:
        """Update GPU card with latest GPU metrics.

        Args:
            overview: GPUOverview with aggregated GPU statistics
        """
        if not overview.detected:
            self.update("[dim]🚫 No NVIDIA GPU detected[/]\n" "[dim]or NVML unavailable[/]")
            return

        # Calculate VRAM percentage
        vram_percent = (
            (overview.total_used_mb / overview.total_capacity_mb * 100)
            if overview.total_capacity_mb
            else 0
        )

        # Color code VRAM usage
        vram_color = "red" if vram_percent > 90 else "yellow" if vram_percent > 75 else "cyan"

        # Color code GPU utilization
        util_color = (
            "red"
            if overview.peak_util_percent > 90
            else "yellow"
            if overview.peak_util_percent > 75
            else "green"
        )

        # Build output
        lines = [
            "[b cyan]💾 VRAM Usage[/]",
            f"[{vram_color}]■■■[/] {overview.total_used_mb:.0f} / {overview.total_capacity_mb:.0f} MB ([b]{vram_percent:.1f}%[/])",
            "",
            "[b cyan]⚡ GPU Utilization[/]",
            f"[{util_color}]▲▲▲[/] Peak: [b]{overview.peak_util_percent:.1f}%[/]",
        ]

        # Add per-GPU breakdown if multiple GPUs
        if len(overview.per_gpu) > 1:
            lines.append("")
            lines.append("[b cyan]📊 Per-GPU Breakdown[/]")

        for entry in overview.per_gpu:
            gpu_vram_percent = entry["memory_util_percent"]
            gpu_util_percent = entry["gpu_util_percent"]

            # Color code each GPU
            gpu_vram_color = (
                "red" if gpu_vram_percent > 90 else "yellow" if gpu_vram_percent > 75 else "cyan"
            )
            gpu_util_color = (
                "red" if gpu_util_percent > 90 else "yellow" if gpu_util_percent > 75 else "green"
            )

            lines.append(
                f"  [b]GPU {int(entry['id'])}:[/] "
                f"[{gpu_vram_color}]{entry['memory_used_mb']:.0f}MB[/] "
                f"([{gpu_util_color}]{gpu_util_percent:.0f}% util[/])"
            )

        self.update("\n".join(lines))
