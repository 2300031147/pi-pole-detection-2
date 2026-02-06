"""
Feature Extraction Module
Extracts high-level features from geometry and insulator detection
Pure mathematical analysis - no ML required
"""

import numpy as np
from typing import Dict


class FeatureExtractor:
    """Extracts features from detected geometry and insulators"""
    
    def __init__(self):
        pass
    
    def extract_features(self, geometry_data: Dict, insulator_data: Dict) -> Dict:
        """
        Extract all features for classification
        
        Args:
            geometry_data: Output from GeometryDetector.analyze_geometry()
            insulator_data: Output from InsulatorDetector.get_insulator_features()
            
        Returns:
            Dictionary with all extracted features
        """
        features = {
            # Geometry features
            'level_count': geometry_data['level_count'],
            'crossarm_count': geometry_data['crossarm_count'],
            'vertical_pole_detected': geometry_data['vertical_pole_detected'],
            'top_spacing_larger': geometry_data['top_spacing_larger'],
            'diagonal_arms': geometry_data['diagonal_arms'],
            'symmetry_score': geometry_data['symmetry_score'],
            
            # Insulator features
            'total_insulators': insulator_data['total_insulators'],
            'insulator_levels': insulator_data['insulator_levels'],
            'insulators_per_level': insulator_data['insulators_per_level'],
            
            # Derived features
            'wire_density': self._calculate_wire_density(geometry_data),
            'avg_spacing': self._calculate_avg_spacing(geometry_data['spacings']),
            'spacing_variance': self._calculate_spacing_variance(geometry_data['spacings']),
            'has_multi_levels': geometry_data['level_count'] > 1,
        }
        
        return features
    
    def _calculate_wire_density(self, geometry_data: Dict) -> float:
        """
        Calculate wire density (crossarms per level)
        
        Args:
            geometry_data: Geometry analysis results
            
        Returns:
            Average number of crossarms per level
        """
        if geometry_data['level_count'] == 0:
            return 0.0
        
        return geometry_data['crossarm_count'] / geometry_data['level_count']
    
    def _calculate_avg_spacing(self, spacings: list) -> float:
        """
        Calculate average spacing between levels
        
        Args:
            spacings: List of spacing values
            
        Returns:
            Average spacing
        """
        if not spacings:
            return 0.0
        
        return np.mean(spacings)
    
    def _calculate_spacing_variance(self, spacings: list) -> float:
        """
        Calculate variance in spacing (indicates uniformity)
        
        Args:
            spacings: List of spacing values
            
        Returns:
            Spacing variance
        """
        if len(spacings) < 2:
            return 0.0
        
        return np.var(spacings)
