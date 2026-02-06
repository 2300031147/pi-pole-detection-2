# Manual Annotation Guide

For your 8 images, you need to manually observe and note key features.
This is NOT for training a model - it's for validating detection and tuning parameters.

## 📝 Annotation Template

Copy this template for each of your 8 images:

```
IMAGE: image_name.jpg
ACTUAL VOLTAGE: [33kV / 11kV / LT]

FEATURES:
- Crossarms (horizontal bars): _____
- Vertical levels: _____
- Insulator type: [disc / pin / polymer]
- Top spacing: [wide / medium / narrow]
- Bottom wires/insulators: _____
- Symmetry: [symmetric / asymmetric]
- Circuit type: [single / multi]

NOTES:
- Any unusual characteristics: _____
- Occlusions or obstacles: _____
- Image quality: [excellent / good / fair / poor]
```

## 🖼️ Example Annotations

### Example 1: 33kV Transmission Pole

```
IMAGE: pole_33kv_01.jpg
ACTUAL VOLTAGE: 33kV

FEATURES:
- Crossarms (horizontal bars): 6
- Vertical levels: 3
- Insulator type: disc
- Top spacing: wide
- Bottom wires/insulators: 8 disc insulators
- Symmetry: symmetric
- Circuit type: multi

NOTES:
- Clear sky background
- Straight-on view
- Image quality: excellent
```

### Example 2: 11kV Distribution Pole

```
IMAGE: pole_11kv_01.jpg
ACTUAL VOLTAGE: 11kV

FEATURES:
- Crossarms (horizontal bars): 4
- Vertical levels: 2
- Insulator type: pin
- Top spacing: medium
- Bottom wires/insulators: 4 pin insulators
- Symmetry: symmetric
- Circuit type: multi

NOTES:
- Some tree branches visible
- Slight angle view
- Image quality: good
```

### Example 3: LT (Low Tension) Pole

```
IMAGE: pole_lt_01.jpg
ACTUAL VOLTAGE: LT

FEATURES:
- Crossarms (horizontal bars): 6
- Vertical levels: 1
- Insulator type: pin
- Top spacing: N/A (single level)
- Bottom wires/insulators: 6 wires
- Symmetry: symmetric
- Circuit type: single

NOTES:
- Distribution wires to homes
- Multiple wires on single level
- Image quality: good
```

## 📊 Create a Summary Table

After annotating all 8 images, create a summary:

| Image | Voltage | Levels | Crossarms | Insulators | Top Spacing | Circuit |
|-------|---------|--------|-----------|------------|-------------|---------|
| img1.jpg | 33kV | 3 | 6 | 8 | wide | multi |
| img2.jpg | 33kV | 3 | 6 | 9 | wide | multi |
| img3.jpg | 11kV | 2 | 4 | 4 | medium | multi |
| img4.jpg | 11kV | 2 | 4 | 5 | medium | multi |
| img5.jpg | LT | 1 | 5 | 2 | N/A | single |
| img6.jpg | LT | 1 | 6 | 3 | N/A | single |
| img7.jpg | 33kV | 3 | 6 | 7 | wide | multi |
| img8.jpg | 11kV | 2 | 3 | 4 | medium | multi |

## 🎯 What to Look For

### 1. Vertical Levels

Count distinct horizontal levels:
```
    ═══════    ← Level 1 (top)
    
    ═══════    ← Level 2 (middle)
    
    ═══════    ← Level 3 (bottom)
```

### 2. Crossarms

Count individual horizontal bars:
- Each arm extending from pole = 1 crossarm
- Left and right arms = 2 crossarms (if present)
- Multiple levels × 2 arms = total crossarms

### 3. Insulators

Count visible insulators:
- **Disc insulators**: Stack of disc-shaped objects
- **Pin insulators**: Single piece on top of crossarm
- **Polymer insulators**: Long, composite material

### 4. Spacing

