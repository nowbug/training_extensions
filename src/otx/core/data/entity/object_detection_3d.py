# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
"""Module for OTX detection data entities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from torchvision import tv_tensors

from otx.core.data.entity.base import (
    OTXBatchDataEntity,
    OTXBatchPredEntity,
    OTXDataEntity,
    OTXPredEntity,
)
from otx.core.data.entity.utils import register_pytree_node
from otx.core.types.task import OTXTaskType

if TYPE_CHECKING:
    from numpy import ndarray
    from torch import LongTensor, Tensor


@register_pytree_node
@dataclass
class Det3DDataEntity(OTXDataEntity):
    """Data entity for 3d object detection task.

    : param boxes (tv_tensors.BoundingBoxes): The bounding boxes for the objects in the image.
    : param calib_matrix (Tensor): The calibration matrix for the 3D object detection.
    : param boxes_3d (Tensor): The 3D bounding boxes for the objects.
    : param size_2d (Tensor): The 2D size of the objects.
    : param size_3d (Tensor): The 3D size of the objects.
    : param depth (Tensor): The depth of the objects.
    : param heading_angle (Tensor): The heading angle of the objects.
    : param labels (LongTensor): The labels of the objects.
    : param original_kitti_format (list[dict[str, Any]] | None): The original KITTI format of the objects, if available.

    """

    @property
    def task(self) -> OTXTaskType:
        """OTX Task type definition."""
        return OTXTaskType.OBJECT_DETECTION_3D

    boxes: tv_tensors.BoundingBoxes | ndarray
    calib_matrix: Tensor | ndarray
    boxes_3d: Tensor | ndarray
    size_2d: Tensor | ndarray
    size_3d: Tensor | ndarray
    depth: Tensor | ndarray
    heading_angle: Tensor | ndarray
    labels: LongTensor | ndarray
    original_kitti_format: dict[str, Any] | None


@dataclass
class Det3DPredEntity(OTXPredEntity, Det3DDataEntity):
    """Data entity to represent the 3d object detection model output prediction."""


@dataclass
class Det3DBatchDataEntity(OTXBatchDataEntity[Det3DDataEntity]):
    """Data entity for 3d object detection task.

    : param boxes list[tv_tensors.BoundingBoxes]: The bounding boxes for the objects in the image.
    : param calib_matrix list[Tensor]: The calibration matrix for the 3D object detection.
    : param boxes_3d list[Tensor]: The 3D bounding boxes for the objects.
    : param size_2d list[Tensor]: The 2D size of the objects.
    : param size_3d list[Tensor]: The 3D size of the objects.
    : param depth list[Tensor]: The depth of the objects.
    : param heading_angle list[Tensor]: The heading angle of the objects.
    : param labels list[LongTensor]: The labels of the objects.
    : param original_kitti_format list[list[dict[str, Any]] | None]: The original KITTI format of the objects,
        if available. Needed for validation and KITTI metric.
    """

    images: Tensor
    boxes: list[tv_tensors.BoundingBoxes]
    calib_matrix: list[Tensor]
    boxes_3d: list[Tensor]
    size_2d: list[Tensor]
    size_3d: list[Tensor]
    depth: list[Tensor]
    heading_angle: list[Tensor]
    labels: list[LongTensor]
    original_kitti_format: list[dict[str, Any] | None]

    @property
    def task(self) -> OTXTaskType:
        """OTX Task type definition."""
        return OTXTaskType.OBJECT_DETECTION_3D

    @classmethod
    def collate_fn(
        cls,
        entities: list[Det3DDataEntity],
        stack_images: bool = True,
    ) -> Det3DBatchDataEntity:
        """Collection function to collect `DetDataEntity` into `DetBatchDataEntity` in data loader.

        Args:
            entities: List of `DetDataEntity`.
            stack_images: If True, return 4D B x C x H x W image tensor.
                Otherwise return a list of 3D C x H x W image tensor.

        Returns:
            Collated `DetBatchDataEntity`
        """
        batch_data = super().collate_fn(entities, stack_images=stack_images)
        batch_input_shape = tuple(batch_data.images[0].size()[-2:])
        for info in batch_data.imgs_info:
            info.batch_input_shape = batch_input_shape
        return Det3DBatchDataEntity(
            batch_size=batch_data.batch_size,
            images=batch_data.images,
            imgs_info=batch_data.imgs_info,
            boxes=[entity.boxes for entity in entities],
            labels=[entity.labels for entity in entities],
            calib_matrix=[entity.calib_matrix for entity in entities],
            boxes_3d=[entity.boxes_3d for entity in entities],
            size_2d=[entity.size_2d for entity in entities],
            size_3d=[entity.size_3d for entity in entities],
            depth=[entity.depth for entity in entities],
            heading_angle=[entity.heading_angle for entity in entities],
            original_kitti_format=[entity.original_kitti_format for entity in entities],
        )

    def pin_memory(self) -> Det3DBatchDataEntity:
        """Pin memory for member tensor variables."""
        return (
            super()
            .pin_memory()
            .wrap(
                boxes=[tv_tensors.wrap(bbox.pin_memory(), like=bbox) for bbox in self.boxes],
                labels=[label.pin_memory() for label in self.labels],
                calib_matrix=[calib_matrix.pin_memory() for calib_matrix in self.calib_matrix],
                boxes_3d=[boxes_3d.pin_memory() for boxes_3d in self.boxes_3d],
                size_2d=[size_2d.pin_memory() for size_2d in self.size_2d],
                size_3d=[size_3d.pin_memory() for size_3d in self.size_3d],
                depth=[depth.pin_memory() for depth in self.depth],
                heading_angle=[heading_angle.pin_memory() for heading_angle in self.heading_angle],
                original_kitti_format=self.original_kitti_format,
            )
        )


@dataclass
class Det3DBatchPredEntity(OTXBatchPredEntity, Det3DBatchDataEntity):
    """Data entity to represent model output predictions for 3d object detection task."""

    boxes: tv_tensors.BoundingBoxes
    scores: Tensor
    calib_matrix: Tensor
    boxes_3d: Tensor
    size_2d: Tensor
    size_3d: Tensor
    depth: Tensor
    heading_angle: Tensor
    labels: Tensor
