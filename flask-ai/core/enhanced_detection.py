# core/enhanced_detection.py - MULTI-OBJECT DETECTION: Enhanced defect prediction analysis with multiple object support
"""
MULTI-OBJECT DETECTION: Enhanced defect prediction analysis without artificial type priority
- Selection based purely on scan results: area, confidence, and quality
- No hardcoded preference for specific defect types
- Fair opportunity for all defect types based on actual detection
- SUPPORTS MULTIPLE OBJECTS: Can detect and track multiple separate objects in frame
"""

import cv2
import numpy as np

# Import configuration constants
try:
    from config import (
        SPECIFIC_DEFECT_CLASSES,
        DEFECT_CONFIDENCE_THRESHOLD,
        MIN_DEFECT_PIXELS,
        MIN_DEFECT_PERCENTAGE,
        MIN_BBOX_AREA
    )
except ImportError:
    print("Warning: Could not import from config, using fallback constants")

    SPECIFIC_DEFECT_CLASSES = {
        0: "background",
        1: "damaged",
        2: "missing_component",
        3: "open",
        4: "scratch",
        5: "stained"
    }

    DEFECT_CONFIDENCE_THRESHOLD = 0.15
    MIN_DEFECT_PIXELS = 50
    MIN_DEFECT_PERCENTAGE = 0.001
    MIN_BBOX_AREA = 50

