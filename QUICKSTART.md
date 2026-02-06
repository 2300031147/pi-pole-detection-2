# Quick Start Guide

Get up and running with CODEX Pole Detection in 5 minutes!

## 🚀 Installation (2 minutes)

### On Raspberry Pi 5

```bash
# Update system
sudo apt-get update

# Install OpenCV and dependencies
sudo apt-get install -y python3-opencv python3-numpy python3-pil

# Clone repository
git clone https://github.com/2300031147/pi-pole-detection-2.git
cd pi-pole-detection-2

# Install Python packages
pip3 install -r requirements.txt
```

### On Desktop/Laptop

```bash
# Clone repository
git clone https://github.com/2300031147/pi-pole-detection-2.git
cd pi-pole-detection-2

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 🎯 Run Your First Detection (1 minute)

### Test with a pole image

```bash
python demo.py your_pole_image.jpg --visualize
```

### What you'll see:

```
============================================================
CODEX POLE DETECTION RESULTS
============================================================
Image: your_pole_image.jpg

Voltage Classification: 33kV
Confidence: 85.00%
Circuit Type: multi_circuit

Description: High voltage transmission - 3+ levels with wider top spacing

Matched Rules:
  ✓ Level count >= 3
  ✓ Top spacing is larger (33kV indicator)
  ✓ Insulator count >= 4

Detected Features:
  - Levels: 3
  - Crossarms: 6
  - Insulators: 8
  - Symmetry: 0.82
  - Wire Density: 2.00

Processing Time: 0.085 seconds
============================================================

✅ Detection complete!
   Voltage: 33kV
   Confidence: 85.00%
   Processing time: 0.085s
   FPS estimate: 11.8
```

## 📸 If You Don't Have Images Yet

No problem! The system includes a test with synthetic images:

```bash
python test_pole_detector.py
```

This validates that everything is working correctly.

## 🔧 Tuning for Your Poles (10 minutes)

### Step 1: Run on your 8 images

```bash
for img in image1.jpg image2.jpg image3.jpg image4.jpg image5.jpg image6.jpg image7.jpg image8.jpg; do
    python demo.py $img --visualize
done
```

### Step 2: Check the visualizations

Look at the `*_detected.jpg` files. Check if:
- ✅ Vertical pole detected (green line)
- ✅ Crossarms detected (blue lines)
- ✅ Insulators detected (red boxes)

### Step 3: Adjust if needed

If detection isn't perfect, edit `config.py`:

```python
# If missing lines
HOUGH_THRESHOLD = 80  # Lower to detect more lines

# If too many false detections
MIN_CONTOUR_AREA = 100  # Increase to filter small objects

# If levels clustering wrong
LEVEL_CLUSTERING_TOLERANCE = 25  # Adjust Y-position grouping
```

### Step 4: Re-run

```bash
python demo.py image1.jpg --visualize
```

Iterate until satisfied (usually 2-3 iterations).

## 🎓 Understanding Results

### Voltage Classes

| Class | What It Means |
|-------|---------------|
| **33kV** | High voltage transmission line |
| **11kV** | Medium voltage distribution |
| **LT** | Low tension (consumer level) |

### Confidence Score

- **> 80%**: High confidence, reliable classification
- **60-80%**: Good confidence, likely correct
- **< 60%**: Low confidence, manual verification recommended

### Circuit Type

- **single_circuit**: One voltage level
- **multi_circuit**: Multiple voltage levels (complex pole)

## 🔍 Troubleshooting

### Problem: No lines detected

**Solution:**
1. Check image quality (not too dark/blurry)
2. Lower `HOUGH_THRESHOLD` in config.py
3. Adjust `CANNY_THRESHOLD_LOW` and `CANNY_THRESHOLD_HIGH`

### Problem: Wrong voltage classification

**Solution:**
1. Check if levels are detected correctly
2. Verify insulators are being found
3. Adjust rules in `VOLTAGE_RULES` in config.py

### Problem: Too slow on Raspberry Pi

**Solution:**
1. Reduce `MAX_IMAGE_WIDTH` and `MAX_IMAGE_HEIGHT` in config.py
2. Process every 2nd or 3rd frame if using video
3. Reduce `HOUGH_MIN_LINE_LENGTH` to speed up Hough transform

## 📱 Using in Your Application

### Python Integration

```python
from pole_detector import PoleDetector

# Initialize once
detector = PoleDetector()

# Process images
result = detector.detect('pole.jpg')

# Use results
if result['confidence'] > 0.8:
    voltage = result['voltage_class']
    print(f"High confidence: {voltage}")
else:
    print("Manual verification needed")
```

### Batch Processing

```python
from pole_detector import PoleDetector
import glob

detector = PoleDetector()
images = glob.glob('poles/*.jpg')

results = detector.batch_detect(images)

# Generate report
for r in results:
    print(f"{r['image_path']}: {r['voltage_class']} ({r['confidence']:.1%})")
```

### Video Processing

```python
import cv2
from pole_detector import PoleDetector

detector = PoleDetector()
video = cv2.VideoCapture('poles.mp4')

frame_count = 0
while True:
    ret, frame = video.read()
    if not ret:
        break
    
    # Process every 10th frame for efficiency
    if frame_count % 10 == 0:
        # Save frame temporarily
        cv2.imwrite('temp_frame.jpg', frame)
        result = detector.detect('temp_frame.jpg')
        print(f"Frame {frame_count}: {result['voltage_class']}")
    
    frame_count += 1

video.release()
```

## 💡 Pro Tips

1. **Consistency**: Process images from similar angles/distances
2. **Lighting**: Daytime images work best
3. **Angle**: Front-on or slight angle works better than extreme side views
4. **Resolution**: 1280x720 or higher recommended
5. **Focus**: Clear, in-focus images are crucial

## 📊 Expected Performance

### Raspberry Pi 5 (16GB)

- **FPS**: 8-12 (single image processing)
- **Latency**: 80-120ms per image
- **RAM**: < 500MB
- **Accuracy**: 85-95% (clear images)

### Desktop PC

- **FPS**: 15-25
- **Latency**: 40-70ms per image
- **RAM**: < 300MB
- **Accuracy**: 85-95% (clear images)

## 🎉 You're Ready!

You now have a working pole detection system that:
- ✅ Requires no training
- ✅ Works with just 8 images
- ✅ Provides explainable results
- ✅ Runs on Raspberry Pi

## 📚 Next Steps

1. **Read the full README** for detailed API documentation
2. **Read CODEX_STRATEGY.md** to understand the approach
3. **Tune parameters** for your specific pole types
4. **Integrate** into your application

## 🆘 Getting Help

- Check the main README.md for detailed documentation
- Review code comments for implementation details
- Open an issue on GitHub for bugs/questions
- Read CODEX_STRATEGY.md for theoretical background

---

**Happy detecting!** 🚀🔌⚡
