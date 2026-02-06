"""
Pole Database - Persistent Storage with Deduplication
Maintains spatial model of infrastructure over time
"""

import json
import os
from typing import List, Optional, Dict
from datetime import datetime
from pole_record import PoleRecord, PoleObservation
from geographic_positioner import GeographicPositioner


class PoleDatabase:
    """
    Manages persistent pole records with deduplication
    
    Core responsibilities:
    - Store and retrieve pole records
    - Prevent duplicate pole creation
    - Update existing records on re-detection
    - Provide spatial queries
    """
    
    # Default proximity threshold for pole matching (meters)
    DEFAULT_PROXIMITY_THRESHOLD = 20  # 20 meters
    
    def __init__(self, 
                 database_path: str = "pole_database.json",
                 proximity_threshold: float = DEFAULT_PROXIMITY_THRESHOLD):
        """
        Initialize pole database
        
        Args:
            database_path: Path to JSON database file
            proximity_threshold: Distance threshold for pole matching (meters)
        """
        self.database_path = database_path
        self.proximity_threshold = proximity_threshold
        self.poles: Dict[str, PoleRecord] = {}
        
        # Load existing database if it exists
        self.load()
    
    def load(self):
        """Load pole database from file"""
        if os.path.exists(self.database_path):
            try:
                with open(self.database_path, 'r') as f:
                    data = json.load(f)
                
                self.poles = {
                    pole_id: PoleRecord.from_dict(pole_data)
                    for pole_id, pole_data in data.get('poles', {}).items()
                }
                
                print(f"Loaded {len(self.poles)} poles from database")
            except Exception as e:
                print(f"Warning: Could not load database: {e}")
                self.poles = {}
        else:
            print("No existing database found, starting fresh")
            self.poles = {}
    
    def save(self):
        """Save pole database to file"""
        try:
            data = {
                'poles': {
                    pole_id: pole.to_dict()
                    for pole_id, pole in self.poles.items()
                },
                'metadata': {
                    'total_poles': len(self.poles),
                    'last_updated': datetime.utcnow().isoformat(),
                    'proximity_threshold': self.proximity_threshold
                }
            }
            
            with open(self.database_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"Saved {len(self.poles)} poles to database")
        except Exception as e:
            print(f"Error saving database: {e}")
    
    def find_nearby_pole(self, latitude: float, longitude: float) -> Optional[PoleRecord]:
        """
        Find existing pole within proximity threshold
        
        Args:
            latitude: Latitude to search around
            longitude: Longitude to search around
            
        Returns:
            Matching PoleRecord or None
        """
        closest_pole = None
        closest_distance = float('inf')
        
        for pole in self.poles.values():
            distance = GeographicPositioner.calculate_distance_between_positions(
                latitude, longitude,
                pole.latitude, pole.longitude
            )
            
            if distance < self.proximity_threshold and distance < closest_distance:
                closest_pole = pole
                closest_distance = distance
        
        return closest_pole
    
    def add_or_update_pole(self,
                          latitude: float,
                          longitude: float,
                          observation: PoleObservation,
                          detection_result: Dict) -> PoleRecord:
        """
        Add new pole or update existing one
        
        This implements the core deduplication logic:
        - Check if pole exists within proximity threshold
        - If yes: update existing record
        - If no: create new record
        
        Args:
            latitude: Estimated pole latitude
            longitude: Estimated pole longitude
            observation: Observation data
            detection_result: Detection results from pole detector
            
        Returns:
            PoleRecord (new or updated)
        """
        # Check for existing pole
        existing_pole = self.find_nearby_pole(latitude, longitude)
        
        if existing_pole:
            # Update existing pole
            existing_pole.add_observation(observation, detection_result)
            print(f"Updated existing pole {existing_pole.pole_id[:8]} "
                  f"(now {existing_pole.observation_count} observations)")
            return existing_pole
        else:
            # Create new pole
            new_pole = PoleRecord(
                latitude=latitude,
                longitude=longitude,
                pole_type=detection_result.get('voltage_class', 'unknown'),
                circuit_type=detection_result.get('circuit_type', 'unknown'),
                confidence=detection_result.get('confidence', 0.0),
                first_seen=observation.timestamp,
                last_seen=observation.timestamp,
                observation_count=1,
                observations=[observation],
                metadata={
                    'initial_features': detection_result.get('features', {})
                }
            )
            
            self.poles[new_pole.pole_id] = new_pole
            print(f"Created new pole {new_pole.pole_id[:8]} at "
                  f"{latitude:.6f}, {longitude:.6f}")
            return new_pole
    
    def get_all_poles(self) -> List[PoleRecord]:
        """Get all poles in database"""
        return list(self.poles.values())
    
    def get_pole_by_id(self, pole_id: str) -> Optional[PoleRecord]:
        """Get specific pole by ID"""
        return self.poles.get(pole_id)
    
    def get_poles_in_area(self,
                         center_lat: float,
                         center_lon: float,
                         radius_meters: float) -> List[PoleRecord]:
        """
        Get all poles within radius of a point
        
        Args:
            center_lat: Center latitude
            center_lon: Center longitude
            radius_meters: Search radius in meters
            
        Returns:
            List of poles within radius
        """
        poles_in_area = []
        
        for pole in self.poles.values():
            distance = GeographicPositioner.calculate_distance_between_positions(
                center_lat, center_lon,
                pole.latitude, pole.longitude
            )
            
            if distance <= radius_meters:
                poles_in_area.append(pole)
        
        return poles_in_area
    
    def get_statistics(self) -> dict:
        """Get database statistics"""
        if not self.poles:
            return {
                'total_poles': 0,
                'total_observations': 0,
                'pole_types': {}
            }
        
        pole_types = {}
        total_observations = 0
        
        for pole in self.poles.values():
            pole_type = pole.pole_type
            pole_types[pole_type] = pole_types.get(pole_type, 0) + 1
            total_observations += pole.observation_count
        
        return {
            'total_poles': len(self.poles),
            'total_observations': total_observations,
            'average_observations_per_pole': total_observations / len(self.poles),
            'pole_types': pole_types,
            'database_path': self.database_path,
            'proximity_threshold': self.proximity_threshold
        }
    
    def export_to_geojson(self, output_path: str):
        """
        Export poles to GeoJSON format for mapping
        
        Args:
            output_path: Path to output GeoJSON file
        """
        features = []
        
        for pole in self.poles.values():
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [pole.longitude, pole.latitude]
                },
                'properties': {
                    'pole_id': pole.pole_id,
                    'pole_type': pole.pole_type,
                    'circuit_type': pole.circuit_type,
                    'confidence': pole.confidence,
                    'observations': pole.observation_count,
                    'first_seen': pole.first_seen.isoformat(),
                    'last_seen': pole.last_seen.isoformat()
                }
            }
            features.append(feature)
        
        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }
        
        with open(output_path, 'w') as f:
            json.dump(geojson, f, indent=2)
        
        print(f"Exported {len(features)} poles to {output_path}")
