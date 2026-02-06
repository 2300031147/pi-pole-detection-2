"""
Configuration file for CODEX Pole Detection System
Zero-training approach for voltage classification
"""

# Image Processing Parameters
CANNY_THRESHOLD_LOW = 50
CANNY_THRESHOLD_HIGH = 150
GAUSSIAN_BLUR_KERNEL = (5, 5)

# Hough Line Transform Parameters
HOUGH_RHO = 1
HOUGH_THETA_DEGREES = 1
HOUGH_THRESHOLD = 100
HOUGH_MIN_LINE_LENGTH = 50
HOUGH_MAX_LINE_GAP = 10

# Line Classification Thresholds (in degrees)
VERTICAL_ANGLE_THRESHOLD = 20  # Lines within ±20° of vertical
HORIZONTAL_ANGLE_THRESHOLD = 20  # Lines within ±20° of horizontal

# Clustering Parameters
LEVEL_CLUSTERING_TOLERANCE = 30  # pixels - Y-position tolerance for grouping horizontal lines
SPACING_THRESHOLD_RATIO = 1.3  # Ratio to determine if top spacing is significantly larger

# Insulator Detection Parameters
MIN_CONTOUR_AREA = 50
MAX_CONTOUR_AREA = 5000
MIN_ROUNDNESS = 0.5  # Circularity threshold (1.0 = perfect circle)
INSULATOR_ASPECT_RATIO_MIN = 0.4
INSULATOR_ASPECT_RATIO_MAX = 2.5

# Voltage Classification Rules
VOLTAGE_RULES = {
    '33kV': {
        'min_levels': 3,
        'min_crossarms': 2,
        'top_spacing_larger': True,
        'min_insulators': 4,
        'description': 'High voltage transmission - 3+ levels with wider top spacing'
    },
    '11kV': {
        'min_levels': 2,
        'max_levels': 2,
        'min_crossarms': 1,
        'max_insulators': 6,
        'description': 'Medium voltage distribution - typically 2 levels'
    },
    'LT': {  # Low Tension
        'max_levels': 1,
        'min_wire_density': 4,
        'description': 'Low tension - single level with multiple wires'
    }
}

# Multi-Circuit Detection
MULTI_CIRCUIT_MIN_LEVELS = 2

# Confidence Scoring Weights
CONFIDENCE_WEIGHTS = {
    'level_match': 0.3,
    'crossarm_match': 0.2,
    'spacing_match': 0.2,
    'insulator_match': 0.2,
    'symmetry_match': 0.1
}

# Performance Settings (for Raspberry Pi 5)
MAX_IMAGE_WIDTH = 1280  # Resize larger images to this width
MAX_IMAGE_HEIGHT = 720  # Resize larger images to this height
