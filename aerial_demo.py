"""
Aerial Mapping Demo
Demonstrates autonomous pole mapping from aerial imagery
"""

import sys
import os
from datetime import datetime, timedelta
import cv2
from aerial_mapping_system import AerialMappingSystem
from telemetry import Telemetry


def simulate_aerial_survey():
    """
    Simulate an aerial survey with multiple frames
    
    This creates simulated telemetry for testing purposes
    """
    print("\n" + "="*70)
    print("AUTONOMOUS AERIAL POLE MAPPING SYSTEM - SIMULATION")
    print("="*70)
    
    # Initialize system
    system = AerialMappingSystem(
        database_path="aerial_pole_database.json",
        proximity_threshold=20.0
    )
    
    # Simulated flight path
    # Starting position (example: somewhere in a city)
    base_lat = 40.7128
    base_lon = -74.0060
    base_altitude = 50.0
    
    # Simulate multiple frame captures along a flight path
    print("\nSimulating aerial survey...")
    print("(In production, this would process actual aerial video)\n")
    
    frames = [
        {
            'image': None,  # Would be actual frame
            'telemetry': {
                'latitude': base_lat,
                'longitude': base_lon,
                'altitude': base_altitude,
                'heading': 90,  # East
                'timestamp': datetime.utcnow()
            }
        },
        {
            'image': None,
            'telemetry': {
                'latitude': base_lat + 0.001,
                'longitude': base_lon + 0.001,
                'altitude': base_altitude,
                'heading': 90,
                'timestamp': datetime.utcnow() + timedelta(seconds=5)
            }
        },
        {
            'image': None,
            'telemetry': {
                'latitude': base_lat + 0.0015,
                'longitude': base_lon + 0.0015,
                'altitude': base_altitude + 5,
                'heading': 95,
                'timestamp': datetime.utcnow() + timedelta(seconds=10)
            }
        }
    ]
    
    print("Note: This simulation needs actual pole images.")
    print("Usage: python aerial_demo.py <image_path> [<image_path2> ...]")
    print("\nFor testing, you can provide pole images that will be")
    print("processed as if captured during an aerial survey.\n")
    
    return system


def process_images_as_aerial_survey(image_paths):
    """
    Process provided images as aerial survey frames
    
    Args:
        image_paths: List of image paths
    """
    print("\n" + "="*70)
    print("AUTONOMOUS AERIAL POLE MAPPING SYSTEM")
    print("="*70)
    
    # Initialize system
    system = AerialMappingSystem(
        database_path="aerial_pole_database.json",
        proximity_threshold=20.0
    )
    
    # Simulated flight path parameters
    base_lat = 40.7128  # Example: New York
    base_lon = -74.0060
    altitude = 50.0
    heading = 90  # East
    
    print(f"\nProcessing {len(image_paths)} images as aerial survey frames...")
    print(f"Simulated starting position: {base_lat:.6f}, {base_lon:.6f}")
    print(f"Altitude: {altitude}m, Heading: {heading}°\n")
    
    for i, image_path in enumerate(image_paths):
        if not os.path.exists(image_path):
            print(f"Warning: Image not found: {image_path}")
            continue
        
        # Simulate telemetry (moving along a path)
        telemetry = Telemetry(
            latitude=base_lat + (i * 0.0005),  # Move ~50m per frame
            longitude=base_lon + (i * 0.0005),
            altitude=altitude + (i * 2),  # Slight altitude change
            heading=heading + (i * 2),  # Slight heading change
            timestamp=datetime.utcnow()
        )
        
        print(f"\n--- Frame {i+1}/{len(image_paths)} ---")
        print(f"Position: {telemetry.latitude:.6f}, {telemetry.longitude:.6f}")
        print(f"Processing: {os.path.basename(image_path)}")
        
        # Process frame
        result = system.process_frame(image_path, telemetry, visualize=False)
        
        if 'error' in result:
            print(f"Error: {result['error']}")
            continue
        
        # Display results
        if result['detection'] == 'pole_detected':
            print(f"\n✓ Pole Detected!")
            print(f"  Pole ID: {result['pole_id_short']}")
            print(f"  Type: {result['voltage_class']} ({result['circuit_type']})")
            print(f"  Confidence: {result['confidence']:.2%}")
            print(f"  Position: {result['position']['latitude']:.6f}, "
                  f"{result['position']['longitude']:.6f}")
            print(f"  Distance: {result['estimated_distance']:.1f}m")
            print(f"  Bearing: {result['bearing']:.1f}°")
            print(f"  Observations: {result['observation_count']}")
            
            if result['is_new_pole']:
                print(f"  Status: NEW POLE")
            else:
                print(f"  Status: UPDATED EXISTING POLE")
        else:
            print("  No pole detected (low confidence)")
    
    # Print summary
    system.print_summary()
    
    # Export to GeoJSON
    geojson_path = "aerial_poles.geojson"
    system.export_to_geojson(geojson_path)
    print(f"✓ Exported pole locations to {geojson_path}")
    print("  (Can be viewed in GIS software or online mapping tools)\n")
    
    return system


def main():
    """Main demo function"""
    
    if len(sys.argv) < 2:
        print("\n" + "="*70)
        print("AUTONOMOUS AERIAL POLE MAPPING SYSTEM")
        print("="*70)
        print("\nUsage: python aerial_demo.py <image1> [<image2> ...]")
        print("\nExample:")
        print("  python aerial_demo.py pole1.jpg pole2.jpg pole3.jpg")
        print("\nThis will:")
        print("  • Detect poles in each image")
        print("  • Simulate aerial telemetry")
        print("  • Estimate geographic positions")
        print("  • Store poles in persistent database")
        print("  • Avoid duplicates (if same pole seen multiple times)")
        print("  • Export results to GeoJSON")
        print("\nFeatures:")
        print("  ✓ Zero-training detection")
        print("  ✓ Geographic positioning")
        print("  ✓ Persistent storage")
        print("  ✓ Duplicate prevention")
        print("  ✓ Confidence accumulation")
        print("  ✓ Real-time capable")
        print("\nNote: This demo simulates aerial telemetry.")
        print("In production, use actual GPS/IMU data from aerial platform.\n")
        return
    
    # Get image paths from arguments
    image_paths = sys.argv[1:]
    
    # Process images as aerial survey
    system = process_images_as_aerial_survey(image_paths)
    
    # Display database stats
    print("\n" + "="*70)
    print("FINAL DATABASE STATE")
    print("="*70)
    
    all_poles = system.get_all_poles()
    
    if all_poles:
        print(f"\nDetected Poles ({len(all_poles)}):\n")
        for i, pole in enumerate(all_poles, 1):
            summary = pole.get_summary()
            print(f"{i}. Pole {summary['id']}")
            print(f"   Position: {summary['position']}")
            print(f"   Type: {summary['type']}")
            print(f"   Confidence: {summary['confidence']}")
            print(f"   Observations: {summary['observations']}")
            print(f"   First seen: {summary['first_seen']}")
            print(f"   Last seen: {summary['last_seen']}")
            print()
    else:
        print("\nNo poles in database yet.")
    
    print("="*70)
    print("✓ Aerial survey simulation complete!")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
