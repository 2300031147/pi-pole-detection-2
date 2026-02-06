# Manual-Flight Aerial Pole Mapping System

**CODEX: Situational Awareness Intelligence for Human-Piloted Aircraft**

⚠️ **CRITICAL: This system is a PASSIVE OBSERVER ONLY**
- Does NOT control aircraft
- Does NOT issue navigation commands
- Does NOT influence pilot decisions
- Operates as situational awareness tool for manually piloted flight

---

## 🎯 System Role

This is an **observer and analyst** that augments human pilots with structured infrastructure awareness. It processes visual and telemetry data to detect, classify, and persistently track electrical poles, without any control over the aircraft.

### What This System DOES

✅ **Observe** - Analyze imagery from onboard camera  
✅ **Infer** - Classify poles using geometry and structure  
✅ **Localize** - Estimate geographic position using telemetry  
✅ **Record** - Maintain persistent spatial database  
✅ **Display** - Provide real-time situational awareness  

### What This System DOES NOT DO

❌ Control aircraft flight  
❌ Issue navigation commands  
❌ Request pilot actions  
❌ Assume planned flight paths  
❌ Rely on smooth motion  
❌ Track between frames  

---

## 🚁 Manual Flight Characteristics

The system is designed for **human-piloted aircraft** with:

- **Non-uniform speed** - Variable velocity
- **Non-linear trajectories** - Manual maneuvering
- **Variable camera orientation** - Dynamic viewing angles
- **Irregular detection intervals** - Frames processed as available
- **Independent observations** - Each frame stands alone

### Key Design Principles

1. **Temporal Agnosticism** - No reliance on frame continuity
2. **Independent Validation** - Each observation is self-contained
3. **Geographic Deduplication** - Poles matched by location, not time
4. **Confidence-Based Uncertainty** - Unknown = low confidence, not forced classification
5. **Passive Operation** - Functions without operator interaction

---

## 🔧 Architecture

```
Human Pilot
    ↓
Manual Aircraft Control
    ↓
[Onboard Camera] + [GPS/IMU Telemetry]
    ↓
CODEX Observer System (THIS)
    ↓
Persistent Pole Database + Live Display
```

### Core Components

1. **Visual Analyzer** (pole_detector.py)
   - Geometry-based detection
   - Structure classification
   - No training required

2. **Geographic Positioner** (geographic_positioner.py)
   - Distance estimation
   - Bearing calculation
   - Position projection

3. **Persistence Manager** (pole_database.py)
   - Spatial deduplication
   - Confidence accumulation
   - GeoJSON export

4. **Observation Coordinator** (aerial_mapping_system.py)
   - Frame processing
   - Independent observations
   - Real-time output

---

## 📊 Position Estimation Under Manual Motion

The system handles **non-predictable motion** by:

### Per-Frame Independence

Each frame is processed independently:
- No motion prediction
- No optical flow tracking
- No frame-to-frame dependencies

### Position Calculation

```python
For each frame:
  1. Detect pole in image
  2. Read current telemetry (lat, lon, alt, heading)
  3. Estimate distance (geometric scaling)
  4. Calculate bearing (image position + heading)
  5. Project geographic position
  6. Store as independent observation
```

### Deduplication Strategy

Poles are matched by **geographic proximity only**:
- Within 20m threshold → Same pole (update)
- Beyond threshold → New pole (create)

No reliance on:
- Detection timing
- Frame sequence
- Flight path continuity

---

## 🔒 Safety Axioms

### ⚡ All Infrastructure is LIVE

**CRITICAL SAFETY RULE:**
All detected electrical infrastructure shall be treated as **energized and hazardous** at all times.

- No inference indicates de-energization
- No classification implies safety clearance
- No confidence score grants approval to approach

### 🚁 Pilot Authority

**OPERATIONAL RULE:**
The human pilot has **complete and sole authority** over:
- Flight operations
- Navigation decisions
- Safety procedures
- Aircraft control

This system provides information only.

---

## 📦 Installation

### Requirements

```bash
pip install opencv-python numpy pillow
```

