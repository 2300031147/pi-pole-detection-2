"""
Demo script for CODEX Pole Detection System
Shows how to use the detection pipeline
"""

import sys
import os
import cv2
from pole_detector import PoleDetector


def main():
    """Main demo function"""
    
    print("\n" + "="*60)
    print("CODEX POLE DETECTION SYSTEM")
    print("Zero-Training Voltage Classification")
    print("="*60)
    
    # Check if image path provided
    if len(sys.argv) < 2:
        print("\nUsage: python demo.py <image_path> [--visualize]")
        print("\nExample:")
        print("  python demo.py pole_image.jpg --visualize")
        print("\nThis system works with as few as 8 images!")
        print("No ML training required - uses geometry and rules.")
        return
    
    image_path = sys.argv[1]
    visualize = '--visualize' in sys.argv or '-v' in sys.argv
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"\nError: Image not found: {image_path}")
        return
    
    # Initialize detector
    print("\nInitializing CODEX detector...")
    detector = PoleDetector()
    
    # Run detection
    print(f"Processing: {image_path}")
    results = detector.detect(image_path, visualize=visualize)
    
    # Check for errors
    if 'error' in results:
        print(f"\nError: {results['error']}")
        return
    
    # Print results
    detector.print_results(results)
    
    # Show/save visualization if requested
    if visualize and 'visualization' in results:
        output_path = image_path.replace('.', '_detected.')
        cv2.imwrite(output_path, results['visualization'])
        print(f"Visualization saved to: {output_path}")
        
        # Try to display (may not work in headless environments)
        try:
            cv2.imshow('Pole Detection', results['visualization'])
            print("\nPress any key to close the visualization window...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        except:
            print("(Display not available in headless environment)")
    
    # Print summary
    print("\n✅ Detection complete!")
    print(f"   Voltage: {results['voltage_class']}")
    print(f"   Confidence: {results['confidence']:.2%}")
    print(f"   Processing time: {results['processing_time_seconds']:.3f}s")
    print(f"   FPS estimate: {1.0/results['processing_time_seconds']:.1f}")
    print("\nThis approach:")
    print("  • Requires NO training data")
    print("  • Works with as few as 8 images")
    print("  • Uses pure geometry and rules")
    print("  • Runs efficiently on Raspberry Pi 5")
    print("  • Provides explainable results")


def batch_demo(image_dir: str):
    """
    Process all images in a directory
    
    Args:
        image_dir: Directory containing images
    """
    import glob
    
    # Find all images
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp']
    image_paths = []
    for ext in extensions:
        image_paths.extend(glob.glob(os.path.join(image_dir, ext)))
        image_paths.extend(glob.glob(os.path.join(image_dir, ext.upper())))
    
    if not image_paths:
        print(f"No images found in {image_dir}")
        return
    
    print(f"\nFound {len(image_paths)} images")
    
    # Initialize detector
    detector = PoleDetector()
    
    # Process all images
    results = detector.batch_detect(image_paths, visualize=True)
    
    # Print summary
    print("\n" + "="*60)
    print("BATCH PROCESSING SUMMARY")
    print("="*60)
    
    voltage_counts = {}
    total_time = 0
    
    for result in results:
        if 'error' not in result:
            voltage = result['voltage_class']
            voltage_counts[voltage] = voltage_counts.get(voltage, 0) + 1
            total_time += result['processing_time_seconds']
            
            # Save visualization
            if 'visualization' in result:
                output_path = result['image_path'].replace('.', '_detected.')
                cv2.imwrite(output_path, result['visualization'])
    
    print(f"\nProcessed: {len(results)} images")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average time: {total_time/len(results):.3f}s per image")
    print(f"Average FPS: {len(results)/total_time:.1f}")
    
    print("\nVoltage Distribution:")
    for voltage, count in sorted(voltage_counts.items()):
        print(f"  {voltage}: {count} images")


if __name__ == '__main__':
    main()
