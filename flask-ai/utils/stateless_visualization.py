"""
IMPROVED Product-aware visualization with:
1. INTELLIGENT DEFECT FILTERING - Reduce random bounding boxes
2. MULTI-PRODUCT DETECTION - Individual product borders
3. SMART DEFECT GROUPING - Merge overlapping/nearby defects
"""

import cv2
import numpy as np
import base64
import logging
from config import DEFECT_COLORS, SPECIFIC_DEFECT_CLASSES

logger = logging.getLogger(__name__)

def create_annotated_image_base64(image_path, result):
    """Create base64 encoded annotated image with improved defect filtering and multi-product support"""
    try:
        # Load original image
        image = cv2.imread(image_path)
        if image is None:
            logger.warning(f"Could not load image for annotation: {image_path}")
            return None
        
        # Create annotated version with IMPROVED filtering and multi-product borders
        annotated_image = annotate_detection_result_improved_multi_product(image, result)
        
        # Encode to base64
        _, buffer = cv2.imencode('.jpg', annotated_image, [cv2.IMWRITE_JPEG_QUALITY, 85])
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return image_base64
        
    except Exception as e:
        logger.error(f"Error creating annotated image: {e}")
        return None

def annotate_detection_result_improved_multi_product(image, result):
    """IMPROVED: Add annotations with intelligent filtering and multi-product borders"""
    try:
        annotated_frame = image.copy()
        height, width = annotated_frame.shape[:2]
        
        if result:
            # STEP 1: Detect individual products in the image
            product_regions = detect_individual_products(image)
            
            # STEP 2: Assess each product individually
            if len(product_regions) > 1:
                # Multiple products - individual assessment
                annotate_multiple_products_individually(annotated_frame, result, product_regions)
            else:
                # Single product - standard processing with improved filtering
                annotate_single_product_improved(annotated_frame, result, product_regions[0] if product_regions else None)
            
            # STEP 3: Draw FILTERED defect bounding boxes (MUCH fewer, more accurate)
            if result['final_decision'] == 'DEFECT':
                draw_intelligent_filtered_defect_boxes(annotated_frame, result)
        
        return annotated_frame
        
    except Exception as e:
        logger.error(f"Error annotating detection result: {e}")
        return image

def detect_individual_products(image):
    """Detect individual product regions in the image"""
    try:
        height, width = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Enhanced edge detection for product separation
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 30, 100)
        
        # Morphological operations to connect product boundaries
        kernel = np.ones((5, 5), np.uint8)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        edges = cv2.dilate(edges, kernel, iterations=2)
        
        # Find contours for individual products
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        product_regions = []
        min_product_area = (width * height) * 0.05  # Minimum 5% of image
        max_product_area = (width * height) * 0.8   # Maximum 80% of image
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if min_product_area < area < max_product_area:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Validate aspect ratio and position
                aspect_ratio = w / h if h > 0 else 0
                margin = min(width, height) * 0.03
                
                if (0.2 < aspect_ratio < 5.0 and  # Reasonable aspect ratio
                    x > margin and y > margin and 
                    x + w < width - margin and y + h < height - margin):
                    
                    product_regions.append({
                        'x': x, 'y': y, 'width': w, 'height': h,
                        'center_x': x + w // 2, 'center_y': y + h // 2,
                        'area': area, 'contour': contour
                    })
        
        # If no products detected, use whole image as single product
        if not product_regions:
            margin = min(width, height) * 0.05
            product_regions = [{
                'x': margin, 'y': margin, 
                'width': width - 2*margin, 'height': height - 2*margin,
                'center_x': width // 2, 'center_y': height // 2,
                'area': (width - 2*margin) * (height - 2*margin)
            }]
        
        # Sort by area (largest first) and limit to max 3 products for performance
        product_regions.sort(key=lambda x: x['area'], reverse=True)
        return product_regions[:3]
        
    except Exception as e:
        logger.error(f"Error detecting individual products: {e}")
        # Fallback to whole image
        margin = min(image.shape[1], image.shape[0]) * 0.05
        return [{
            'x': int(margin), 'y': int(margin), 
            'width': int(image.shape[1] - 2*margin), 
            'height': int(image.shape[0] - 2*margin),
            'center_x': image.shape[1] // 2, 
            'center_y': image.shape[0] // 2
        }]