### Quick Start

```python
from aerial_mapping_system import AerialMappingSystem
from telemetry import Telemetry

# Initialize system
system = AerialMappingSystem(
    database_path="poles.json",
    proximity_threshold=20.0
)

# Process frame with telemetry
telemetry = Telemetry(
    latitude=40.7128,
    longitude=-74.0060,
    altitude=50.0,
    heading=90.0,
    timestamp=datetime.utcnow()
)

result = system.process_frame(image_path, telemetry)
```

---

## 🎮 Usage

### Command-Line Demo

```bash
# Process images as aerial observations
python aerial_demo.py image1.jpg image2.jpg image3.jpg

# System will:
# - Detect poles in each image
# - Simulate manual flight telemetry
# - Estimate geographic positions
# - Store in persistent database
# - Avoid duplicates
# - Export to GeoJSON
```

### Python API

```python
# Process single frame
result = system.process_frame(image, telemetry, visualize=True)

if result['detection'] == 'pole_detected':
    print(f"Pole ID: {result['pole_id_short']}")
    print(f"Type: {result['voltage_class']}")
    print(f"Position: {result['position']}")
    print(f"Distance: {result['estimated_distance']}m")
    print(f"Observations: {result['observation_count']}")

# Query database
all_poles = system.get_all_poles()
nearby_poles = system.get_poles_near_position(lat, lon, radius=1000)

# Export to GeoJSON
system.export_to_geojson("poles.geojson")
```

---

## 📈 Output Format

### Per-Frame Results

```python
{
    'frame_number': 42,
    'detection': 'pole_detected',
    'pole_id': 'abc123...',
    'pole_id_short': 'abc123',
    'voltage_class': '33kV',
    'circuit_type': 'multi_circuit',
    'confidence': 0.87,
    'position': {
        'latitude': 40.712834,
        'longitude': -74.005987
    },
    'estimated_distance': 127.5,
    'bearing': 92.3,
    'observation_count': 3,
    'is_new_pole': False,
    'telemetry': {...},
    'session_stats': {...}
}
```

### Pole Record

```python
{
    'pole_id': 'unique-uuid',
    'latitude': 40.712834,
    'longitude': -74.005987,
    'pole_type': '33kV',
    'circuit_type': 'multi_circuit',
    'confidence': 0.91,
    'first_seen': '2026-02-06T10:23:15Z',
    'last_seen': '2026-02-06T10:28:42Z',
    'observation_count': 5,
    'observations': [...]
}
```

---

## 🧪 Testing

```bash
# Run all tests
python test_aerial_mapping.py

# Tests cover:
# - Telemetry validation
# - Geographic calculations
# - Position estimation
# - Database operations
# - Deduplication logic
# - End-to-end processing
```

---

## 🗺️ GeoJSON Export

Export pole database for use in GIS software:

```python
system.export_to_geojson("poles.geojson")
```

Load in:
- QGIS
- ArcGIS
- Google Earth Pro
- Mapbox
- OpenStreetMap editors

---

## 🔧 Configuration

### Camera Parameters

Adjust for your specific camera:

```python
system = AerialMappingSystem(
    camera_fov_h=60.0,  # Horizontal FOV (degrees)
    camera_fov_v=45.0   # Vertical FOV (degrees)
)
```

### Proximity Threshold

Adjust pole matching sensitivity:

```python
system = AerialMappingSystem(
    proximity_threshold=20.0  # meters
)
```

Lower threshold = More strict matching (more duplicates)  
Higher threshold = More lenient (fewer duplicates, possible merging)

---

## 📝 Operational Notes

### Manual Flight Considerations

1. **Variable Altitude**
   - System handles altitude changes
   - Distance estimation adjusts automatically

2. **Non-Linear Paths**
   - No assumptions about trajectory
   - Each frame processed independently

3. **Camera Orientation**
   - Bearing calculated from heading + image position
   - Works with pan/tilt variations

4. **Detection Gaps**
   - Missing frames are okay
   - Poles remain in database
   - Re-detection updates confidence

