import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest
from services.metrics import (
    compute_iou_bbox,
    compute_dice_bbox,
    compute_iou_mask,
    compute_dice_mask,
    compute_cohens_kappa,
    polygon_to_mask,
    rle_to_mask,
    mask_to_rle,
)


class TestIoUBbox:
    def test_perfect_overlap(self):
        assert compute_iou_bbox([0, 0, 10, 10], [0, 0, 10, 10]) == 1.0

    def test_no_overlap(self):
        assert compute_iou_bbox([0, 0, 5, 5], [10, 10, 15, 15]) == 0.0

    def test_partial_overlap(self):
        # [0,0,10,10] and [5,0,15,10]: intersection=5*10=50, union=100+100-50=150
        result = compute_iou_bbox([0, 0, 10, 10], [5, 0, 15, 10])
        assert abs(result - 50 / 150) < 1e-9

    def test_contained_box(self):
        # [0,0,10,10] contains [2,2,8,8]: intersection=6*6=36, union=100+36-36=100
        result = compute_iou_bbox([0, 0, 10, 10], [2, 2, 8, 8])
        assert abs(result - 36 / 100) < 1e-9

    def test_touching_edges(self):
        # Adjacent boxes with no overlap
        assert compute_iou_bbox([0, 0, 5, 5], [5, 0, 10, 5]) == 0.0

    def test_zero_area_box(self):
        assert compute_iou_bbox([5, 5, 5, 5], [0, 0, 10, 10]) == 0.0

    def test_symmetric(self):
        a = [1, 2, 7, 9]
        b = [3, 4, 10, 11]
        assert compute_iou_bbox(a, b) == compute_iou_bbox(b, a)


class TestDiceBbox:
    def test_perfect_overlap(self):
        assert compute_dice_bbox([0, 0, 10, 10], [0, 0, 10, 10]) == 1.0

    def test_no_overlap(self):
        assert compute_dice_bbox([0, 0, 5, 5], [10, 10, 15, 15]) == 0.0

    def test_partial_overlap(self):
        # intersection=50, total areas=200, dice=2*50/200=0.5
        result = compute_dice_bbox([0, 0, 10, 10], [5, 0, 15, 10])
        assert abs(result - 0.5) < 1e-9


class TestIoUMask:
    def test_identical_masks(self):
        mask = np.ones((10, 10), dtype=bool)
        assert compute_iou_mask(mask, mask) == 1.0

    def test_no_overlap_masks(self):
        a = np.zeros((10, 10), dtype=bool)
        b = np.zeros((10, 10), dtype=bool)
        a[:5, :] = True
        b[5:, :] = True
        assert compute_iou_mask(a, b) == 0.0

    def test_partial_overlap_masks(self):
        a = np.zeros((10, 10), dtype=bool)
        b = np.zeros((10, 10), dtype=bool)
        a[:7, :] = True  # 70 pixels
        b[3:, :] = True  # 70 pixels
        # intersection: rows 3-6 = 4*10=40, union: rows 0-9 = 100
        result = compute_iou_mask(a, b)
        assert abs(result - 40 / 100) < 1e-9

    def test_empty_masks(self):
        a = np.zeros((10, 10), dtype=bool)
        b = np.zeros((10, 10), dtype=bool)
        assert compute_iou_mask(a, b) == 0.0


class TestDiceMask:
    def test_identical_masks(self):
        mask = np.ones((10, 10), dtype=bool)
        assert compute_dice_mask(mask, mask) == 1.0

    def test_no_overlap_masks(self):
        a = np.zeros((10, 10), dtype=bool)
        b = np.zeros((10, 10), dtype=bool)
        a[:5, :] = True
        b[5:, :] = True
        assert compute_dice_mask(a, b) == 0.0

    def test_known_value(self):
        # A=60 pixels, B=40 pixels, intersection=20 pixels
        # Dice = 2*20 / (60+40) = 0.4
        a = np.zeros((10, 10), dtype=bool)
        b = np.zeros((10, 10), dtype=bool)
        a[:6, :] = True  # 60 pixels
        b[4:8, :] = True  # 40 pixels
        # intersection: rows 4,5 = 20 pixels
        result = compute_dice_mask(a, b)
        assert abs(result - 0.4) < 1e-9

    def test_empty_masks(self):
        a = np.zeros((10, 10), dtype=bool)
        b = np.zeros((10, 10), dtype=bool)
        assert compute_dice_mask(a, b) == 0.0

    def test_relationship_to_iou(self):
        # Dice = 2*IoU / (1+IoU) when derived from the same sets
        a = np.zeros((10, 10), dtype=bool)
        b = np.zeros((10, 10), dtype=bool)
        a[:7, :] = True
        b[3:, :] = True
        iou = compute_iou_mask(a, b)
        dice = compute_dice_mask(a, b)
        expected_dice = 2 * iou / (1 + iou)
        assert abs(dice - expected_dice) < 1e-9


