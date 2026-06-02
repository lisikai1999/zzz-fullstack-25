import numpy as np
from typing import List, Tuple, Dict


def compute_iou_bbox(box_a: List[float], box_b: List[float]) -> float:
    x_inter_min = max(box_a[0], box_b[0])
    y_inter_min = max(box_a[1], box_b[1])
    x_inter_max = min(box_a[2], box_b[2])
    y_inter_max = min(box_a[3], box_b[3])

    inter_width = max(0, x_inter_max - x_inter_min)
    inter_height = max(0, y_inter_max - y_inter_min)
    intersection = inter_width * inter_height

    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    union = area_a + area_b - intersection

    if union == 0:
        return 0.0
    return intersection / union


def compute_dice_bbox(box_a: List[float], box_b: List[float]) -> float:
    x_inter_min = max(box_a[0], box_b[0])
    y_inter_min = max(box_a[1], box_b[1])
    x_inter_max = min(box_a[2], box_b[2])
    y_inter_max = min(box_a[3], box_b[3])

    inter_width = max(0, x_inter_max - x_inter_min)
    inter_height = max(0, y_inter_max - y_inter_min)
    intersection = inter_width * inter_height

    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    total = area_a + area_b

    if total == 0:
        return 0.0
    return (2 * intersection) / total


def compute_iou_mask(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
    intersection = np.logical_and(mask_a, mask_b).sum()
    union = np.logical_or(mask_a, mask_b).sum()
    if union == 0:
        return 0.0
    return float(intersection) / float(union)


def compute_dice_mask(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
    intersection = np.logical_and(mask_a, mask_b).sum()
    total = mask_a.sum() + mask_b.sum()
    if total == 0:
        return 0.0
    return float(2 * intersection) / float(total)


def compute_cohens_kappa(labels_a: List[str], labels_b: List[str]) -> float:
    assert len(labels_a) == len(labels_b)
    n = len(labels_a)
    if n == 0:
        return 0.0

    p_o = sum(1 for a, b in zip(labels_a, labels_b) if a == b) / n

    all_labels = set(labels_a) | set(labels_b)
    p_e = 0.0
    for label in all_labels:
        freq_a = labels_a.count(label) / n
        freq_b = labels_b.count(label) / n
        p_e += freq_a * freq_b

    if p_e >= 1.0:
        return 1.0
    return (p_o - p_e) / (1.0 - p_e)


def polygon_to_mask(polygon_points: List[Tuple[int, int]], width: int, height: int) -> np.ndarray:
    mask = np.zeros((height, width), dtype=bool)
    if len(polygon_points) < 3:
        return mask

    min_y = max(0, min(p[1] for p in polygon_points))
    max_y = min(height - 1, max(p[1] for p in polygon_points))

    for y in range(min_y, max_y + 1):
        intersections = []
        n = len(polygon_points)
        for i in range(n):
            j = (i + 1) % n
            y1, y2 = polygon_points[i][1], polygon_points[j][1]
            x1, x2 = polygon_points[i][0], polygon_points[j][0]

            if y1 == y2:
                continue
            if y < min(y1, y2) or y >= max(y1, y2):
                continue

            x_intersect = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            intersections.append(x_intersect)

        intersections.sort()

        for k in range(0, len(intersections) - 1, 2):
            x_start = max(0, int(np.ceil(intersections[k])))
            x_end = min(width - 1, int(np.floor(intersections[k + 1])))
            if x_start <= x_end:
                mask[y, x_start:x_end + 1] = True

    return mask


def rle_to_mask(rle: Dict, width: int, height: int) -> np.ndarray:
    counts = rle["counts"]
    mask_flat = np.zeros(width * height, dtype=bool)
    pos = 0
    for i, count in enumerate(counts):
        if i % 2 == 1:
            mask_flat[pos:pos + count] = True
        pos += count
    return mask_flat.reshape((height, width))


def mask_to_rle(mask: np.ndarray) -> Dict:
    flat = mask.flatten()
    counts = []
    current_val = False
    current_count = 0

    for val in flat:
        if val == current_val:
            current_count += 1
        else:
            counts.append(current_count)
            current_val = val
            current_count = 1

    counts.append(current_count)
    if len(counts) % 2 == 0:
        counts.append(0)

    return {"counts": counts, "size": [mask.shape[0], mask.shape[1]]}