### Best Practices

✅ **DO:**
- Process frames as available
- Trust confidence scores
- Review low-confidence detections manually
- Export data regularly
- Back up database file

❌ **DON'T:**
- Assume continuous frame capture
- Force classifications on low confidence
- Delete poles without verification
- Rely on detection for flight decisions
- Use for safety-critical operations

---

## 🎓 Technical Details

### Detection Method

**Zero-Training Approach:**
- Canny edge detection
- Hough line transform
- Geometric feature extraction
- Engineering rule-based classification

**No Machine Learning Required:**
- No training dataset
- No GPU needed
- Works with 8 reference images
- Explainable results

### Position Estimation

**Method 1 (Pixel Height):**
```
distance = (actual_pole_height × focal_length) / pixel_height
```

**Method 2 (Altitude-Based):**
```
distance = altitude / tan(viewing_angle)
```

**Bearing Calculation:**
```
bearing = vehicle_heading + angular_offset_in_image
```

**Geographic Projection:**
Uses Haversine formula to project position from vehicle location, distance, and bearing.

### Deduplication Algorithm

```python
for new_observation:
    for existing_pole in database:
        distance = haversine(new_pos, existing_pole.position)
        if distance < proximity_threshold:
            update_existing_pole()
            return
    create_new_pole()
```

---

## 🔍 Limitations

### Known Constraints

1. **Distance Accuracy**
   - ±20% error typical
   - Better with known pole heights
   - Degrades with extreme angles

2. **Detection Range**
   - Optimal: 50-200m
   - Maximum: ~500m
   - Minimum: 20m

3. **Environmental Factors**
   - Requires visible poles
   - Poor in heavy occlusion
   - Lighting dependent

4. **Camera Requirements**
   - Minimum 720p resolution
   - Stable exposure
   - Forward-looking mount preferred

### Not Suitable For

❌ Aircraft control or automation  
❌ Safety-critical decisions  
❌ Real-time collision avoidance  
❌ Regulatory compliance verification  
❌ Warranty/guarantee of completeness  

---

## 📚 Documentation Files

- **README.md** - This file
- **AERIAL_CODEX.md** - Full CODEX specification
- **QUICKSTART.md** - Original detection system guide
- **CODEX_STRATEGY.md** - Zero-training technical approach
- **PROJECT_STRUCTURE.md** - Architecture overview

---

## 🤝 Integration

### Real-Time Video Processing

```python
import cv2

cap = cv2.VideoCapture(0)  # Camera
system = AerialMappingSystem()

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Get current telemetry from GPS/IMU
    telemetry = get_current_telemetry()
    
    # Process frame
    result = system.process_frame(frame, telemetry)
    
    # Display results
    if result['detection'] == 'pole_detected':
        show_overlay(result)
```

### External Database Access

```python
# Query system state
stats = system.get_database_stats()
all_poles = system.get_all_poles()

# Get poles near current position
nearby = system.get_poles_near_position(
    current_lat, current_lon, radius=500
)

# Export for external use
system.export_to_geojson("export.geojson")
```

---

## ⚠️ Disclaimers

### Operational Disclaimer

This system is provided as a **situational awareness tool only**. It does not:
- Replace pilot judgment
- Guarantee detection completeness
- Ensure position accuracy
- Provide safety clearance

### Safety Disclaimer

All electrical infrastructure must be treated as **live and hazardous**. This system:
- Cannot determine energization status
- Cannot assess safety distances
- Cannot approve approach procedures

### Accuracy Disclaimer

Position estimates are **approximate** and subject to:
- Camera calibration errors
- Telemetry accuracy
- Geometric approximations
- Environmental conditions

**Always verify critical information through established procedures.**

---

## 📄 License

MIT License - See LICENSE file

---

## 🆘 Support

For questions or issues:
- Review documentation
- Check test cases
- Open GitHub issue

---

**Remember: You are the pilot. This system is your observer. All decisions remain yours.** 🚁

---

*Manual-Flight CODEX System v2.0*  
*Passive Observer | Independent Observations | Human Authority*
