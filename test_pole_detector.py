"""
Unit tests for CODEX Pole Detection System
Tests core functionality without requiring actual images
"""

import unittest
import numpy as np
import cv2
from geometry_detector import GeometryDetector
from insulator_detector import InsulatorDetector
from feature_extractor import FeatureExtractor
from rule_engine import RuleEngine


class TestGeometryDetector(unittest.TestCase):
    """Test geometry detection functionality"""
    
    def setUp(self):
        self.detector = GeometryDetector()
    
    def test_line_classification_vertical(self):
        """Test vertical line classification"""
        # Vertical line (90 degrees)
        orientation = self.detector.classify_line_orientation(100, 50, 100, 150)
        self.assertEqual(orientation, 'vertical')
    
    def test_line_classification_horizontal(self):
        """Test horizontal line classification"""
        # Horizontal line (0 degrees)
        orientation = self.detector.classify_line_orientation(50, 100, 150, 100)
        self.assertEqual(orientation, 'horizontal')
    
    def test_line_classification_diagonal(self):
        """Test diagonal line classification"""
        # 45 degree line
        orientation = self.detector.classify_line_orientation(50, 50, 150, 150)
        self.assertEqual(orientation, 'diagonal')
    
    def test_classify_lines(self):
        """Test line classification into categories"""
        lines = [
            (100, 50, 100, 150),   # vertical
            (50, 100, 150, 100),   # horizontal
            (50, 50, 150, 150),    # diagonal
            (200, 0, 200, 100),    # vertical
        ]
        self.detector.classify_lines(lines)
        
        self.assertEqual(len(self.detector.vertical_lines), 2)
        self.assertEqual(len(self.detector.horizontal_lines), 1)
        self.assertEqual(len(self.detector.diagonal_lines), 1)
    
    def test_level_clustering(self):
        """Test horizontal line clustering by level"""
        # Horizontal lines at two different levels
        self.detector.horizontal_lines = [
            (50, 100, 150, 100),   # level 1
            (50, 105, 150, 105),   # level 1 (within tolerance)
            (50, 200, 150, 200),   # level 2
            (50, 205, 150, 205),   # level 2 (within tolerance)
        ]
        
        clusters = self.detector.cluster_horizontal_lines_by_level()
        self.assertEqual(len(clusters), 2)
        self.assertEqual(len(clusters[0]), 2)
        self.assertEqual(len(clusters[1]), 2)
    
    def test_spacing_calculation(self):
        """Test spacing calculation between levels"""
        clusters = [
            [(50, 100, 150, 100)],  # level at y=100
            [(50, 200, 150, 200)],  # level at y=200
            [(50, 250, 150, 250)],  # level at y=250
        ]
        
        spacings = self.detector.get_level_spacing(clusters)
        self.assertEqual(len(spacings), 2)
        self.assertAlmostEqual(spacings[0], 100.0, delta=1.0)
        self.assertAlmostEqual(spacings[1], 50.0, delta=1.0)


class TestFeatureExtractor(unittest.TestCase):
    """Test feature extraction functionality"""
    
    def setUp(self):
        self.extractor = FeatureExtractor()
    
    def test_wire_density_calculation(self):
        """Test wire density calculation"""
        geometry_data = {
            'level_count': 3,
            'crossarm_count': 6
        }
        density = self.extractor._calculate_wire_density(geometry_data)
        self.assertEqual(density, 2.0)
    
    def test_wire_density_zero_levels(self):
        """Test wire density with zero levels"""
        geometry_data = {
            'level_count': 0,
            'crossarm_count': 6
        }
        density = self.extractor._calculate_wire_density(geometry_data)
        self.assertEqual(density, 0.0)
    
    def test_spacing_average(self):
        """Test average spacing calculation"""
        spacings = [100.0, 80.0, 90.0]
        avg = self.extractor._calculate_avg_spacing(spacings)
        self.assertAlmostEqual(avg, 90.0, delta=0.1)
    
    def test_spacing_variance(self):
        """Test spacing variance calculation"""
        spacings = [100.0, 100.0, 100.0]
        variance = self.extractor._calculate_spacing_variance(spacings)
        self.assertEqual(variance, 0.0)


