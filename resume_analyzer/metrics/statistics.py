from __future__ import annotations
from math import sqrt
from typing import Optional

def pearson_correlation(x_values: list[float], y_values: list[float]) -> Optional[float]:
    count = len(x_values)
    if count < 3:
        return None
    mean_x, mean_y = sum(x_values) / count, sum(y_values) / count
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values))
    denominator_x = sqrt(sum((x - mean_x) ** 2 for x in x_values))
    denominator_y = sqrt(sum((y - mean_y) ** 2 for y in y_values))
    denominator = denominator_x * denominator_y
    return numerator / denominator if denominator != 0 else 0.0

def linear_regression_slope(x_values: list[float], y_values: list[float]) -> Optional[float]:
    count = len(x_values)
    if count < 2:
        return None
    mean_x, mean_y = sum(x_values) / count, sum(y_values) / count
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values))
    denominator = sum((x - mean_x) ** 2 for x in x_values)
    return numerator / denominator if denominator != 0 else 0.0