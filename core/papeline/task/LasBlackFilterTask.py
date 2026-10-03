# -*- coding: utf-8 -*-
"""
LasBlackFilterTask — Task to filter black points in LAS/LAZ point clouds
==========================================================================
Removes points where R, G and B are all below a configurable threshold.
Generates new files with _filtered suffix without altering originals.
Option to save removed black points in separate files.

NOTE: Emits progress via SignalManager during _run().
Qt signals are thread-safe — they work from inside QThread.
"""

from __future__ import annotations

import os
from typing import Optional

import numpy as np

from core.manager.SignalManager import SignalManager
from utils.las.LasLayerSource import LasLayerSource
from ..BaseTask import BaseTask


class LasBlackFilterTask(BaseTask):
    """
    Task that filters black points from LAS/LAZ files.

    Args:
        files: List of LAS/LAZ file paths to process.
        output_dir: Directory to save filtered files.
        threshold: Maximum R/G/B value to consider black (0-255).
        save_black_points: If True, saves removed black points separately.

    Result produces (dict):
        - n_total: Total points across all files
        - n_removed: Total removed points
        - n_kept: Total kept points
        - n_black: Total black points saved
        - output_clean: List of filtered file paths
        - output_black: List of black points file paths
    """

    def __init__(
        self,
        files: list[str],
        output_dir: str,
        threshold: int = 0,
        save_black_points: bool = False,
    ):
        super().__init__(description=f"Filter black points: {len(files)} file(s)")
        self._files = files
        self._output_dir = output_dir
        self._threshold = threshold
        self._save_black_points = save_black_points

    def _run(self) -> bool:
        """
        Executes filtering in background thread emitting progress.

        4 stages per file synchronized with HUD Mode 3:
          Stage 0: Read           (0% -> 25%)
          Stage 1: Filter         (25% -> 50%)
          Stage 2: Save Filtered  (50% -> 75%)
          Stage 3: Save Black     (75% -> 100%)
        """
        signals = SignalManager.instance()
        os.makedirs(self._output_dir, exist_ok=True)

        total_all = 0
        removed_all = 0
        kept_all = 0
        black_all = 0
        output_clean_list = []
        output_black_list = []

        for file_idx, file_path in enumerate(self._files):
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            ext = os.path.splitext(file_path)[1].lower()

            output_clean = os.path.join(self._output_dir, f"{base_name}_filtered{ext}")
            output_black = os.path.join(self._output_dir, f"{base_name}_black{ext}") if self._save_black_points else ""

            # ── Stage 0: Read (0% -> 25%) ────────────────────────────
            signals.hud_update.emit({
                "message": f"[{file_idx+1}/{len(self._files)}] Reading {base_name}...",
                "progress": 5.0,
            })
            signals.progress_update.emit(5.0)

            rgb = LasLayerSource.get_rgb_arrays(file_path)
            if not rgb:
                raise RuntimeError(f"Failed to read RGB arrays from {file_path}")

            n_total = len(rgb["red"])
            total_all += n_total

            signals.hud_update.emit({
                "message": f"Analyzing {n_total:,} points...",
                "progress": 20.0,
            })
            signals.progress_update.emit(20.0)

            signals.hud_stage_done.emit(0)

            # ── Stage 1: Filter (25% -> 50%) ─────────────────────────
            mask_valid = (
                (rgb["red"] > self._threshold)
                | (rgb["green"] > self._threshold)
                | (rgb["blue"] > self._threshold)
            )
            n_removed = n_total - int(np.sum(mask_valid))
            removed_all += n_removed

            signals.hud_update.emit({
                "message": f"Removing {n_removed:,} black points...",
                "progress": 50.0,
            })
            signals.progress_update.emit(50.0)

            signals.hud_stage_done.emit(1)

            # ── Stage 2: Save Filtered LAS (50% -> 75%) ──────────────
            import laspy
            las = laspy.read(file_path)

            n_kept = LasLayerSource.create_filtered_las(las, mask_valid, output_clean)
            if n_kept is None:
                raise RuntimeError(f"Error saving filtered LAS: {output_clean}")
            kept_all += n_kept
            output_clean_list.append(output_clean)

            signals.hud_update.emit({
                "message": f"Saving filtered ({n_kept:,} points)...",
                "progress": 75.0,
            })
            signals.progress_update.emit(75.0)

            signals.hud_stage_done.emit(2)

            # ── Stage 3: Save Black Points (optional, 75% -> 100%) ───
            if self._save_black_points and n_removed > 0:
                mask_black = ~mask_valid
                n_black_saved = LasLayerSource.create_filtered_las(las, mask_black, output_black)
                if n_black_saved is not None:
                    black_all += n_black_saved
                    output_black_list.append(output_black)

                signals.hud_update.emit({
                    "message": f"Saving {n_black_saved:,} black points...",
                    "progress": 95.0,
                })
                signals.progress_update.emit(95.0)

            signals.hud_stage_done.emit(3)

        # ── Result ───────────────────────────────────────────────
        self.result = {
            "n_total": total_all,
            "n_removed": removed_all,
            "n_kept": kept_all,
            "n_black": black_all,
            "output_clean": output_clean_list,
            "output_black": output_black_list,
        }
        return True

    def __repr__(self) -> str:
        return (
            f"<LasBlackFilterTask "
            f"files={len(self._files)}, "
            f"threshold={self._threshold}>"
        )