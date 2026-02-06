"""
CODEX Pole Detection System
Zero-training pole voltage classification using geometry and rules
Main detection pipeline
"""

import cv2
import numpy as np
from typing import Dict, Optional
import time

from geometry_detector import GeometryDetector
from insulator_detector import InsulatorDetector
from feature_extractor import FeatureExtractor
from rule_engine import RuleEngine
import config


class PoleDetector:
    """Main pole detection pipeline - coordinates all modules"""
    
    def __init__(self):
        self.geometry_detector = GeometryDetector()
        self.insulator_detector = InsulatorDetector()
        self.feature_extractor = FeatureExtractor()
        self.rule_engine = RuleEngine()
        
    def detect(self, image_path: str, visualize: bool = False) -> Dict:
        """
        Complete detection pipeline
        
        Args:
            image_path: Path to input image
            visualize: Whether to generate visualization
            
        Returns:
            Dictionary with detection results
        """
        start_time = time.time()
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            return {
                'error': 'Failed to load image',
                'image_path': image_path
            }
        
        # Step 1: Geometry detection
        geometry_data = self.geometry_detector.analyze_geometry(image)
        
        # Step 2: Insulator detection
        insulator_data = self.insulator_detector.get_insulator_features(
            image,
            geometry_data['edges']
        )
        
        # Step 3: Feature extraction
        features = self.feature_extractor.extract_features(geometry_data, insulator_data)
        
        # Step 4: Voltage classification
        voltage_class, confidence, matched_rules = self.rule_engine.classify_voltage(features)
        
        # Step 5: Multi-circuit detection
        is_multi_circuit = self.rule_engine.detect_multi_circuit(features)
        
        # Step 6: Detailed confidence scoring
        confidence_details = self.rule_engine.calculate_confidence_score(features, matched_rules)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Compile results
        results = {
            'image_path': image_path,
            'voltage_class': voltage_class,
            'confidence': confidence,
            'confidence_details': confidence_details,
            'matched_rules': matched_rules,
            'is_multi_circuit': is_multi_circuit,
            'circuit_type': 'multi_circuit' if is_multi_circuit else 'single_circuit',
            'features': features,
            'processing_time_seconds': processing_time,
            'rule_description': config.VOLTAGE_RULES[voltage_class]['description']
        }
        
        # Generate visualization if requested
        if visualize:
            vis_image = self._visualize_detection(image, geometry_data, insulator_data, results)
            results['visualization'] = vis_image
        
        return results
    
    def _visualize_detection(self, image: np.ndarray, geometry_data: Dict, 
                           insulator_data: Dict, results: Dict) -> np.ndarray:
        """
        Create visualization of detection results
        
        Args:
            image: Original image
            geometry_data: Geometry detection results
            insulator_data: Insulator detection results
            results: Final detection results
            
        Returns:
            Visualization image
        """
        vis_image = image.copy()
        
        # Draw vertical lines (pole) in green
        for line in self.geometry_detector.vertical_lines:
            x1, y1, x2, y2 = line
            cv2.line(vis_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Draw horizontal lines (crossarms) in blue
        for line in self.geometry_detector.horizontal_lines:
            x1, y1, x2, y2 = line
            cv2.line(vis_image, (x1, y1), (x2, y2), (255, 0, 0), 2)
        
        # Draw diagonal lines in yellow
        for line in self.geometry_detector.diagonal_lines:
            x1, y1, x2, y2 = line
            cv2.line(vis_image, (x1, y1), (x2, y2), (0, 255, 255), 2)
        
        # Draw insulators in red
        for insulator in insulator_data['insulators']:
            x, y, w, h = insulator['bbox']
            cv2.rectangle(vis_image, (x, y), (x + w, y + h), (0, 0, 255), 2)
        
        # Add text overlay with results
        font = cv2.FONT_HERSHEY_SIMPLEX
        y_offset = 30
        
        cv2.putText(vis_image, f"Voltage: {results['voltage_class']}", 
                   (10, y_offset), font, 1, (255, 255, 255), 2)
        y_offset += 30
        
        cv2.putText(vis_image, f"Confidence: {results['confidence']:.2f}", 
                   (10, y_offset), font, 1, (255, 255, 255), 2)
        y_offset += 30
        
        cv2.putText(vis_image, f"Circuit: {results['circuit_type']}", 
                   (10, y_offset), font, 1, (255, 255, 255), 2)
        y_offset += 30
        
        cv2.putText(vis_image, f"Levels: {results['features']['level_count']}", 
                   (10, y_offset), font, 0.8, (255, 255, 255), 2)
        
        return vis_image
    
    def batch_detect(self, image_paths: list, visualize: bool = False) -> list:
        """
        Process multiple images
        
        Args:
            image_paths: List of image paths
            visualize: Whether to generate visualizations
            
        Returns:
            List of detection results
        """
        results = []
        for image_path in image_paths:
            result = self.detect(image_path, visualize)
            results.append(result)
        
        return results
    
    def print_results(self, results: Dict):
        """
        Pretty print detection results
        
        Args:
            results: Detection results dictionary
        """
        print("\n" + "="*60)
        print("CODEX POLE DETECTION RESULTS")
        print("="*60)
        print(f"Image: {results['image_path']}")
        print(f"\nVoltage Classification: {results['voltage_class']}")
        print(f"Confidence: {results['confidence']:.2%}")
        print(f"Circuit Type: {results['circuit_type']}")
        print(f"\nDescription: {results['rule_description']}")
        print(f"\nMatched Rules:")
        for rule in results['matched_rules']:
            print(f"  ✓ {rule}")
        
        print(f"\nDetected Features:")
        print(f"  - Levels: {results['features']['level_count']}")
        print(f"  - Crossarms: {results['features']['crossarm_count']}")
        print(f"  - Insulators: {results['features']['total_insulators']}")
        print(f"  - Symmetry: {results['features']['symmetry_score']:.2f}")
        print(f"  - Wire Density: {results['features']['wire_density']:.2f}")
        
        print(f"\nProcessing Time: {results['processing_time_seconds']:.3f} seconds")
        print("="*60 + "\n")
