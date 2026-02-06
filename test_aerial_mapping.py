"""
Tests for Aerial Mapping System
"""

import unittest
import math
import os
import json
from datetime import datetime, timedelta
import numpy as np
import cv2

from telemetry import Telemetry, ImagePosition
from geographic_positioner import GeographicPositioner
from pole_record import PoleRecord, PoleObservation
from pole_database import PoleDatabase
from aerial_mapping_system import AerialMappingSystem


class TestTelemetry(unittest.TestCase):
    """Test telemetry data structures"""
    
    def test_valid_telemetry(self):
        """Test creating valid telemetry"""
        tel = Telemetry(
            latitude=40.7128,
            longitude=-74.0060,
            altitude=50.0,
            heading=90.0,
            timestamp=datetime.utcnow()
        )
        self.assertEqual(tel.latitude, 40.7128)
        self.assertEqual(tel.longitude, -74.0060)
        self.assertEqual(tel.heading, 90.0)
    
    def test_heading_normalization(self):
        """Test heading normalization to 0-360"""
        tel = Telemetry(
            latitude=40.0,
            longitude=-74.0,
            altitude=50.0,
            heading=370.0,  # Should normalize to 10
            timestamp=datetime.utcnow()
        )
        self.assertEqual(tel.heading, 10.0)
    
    def test_invalid_latitude(self):
        """Test invalid latitude raises error"""
        with self.assertRaises(ValueError):
            Telemetry(
                latitude=100.0,  # Invalid
                longitude=-74.0,
                altitude=50.0,
                heading=90.0,
                timestamp=datetime.utcnow()
            )
    
    def test_telemetry_dict_conversion(self):
        """Test to/from dict conversion"""
        tel = Telemetry(
            latitude=40.7128,
            longitude=-74.0060,
            altitude=50.0,
            heading=90.0,
            timestamp=datetime.utcnow()
        )
        
        tel_dict = tel.to_dict()
        tel2 = Telemetry.from_dict(tel_dict)
        
        self.assertAlmostEqual(tel2.latitude, tel.latitude)
        self.assertAlmostEqual(tel2.longitude, tel.longitude)


class TestImagePosition(unittest.TestCase):
    """Test image position calculations"""
    
    def test_valid_position(self):
        """Test creating valid image position"""
        pos = ImagePosition(x=0.5, y=0.5, image_width=640, image_height=480)
        self.assertEqual(pos.x, 0.5)
        self.assertEqual(pos.y, 0.5)
    
    def test_pixel_position(self):
        """Test pixel coordinate calculation"""
        pos = ImagePosition(x=0.5, y=0.5, image_width=640, image_height=480)
        px, py = pos.get_pixel_position()
        self.assertEqual(px, 320)
        self.assertEqual(py, 240)
    
    def test_offset_from_center(self):
        """Test center offset calculation"""
        pos = ImagePosition(x=0.75, y=0.25, image_width=640, image_height=480)
        x_offset, y_offset = pos.get_offset_from_center()
        self.assertAlmostEqual(x_offset, 0.25)
        self.assertAlmostEqual(y_offset, -0.25)


class TestGeographicPositioner(unittest.TestCase):
    """Test geographic positioning calculations"""
    
    def setUp(self):
        self.positioner = GeographicPositioner()
        self.telemetry = Telemetry(
            latitude=40.7128,
            longitude=-74.0060,
            altitude=50.0,
            heading=90.0,
            timestamp=datetime.utcnow()
        )
    
    def test_distance_estimation(self):
        """Test distance estimation"""
        image_pos = ImagePosition(x=0.5, y=0.6, image_width=640, image_height=480)
        distance = self.positioner.estimate_distance(self.telemetry, image_pos)
        
        # Should return a reasonable distance
        self.assertGreater(distance, 10)
        self.assertLess(distance, 1000)
    
    def test_bearing_calculation_center(self):
        """Test bearing calculation for center of image"""
        image_pos = ImagePosition(x=0.5, y=0.5, image_width=640, image_height=480)
        bearing = self.positioner.calculate_bearing(self.telemetry, image_pos)
        
        # Should be same as vehicle heading
        self.assertAlmostEqual(bearing, self.telemetry.heading, delta=1.0)
    
    def test_bearing_calculation_offset(self):
        """Test bearing calculation for offset position"""
        # Object to the right of center
        image_pos = ImagePosition(x=0.75, y=0.5, image_width=640, image_height=480)
        bearing = self.positioner.calculate_bearing(self.telemetry, image_pos)
        
        # Should be to the right of vehicle heading
        self.assertGreater(bearing, self.telemetry.heading)
    
    def test_position_projection(self):
        """Test geographic position projection"""
        distance = 100  # meters
        bearing = 90  # East
        
        lat, lon = self.positioner.project_position(
            self.telemetry, distance, bearing
        )
        
        # Should be east of starting position
        self.assertGreater(lon, self.telemetry.longitude)
        # Latitude should be approximately the same
        self.assertAlmostEqual(lat, self.telemetry.latitude, delta=0.001)
    
    def test_distance_between_positions(self):
        """Test distance calculation between two positions"""
        lat1, lon1 = 40.7128, -74.0060
        lat2, lon2 = 40.7138, -74.0050  # ~100m northeast
        
        distance = GeographicPositioner.calculate_distance_between_positions(
            lat1, lon1, lat2, lon2
        )
        
        # Should be roughly 100-150 meters
        self.assertGreater(distance, 50)
        self.assertLess(distance, 200)
    
    def test_complete_position_estimation(self):
        """Test complete position estimation pipeline"""
        image_pos = ImagePosition(x=0.5, y=0.6, image_width=640, image_height=480)
        
        result = self.positioner.estimate_pole_position(
            self.telemetry, image_pos
        )
        
        self.assertIn('latitude', result)
        self.assertIn('longitude', result)
        self.assertIn('estimated_distance', result)
        self.assertIn('bearing', result)


