#!/usr/bin/env python3
"""Test GPU VRAM display in dashboard"""

from dashboard.models import GPUOverview
from dashboard.monitors.gpu import GPUMonitor
from dashboard.widgets.gpu_card import GPUCard

print("=== TESTING VRAM DISPLAY ===")

gpu = GPUMonitor()
print(f"✓ GPU Monitor initialized: {gpu.initialized}")
print(f"✓ Device count: {gpu.device_count}")

gpu_info = gpu.get_gpu_info()
print(f"✓ GPU Info retrieved: {len(gpu_info)} GPUs")

if gpu_info:
    total_used = sum(entry["memory_used_mb"] for entry in gpu_info)
    total_capacity = sum(entry["memory_total_mb"] for entry in gpu_info)
    peak_util = max(entry["gpu_util_percent"] for entry in gpu_info)

    overview = GPUOverview(
        detected=True,
        per_gpu=gpu_info,
        total_used_mb=total_used,
        total_capacity_mb=total_capacity,
        peak_util_percent=peak_util,
    )

    print(f"✓ Overview created: detected={overview.detected}")
    print(f"✓ Total Used: {overview.total_used_mb} MB")
    print(f"✓ Total Capacity: {overview.total_capacity_mb} MB")
    print(f"✓ Peak Util: {overview.peak_util_percent:.1f}%")

    print("\nCreating GPUCard widget...")
    widget = GPUCard()

    print("✓ Widget created")

    print("Calling update_overview...")
    widget.update_overview(overview)

    print("✓ Widget updated")

    print("\nWidget content preview:")
    content = str(widget)
    if content and len(content) > 50:
        print(content[:200] + "...")
    else:
        print(content)

    print("\n=== TEST COMPLETE ===")

else:
    print("✗ No GPU detected or NVML unavailable")