class TestRuleEngine(unittest.TestCase):
    """Test rule engine functionality"""
    
    def setUp(self):
        self.engine = RuleEngine()
    
    def test_33kv_classification(self):
        """Test 33kV classification"""
        features = {
            'level_count': 3,
            'crossarm_count': 6,
            'total_insulators': 8,
            'top_spacing_larger': True,
            'wire_density': 2.0,
            'symmetry_score': 0.8
        }
        
        voltage, confidence, rules = self.engine.classify_voltage(features)
        self.assertEqual(voltage, '33kV')
        self.assertGreater(confidence, 0.5)
        self.assertGreater(len(rules), 0)
    
    def test_11kv_classification(self):
        """Test 11kV classification"""
        features = {
            'level_count': 2,
            'crossarm_count': 4,
            'total_insulators': 4,
            'top_spacing_larger': False,
            'wire_density': 2.0,
            'symmetry_score': 0.8
        }
        
        voltage, confidence, rules = self.engine.classify_voltage(features)
        self.assertEqual(voltage, '11kV')
        self.assertGreater(confidence, 0.5)
    
    def test_lt_classification(self):
        """Test LT classification"""
        features = {
            'level_count': 1,
            'crossarm_count': 5,
            'total_insulators': 2,
            'top_spacing_larger': False,
            'wire_density': 5.0,
            'symmetry_score': 0.7
        }
        
        voltage, confidence, rules = self.engine.classify_voltage(features)
        self.assertEqual(voltage, 'LT')
        self.assertGreater(confidence, 0.5)
    
    def test_multi_circuit_detection(self):
        """Test multi-circuit detection"""
        features_single = {'level_count': 1}
        features_multi = {'level_count': 3}
        
        self.assertFalse(self.engine.detect_multi_circuit(features_single))
        self.assertTrue(self.engine.detect_multi_circuit(features_multi))


class TestInsulatorDetector(unittest.TestCase):
    """Test insulator detection functionality"""
    
    def setUp(self):
        self.detector = InsulatorDetector()
    
    def test_insulator_clustering(self):
        """Test insulator clustering by level"""
        insulators = [
            {'center': (100, 100)},  # level 1
            {'center': (150, 105)},  # level 1
            {'center': (100, 200)},  # level 2
            {'center': (150, 205)},  # level 2
        ]
        
        clusters = self.detector.cluster_insulators_by_level(insulators)
        self.assertEqual(len(clusters), 2)
        self.assertEqual(len(clusters[0]), 2)
        self.assertEqual(len(clusters[1]), 2)
    
    def test_count_by_level(self):
        """Test counting insulators by level"""
        insulators = [
            {'center': (100, 100)},
            {'center': (150, 105)},
            {'center': (100, 200)},
        ]
        
        counts = self.detector.count_insulators_by_level(insulators)
        self.assertEqual(len(counts), 2)
        self.assertEqual(counts[0], 2)
        self.assertEqual(counts[1], 1)


def create_test_image():
    """Create a simple test image with lines for testing"""
    img = np.zeros((400, 400, 3), dtype=np.uint8)
    
    # Draw vertical line (pole)
    cv2.line(img, (200, 50), (200, 350), (255, 255, 255), 5)
    
    # Draw horizontal lines (crossarms at different levels)
    cv2.line(img, (100, 100), (300, 100), (255, 255, 255), 3)
    cv2.line(img, (100, 200), (300, 200), (255, 255, 255), 3)
    cv2.line(img, (100, 300), (300, 300), (255, 255, 255), 3)
    
    # Draw some circles (insulators)
    cv2.circle(img, (120, 100), 10, (255, 255, 255), -1)
    cv2.circle(img, (280, 100), 10, (255, 255, 255), -1)
    cv2.circle(img, (120, 200), 10, (255, 255, 255), -1)
    cv2.circle(img, (280, 200), 10, (255, 255, 255), -1)
    
    return img


class TestIntegration(unittest.TestCase):
    """Integration tests with synthetic images"""
    
    def test_full_pipeline_synthetic(self):
        """Test complete detection pipeline with synthetic image"""
        from pole_detector import PoleDetector
        import tempfile
        import os
        
        # Create synthetic test image
        test_img = create_test_image()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            temp_path = f.name
            cv2.imwrite(temp_path, test_img)
        
        try:
            # Run detection
            detector = PoleDetector()
            results = detector.detect(temp_path, visualize=False)
            
            # Verify results structure
            self.assertIn('voltage_class', results)
            self.assertIn('confidence', results)
            self.assertIn('features', results)
            self.assertIn('matched_rules', results)
            self.assertIn('is_multi_circuit', results)
            
            # Verify voltage class is valid
            self.assertIn(results['voltage_class'], ['33kV', '11kV', 'LT'])
            
            # Verify confidence is between 0 and 1
            self.assertGreaterEqual(results['confidence'], 0.0)
            self.assertLessEqual(results['confidence'], 1.0)
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
