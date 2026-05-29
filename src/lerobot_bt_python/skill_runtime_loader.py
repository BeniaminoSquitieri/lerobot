"""@file skill_runtime_loader.py
@brief Build the cached policy runtime bundle used by `SkillRunner`.

Splitting the heavy checkpoint loading out of the executor keeps the control
loop file focused on inference and termination semantics. The runtime cache
(`SkillRunner.skills`) still owns the bundles produced here.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from huggingface_hub import snapshot_download

from lerobot.policies.factory import make_policy, make_pre_post_processors
from lerobot.policies.pretrained import PreTrainedPolicy
from lerobot.processor import PolicyAction, PolicyProcessorPipeline, RobotProcessorPipeline
from lerobot.processor.rename_processor import rename_stats

from .config import PrimitiveSkillConfig

if TYPE_CHECKING:
    from lerobot.robots.custom_manipulator.custom_manipulator import CustomManipulator


@dataclass
class SkillRuntime:
    """@brief Runtime bundle for one configured learned primitive."""

    cfg: PrimitiveSkillConfig
    """Skill YAML entry that owns names, policy config, task text, and transitions."""

    ds_meta: Any
    """Dataset metadata or live robot metadata used to build policy features."""

    policy: PreTrainedPolicy
    """Loaded LeRobot policy object used for inference."""

    preprocessor: PolicyProcessorPipeline[dict, dict]
    """Policy observation preprocessor applied before inference."""

    postprocessor: PolicyProcessorPipeline[PolicyAction, PolicyAction]
    """Policy action postprocessor applied after inference."""

    def reset(self) -> None:
        """@brief Reset stateful policy/preprocessor/postprocessor queues."""
        self.policy.reset()
        self.preprocessor.reset()
        self.postprocessor.reset()


@dataclass
class LiveRobotDatasetMetadata:
    """@brief Minimal metadata object for live robot rollouts."""

    repo_id: str
    """Logical dataset repository id used by policy loading code."""

    features: dict[str, dict]
    """Feature schema assembled from robot action and observation pipelines."""

    stats: dict | None = None
    """Optional dataset statistics; live metadata leaves this absent by default."""


def build_skill_runtime(
    skill_cfg: PrimitiveSkillConfig,
    rename_map: dict[str, str],
    robot: "CustomManipulator",
    robot_action_processor: RobotProcessorPipeline,
    robot_observation_processor: RobotProcessorPipeline,
    force_download: bool = False,
) -> SkillRuntime:
    """@brief Create the cached runtime bundle for one skill."""
    if skill_cfg.policy is None:
        raise ValueError(f"Skill '{skill_cfg.name}' has no active policy selected.")

    if force_download and skill_cfg.policy.pretrained_path:
        pretrained_path_str = str(skill_cfg.policy.pretrained_path)
        if not Path(pretrained_path_str).is_dir():
            logging.info(
                "Force-downloading policy '%s' from HuggingFace Hub (force_download=True).",
                pretrained_path_str,
            )
            try:
                snapshot_download(
                    repo_id=pretrained_path_str,
                    force_download=True,
                    resume_download=True,
                )
            except Exception as exc:
                logging.warning(
                    "Force-download of '%s' failed (%s). Falling back to cached copy.",
                    pretrained_path_str, exc,
                )

    if skill_cfg.metadata_source == "robot":
        from lerobot.datasets.pipeline_features import (
            aggregate_pipeline_dataset_features,
            create_initial_features,
        )
        from lerobot.utils.feature_utils import combine_feature_dicts

        features = combine_feature_dicts(
            aggregate_pipeline_dataset_features(
                pipeline=robot_action_processor,
                initial_features=create_initial_features(action=robot.action_features),
                use_videos=True,
            ),
            aggregate_pipeline_dataset_features(
                pipeline=robot_observation_processor,
                initial_features=create_initial_features(observation=robot.observation_features),
                use_videos=True,
            ),
        )
        ds_meta = LiveRobotDatasetMetadata(repo_id=skill_cfg.dataset_repo_id, features=features)
        logging.info(
            "Skill '%s' using live robot rollout metadata with features=%s.",
            skill_cfg.name,
            sorted(features),
        )
    else:
        from lerobot.datasets.lerobot_dataset import LeRobotDatasetMetadata

        ds_meta = LeRobotDatasetMetadata(
            skill_cfg.dataset_repo_id,
            root=skill_cfg.dataset_root,
            revision=skill_cfg.dataset_revision,
        )

    policy = make_policy(skill_cfg.policy, ds_meta=ds_meta, rename_map=rename_map)
    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=skill_cfg.policy,
        pretrained_path=skill_cfg.policy.pretrained_path,
        dataset_stats=rename_stats(ds_meta.stats, rename_map),
        preprocessor_overrides={
            "device_processor": {"device": skill_cfg.policy.device},
            "rename_observations_processor": {"rename_map": rename_map},
        },
    )
    return SkillRuntime(
        cfg=skill_cfg,
        ds_meta=ds_meta,
        policy=policy,
        preprocessor=preprocessor,
        postprocessor=postprocessor,
    )
