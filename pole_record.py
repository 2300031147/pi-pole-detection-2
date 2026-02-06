"""
Pole Record Data Model
Represents a detected pole with all metadata
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid
import numpy as np


def make_serializable(obj: Any) -> Any:
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, (np.integer, int)):
        return int(obj)
    elif isinstance(obj, (np.floating, float)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [make_serializable(item) for item in obj]
    return obj


@dataclass
class PoleObservation:
    """Single observation of a pole"""
    timestamp: datetime
    latitude: float
    longitude: float
    distance: float
    bearing: float
    confidence: float
    vehicle_altitude: float
    features: Dict
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'latitude': self.latitude,
            'longitude': self.longitude,
            'distance': self.distance,
            'bearing': self.bearing,
            'confidence': self.confidence,
            'vehicle_altitude': self.vehicle_altitude,
            'features': self.features
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PoleObservation':
        """Create from dictionary"""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        return cls(
            timestamp=timestamp,
            latitude=data['latitude'],
            longitude=data['longitude'],
            distance=data['distance'],
            bearing=data['bearing'],
            confidence=data['confidence'],
            vehicle_altitude=data['vehicle_altitude'],
            features=data['features']
        )


@dataclass
class PoleRecord:
    """
    Persistent record of a detected pole
    
    Attributes:
        pole_id: Unique identifier
        latitude: Best estimate of pole latitude
        longitude: Best estimate of pole longitude
        pole_type: Voltage class (33kV, 11kV, LT, etc.)
        circuit_type: Single or multi-circuit
        confidence: Current confidence score (0-1)
        first_seen: Timestamp of first detection
        last_seen: Timestamp of most recent detection
        observation_count: Number of times observed
        observations: List of all observations
        metadata: Additional metadata
    """
    pole_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    latitude: float = 0.0
    longitude: float = 0.0
    pole_type: str = "unknown"
    circuit_type: str = "unknown"
    confidence: float = 0.0
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    observation_count: int = 0
    observations: List[PoleObservation] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def add_observation(self, observation: PoleObservation, 
                       detection_result: Dict):
        """
        Add a new observation and update pole record
        
        Args:
            observation: New observation data
            detection_result: Detection results from pole detector
        """
        self.observations.append(observation)
        self.observation_count += 1
        self.last_seen = observation.timestamp
        
        # Update position (weighted average favoring recent observations)
        if self.observation_count == 1:
            # First observation - use it directly
            self.latitude = observation.latitude
            self.longitude = observation.longitude
        else:
            # Weighted average: newer observations get more weight
            weight_new = 0.3  # 30% weight to new observation
            weight_old = 1.0 - weight_new
            
            self.latitude = (self.latitude * weight_old + 
                           observation.latitude * weight_new)
            self.longitude = (self.longitude * weight_old + 
                            observation.longitude * weight_new)
        
        # Update classification (take highest confidence)
        if detection_result.get('confidence', 0) > self.confidence:
            self.pole_type = detection_result.get('voltage_class', 'unknown')
            self.circuit_type = detection_result.get('circuit_type', 'unknown')
            self.confidence = detection_result.get('confidence', 0)
        
        # Accumulate confidence (but cap at 1.0)
        # Each observation increases confidence slightly
        confidence_boost = 0.05 * (observation.confidence)
        self.confidence = min(1.0, self.confidence + confidence_boost)
        
        # Update metadata
        if 'features' in detection_result:
            self.metadata['last_features'] = make_serializable(detection_result['features'])
        
        self.metadata['observation_count'] = self.observation_count
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            'pole_id': self.pole_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'pole_type': self.pole_type,
            'circuit_type': self.circuit_type,
            'confidence': self.confidence,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'observation_count': self.observation_count,
            'observations': [obs.to_dict() for obs in self.observations],
            'metadata': make_serializable(self.metadata)
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PoleRecord':
        """Create from dictionary"""
        first_seen = data.get('first_seen')
        if isinstance(first_seen, str):
            first_seen = datetime.fromisoformat(first_seen)
        
        last_seen = data.get('last_seen')
        if isinstance(last_seen, str):
            last_seen = datetime.fromisoformat(last_seen)
        
        observations = [
            PoleObservation.from_dict(obs) 
            for obs in data.get('observations', [])
        ]
        
        return cls(
            pole_id=data['pole_id'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            pole_type=data['pole_type'],
            circuit_type=data['circuit_type'],
            confidence=data['confidence'],
            first_seen=first_seen,
            last_seen=last_seen,
            observation_count=data['observation_count'],
            observations=observations,
            metadata=data.get('metadata', {})
        )
    
    def get_summary(self) -> dict:
        """Get human-readable summary"""
        return {
            'id': self.pole_id[:8],  # Short ID
            'position': f"{self.latitude:.6f}, {self.longitude:.6f}",
            'type': f"{self.pole_type} ({self.circuit_type})",
            'confidence': f"{self.confidence:.2%}",
            'observations': self.observation_count,
            'first_seen': self.first_seen.strftime('%Y-%m-%d %H:%M:%S'),
            'last_seen': self.last_seen.strftime('%Y-%m-%d %H:%M:%S')
        }
