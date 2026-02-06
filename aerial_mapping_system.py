"""
Aerial Mapping System
Autonomous pole detection and mapping from aerial platform
"""

import cv2
import numpy as np
from typing import Dict, Optional, Union
from datetime import datetime

from pole_detector import PoleDetector
from geographic_positioner import GeographicPositioner
from pole_database import PoleDatabase
from telemetry import Telemetry, ImagePosition
from pole_record import PoleObservation


class AerialMappingSystem:
    """
    Autonomous aerial pole mapping and persistence system
    
    ⚠️ CRITICAL SAFETY NOTICE ⚠️
    
    This system is a PASSIVE OBSERVER ONLY:
    - Does NOT control aircraft
    - Does NOT issue navigation commands
    - Does NOT influence pilot decisions
    - Provides INFORMATION ONLY
    
    All detected electrical infrastructure must be treated as
    ENERGIZED and HAZARDOUS at all times.
    
    The human pilot has SOLE AUTHORITY over flight operations.
    
    Core capabilities:
    - Process aerial imagery with telemetry
    - Detect and classify poles
    - Estimate geographic positions
    - Maintain persistent spatial model
    - Avoid duplicate pole creation
    """
    
    # Safety warnings
    SAFETY_WARNING = (
        "⚠️  All detected infrastructure must be treated as energized and hazardous. "
        "Position estimates are approximate - verify through established procedures. "
        "This system does not replace pilot authority or safety protocols."
    )
    
    def __init__(self,
                 database_path: str = "pole_database.json",
                 proximity_threshold: float = 20.0,
                 camera_fov_h: float = 60.0,
                 camera_fov_v: float = 45.0):
        """
        Initialize aerial mapping system
        
        Args:
            database_path: Path to pole database file
            proximity_threshold: Distance threshold for pole matching (meters)
            camera_fov_h: Horizontal camera FOV (degrees)
            camera_fov_v: Vertical camera FOV (degrees)
        """
        # Core components
        self.pole_detector = PoleDetector()
        self.geo_positioner = GeographicPositioner(
            camera_fov_h=camera_fov_h,
            camera_fov_v=camera_fov_v
        )
        self.pole_database = PoleDatabase(
            database_path=database_path,
            proximity_threshold=proximity_threshold
        )
        
        # System state
        self.frames_processed = 0
        self.poles_detected_this_session = 0
        self.poles_updated_this_session = 0
    
    def process_frame(self,
                     image: Union[str, np.ndarray],
                     telemetry: Telemetry,
                     visualize: bool = False) -> Dict:
        """
        Process single aerial frame with telemetry
        
        Args:
            image: Image path or numpy array
            telemetry: Vehicle telemetry data
            visualize: Whether to generate visualization
            
        Returns:
            Processing results dictionary
        """
        self.frames_processed += 1
        
        # Load image if path provided
        if isinstance(image, str):
            img_array = cv2.imread(image)
            if img_array is None:
                return {
                    'error': 'Failed to load image',
                    'frame_number': self.frames_processed
                }
        else:
            img_array = image
        
        # Get image dimensions
        height, width = img_array.shape[:2]
        
        # Run detection
        detection_result = self._detect_from_array(img_array, visualize)
        
        if 'error' in detection_result:
            return detection_result
        
        # Check if pole detected
        if detection_result.get('confidence', 0) < 0.3:
            # Low confidence - don't persist
            return {
                'frame_number': self.frames_processed,
                'detection': 'no_pole',
                'confidence': detection_result.get('confidence', 0),
                'telemetry': telemetry.to_dict()
            }
        
        # Estimate pole position in image (use center for now)
        # In production, would use actual detected bounding box
        image_pos = ImagePosition(
            x=0.5,  # Center
            y=0.6,  # Slightly below center (typical for poles)
            image_width=width,
            image_height=height
        )
        
        # Get pole height in pixels if available (from geometry detection)
        pole_height_pixels = self._estimate_pole_height_pixels(detection_result)
        
        # Estimate geographic position
        position_result = self.geo_positioner.estimate_pole_position(
            telemetry,
            image_pos,
            pole_height_pixels
        )
        
        # Create observation record
        observation = PoleObservation(
            timestamp=telemetry.timestamp,
            latitude=position_result['latitude'],
            longitude=position_result['longitude'],
            distance=position_result['estimated_distance'],
            bearing=position_result['bearing'],
            confidence=detection_result['confidence'],
            vehicle_altitude=telemetry.altitude,
            features=detection_result.get('features', {})
        )
        
        # Add or update pole in database
        pole_record = self.pole_database.add_or_update_pole(
            position_result['latitude'],
            position_result['longitude'],
            observation,
            detection_result
        )
        
        # Track session statistics
        if pole_record.observation_count == 1:
            self.poles_detected_this_session += 1
        else:
            self.poles_updated_this_session += 1
        
        # Save database (can be optimized to save periodically)
        self.pole_database.save()
        
        # Compile results
        result = {
            'frame_number': self.frames_processed,
            'detection': 'pole_detected',
            'pole_id': pole_record.pole_id,
            'pole_id_short': pole_record.pole_id[:8],
            'voltage_class': pole_record.pole_type,
            'circuit_type': pole_record.circuit_type,
            'confidence': pole_record.confidence,
            'position': {
                'latitude': pole_record.latitude,
                'longitude': pole_record.longitude
            },
            'estimated_distance': position_result['estimated_distance'],
            'bearing': position_result['bearing'],
            'observation_count': pole_record.observation_count,
            'is_new_pole': pole_record.observation_count == 1,
            'telemetry': telemetry.to_dict(),
            'session_stats': self.get_session_stats(),
            'safety_warning': self.SAFETY_WARNING,
            'system_role': 'passive_observer'
        }
        
        if visualize and 'visualization' in detection_result:
            result['visualization'] = detection_result['visualization']
        
        return result
    
    def _detect_from_array(self, image: np.ndarray, visualize: bool) -> Dict:
        """
        Run pole detection on image array
        
        Args:
            image: Image as numpy array
            visualize: Whether to generate visualization
            
        Returns:
            Detection results
        """
        # Step 1: Geometry detection
        geometry_data = self.pole_detector.geometry_detector.analyze_geometry(image)
        
        # Step 2: Insulator detection
        insulator_data = self.pole_detector.insulator_detector.get_insulator_features(
            image,
            geometry_data['edges']
        )
        
        # Step 3: Feature extraction
        features = self.pole_detector.feature_extractor.extract_features(
            geometry_data,
            insulator_data
        )
        
        # Step 4: Classification
        voltage_class, confidence, matched_rules = \
            self.pole_detector.rule_engine.classify_voltage(features)
        
        # Step 5: Multi-circuit detection
        is_multi_circuit = self.pole_detector.rule_engine.detect_multi_circuit(features)
        
        # Compile results
        result = {
            'voltage_class': voltage_class,
            'confidence': confidence,
            'circuit_type': 'multi_circuit' if is_multi_circuit else 'single_circuit',
            'matched_rules': matched_rules,
            'features': features
        }
        
        # Generate visualization if requested
        if visualize:
            vis_image = self.pole_detector._visualize_detection(
                image,
                geometry_data,
                insulator_data,
                result
            )
            result['visualization'] = vis_image
        
        return result
    
    def _estimate_pole_height_pixels(self, detection_result: Dict) -> Optional[int]:
        """
        Estimate pole height in pixels from detection features
        
        Args:
            detection_result: Detection results
            
        Returns:
            Estimated pole height in pixels or None
        """
        # Use vertical extent of detected lines as proxy for pole height
        # This is a rough estimate - could be improved
        features = detection_result.get('features', {})
        
        # If we have level information, estimate from that
        level_count = features.get('level_count', 0)
        if level_count > 0:
            # Estimate roughly 50 pixels per level
            return level_count * 50
        
        return None
    
    def get_session_stats(self) -> Dict:
        """Get statistics for current session"""
        return {
            'frames_processed': self.frames_processed,
            'poles_detected': self.poles_detected_this_session,
            'poles_updated': self.poles_updated_this_session,
            'total_poles_in_database': len(self.pole_database.poles)
        }
    
    def get_all_poles(self):
        """Get all poles from database"""
        return self.pole_database.get_all_poles()
    
    def get_pole_by_id(self, pole_id: str):
        """Get specific pole by ID"""
        return self.pole_database.get_pole_by_id(pole_id)
    
    def get_poles_near_position(self, latitude: float, longitude: float,
                               radius_meters: float = 1000):
        """Get poles near a position"""
        return self.pole_database.get_poles_in_area(
            latitude, longitude, radius_meters
        )
    
    def export_to_geojson(self, output_path: str):
        """Export poles to GeoJSON"""
        self.pole_database.export_to_geojson(output_path)
    
    def get_database_stats(self):
        """Get database statistics"""
        return self.pole_database.get_statistics()
    
    def print_summary(self):
        """Print system summary"""
        print("\n" + "="*70)
        print("AERIAL MAPPING SYSTEM - SESSION SUMMARY")
        print("="*70)
        print("\n⚠️  SAFETY NOTICE:")
        print("  " + self.SAFETY_WARNING)
        print("\n  System Role: PASSIVE OBSERVER")
        print("  Pilot Authority: SOLE CONTROL")
        
        session_stats = self.get_session_stats()
        db_stats = self.get_database_stats()
        
        print(f"\nSession Statistics:")
        print(f"  Frames Processed: {session_stats['frames_processed']}")
        print(f"  New Poles Detected: {session_stats['poles_detected']}")
        print(f"  Existing Poles Updated: {session_stats['poles_updated']}")
        
        print(f"\nDatabase Statistics:")
        print(f"  Total Poles: {db_stats['total_poles']}")
        print(f"  Total Observations: {db_stats['total_observations']}")
        
        if db_stats['total_poles'] > 0:
            print(f"  Avg Observations/Pole: {db_stats['average_observations_per_pole']:.1f}")
            print(f"\n  Pole Types:")
            for pole_type, count in db_stats['pole_types'].items():
                print(f"    {pole_type}: {count}")
        
        print("\n" + "="*70 + "\n")
