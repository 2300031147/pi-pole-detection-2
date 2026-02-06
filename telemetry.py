"""
Telemetry Data Structures
Handles navigation data from aerial platform
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Telemetry:
    """
    Navigation telemetry from aerial platform
    
    Attributes:
        latitude: Vehicle latitude in decimal degrees
        longitude: Vehicle longitude in decimal degrees
        altitude: Altitude above ground level in meters
        heading: Heading/yaw in degrees (0=North, 90=East, 180=South, 270=West)
        timestamp: UTC timestamp of measurement
    """
    latitude: float
    longitude: float
    altitude: float
    heading: float
    timestamp: datetime
    
    def __post_init__(self):
        """Validate telemetry data"""
        # Validate latitude
        if not -90 <= self.latitude <= 90:
            raise ValueError(f"Invalid latitude: {self.latitude}")
        
        # Validate longitude
        if not -180 <= self.longitude <= 180:
            raise ValueError(f"Invalid longitude: {self.longitude}")
        
        # Validate altitude (must be positive)
        if self.altitude < 0:
            raise ValueError(f"Invalid altitude: {self.altitude}")
        
        # Normalize heading to 0-360
        self.heading = self.heading % 360
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Telemetry':
        """Create Telemetry from dictionary"""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.utcnow()
        
        return cls(
            latitude=float(data['latitude']),
            longitude=float(data['longitude']),
            altitude=float(data['altitude']),
            heading=float(data['heading']),
            timestamp=timestamp
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude': self.altitude,
            'heading': self.heading,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ImagePosition:
    """
    Position of detected object within image frame
    
    Attributes:
        x: Horizontal position (0 = left, 1 = right)
        y: Vertical position (0 = top, 1 = bottom)
        image_width: Image width in pixels
        image_height: Image height in pixels
    """
    x: float
    y: float
    image_width: int
    image_height: int
    
    def __post_init__(self):
        """Validate position"""
        if not 0 <= self.x <= 1:
            raise ValueError(f"Invalid x position: {self.x}")
        if not 0 <= self.y <= 1:
            raise ValueError(f"Invalid y position: {self.y}")
    
    def get_pixel_position(self) -> tuple:
        """Get pixel coordinates"""
        return (int(self.x * self.image_width), int(self.y * self.image_height))
    
    def get_offset_from_center(self) -> tuple:
        """Get offset from image center in normalized coordinates"""
        return (self.x - 0.5, self.y - 0.5)
