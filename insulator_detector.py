"""
Insulator Detection Module
Detects insulators using contour analysis - no training required
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict
import config


class InsulatorDetector:
    """Detects insulators based on shape characteristics"""
    
    def __init__(self):
        self.insulators = []
        
    def detect_insulators(self, image: np.ndarray, edges: np.ndarray) -> List[Dict]:
        """
        Detect insulators using contour analysis
        
        Args:
            image: Original BGR image
            edges: Edge map from Canny detection
            
        Returns:
            List of insulator dictionaries with properties
        """
        # Find contours
        contours, _ = cv2.findContours(
            edges,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        insulators = []
        
        for contour in contours:
            # Calculate properties
            area = cv2.contourArea(contour)
            
            # Filter by area
            if area < config.MIN_CONTOUR_AREA or area > config.MAX_CONTOUR_AREA:
                continue
            
            # Calculate roundness (circularity)
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue
            
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            
            if circularity < config.MIN_ROUNDNESS:
                continue
            
            # Calculate bounding box and aspect ratio
            x, y, w, h = cv2.boundingRect(contour)
            
            if h == 0:
                continue
            
            aspect_ratio = w / h
            
            # Filter by aspect ratio
            if (aspect_ratio < config.INSULATOR_ASPECT_RATIO_MIN or 
                aspect_ratio > config.INSULATOR_ASPECT_RATIO_MAX):
                continue
            
            # This looks like an insulator
            insulator = {
                'contour': contour,
                'area': area,
                'circularity': circularity,
                'aspect_ratio': aspect_ratio,
                'center': (x + w//2, y + h//2),
                'bbox': (x, y, w, h)
            }
            
            insulators.append(insulator)
        
        self.insulators = insulators
        return insulators
    
    def cluster_insulators_by_level(self, insulators: List[Dict]) -> List[List[Dict]]:
        """
        Cluster insulators by their Y position (vertical level)
        
        Args:
            insulators: List of insulator dictionaries
            
        Returns:
            List of insulator clusters (grouped by level)
        """
        if not insulators:
            return []
        
        # Sort by Y position
        sorted_insulators = sorted(insulators, key=lambda ins: ins['center'][1])
        
        # Cluster by Y position
        clusters = []
        current_cluster = [sorted_insulators[0]]
        current_y = sorted_insulators[0]['center'][1]
        
        for insulator in sorted_insulators[1:]:
            y = insulator['center'][1]
            if abs(y - current_y) <= config.LEVEL_CLUSTERING_TOLERANCE:
                current_cluster.append(insulator)
            else:
                clusters.append(current_cluster)
                current_cluster = [insulator]
                current_y = y
        
        clusters.append(current_cluster)
        return clusters
    
    def count_insulators_by_level(self, insulators: List[Dict]) -> Dict[int, int]:
        """
        Count insulators at each level
        
        Args:
            insulators: List of insulator dictionaries
            
        Returns:
            Dictionary mapping level index to insulator count
        """
        clusters = self.cluster_insulators_by_level(insulators)
        return {i: len(cluster) for i, cluster in enumerate(clusters)}
    
    def get_insulator_features(self, image: np.ndarray, edges: np.ndarray) -> Dict:
        """
        Extract all insulator-related features
        
        Args:
            image: Original BGR image
            edges: Edge map from Canny detection
            
        Returns:
            Dictionary with insulator features
        """
        insulators = self.detect_insulators(image, edges)
        clusters = self.cluster_insulators_by_level(insulators)
        level_counts = self.count_insulators_by_level(insulators)
        
        return {
            'total_insulators': len(insulators),
            'insulator_levels': len(clusters),
            'insulators_per_level': level_counts,
            'insulators': insulators,
            'clusters': clusters
        }
