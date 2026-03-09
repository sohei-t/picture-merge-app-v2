"""Shadow generation using Gaussian blur ellipses."""

import cv2
import numpy as np


def generate_shadow(
    canvas_width: int,
    canvas_height: int,
    foot_x: int,
    foot_y: int,
    person_width: int,
    intensity: float,
) -> np.ndarray:
    """Generate a shadow layer for a person.

    Args:
        canvas_width: Canvas width in pixels
        canvas_height: Canvas height in pixels
        foot_x: Foot center X coordinate
        foot_y: Foot Y coordinate
        person_width: Width of the person in pixels
        intensity: Shadow intensity (0.0-1.0)

    Returns:
        RGBA numpy array of the shadow layer
    """
    shadow_layer = np.zeros((canvas_height, canvas_width, 4), dtype=np.uint8)

    if intensity <= 0 or person_width <= 0:
        return shadow_layer

    # Shadow ellipse parameters
    ellipse_width = max(1, int(person_width * 0.4))
    ellipse_height = max(1, int(person_width * 0.075))
    alpha_value = int(255 * intensity * 0.6)
    alpha_value = min(255, max(0, alpha_value))

    # Clamp foot position to canvas bounds
    center_x = max(0, min(canvas_width - 1, foot_x))
    center_y = max(0, min(canvas_height - 1, foot_y))

    # Draw ellipse on shadow layer
    cv2.ellipse(
        shadow_layer,
        center=(center_x, center_y),
        axes=(ellipse_width, ellipse_height),
        angle=0,
        startAngle=0,
        endAngle=360,
        color=(0, 0, 0, alpha_value),
        thickness=-1,
    )

    # Apply Gaussian blur for soft shadow
    shadow_layer = cv2.GaussianBlur(shadow_layer, (21, 21), 10)

    return shadow_layer