class TestPoleRecord(unittest.TestCase):
    """Test pole record data model"""
    
    def test_create_pole_record(self):
        """Test creating pole record"""
        pole = PoleRecord(
            latitude=40.7128,
            longitude=-74.0060,
            pole_type='33kV',
            circuit_type='multi_circuit',
            confidence=0.85
        )
        
        self.assertEqual(pole.pole_type, '33kV')
        self.assertEqual(pole.observation_count, 0)
    
    def test_add_observation(self):
        """Test adding observation to pole"""
        pole = PoleRecord(latitude=40.7128, longitude=-74.0060)
        
        observation = PoleObservation(
            timestamp=datetime.utcnow(),
            latitude=40.7128,
            longitude=-74.0060,
            distance=100.0,
            bearing=90.0,
            confidence=0.8,
            vehicle_altitude=50.0,
            features={}
        )
        
        detection_result = {
            'voltage_class': '33kV',
            'circuit_type': 'multi_circuit',
            'confidence': 0.8
        }
        
        pole.add_observation(observation, detection_result)
        
        self.assertEqual(pole.observation_count, 1)
        self.assertEqual(pole.pole_type, '33kV')
    
    def test_confidence_accumulation(self):
        """Test confidence increases with observations"""
        pole = PoleRecord(latitude=40.7128, longitude=-74.0060, confidence=0.5)
        
        observation = PoleObservation(
            timestamp=datetime.utcnow(),
            latitude=40.7128,
            longitude=-74.0060,
            distance=100.0,
            bearing=90.0,
            confidence=0.8,
            vehicle_altitude=50.0,
            features={}
        )
        
        detection_result = {'voltage_class': '33kV', 'confidence': 0.5}
        
        initial_confidence = pole.confidence
        pole.add_observation(observation, detection_result)
        
        # Confidence should increase
        self.assertGreater(pole.confidence, initial_confidence)
    
    def test_pole_dict_conversion(self):
        """Test pole to/from dict conversion"""
        pole = PoleRecord(
            latitude=40.7128,
            longitude=-74.0060,
            pole_type='33kV'
        )
        
        pole_dict = pole.to_dict()
        pole2 = PoleRecord.from_dict(pole_dict)
        
        self.assertEqual(pole2.pole_type, pole.pole_type)
        self.assertAlmostEqual(pole2.latitude, pole.latitude)