class TestCohensKappa:
    def test_perfect_agreement(self):
        labels = ["a", "b", "c", "a", "b"]
        assert compute_cohens_kappa(labels, labels) == 1.0

    def test_known_value(self):
        a = ["yes", "yes", "no", "yes", "no", "no", "yes", "no"]
        b = ["yes", "no", "no", "yes", "no", "no", "yes", "yes"]
        # p_o = 6/8 = 0.75
        # p_e = (4/8)*(4/8) + (4/8)*(4/8) = 0.25 + 0.25 = 0.5
        # kappa = (0.75 - 0.5) / (1 - 0.5) = 0.5
        result = compute_cohens_kappa(a, b)
        assert abs(result - 0.5) < 1e-9

    def test_complete_disagreement(self):
        a = ["yes", "yes", "yes", "yes"]
        b = ["no", "no", "no", "no"]
        # p_o = 0, p_e = (4/4)*(0/4) + (0/4)*(4/4) = 0
        # kappa = (0 - 0) / (1 - 0) = 0
        result = compute_cohens_kappa(a, b)
        assert result == 0.0

    def test_moderate_agreement(self):
        a = ["cat", "dog", "cat", "cat", "dog", "dog"]
        b = ["cat", "dog", "dog", "cat", "dog", "cat"]
        # p_o = 4/6
        # p_e: cat: (3/6)*(3/6) + dog: (3/6)*(3/6) = 0.25 + 0.25 = 0.5
        # kappa = (4/6 - 0.5) / (1 - 0.5) = (2/3 - 0.5) / 0.5 = (1/6) / 0.5 = 1/3
        result = compute_cohens_kappa(a, b)
        assert abs(result - 1 / 3) < 1e-9

    def test_empty_labels(self):
        assert compute_cohens_kappa([], []) == 0.0

    def test_single_category_perfect(self):
        a = ["yes", "yes", "yes"]
        b = ["yes", "yes", "yes"]
        # p_o = 1.0, p_e = 1.0 -> edge case returns 1.0
        assert compute_cohens_kappa(a, b) == 1.0


class TestPolygonToMask:
    def test_square_polygon(self):
        points = [(2, 2), (8, 2), (8, 8), (2, 8)]
        mask = polygon_to_mask(points, 10, 10)
        # Interior should be filled
        assert mask[5, 5] == True
        # Exterior should be empty
        assert mask[0, 0] == False
        assert mask[9, 9] == False

    def test_triangle(self):
        points = [(5, 0), (10, 10), (0, 10)]
        mask = polygon_to_mask(points, 11, 11)
        # Center of triangle should be filled
        assert mask[7, 5] == True
        # Top corners should be empty
        assert mask[0, 0] == False
        assert mask[0, 10] == False

    def test_empty_polygon(self):
        mask = polygon_to_mask([], 10, 10)
        assert mask.sum() == 0

    def test_two_points(self):
        mask = polygon_to_mask([(0, 0), (5, 5)], 10, 10)
        assert mask.sum() == 0


class TestRLE:
    def test_roundtrip(self):
        mask = np.zeros((10, 10), dtype=bool)
        mask[3:7, 2:8] = True
        rle = mask_to_rle(mask)
        recovered = rle_to_mask(rle, 10, 10)
        assert np.array_equal(mask, recovered)

    def test_empty_mask(self):
        mask = np.zeros((5, 5), dtype=bool)
        rle = mask_to_rle(mask)
        recovered = rle_to_mask(rle, 5, 5)
        assert np.array_equal(mask, recovered)

    def test_full_mask(self):
        mask = np.ones((5, 5), dtype=bool)
        rle = mask_to_rle(mask)
        recovered = rle_to_mask(rle, 5, 5)
        assert np.array_equal(mask, recovered)
