"""
Geographic Positioning Module
Calculates real-world pole positions from aerial telemetry
"""

import math
from typing import Tuple, Optional
from telemetry import Telemetry, ImagePosition


class GeographicPositioner:
    """
    Estimates geographic position of detected poles using telemetry
    
    This module uses geometric scaling and bearing calculations to project
    pole positions from aerial platform telemetry.
    """
    
    # Earth radius in meters (mean radius)
    EARTH_RADIUS = 6371000
    
    # Camera parameters (can be configured for specific hardware)
    # These are estimates - should be calibrated for actual camera
    CAMERA_FOV_HORIZONTAL = 60  # degrees
    CAMERA_FOV_VERTICAL = 45    # degrees
    
    # Pole height estimation (for distance calculation)
    ASSUMED_POLE_HEIGHT = 12  # meters (typical distribution pole)
    
    def __init__(self, 
                 camera_fov_h: float = CAMERA_FOV_HORIZONTAL,
                 camera_fov_v: float = CAMERA_FOV_VERTICAL,
                 assumed_pole_height: float = ASSUMED_POLE_HEIGHT):
        """
        Initialize positioner
        
        Args:
            camera_fov_h: Horizontal field of view in degrees
            camera_fov_v: Vertical field of view in degrees
            assumed_pole_height: Assumed pole height for distance estimation
        """
        self.camera_fov_h = camera_fov_h
        self.camera_fov_v = camera_fov_v
        self.assumed_pole_height = assumed_pole_height
    
    def estimate_distance(self, 
                         telemetry: Telemetry,
                         image_pos: ImagePosition,
                         pole_height_pixels: Optional[int] = None) -> float:
        """
        Estimate distance to pole using geometric scaling
        
        Method 1 (if pole height in pixels known):
            distance = (actual_height * focal_length) / pixel_height
        
        Method 2 (altitude-based estimate):
            Use altitude and viewing angle
        
        Args:
            telemetry: Vehicle telemetry
            image_pos: Position of pole in image
            pole_height_pixels: Height of pole in pixels (if known)
            
        Returns:
            Estimated distance in meters
        """
        if pole_height_pixels and pole_height_pixels > 0:
            # Method 1: Use known pole height
            # Estimate focal length from FOV and image height
            focal_length_pixels = (image_pos.image_height / 2) / \
                                 math.tan(math.radians(self.camera_fov_v / 2))
            
            distance = (self.assumed_pole_height * focal_length_pixels) / pole_height_pixels
        else:
            # Method 2: Altitude-based approximation
            # Assume camera is pointing slightly downward (typical for aerial mapping)
            # Use pole's position in frame to estimate viewing angle
            
            # Vertical offset from center (-0.5 to 0.5)
            _, y_offset = image_pos.get_offset_from_center()
            
            # Convert to viewing angle
            viewing_angle = y_offset * self.camera_fov_v
            
            # Angle from horizontal (positive = looking down)
            angle_from_horizontal = viewing_angle
            
            # If pole is in lower half of image, we're looking down at it
            if y_offset > 0:
                # Distance based on altitude and viewing angle
                if abs(angle_from_horizontal) < 1:  # Nearly horizontal
                    distance = telemetry.altitude * 10  # Very rough estimate
                else:
                    distance = telemetry.altitude / math.tan(math.radians(abs(angle_from_horizontal)))
            else:
                # Pole in upper half - likely far away
                distance = telemetry.altitude * 5
        
        # Clamp to reasonable range (10m to 1000m)
        distance = max(10, min(1000, distance))
        
        return distance
    
    def calculate_bearing(self,
                         telemetry: Telemetry,
                         image_pos: ImagePosition) -> float:
        """
        Calculate bearing to pole from vehicle heading and image position
        
        Args:
            telemetry: Vehicle telemetry
            image_pos: Position of pole in image
            
        Returns:
            Bearing in degrees (0=North, 90=East, etc.)
        """
        # Horizontal offset from center (-0.5 to 0.5)
        x_offset, _ = image_pos.get_offset_from_center()
        
        # Convert to angular offset
        angular_offset = x_offset * self.camera_fov_h
        
        # Add to vehicle heading
        bearing = (telemetry.heading + angular_offset) % 360
        
        return bearing
    
    def project_position(self,
                        telemetry: Telemetry,
                        distance: float,
                        bearing: float) -> Tuple[float, float]:
        """
        Project pole position from vehicle position, distance, and bearing
        
        Uses Haversine formula to compute destination point given:
        - Start position (vehicle lat/lon)
        - Distance
        - Bearing
        
        Args:
            telemetry: Vehicle telemetry
            distance: Distance to pole in meters
            bearing: Bearing to pole in degrees
            
        Returns:
            Tuple of (latitude, longitude) in decimal degrees
        """
        # Convert to radians
        lat1 = math.radians(telemetry.latitude)
        lon1 = math.radians(telemetry.longitude)
        bearing_rad = math.radians(bearing)
        
        # Angular distance
        angular_distance = distance / self.EARTH_RADIUS
        
        # Calculate destination point
        lat2 = math.asin(
            math.sin(lat1) * math.cos(angular_distance) +
            math.cos(lat1) * math.sin(angular_distance) * math.cos(bearing_rad)
        )
        
        lon2 = lon1 + math.atan2(
            math.sin(bearing_rad) * math.sin(angular_distance) * math.cos(lat1),
            math.cos(angular_distance) - math.sin(lat1) * math.sin(lat2)
        )
        
        # Convert back to degrees
        latitude = math.degrees(lat2)
        longitude = math.degrees(lon2)
        
        return (latitude, longitude)
    
    def estimate_pole_position(self,
                              telemetry: Telemetry,
                              image_pos: ImagePosition,
                              pole_height_pixels: Optional[int] = None) -> dict:
        """
        Complete pipeline: estimate pole's geographic position
        
        Args:
            telemetry: Vehicle telemetry
            image_pos: Position of pole in image
            pole_height_pixels: Height of pole in pixels (optional)
            
        Returns:
            Dictionary with position estimation results
        """
        # Estimate distance
        distance = self.estimate_distance(telemetry, image_pos, pole_height_pixels)
        
        # Calculate bearing
        bearing = self.calculate_bearing(telemetry, image_pos)
        
        # Project position
        latitude, longitude = self.project_position(telemetry, distance, bearing)
        
        return {
            'latitude': latitude,
            'longitude': longitude,
            'estimated_distance': distance,
            'bearing': bearing,
            'vehicle_altitude': telemetry.altitude,
            'estimation_method': 'pixel_height' if pole_height_pixels else 'altitude_based'
        }
    
    @staticmethod
    def calculate_distance_between_positions(lat1: float, lon1: float,
                                            lat2: float, lon2: float) -> float:
        """
        Calculate distance between two geographic positions using Haversine
        
        Args:
            lat1, lon1: First position
            lat2, lon2: Second position
            
        Returns:
            Distance in meters
        """
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        distance = GeographicPositioner.EARTH_RADIUS * c
        
        return distance