def annotate_multiple_products_individually(image, result, product_regions):
    """Annotate multiple products with individual borders based on their defect status"""
    try:
        logger.info(f"Annotating {len(product_regions)} individual products")
        
        # Get filtered defect locations
        defect_locations = get_filtered_defect_locations(result)
        
        for i, product in enumerate(product_regions):
            # Check if this product has defects
            product_has_defects = check_product_has_defects(product, defect_locations)
            
            # Determine border color and thickness
            if product_has_defects:
                border_color = (0, 0, 255)  # Red for defect
                border_thickness = 6
                corner_color = (0, 0, 200)
            else:
                border_color = (0, 255, 0)  # Green for good
                border_thickness = 4  
                corner_color = (0, 200, 0)
            
            # Draw individual product border
            draw_product_border_improved(image, product, border_color, border_thickness, corner_color)
            
            # Add product label
            label = f"PRODUCT {i+1}: {'DEFECT' if product_has_defects else 'GOOD'}"
            label_x = product['x'] + 10
            label_y = product['y'] + 25
            
            # Background for text
            text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(image, (label_x - 5, label_y - 20), 
                         (label_x + text_size[0] + 5, label_y + 5), border_color, -1)
            cv2.putText(image, label, (label_x, label_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
        logger.info(f"Multi-product annotation completed for {len(product_regions)} products")
        
    except Exception as e:
        logger.error(f"Error annotating multiple products: {e}")

def annotate_single_product_improved(image, result, product_region):
    """Annotate single product with improved border"""
    try:
        if result['final_decision'] == 'GOOD':
            border_color = (0, 255, 0)  # Green
            border_thickness = 5
        else:
            border_color = (0, 0, 255)  # Red 
            border_thickness = 7
            
        # Use detected product region or fallback to image border
        if product_region:
            draw_product_border_improved(image, product_region, border_color, border_thickness, border_color)
        else:
            # Fallback to full image border
            image = cv2.copyMakeBorder(image, border_thickness, border_thickness, 
                                     border_thickness, border_thickness, 
                                     cv2.BORDER_CONSTANT, value=border_color)
        
    except Exception as e:
        logger.error(f"Error annotating single product: {e}")

def get_filtered_defect_locations(result):
    """Get FILTERED defect locations (reduce random boxes)"""
    try:
        defect_locations = []
        
        defect_classification = result.get('defect_classification', {})
        if 'defect_analysis' in defect_classification:
            bounding_boxes = defect_classification['defect_analysis'].get('bounding_boxes', {})
        else:
            bounding_boxes = defect_classification.get('bounding_boxes', {})
            
        for defect_type, boxes in bounding_boxes.items():
            if defect_type == 'background':
                continue
                
            # INTELLIGENT FILTERING - Only keep high-quality detections
            filtered_boxes = filter_high_quality_defects(boxes, defect_type)
            
            for box in filtered_boxes:
                defect_locations.append({
                    'type': defect_type,
                    'x': box['x'], 'y': box['y'],
                    'width': box['width'], 'height': box['height'],
                    'center_x': box.get('center_x', box['x'] + box['width']//2),
                    'center_y': box.get('center_y', box['y'] + box['height']//2),
                    'confidence': box.get('confidence', 0),
                    'area_percentage': box.get('area_percentage', 0)
                })
        
        return defect_locations
        
    except Exception as e:
        logger.error(f"Error getting filtered defect locations: {e}")
        return []

def filter_high_quality_defects(boxes, defect_type):
    """RELAXED FILTERING: Show more defect boxes but still intelligent"""
    try:
        if not boxes:
            return []
            
        # Step 1: RELAXED confidence and area thresholds
        quality_filtered = []
        for box in boxes:
            confidence = box.get('confidence', 0)
            area_pct = box.get('area_percentage', 0)
            
            # MUCH MORE RELAXED thresholds per defect type
            if defect_type in ['missing_component', 'damaged']:
                min_confidence = 0.15  # Lowered from 0.4
                min_area = 0.01       # Lowered from 0.1  
                max_area = 25.0       # Increased from 15.0
            elif defect_type in ['open']:
                min_confidence = 0.15  # Lowered from 0.5
                min_area = 0.005      # Lowered from 0.05
                max_area = 15.0       # Increased from 8.0
            elif defect_type in ['scratch']:
                min_confidence = 0.10  # Lowered from 0.3
                min_area = 0.005      # Lowered from 0.02
                max_area = 10.0       # Increased from 5.0
            else:  # stained, etc
                min_confidence = 0.15  # Lowered from 0.35
                min_area = 0.01       # Lowered from 0.08
                max_area = 20.0       # Increased from 10.0
                
            if (confidence >= min_confidence and 
                min_area <= area_pct <= max_area):
                quality_filtered.append(box)
        
        # Step 2: RELAXED NMS (keep more overlapping boxes)
        nms_filtered = apply_relaxed_nms(quality_filtered)
        
        # Step 3: Show more boxes per type (3-4 instead of 2)
        nms_filtered.sort(key=lambda x: (x.get('confidence', 0) + x.get('area_percentage', 0)/10), reverse=True)
        max_boxes = 4 if defect_type in ['damaged', 'missing_component'] else 3
        final_filtered = nms_filtered[:max_boxes]
        
        logger.info(f"RELAXED Filtered {defect_type}: {len(boxes)} -> {len(final_filtered)} boxes")
        return final_filtered
        
    except Exception as e:
        logger.error(f"Error in relaxed filtering for {defect_type}: {e}")
        # FALLBACK: If error, return top 2 boxes instead of empty
        return sorted(boxes, key=lambda x: x.get('confidence', 0), reverse=True)[:2]
    
def apply_relaxed_nms(boxes):
    """RELAXED NMS: Keep more overlapping boxes"""
    try:
        if len(boxes) <= 1:
            return boxes
            
        # Convert to NMS format
        nms_boxes = []
        scores = []
        
        for box in boxes:
            x, y, w, h = box['x'], box['y'], box['width'], box['height']
            nms_boxes.append([x, y, x + w, y + h])
            scores.append(box.get('confidence', 0.5))
        
        nms_boxes = np.array(nms_boxes, dtype=np.float32)
        scores = np.array(scores, dtype=np.float32)
        
        # RELAXED NMS thresholds (keep more boxes)
        score_threshold = 0.1   # Lower score threshold
        nms_threshold = 0.6     # Higher NMS threshold (allow more overlap)
        
        indices = cv2.dnn.NMSBoxes(nms_boxes, scores, score_threshold, nms_threshold)
        
        filtered_boxes = []
        if len(indices) > 0:
            indices = indices.flatten()
            for i in indices:
                filtered_boxes.append(boxes[i])
                
        return filtered_boxes
        
    except Exception as e:
        logger.error(f"Error in relaxed NMS: {e}")
        return boxes

def apply_smart_nms(boxes):
    """Apply smart Non-Maximum Suppression to remove overlapping boxes"""
    try:
        if len(boxes) <= 1:
            return boxes
            
        # Convert to NMS format
        nms_boxes = []
        scores = []
        
        for box in boxes:
            x, y, w, h = box['x'], box['y'], box['width'], box['height']
            nms_boxes.append([x, y, x + w, y + h])
            scores.append(box.get('confidence', 0.5))
        
        nms_boxes = np.array(nms_boxes, dtype=np.float32)
        scores = np.array(scores, dtype=np.float32)
        
        # Apply NMS with moderate threshold
        indices = cv2.dnn.NMSBoxes(nms_boxes, scores, 0.3, 0.4)
        
        filtered_boxes = []
        if len(indices) > 0:
            indices = indices.flatten()
            for i in indices:
                filtered_boxes.append(boxes[i])
                
        return filtered_boxes
        
    except Exception as e:
        logger.error(f"Error in smart NMS: {e}")
        return boxes

def check_product_has_defects(product, defect_locations):
    """Check if a specific product region contains defects"""
    try:
        product_x1 = product['x']
        product_y1 = product['y'] 
        product_x2 = product['x'] + product['width']
        product_y2 = product['y'] + product['height']
        
        for defect in defect_locations:
            defect_center_x = defect['center_x']
            defect_center_y = defect['center_y']
            
            # Check if defect center is inside this product region
            if (product_x1 <= defect_center_x <= product_x2 and 
                product_y1 <= defect_center_y <= product_y2):
                return True
                
        return False
        
    except Exception as e:
        logger.error(f"Error checking product defects: {e}")
        return False

def draw_product_border_improved(image, product, border_color, thickness, corner_color):
    """Draw improved product border with enhanced corners"""
    try:
        x, y, w, h = product['x'], product['y'], product['width'], product['height']
        
        # Main border rectangle
        cv2.rectangle(image, (x, y), (x + w, y + h), border_color, thickness)
        
        # Enhanced corner markers
        corner_size = min(w, h) // 15
        corner_thickness = thickness + 2
        
        # Top-left corner
        cv2.line(image, (x, y), (x + corner_size, y), corner_color, corner_thickness)
        cv2.line(image, (x, y), (x, y + corner_size), corner_color, corner_thickness)
        
        # Top-right corner  
        cv2.line(image, (x + w, y), (x + w - corner_size, y), corner_color, corner_thickness)
        cv2.line(image, (x + w, y), (x + w, y + corner_size), corner_color, corner_thickness)
        
        # Bottom-left corner
        cv2.line(image, (x, y + h), (x + corner_size, y + h), corner_color, corner_thickness)
        cv2.line(image, (x, y + h), (x, y + h - corner_size), corner_color, corner_thickness)
        
        # Bottom-right corner
        cv2.line(image, (x + w, y + h), (x + w - corner_size, y + h), corner_color, corner_thickness)
        cv2.line(image, (x + w, y + h), (x + w, y + h - corner_size), corner_color, corner_thickness)
        
    except Exception as e:
        logger.error(f"Error drawing product border: {e}")

def draw_intelligent_filtered_defect_boxes(image, result):
    """Draw RELAXED filtered defect bounding boxes - Show more boxes"""
    try:
        defect_classification = result.get('defect_classification', {})
        
        if 'defect_analysis' in defect_classification:
            bounding_boxes = defect_classification['defect_analysis'].get('bounding_boxes', {})
        else:
            bounding_boxes = defect_classification.get('bounding_boxes', {})
            
        total_boxes_drawn = 0
        
        for defect_type, boxes in bounding_boxes.items():
            if defect_type == 'background':
                continue
                
            # RELAXED FILTERING - Show more boxes
            filtered_boxes = filter_high_quality_defects(boxes, defect_type)
            
            # FALLBACK: If filtering too aggressive, show at least 1 box
            if not filtered_boxes and boxes:
                # Take the box with highest confidence or area
                best_box = max(boxes, key=lambda x: (x.get('confidence', 0) + x.get('area_percentage', 0)/100))
                filtered_boxes = [best_box]
                logger.info(f"Fallback: Showing 1 {defect_type} box to prevent empty result")
            
            if not filtered_boxes:
                continue
                
            # Get color for this defect type
            color = get_defect_color(defect_type)
            
            # Draw the filtered boxes
            for i, bbox in enumerate(filtered_boxes):
                x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
                
                # Vary color slightly for multiple boxes of same type
                if len(filtered_boxes) > 1:
                    draw_color = vary_color(color, i)
                else:
                    draw_color = color
                
                # Draw main bounding box
                thickness = 3
                cv2.rectangle(image, (x, y), (x + w, y + h), draw_color, thickness)
                
                # Draw corner markers for better visibility
                corner_size = min(w, h) // 10
                if corner_size > 3:
                    draw_defect_corner_markers(image, x, y, w, h, draw_color, thickness, corner_size)
                
                # Compact label
                label = f"{defect_type.upper()[:4]}"
                if len(filtered_boxes) > 1:
                    label += f"#{i+1}"
                
                # Add confidence info
                conf = bbox.get('confidence', 0)
                area = bbox.get('area_percentage', 0)
                if conf > 0:
                    label += f" {conf:.2f}"
                
                # Label with background
                label_y = max(y - 5, 15)
                text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)[0]
                cv2.rectangle(image, (x, label_y - text_size[1] - 2), 
                             (x + text_size[0] + 4, label_y + 2), draw_color, -1)
                cv2.putText(image, label, (x + 2, label_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
                
                total_boxes_drawn += 1
        
        logger.info(f"Drew {total_boxes_drawn} RELAXED filtered defect boxes")
        
        # ADDITIONAL FALLBACK: If still no boxes drawn but defects detected
        if total_boxes_drawn == 0:
            detected_defects = result.get('detected_defect_types', [])
            if detected_defects:
                logger.warning(f"NO BOXES DRAWN but defects detected: {detected_defects}")
                # Draw simple text indication
                cv2.putText(image, f"DEFECTS: {', '.join(detected_defects[:2])}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
    except Exception as e:
        logger.error(f"Error drawing relaxed filtered defect boxes: {e}")

def get_defect_color(defect_type):
    """Get color for defect type from config"""
    try:
        # Map defect type to class ID
        for class_id, class_name in SPECIFIC_DEFECT_CLASSES.items():
            if class_name == defect_type:
                if class_id in DEFECT_COLORS:
                    return DEFECT_COLORS[class_id]
                    
        # Fallback colors
        color_map = {
            'scratch': (0, 255, 255),      # Cyan
            'stained': (128, 0, 128),      # Purple  
            'damaged': (255, 0, 0),        # Red
            'missing_component': (255, 255, 0),  # Yellow
            'open': (255, 0, 255),         # Magenta
        }
        return color_map.get(defect_type, (255, 255, 255))  # White default
        
    except Exception as e:
        logger.error(f"Error getting defect color: {e}")
        return (255, 255, 255)

def vary_color(base_color, index):
    """Create slight color variation for multiple boxes"""
    try:
        b, g, r = base_color
        factor = 0.7 + (index * 0.3) % 0.6  # Variation factor
        
        new_b = min(255, max(50, int(b * factor)))
        new_g = min(255, max(50, int(g * factor)))
        new_r = min(255, max(50, int(r * factor)))
        
        return (new_b, new_g, new_r)
        
    except Exception as e:
        logger.error(f"Error varying color: {e}")
        return base_color

def draw_defect_corner_markers(image, x, y, w, h, color, thickness, corner_size):
    """Draw corner markers for defect boxes"""
    try:
        marker_thickness = thickness + 1
        
        # Top-left
        cv2.line(image, (x, y), (x + corner_size, y), color, marker_thickness)
        cv2.line(image, (x, y), (x, y + corner_size), color, marker_thickness)
        
        # Top-right
        cv2.line(image, (x + w, y), (x + w - corner_size, y), color, marker_thickness)
        cv2.line(image, (x + w, y), (x + w, y + corner_size), color, marker_thickness)
        
        # Bottom-right
        cv2.line(image, (x + w, y + h), (x + w - corner_size, y + h), color, marker_thickness)
        cv2.line(image, (x + w, y + h), (x + w, y + h - corner_size), color, marker_thickness)
        
        # Bottom-left
        cv2.line(image, (x, y + h), (x + corner_size, y + h), color, marker_thickness)
        cv2.line(image, (x, y + h), (x, y + h - corner_size), color, marker_thickness)
        
    except Exception as e:
        logger.error(f"Error drawing corner markers: {e}")

# Utility functions for backward compatibility
def count_total_detected_objects(result):
    """Count total objects with improved filtering"""
    try:
        defect_classification = result.get('defect_classification', {})
        
        if 'defect_analysis' in defect_classification:
            bounding_boxes = defect_classification['defect_analysis'].get('bounding_boxes', {})
        else:
            bounding_boxes = defect_classification.get('bounding_boxes', {})
        
        total_filtered = 0
        for defect_type, boxes in bounding_boxes.items():
            if defect_type != 'background':
                filtered = filter_high_quality_defects(boxes, defect_type)
                total_filtered += len(filtered)
        
        return total_filtered
    
    except Exception as e:
        logger.error(f"Error counting filtered objects: {e}")
        return 0