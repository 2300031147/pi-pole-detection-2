"""
Geometry Detection Module
Core OpenCV-based detection for pole structure analysis
No ML training required - pure computer vision
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict
import config


class GeometryDetector:
    """Detects pole geometry using edge and line detection"""
    
    def __init__(self):
        self.vertical_lines = []
        self.horizontal_lines = []
        self.diagonal_lines = []
        
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better edge detection
        
        Args:
            image: Input BGR image
            
        Returns:
            Preprocessed grayscale image
        """
        # Resize if too large (for Pi 5 performance)
        h, w = image.shape[:2]
        if w > config.MAX_IMAGE_WIDTH or h > config.MAX_IMAGE_HEIGHT:
            scale = min(config.MAX_IMAGE_WIDTH / w, config.MAX_IMAGE_HEIGHT / h)
            new_w, new_h = int(w * scale), int(h * scale)
            image = cv2.resize(image, (new_w, new_h))
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, config.GAUSSIAN_BLUR_KERNEL, 0)
        
        return blurred
    
    def detect_edges(self, image: np.ndarray) -> np.ndarray:
        """
        Apply Canny edge detection
        
        Args:
            image: Preprocessed grayscale image
            
        Returns:
            Edge map
        """
        edges = cv2.Canny(
            image,
            config.CANNY_THRESHOLD_LOW,
            config.CANNY_THRESHOLD_HIGH
        )
        return edges
    
    def detect_lines(self, edges: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect lines using Hough Line Transform
        
        Args:
            edges: Edge map from Canny detection
            
        Returns:
            List of lines as (x1, y1, x2, y2) tuples
        """
        lines = cv2.HoughLinesP(
            edges,
            config.HOUGH_RHO,
            np.pi / 180 * config.HOUGH_THETA_DEGREES,
            config.HOUGH_THRESHOLD,
            minLineLength=config.HOUGH_MIN_LINE_LENGTH,
            maxLineGap=config.HOUGH_MAX_LINE_GAP
        )
        
        if lines is None:
            return []
        
        # Convert to list of tuples
        return [tuple(line[0]) for line in lines]
    
    def classify_line_orientation(self, x1: int, y1: int, x2: int, y2: int) -> str:
        """
        Classify line as vertical, horizontal, or diagonal
        
        Args:
            x1, y1, x2, y2: Line endpoints
            
        Returns:
            'vertical', 'horizontal', or 'diagonal'
        """
        # Calculate angle from vertical
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        
        if dx == 0:
            return 'vertical'
        
        angle = np.degrees(np.arctan2(dy, dx))
        
        # Vertical: close to 90 degrees
        if angle >= (90 - config.VERTICAL_ANGLE_THRESHOLD):
            return 'vertical'
        # Horizontal: close to 0 degrees
        elif angle <= config.HORIZONTAL_ANGLE_THRESHOLD:
            return 'horizontal'
        else:
            return 'diagonal'
    
    def classify_lines(self, lines: List[Tuple[int, int, int, int]]):
        """
        Classify all lines into vertical, horizontal, diagonal
        
        Args:
            lines: List of (x1, y1, x2, y2) tuples
        """
        self.vertical_lines = []
        self.horizontal_lines = []
        self.diagonal_lines = []
        
        for line in lines:
            x1, y1, x2, y2 = line
            orientation = self.classify_line_orientation(x1, y1, x2, y2)
            
            if orientation == 'vertical':
                self.vertical_lines.append(line)
            elif orientation == 'horizontal':
                self.horizontal_lines.append(line)
            else:
                self.diagonal_lines.append(line)
    
    def cluster_horizontal_lines_by_level(self) -> List[List[Tuple[int, int, int, int]]]:
        """
        Cluster horizontal lines by their Y position to identify levels
        
        Returns:
            List of line clusters (each cluster is a level)
        """
        if not self.horizontal_lines:
            return []
        
        # Sort lines by average Y position
        lines_with_y = [(line, (line[1] + line[3]) / 2) for line in self.horizontal_lines]
        lines_with_y.sort(key=lambda x: x[1])
        
        # Cluster by Y position
        clusters = []
        current_cluster = [lines_with_y[0][0]]
        current_y = lines_with_y[0][1]
        
        for line, y in lines_with_y[1:]:
            if abs(y - current_y) <= config.LEVEL_CLUSTERING_TOLERANCE:
                current_cluster.append(line)
            else:
                clusters.append(current_cluster)
                current_cluster = [line]
                current_y = y
        
        clusters.append(current_cluster)
        return clusters
    
    def get_level_spacing(self, clusters: List[List[Tuple[int, int, int, int]]]) -> List[float]:
        """
        Calculate spacing between levels
        
        Args:
            clusters: Line clusters from cluster_horizontal_lines_by_level
            
        Returns:
            List of spacing values between consecutive levels
        """
        if len(clusters) < 2:
            return []
        
        # Get average Y position for each cluster
        cluster_y_positions = []
        for cluster in clusters:
            avg_y = np.mean([[(line[1] + line[3]) / 2 for line in cluster]])
            cluster_y_positions.append(avg_y)
        
        # Calculate spacing
        spacings = []
        for i in range(len(cluster_y_positions) - 1):
            spacing = abs(cluster_y_positions[i+1] - cluster_y_positions[i])
            spacings.append(spacing)
        
        return spacings
    
    def analyze_geometry(self, image: np.ndarray) -> Dict:
        """
        Complete geometry analysis pipeline
        
        Args:
            image: Input BGR image
            
        Returns:
            Dictionary with geometry features
        """
        # Preprocess
        preprocessed = self.preprocess_image(image)
        
        # Detect edges
        edges = self.detect_edges(preprocessed)
        
        # Detect and classify lines
        lines = self.detect_lines(edges)
        self.classify_lines(lines)
        
        # Cluster horizontal lines into levels
        level_clusters = self.cluster_horizontal_lines_by_level()
        
        # Calculate spacing
        spacings = self.get_level_spacing(level_clusters)
        
        # Determine if top spacing is larger (33kV characteristic)
        top_spacing_larger = False
        if len(spacings) >= 2:
            top_spacing_larger = spacings[0] > spacings[1] * config.SPACING_THRESHOLD_RATIO
        
        # Calculate symmetry (left vs right crossarms)
        symmetry_score = self._calculate_symmetry()
        
        return {
            'level_count': len(level_clusters),
            'crossarm_count': len(self.horizontal_lines),
            'vertical_pole_detected': len(self.vertical_lines) > 0,
            'spacings': spacings,
            'top_spacing_larger': top_spacing_larger,
            'diagonal_arms': len(self.diagonal_lines),
            'symmetry_score': symmetry_score,
            'edges': edges,
            'preprocessed': preprocessed
        }
    
    def _calculate_symmetry(self) -> float:
        """
        Calculate left-right symmetry of crossarms
        
        Returns:
            Symmetry score (0.0 to 1.0)
        """
        if not self.horizontal_lines:
            return 0.5
        
        # Get image center (assumed to be pole center)
        # This is a simplified calculation
        x_positions = [line[0] for line in self.horizontal_lines] + \
                     [line[2] for line in self.horizontal_lines]
        
        if not x_positions:
            return 0.5
        
        center_x = np.mean(x_positions)
        
        # Count lines on left vs right
        left_count = sum(1 for line in self.horizontal_lines 
                        if (line[0] + line[2]) / 2 < center_x)
        right_count = len(self.horizontal_lines) - left_count
        
        if left_count + right_count == 0:
            return 0.5
        
        # Calculate symmetry (perfect symmetry = 1.0)
        symmetry = 1.0 - abs(left_count - right_count) / (left_count + right_count)
        return symmetry