Measure relative spacing between levels:
- **Wide**: Top spacing noticeably larger (33kV indicator)
- **Medium**: Equal spacing between all levels
- **Narrow**: Compressed spacing

### 5. Symmetry

Check left-right balance:
- **Symmetric**: Equal crossarms on both sides
- **Asymmetric**: Unbalanced configuration

## 🔍 How to Use Your Annotations

### 1. Validation

After running detection:
```bash
python demo.py image1.jpg
```

Compare detected features to your annotations:
- ✅ Level count matches?
- ✅ Crossarm count close?
- ✅ Insulator count reasonable?
- ✅ Voltage classification correct?

### 2. Parameter Tuning

If detection doesn't match your annotations:

**Too few lines detected:**
```python
# In config.py
HOUGH_THRESHOLD = 80  # Lower (was 100)
```

**Too many false insulators:**
```python
MIN_ROUNDNESS = 0.6  # Higher (was 0.5)
MIN_CONTOUR_AREA = 75  # Higher (was 50)
```

**Levels clustering incorrectly:**
```python
LEVEL_CLUSTERING_TOLERANCE = 25  # Adjust (was 30)
```

### 3. Rule Refinement

If voltage classification is wrong, check rules:

```python
# In config.py
VOLTAGE_RULES = {
    '33kV': {
        'min_levels': 3,  # Your 33kV poles have 3 levels?
        'min_crossarms': 2,  # Adjust based on your data
        'min_insulators': 4,  # Typical count in your images?
    }
}
```

## 📈 Statistical Analysis

Calculate ranges from your 8 images:

```
33kV poles:
- Levels: 3 (consistent)
- Crossarms: 6-6 (range)
- Insulators: 7-9 (range)
- Top spacing: Always wide

11kV poles:
- Levels: 2 (consistent)
- Crossarms: 3-4 (range)
- Insulators: 4-5 (range)
- Top spacing: Always medium

LT poles:
- Levels: 1 (consistent)
- Crossarms: 5-6 (range)
- Insulators: 2-3 (range)
- Top spacing: N/A
```

Use these ranges to set rule thresholds.

## 🎓 Engineering Knowledge Integration

### Why Top Spacing Matters (33kV)

High voltage requires more clearance:
```
33kV:  ═══  ← Large gap (safety clearance)
       
       ═══  ← Smaller gap
       
       ═══
```

### Why Wire Density Matters (LT)

Low tension often has many distribution wires:
```
LT:  ══════════  ← Many wires on one level
```

### Why Level Count Matters

More voltage = more isolation:
- 1 level → Low tension (< 1kV)
- 2 levels → Medium voltage (11kV)
- 3+ levels → High voltage (33kV+)

## ✅ Checklist

After annotating your 8 images:

- [ ] All 8 images annotated
- [ ] Summary table created
- [ ] Statistical ranges calculated
- [ ] Detected vs. Actual compared for each image
- [ ] Parameters tuned based on results
- [ ] Rules adjusted if needed
- [ ] All images now detecting correctly

## 💾 Save Your Work

Save your annotations in a CSV file:

```csv
image,voltage,levels,crossarms,insulators,top_spacing,circuit_type
img1.jpg,33kV,3,6,8,wide,multi
img2.jpg,33kV,3,6,9,wide,multi
img3.jpg,11kV,2,4,4,medium,multi
img4.jpg,11kV,2,4,5,medium,multi
img5.jpg,LT,1,5,2,none,single
img6.jpg,LT,1,6,3,none,single
img7.jpg,33kV,3,6,7,wide,multi
img8.jpg,11kV,2,3,4,medium,multi
```

This serves as your ground truth for validation.

## 🚀 Remember

You're NOT training a model with these annotations.

You're:
1. ✅ Building **engineering knowledge** into code
2. ✅ Validating that **detection works**
3. ✅ Tuning **parameters** for your environment
4. ✅ Creating **test cases** for validation

This is **domain expertise**, not machine learning!

---

**30 minutes of annotation** = System that works with 8 images! 🎯
