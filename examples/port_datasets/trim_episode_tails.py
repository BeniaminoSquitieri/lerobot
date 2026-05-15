#!/usr/bin/env python

"""Create a cleaned LeRobot dataset by trimming episode tails.

Example:
    python examples/port_datasets/trim_episode_tails.py \
        --repo-id Squitieri/close_machine \
        --output-repo-id Squitieri/close_machine_clean \
        --output-root /tmp/close_machine_clean \
        --trim-tail 0:1 \
        --trim-tail 2:1
"""

from __future__ import annotations

import argparse
import copy
import shutil
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from tqdm import tqdm

from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.utils.constants import DEFAULT_FEATURES


def parse_episode_counts(values: list[str]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for value in values:
        for item in value.split(","):
            if not item:
                continue
            episode, count = item.split(":", maxsplit=1)
            episode_idx = int(episode)
            frame_count = int(count)
            if frame_count < 0:
                raise ValueError(f"Trim count must be non-negative: {item}")
            counts[episode_idx] = frame_count
    return counts


def parse_episode_list(values: list[str]) -> set[int]:
    episodes: set[int] = set()
    for value in values:
        for item in value.split(","):
            if item:
                episodes.add(int(item))
    return episodes


def image_to_pil(value) -> Image.Image:
    if isinstance(value, Image.Image):
        return value.convert("RGB")

    if isinstance(value, torch.Tensor):
        value = value.detach().cpu()
        if value.ndim == 3 and value.shape[0] in (1, 3, 4):
            value = value.permute(1, 2, 0)
        value = value.numpy()

    array = np.asarray(value)
    if array.dtype != np.uint8:
        array = np.clip(array, 0.0, 1.0)
        array = (array * 255).astype(np.uint8)

    return Image.fromarray(array).convert("RGB")


def feature_value(raw_item: dict, decoded_item: dict, key: str, feature: dict):
    if feature["dtype"] in {"image", "video"}:
        return image_to_pil(decoded_item[key])

    value = raw_item[key]
    dtype = np.dtype(feature["dtype"])
    return np.asarray(value, dtype=dtype)


def task_by_index(dataset: LeRobotDataset) -> dict[int, str]:
    return {int(row.task_index): str(task) for task, row in dataset.meta.tasks.iterrows()}


def copy_episode(
    source: LeRobotDataset,
    dest: LeRobotDataset,
    episode_idx: int,
    from_index: int,
    to_index: int,
    tasks_by_index: dict[int, str],
) -> int:
    copied = 0
    data_keys = [key for key in source.meta.features if key not in DEFAULT_FEATURES]

    for global_idx in range(from_index, to_index):
        raw_item = source.get_raw_item(global_idx)
        decoded_item = source[global_idx]
        task = tasks_by_index[int(raw_item["task_index"])]
        frame = {
            key: feature_value(raw_item, decoded_item, key, source.meta.features[key]) for key in data_keys
        }
        frame["task"] = task
        dest.add_frame(frame)
        copied += 1

    if copied == 0:
        raise ValueError(f"Episode {episode_idx} has no frames after trimming")

    dest.save_episode()
    return copied


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-id", required=True, help="Source LeRobot dataset repo id.")
    parser.add_argument("--root", type=Path, default=None, help="Optional local source dataset root.")
    parser.add_argument("--revision", default=None, help="Optional source revision.")
    parser.add_argument("--output-repo-id", required=True, help="Repo id stored in the cleaned dataset.")
    parser.add_argument("--output-root", type=Path, required=True, help="Local output directory.")
    parser.add_argument(
        "--trim-tail",
        action="append",
        default=[],
        metavar="EPISODE:N",
        help="Trim N frames from the end of EPISODE. Can be repeated or comma-separated.",
    )
    parser.add_argument(
        "--drop-episode",
        action="append",
        default=[],
        metavar="EPISODE",
        help="Drop an entire episode. Can be repeated or comma-separated.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Delete output-root if it already exists.")
    parser.add_argument("--dry-run", action="store_true", help="Print the planned edit without writing files.")
    parser.add_argument("--push-to-hub", action="store_true", help="Upload the cleaned dataset after creation.")
    parser.add_argument("--private", action="store_true", help="Create/upload the Hub dataset as private.")
    args = parser.parse_args()

    trims = parse_episode_counts(args.trim_tail)
    dropped = parse_episode_list(args.drop_episode)

    source = LeRobotDataset(args.repo_id, root=args.root, revision=args.revision)

    invalid = (set(trims) | dropped) - set(range(source.meta.total_episodes))
    if invalid:
        raise ValueError(f"Invalid episode indices: {sorted(invalid)}")

    print(f"Source: {args.repo_id} ({source.meta.total_episodes} episodes, {source.meta.total_frames} frames)")
    print("Video-only surplus frames, when present, are removed by rewriting the dataset from indexed frames.")
    for episode_idx, episode in enumerate(source.meta.episodes):
        length = int(episode["length"])
        trim = trims.get(episode_idx, 0)
        action = "drop" if episode_idx in dropped else f"keep {length - trim}/{length}"
        if trim:
            action += f" (trim tail {trim})"

        surplus = []
        for video_key in source.meta.video_keys:
            from_key = f"videos/{video_key}/from_timestamp"
            to_key = f"videos/{video_key}/to_timestamp"
            if from_key not in episode or to_key not in episode:
                continue
            video_frames = round((float(episode[to_key]) - float(episode[from_key])) * source.meta.fps)
            extra_frames = video_frames - length
            if extra_frames:
                surplus.append(f"{video_key} {extra_frames:+d}f")

        suffix = f" | video surplus: {', '.join(surplus)}" if surplus else ""
        print(f"episode {episode_idx}: {action}{suffix}")

    if args.dry_run:
        return

    if args.output_root.exists():
        if not args.overwrite:
            raise FileExistsError(f"{args.output_root} already exists. Use --overwrite to replace it.")
        shutil.rmtree(args.output_root)

    dest = LeRobotDataset.create(
        repo_id=args.output_repo_id,
        fps=source.meta.fps,
        features=copy.deepcopy(source.meta.features),
        root=args.output_root,
        robot_type=source.meta.robot_type,
        use_videos=bool(source.meta.video_keys),
    )

    tasks_by_idx = task_by_index(source)
    total_copied = 0
    try:
        for episode_idx, episode in enumerate(tqdm(source.meta.episodes, desc="Copying episodes")):
            if episode_idx in dropped:
                continue

            from_index = int(episode["dataset_from_index"])
            to_index = int(episode["dataset_to_index"]) - trims.get(episode_idx, 0)
            copied = copy_episode(source, dest, episode_idx, from_index, to_index, tasks_by_idx)
            total_copied += copied
    finally:
        dest.finalize()

    print(f"Created {args.output_root} with {dest.meta.total_episodes} episodes and {total_copied} frames")

    if args.push_to_hub:
        dest.push_to_hub(private=args.private)


if __name__ == "__main__":
    main()