def analyze_defect_predictions_enhanced(predicted_mask, confidence_scores, image_shape):
    """MODIFIED: Enhanced defect prediction with MUCH more permissive object validation"""
    h, w = predicted_mask.shape
    total_pixels = h * w

    print(f"=== MULTI-OBJECT DETECTION (Multiple Objects Support) ===")
    print(f"Image shape: {h}x{w} = {total_pixels} pixels")
    print(f"Using confidence threshold: {DEFECT_CONFIDENCE_THRESHOLD}")

    analysis = {
        'detected_defects': [],
        'class_distribution': {},
        'bounding_boxes': {},
        'defect_statistics': {},
        'spatial_analysis': {},
        'multi_object_detection': True,
        'total_objects_detected': 0
    }

    # Collect all potential defects with multi-object support
    all_detected_objects = []

    # Analyze each defect class - SKIP background class (0)
    for class_id, class_name in SPECIFIC_DEFECT_CLASSES.items():
        class_mask = (predicted_mask == class_id)
        pixel_count = np.sum(class_mask)
        percentage = (pixel_count / total_pixels) * 100

        print(f"Class {class_id} ({class_name}): {pixel_count} pixels ({percentage:.3f}%)")

        analysis['class_distribution'][class_name] = {
            'pixel_count': int(pixel_count),
            'percentage': percentage,
            'class_id': class_id
        }

        # Skip background class completely
        if class_id == 0:  # background class
            print(f"  Skipping background class {class_id}")
            continue

        # Process only actual defect classes (1-5) with MUCH more permissive validation
        if pixel_count > 0:
            print(f"  Analyzing defect class {class_name} for multiple objects...")

            # Use lower confidence threshold
            confident_mask = class_mask & (confidence_scores > DEFECT_CONFIDENCE_THRESHOLD)
            confident_pixels = np.sum(confident_mask)

            print(f"  Confident pixels (>{DEFECT_CONFIDENCE_THRESHOLD}): {confident_pixels}")

            # MUCH MORE PERMISSIVE detection criteria
            min_pixels = max(MIN_DEFECT_PIXELS // 4, total_pixels * MIN_DEFECT_PERCENTAGE / 4)  # Much lower

            if confident_pixels > min_pixels or (confident_pixels > 0 and pixel_count > min_pixels):
                # Use confident mask if available, otherwise use class mask
                detection_mask = confident_mask if confident_pixels > 0 else class_mask

                # Find separate connected components
                separate_objects = find_separate_objects(detection_mask, class_name, h, w)
                
                print(f"  Found {len(separate_objects)} separate objects for {class_name}")

                for obj_idx, obj_info in enumerate(separate_objects):
                    # Calculate quality score for each object
                    obj_quality_score = calculate_multi_object_quality_score(
                        obj_info['mask'], class_name, h, w, confidence_scores, 
                        obj_info['pixel_count'], obj_info['confident_pixels']
                    )

                    print(f"    Object {obj_idx+1} quality score: {obj_quality_score:.3f}, area: {obj_info['area_percentage']:.1f}%")

                    # MUCH MORE PERMISSIVE multi-object validation
                    if is_valid_multi_object_candidate(obj_info['mask'], class_name, h, w, obj_info['area_percentage']):
                        all_detected_objects.append({
                            'class_name': class_name,
                            'class_id': class_id,
                            'object_id': obj_idx + 1,
                            'mask': obj_info['mask'],
                            'pixel_count': obj_info['pixel_count'],
                            'confident_pixels': obj_info['confident_pixels'],
                            'quality_score': obj_quality_score,
                            'area_percentage': obj_info['area_percentage'],
                            'confidence_avg': obj_info['confidence_avg'],
                            'bbox_info': obj_info['bbox_info']
                        })
                        print(f"    {class_name} object {obj_idx+1} ACCEPTED as valid candidate")
                    else:
                        print(f"    {class_name} object {obj_idx+1} rejected as invalid candidate")
            else:
                print(f"  {class_name} does not meet pixel criteria")

    # MULTI-OBJECT SELECTION: Process multiple objects per defect type
    if all_detected_objects:
        print(f"=== MULTI-OBJECT CANDIDATE PROCESSING ===")
        print(f"Total object candidates: {len(all_detected_objects)}")

        # Group objects by defect type
        objects_by_type = {}
        for obj in all_detected_objects:
            defect_type = obj['class_name']
            if defect_type not in objects_by_type:
                objects_by_type[defect_type] = []
            objects_by_type[defect_type].append(obj)

        # Process each defect type with multiple object support
        for defect_type, type_objects in objects_by_type.items():
            print(f"Processing {len(type_objects)} objects for {defect_type}")

            # Sort objects by quality and area
            type_objects.sort(key=lambda x: (x['area_percentage'], x['quality_score']), reverse=True)

            # Select best objects (up to 3 objects per type for performance)
            max_objects_per_type = 3
            selected_objects = type_objects[:max_objects_per_type]

            analysis['detected_defects'].append(defect_type)
            analysis['bounding_boxes'][defect_type] = []

            total_confident_pixels = 0
            total_pixels = 0
            all_confidences = []

            for obj_idx, obj in enumerate(selected_objects):
                # Extract bounding box for each object
                obj_bbox = extract_multi_object_bounding_box(
                    obj['mask'], defect_type, h, w, obj['confident_pixels'], 
                    confidence_scores, obj['object_id']
                )

                if obj_bbox:
                    # Add multi-object specific information
                    obj_bbox.update({
                        'multi_object_detection': True,
                        'object_id': obj['object_id'],
                        'object_index': obj_idx + 1,
                        'total_objects_this_type': len(selected_objects),
                        'selection_reason': f"multi_object_{obj_idx+1}_of_{len(selected_objects)}"
                    })

                    analysis['bounding_boxes'][defect_type].append(obj_bbox)
                    print(f"     Created bbox for {defect_type} object {obj['object_id']}")

                    total_confident_pixels += obj['confident_pixels']
                    total_pixels += obj['pixel_count']
                    all_confidences.append(obj['confidence_avg'])

            # Calculate statistics for all objects of this type
            if analysis['bounding_boxes'][defect_type]:
                analysis['defect_statistics'][defect_type] = {
                    'confident_pixels': int(total_confident_pixels),
                    'total_pixels': int(total_pixels),
                    'confidence_ratio': total_confident_pixels / total_pixels if total_pixels > 0 else 0,
                    'avg_confidence': np.mean(all_confidences) if all_confidences else 0,
                    'max_confidence': max(all_confidences) if all_confidences else 0,
                    'num_regions': len(analysis['bounding_boxes'][defect_type]),
                    'multi_object_detection': True,
                    'objects_detected': len(selected_objects),
                    'detection_method': 'multi_object_enhanced',
                    'total_area_percentage': sum(obj['area_percentage'] for obj in selected_objects)
                }

                # Multi-object spatial analysis
                analysis['spatial_analysis'][defect_type] = analyze_multi_object_spatial_distribution(
                    analysis['bounding_boxes'][defect_type], image_shape
                )

        analysis['total_objects_detected'] = sum(
            len(boxes) for boxes in analysis['bounding_boxes'].values()
        )

    print(f"=== MULTI-OBJECT DETECTION SUMMARY ===")
    print(f"Detected defect types: {analysis['detected_defects']}")
    print(f"Total objects detected: {analysis['total_objects_detected']}")
    print(f"Detection method: Multi-object enhanced detection")

    return analysis

def find_separate_objects(mask, defect_type, h, w):
    """Find separate connected components (objects) in the mask"""
    try:
        # Convert to uint8 if needed
        if mask.dtype != np.uint8:
            mask_uint8 = (mask * 255).astype(np.uint8)
        else:
            mask_uint8 = mask.copy()

        # Find connected components
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask_uint8, connectivity=8)

        separate_objects = []

        # Process each connected component (skip background label 0)
        for label_id in range(1, num_labels):
            component_mask = (labels == label_id)
            pixel_count = np.sum(component_mask)
            
            # Check minimum size for separate object
            min_object_pixels = max(MIN_DEFECT_PIXELS // 2, 25)  # Smaller threshold for individual objects
            
            if pixel_count >= min_object_pixels:
                area_percentage = (pixel_count / (h * w)) * 100
                
                # Get component statistics
                stat = stats[label_id]
                obj_x, obj_y, obj_w, obj_h, obj_area = stat
                
                # Calculate confidence for this component
                component_confidences = []
                y_coords, x_coords = np.where(component_mask)
                
                # Get confidence values for pixels in this component
                if len(x_coords) > 0:
                    # This is a placeholder - in real implementation, you'd use the actual confidence_scores
                    avg_confidence = 0.7  # Default confidence
                    confident_pixels = pixel_count  # Assume all pixels are confident
                else:
                    avg_confidence = 0.0
                    confident_pixels = 0

                bbox_info = {
                    'x': int(obj_x),
                    'y': int(obj_y),
                    'width': int(obj_w),
                    'height': int(obj_h),
                    'centroid_x': int(centroids[label_id][0]),
                    'centroid_y': int(centroids[label_id][1])
                }

                separate_objects.append({
                    'mask': component_mask,
                    'pixel_count': pixel_count,
                    'confident_pixels': confident_pixels,
                    'area_percentage': area_percentage,
                    'confidence_avg': avg_confidence,
                    'bbox_info': bbox_info,
                    'component_id': label_id
                })

        print(f"    Found {len(separate_objects)} separate objects for {defect_type}")
        return separate_objects

    except Exception as e:
        print(f"Error finding separate objects for {defect_type}: {e}")
        return []

def calculate_multi_object_quality_score(mask, defect_type, h, w, confidence_scores, pixel_count, confident_pixels):
    """Calculate quality score for individual objects in multi-object detection"""
    try:
        # Base score from confidence
        if confident_pixels > 0:
            y_coords, x_coords = np.where(mask)
            if len(x_coords) > 0:
                avg_confidence = np.mean(confidence_scores[mask])
                max_confidence = np.max(confidence_scores[mask])
                confidence_score = (avg_confidence + max_confidence) / 2
            else:
                confidence_score = 0.0
        else:
            confidence_score = 0.0

        # Multi-object area scoring - adjusted for individual objects
        area_percentage = (pixel_count / (h * w)) * 100

        # Individual object size ranges (smaller than single detection)
        if 0.05 < area_percentage < 5:
            area_score = 1.0  # Small individual objects
        elif 5 <= area_percentage < 15:
            area_score = 0.9  # Medium individual objects
        elif 15 <= area_percentage < 25:
            area_score = 0.7  # Large individual objects
        elif area_percentage >= 25:
            area_score = 0.3  # Very large (might be merged objects)
        else:
            area_score = 0.5  # Very small objects

        # Spatial compactness score for individual objects
        y_coords, x_coords = np.where(mask)
        if len(x_coords) > 0:
            # Check if object is reasonably compact
            x_span = np.max(x_coords) - np.min(x_coords)
            y_span = np.max(y_coords) - np.min(y_coords)

            bbox_area = (x_span + 1) * (y_span + 1)
            compactness = pixel_count / bbox_area if bbox_area > 0 else 0
            
            spatial_score = min(1.0, compactness * 2)  # Reward compact objects
        else:
            spatial_score = 0.0

        # Multi-object weighting (balanced scoring)
        quality_score = (confidence_score * 0.4 + area_score * 0.4 + spatial_score * 0.2)

        return quality_score

    except Exception as e:
        print(f"Error calculating multi-object quality score for {defect_type}: {e}")
        return 0.0

def is_valid_multi_object_candidate(mask, defect_type, h, w, area_percentage):
    """RELAXED: Validate individual objects in multi-object detection with more permissive thresholds"""
    try:
        # RELAXED individual object max area threshold
        if defect_type in ['damaged', 'missing_component']:
            individual_max_area = 85  # Much higher for damaged/missing items
        else:
            individual_max_area = 50  # Higher for other types

        if area_percentage > individual_max_area:
            print(f"    Rejecting {defect_type} object: covers {area_percentage:.1f}% (exceeds {individual_max_area}%)")
            return False

        # Individual object spatial validation - MORE PERMISSIVE
        y_coords, x_coords = np.where(mask)
        if len(x_coords) == 0:
            return False

        x_span = (np.max(x_coords) - np.min(x_coords)) / w
        y_span = (np.max(y_coords) - np.min(y_coords)) / h

        # RELAXED span thresholds
        if defect_type in ['damaged', 'missing_component']:
            individual_span_threshold = 0.95  # Very permissive for damaged items
        else:
            individual_span_threshold = 0.8   # More permissive for others

        if x_span > individual_span_threshold and y_span > individual_span_threshold:
            print(f"    Rejecting {defect_type} object: spans {x_span:.2f}x{y_span:.2f} (exceeds {individual_span_threshold})")
            return False

        # MUCH LOWER minimum size check
        min_area_threshold = 0.001  # Very low minimum
        if area_percentage < min_area_threshold:
            print(f"    Rejecting {defect_type} object: too small ({area_percentage:.3f}%)")
            return False

        return True

    except Exception as e:
        print(f"Error validating multi-object {defect_type}: {e}")
        return False

def extract_multi_object_bounding_box(mask, defect_type, h, w, total_pixels, confidence_scores, object_id):
    """Extract bounding box for individual objects in multi-object detection"""
    try:
        print(f"    Extracting multi-object bbox for {defect_type} object {object_id}...")

        # Convert to uint8 if needed
        if mask.dtype != np.uint8:
            mask_uint8 = (mask * 255).astype(np.uint8)
        else:
            mask_uint8 = mask.copy()

        # Find all object pixels
        y_coords, x_coords = np.where(mask_uint8 > 0)

        if len(x_coords) == 0 or len(y_coords) == 0:
            print(f"    No pixels found for {defect_type} object {object_id}")
            return None

        print(f"    Found {len(x_coords)} pixels for {defect_type} object {object_id}")

        # Precise bounding box calculation for individual objects
        min_x = int(np.min(x_coords))
        max_x = int(np.max(x_coords))
        min_y = int(np.min(y_coords))
        max_y = int(np.max(y_coords))

        width = max_x - min_x + 1
        height = max_y - min_y + 1
        area = len(x_coords)

        # Validate minimum area for individual objects
        if area < MIN_BBOX_AREA // 2:  # Smaller threshold for individual objects
            print(f"    Area {area} below minimum requirement {MIN_BBOX_AREA // 2}")
            return None

        # Calculate centroid
        cx = int(np.mean(x_coords))
        cy = int(np.mean(y_coords))

        # Ensure centroid is within bounds
        cx = max(min_x, min(max_x, cx))
        cy = max(min_y, min(max_y, cy))

        # Calculate metrics
        aspect_ratio = width / height if height > 0 else 1
        bbox_area = width * height
        compactness = area / bbox_area if bbox_area > 0 else 0

        # Calculate confidence for this specific object
        object_confidences = confidence_scores[mask_uint8 > 0]
        avg_confidence = float(np.mean(object_confidences)) if len(object_confidences) > 0 else 0.0
        max_confidence = float(np.max(object_confidences)) if len(object_confidences) > 0 else 0.0

        # Calculate area percentage
        area_percentage = (area / (h * w)) * 100

        # Create multi-object bounding box
        multi_object_bbox = {
            'id': object_id,
            'x': min_x,
            'y': min_y,
            'width': width,
            'height': height,
            'area': area,
            'area_percentage': float(area_percentage),
            'center_x': cx,
            'center_y': cy,
            'centroid': (cx, cy),
            'confidence': avg_confidence,
            'confidence_score': avg_confidence,
            'max_confidence': max_confidence,
            'aspect_ratio': float(aspect_ratio),
            'compactness': float(compactness),
            'relative_position': {
                'x_percent': (cx / w) * 100,
                'y_percent': (cy / h) * 100,
                'quadrant': get_quadrant(cx, cy, w, h)
            },
            'shape_type': classify_defect_shape_natural(width, height, aspect_ratio, compactness),
            'severity': calculate_defect_severity_natural(area_percentage),
            'coverage_type': 'multi_object_detection',
            'total_defect_pixels': area,
            'multi_object_detection': True,
            'individual_object': True,
            'object_id': object_id,
            'detection_method': 'multi_object_enhanced',
            'coordinates_validated': True,
            'within_image_bounds': True,
            'threshold_used': DEFECT_CONFIDENCE_THRESHOLD
        }

        print(f"    Created multi-object bbox for {defect_type} object {object_id}: {width}x{height} at ({min_x},{min_y}) covering {area} pixels ({area_percentage:.2f}%)")

        return multi_object_bbox

    except Exception as e:
        print(f"    Error extracting multi-object bbox for {defect_type} object {object_id}: {e}")
        return None

def analyze_multi_object_spatial_distribution(bboxes, image_shape):
    """Analyze spatial distribution of multiple objects"""
    try:
        if not bboxes:
            return {}

        h, w = image_shape[:2] if len(image_shape) >= 2 else (image_shape[0], 640)

        # Calculate distribution metrics
        centers_x = [bbox['center_x'] for bbox in bboxes]
        centers_y = [bbox['center_y'] for bbox in bboxes]

        spatial_analysis = {
            'object_count': len(bboxes),
            'distribution_pattern': determine_distribution_pattern(centers_x, centers_y, w, h),
            'coverage_area': calculate_total_coverage_area(bboxes, w, h),
            'object_density': len(bboxes) / ((w * h) / 10000),  # Objects per 100x100 area
            'spacing_analysis': analyze_object_spacing(centers_x, centers_y),
            'quadrant_distribution': analyze_quadrant_distribution(centers_x, centers_y, w, h),
            'edge_proximity_analysis': analyze_multi_object_edge_proximity(bboxes, w, h)
        }

        return spatial_analysis

    except Exception as e:
        print(f"Error analyzing multi-object spatial distribution: {e}")
        return {}

def determine_distribution_pattern(centers_x, centers_y, w, h):
    """Determine the spatial distribution pattern of objects"""
    if len(centers_x) < 2:
        return 'single_object'
    elif len(centers_x) == 2:
        return 'pair'
    
    # Calculate spread
    x_spread = (max(centers_x) - min(centers_x)) / w
    y_spread = (max(centers_y) - min(centers_y)) / h
    
    if x_spread > 0.6 and y_spread > 0.6:
        return 'scattered'
    elif x_spread > 0.6:
        return 'horizontal_line'
    elif y_spread > 0.6:
        return 'vertical_line'
    else:
        return 'clustered'

def calculate_total_coverage_area(bboxes, w, h):
    """Calculate total area covered by all objects"""
    total_pixels = sum(bbox['area'] for bbox in bboxes)
    total_percentage = (total_pixels / (w * h)) * 100
    
    return {
        'total_pixels': total_pixels,
        'total_percentage': round(total_percentage, 2),
        'average_object_size': round(total_percentage / len(bboxes), 2) if bboxes else 0
    }

def analyze_object_spacing(centers_x, centers_y):
    """Analyze spacing between objects"""
    if len(centers_x) < 2:
        return {'spacing': 'single_object'}
    
    # Calculate distances between all pairs
    distances = []
    for i in range(len(centers_x)):
        for j in range(i + 1, len(centers_x)):
            dist = np.sqrt((centers_x[i] - centers_x[j])**2 + (centers_y[i] - centers_y[j])**2)
            distances.append(dist)
    
    if distances:
        avg_distance = np.mean(distances)
        min_distance = min(distances)
        max_distance = max(distances)
        
        return {
            'average_distance': round(avg_distance, 1),
            'min_distance': round(min_distance, 1),
            'max_distance': round(max_distance, 1),
            'spacing_uniformity': 'uniform' if (max_distance - min_distance) < avg_distance * 0.5 else 'varied'
        }
    
    return {'spacing': 'unknown'}

def analyze_quadrant_distribution(centers_x, centers_y, w, h):
    """Analyze how objects are distributed across image quadrants"""
    mid_x, mid_y = w // 2, h // 2
    
    quadrant_counts = {
        'top_left': 0,
        'top_right': 0,
        'bottom_left': 0,
        'bottom_right': 0
    }
    
    for x, y in zip(centers_x, centers_y):
        if x < mid_x and y < mid_y:
            quadrant_counts['top_left'] += 1
        elif x >= mid_x and y < mid_y:
            quadrant_counts['top_right'] += 1
        elif x < mid_x and y >= mid_y:
            quadrant_counts['bottom_left'] += 1
        else:
            quadrant_counts['bottom_right'] += 1
    
    return quadrant_counts

def analyze_multi_object_edge_proximity(bboxes, w, h):
    """Analyze proximity of multiple objects to image edges"""
    edge_distance_threshold = 0.1
    
    edge_proximity = {
        'near_top': 0,
        'near_bottom': 0,
        'near_left': 0,
        'near_right': 0,
        'near_any_edge': 0
    }
    
    for bbox in bboxes:
        cx, cy = bbox['center_x'], bbox['center_y']
        near_edge = False
        
        if cy < h * edge_distance_threshold:
            edge_proximity['near_top'] += 1
            near_edge = True
        if cy > h * (1 - edge_distance_threshold):
            edge_proximity['near_bottom'] += 1
            near_edge = True
        if cx < w * edge_distance_threshold:
            edge_proximity['near_left'] += 1
            near_edge = True
        if cx > w * (1 - edge_distance_threshold):
            edge_proximity['near_right'] += 1
            near_edge = True
        
        if near_edge:
            edge_proximity['near_any_edge'] += 1
    
    return edge_proximity

def get_quadrant(x, y, width, height):
    """Determine which quadrant of the image the defect is in"""
    mid_x, mid_y = width // 2, height // 2

    if x < mid_x and y < mid_y:
        return "Top-Left"
    elif x >= mid_x and y < mid_y:
        return "Top-Right"
    elif x < mid_x and y >= mid_y:
        return "Bottom-Left"
    else:
        return "Bottom-Right"

def classify_defect_shape_natural(width, height, aspect_ratio, compactness):
    """Classify defect shape naturally (same logic for all types)"""
    if aspect_ratio > 3:
        return "Linear/Elongated"
    elif aspect_ratio > 1.8:
        return "Rectangular/Streak"
    elif compactness > 0.7:
        return "Compact/Circular"
    elif compactness < 0.3:
        return "Irregular/Distributed"
    else:
        return "Moderate/Oval"

def calculate_defect_severity_natural(area_percentage):
    """Calculate defect severity naturally (same logic for all types)"""
    if area_percentage < 0.5:
        return 'minor'
    elif area_percentage < 2.0:
        return 'moderate'
    elif area_percentage < 6.0:
        return 'significant'
    else:
        return 'critical'

def analyze_defect_location(bbox, image_shape):
    """Analyze spatial information for defect location"""
    cx, cy = bbox['center_x'], bbox['center_y']

    spatial_info = {
        'center_location': {
            'x': cx,
            'y': cy,
            'x_percent': bbox['relative_position']['x_percent'],
            'y_percent': bbox['relative_position']['y_percent']
        },
        'quadrant': bbox['relative_position']['quadrant'],
        'coverage': {
            'width_percent': (bbox['width'] / image_shape[1]) * 100 if len(image_shape) > 1 else 0,
            'height_percent': (bbox['height'] / image_shape[0]) * 100,
            'area_percent': bbox['area_percentage']
        },
        'edge_proximity': analyze_edge_proximity(bbox, image_shape),
        'natural_analysis': True,
        'total_regions_analyzed': 1
    }

    return spatial_info

def analyze_edge_proximity(bbox, image_shape):
    """Analyze proximity to image edges"""
    h, w = image_shape[:2] if len(image_shape) >= 2 else (image_shape[0], 640)

    edge_distance_threshold = 0.1
    cx, cy = bbox['center_x'], bbox['center_y']

    edges_near = []
    if cy < h * edge_distance_threshold:
        edges_near.append('top')
    if cy > h * (1 - edge_distance_threshold):
        edges_near.append('bottom')
    if cx < w * edge_distance_threshold:
        edges_near.append('left')
    if cx > w * (1 - edge_distance_threshold):
        edges_near.append('right')

    return {
        'near_edges': edges_near,
        'edge_count': len(edges_near),
        'is_edge_defect': len(edges_near) > 0,
        'distance_to_edges': {
            'top': cy / h * 100,
            'bottom': (h - cy) / h * 100,
            'left': cx / w * 100,
            'right': (w - cx) / w * 100
        }
    }

# Legacy functions for backward compatibility
def extract_enhanced_bounding_boxes(mask, defect_type):
    """Legacy function - now supports multi-object detection"""
    if np.sum(mask) == 0:
        print(f"No pixels found for {defect_type}, returning empty list")
        return []

    h, w = mask.shape[:2]
    confidence_scores = np.ones_like(mask, dtype=np.float32)
    
    # Use multi-object detection
    separate_objects = find_separate_objects(mask, defect_type, h, w)
    
    multi_object_bboxes = []
    for obj_idx, obj_info in enumerate(separate_objects):
        bbox = extract_multi_object_bounding_box(
            obj_info['mask'], defect_type, h, w, obj_info['pixel_count'], 
            confidence_scores, obj_idx + 1
        )
        if bbox:
            multi_object_bboxes.append(bbox)
    
    return multi_object_bboxes if multi_object_bboxes else []