class TestPoleDatabase(unittest.TestCase):
    """Test pole database operations"""
    
    def setUp(self):
        """Set up test database"""
        self.test_db_path = "test_pole_database.json"
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        
        self.db = PoleDatabase(
            database_path=self.test_db_path,
            proximity_threshold=20.0
        )
    
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_add_new_pole(self):
        """Test adding new pole to database"""
        observation = PoleObservation(
            timestamp=datetime.utcnow(),
            latitude=40.7128,
            longitude=-74.0060,
            distance=100.0,
            bearing=90.0,
            confidence=0.8,
            vehicle_altitude=50.0,
            features={}
        )
        
        detection_result = {'voltage_class': '33kV', 'confidence': 0.8}
        
        pole = self.db.add_or_update_pole(
            40.7128, -74.0060, observation, detection_result
        )
        
        self.assertEqual(len(self.db.poles), 1)
        self.assertEqual(pole.observation_count, 1)
    
    def test_update_existing_pole(self):
        """Test updating existing pole (deduplication)"""
        # Add first pole
        obs1 = PoleObservation(
            timestamp=datetime.utcnow(),
            latitude=40.7128,
            longitude=-74.0060,
            distance=100.0,
            bearing=90.0,
            confidence=0.8,
            vehicle_altitude=50.0,
            features={}
        )
        
        detection_result = {'voltage_class': '33kV', 'confidence': 0.8}
        
        pole1 = self.db.add_or_update_pole(
            40.7128, -74.0060, obs1, detection_result
        )
        
        # Add second observation of same pole (within proximity threshold)
        obs2 = PoleObservation(
            timestamp=datetime.utcnow() + timedelta(seconds=5),
            latitude=40.71282,  # Very close
            longitude=-74.00602,
            distance=100.0,
            bearing=90.0,
            confidence=0.85,
            vehicle_altitude=50.0,
            features={}
        )
        
        pole2 = self.db.add_or_update_pole(
            40.71282, -74.00602, obs2, detection_result
        )
        
        # Should still be only one pole
        self.assertEqual(len(self.db.poles), 1)
        # Should be same pole
        self.assertEqual(pole1.pole_id, pole2.pole_id)
        # Should have 2 observations
        self.assertEqual(pole2.observation_count, 2)
    
    def test_find_nearby_pole(self):
        """Test finding nearby pole"""
        # Add pole
        obs = PoleObservation(
            timestamp=datetime.utcnow(),
            latitude=40.7128,
            longitude=-74.0060,
            distance=100.0,
            bearing=90.0,
            confidence=0.8,
            vehicle_altitude=50.0,
            features={}
        )
        
        self.db.add_or_update_pole(
            40.7128, -74.0060, obs, {'voltage_class': '33kV', 'confidence': 0.8}
        )
        
        # Find nearby (within threshold)
        nearby = self.db.find_nearby_pole(40.71282, -74.00602)
        self.assertIsNotNone(nearby)
        
        # Find far away (outside threshold)
        far = self.db.find_nearby_pole(40.8, -74.1)
        self.assertIsNone(far)
    
    def test_save_and_load(self):
        """Test database persistence"""
        # Add pole
        obs = PoleObservation(
            timestamp=datetime.utcnow(),
            latitude=40.7128,
            longitude=-74.0060,
            distance=100.0,
            bearing=90.0,
            confidence=0.8,
            vehicle_altitude=50.0,
            features={}
        )
        
        self.db.add_or_update_pole(
            40.7128, -74.0060, obs, {'voltage_class': '33kV', 'confidence': 0.8}
        )
        
        # Save
        self.db.save()
        
        # Load in new database instance
        db2 = PoleDatabase(database_path=self.test_db_path)
        
        self.assertEqual(len(db2.poles), 1)
        pole = list(db2.poles.values())[0]
        self.assertEqual(pole.pole_type, '33kV')
    
    def test_get_statistics(self):
        """Test database statistics"""
        stats = self.db.get_statistics()
        self.assertEqual(stats['total_poles'], 0)
        
        # Add a pole
        obs = PoleObservation(
            timestamp=datetime.utcnow(),
            latitude=40.7128,
            longitude=-74.0060,
            distance=100.0,
            bearing=90.0,
            confidence=0.8,
            vehicle_altitude=50.0,
            features={}
        )
        
        self.db.add_or_update_pole(
            40.7128, -74.0060, obs, {'voltage_class': '33kV', 'confidence': 0.8}
        )
        
        stats = self.db.get_statistics()
        self.assertEqual(stats['total_poles'], 1)
        self.assertEqual(stats['total_observations'], 1)


class TestAerialMappingIntegration(unittest.TestCase):
    """Integration tests for aerial mapping system"""
    
    def setUp(self):
        """Set up test system"""
        self.test_db_path = "test_aerial_db.json"
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        
        self.system = AerialMappingSystem(
            database_path=self.test_db_path,
            proximity_threshold=20.0
        )
    
    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_process_frame_with_synthetic_image(self):
        """Test processing frame with synthetic image"""
        # Create synthetic test image
        test_img = self._create_test_image()
        
        telemetry = Telemetry(
            latitude=40.7128,
            longitude=-74.0060,
            altitude=50.0,
            heading=90.0,
            timestamp=datetime.utcnow()
        )
        
        result = self.system.process_frame(test_img, telemetry)
        
        self.assertIn('frame_number', result)
        self.assertEqual(result['frame_number'], 1)
    
    def _create_test_image(self):
        """Create synthetic test image"""
        img = np.zeros((400, 400, 3), dtype=np.uint8)
        
        # Draw vertical line (pole)
        cv2.line(img, (200, 50), (200, 350), (255, 255, 255), 5)
        
        # Draw horizontal lines (crossarms)
        cv2.line(img, (100, 100), (300, 100), (255, 255, 255), 3)
        cv2.line(img, (100, 200), (300, 200), (255, 255, 255), 3)
        cv2.line(img, (100, 300), (300, 300), (255, 255, 255), 3)
        
        return img


if __name__ == '__main__':
    unittest.main(verbosity=2)
