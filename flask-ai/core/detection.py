# core/detection.py - Enhanced with Natural OpenAI Prompts (API Response Fields UNCHANGED)
"""
Core detection logic with OpenAI analysis integration 
ENHANCED with natural RAG prompts that don't bias toward specific defect types
API response structure remains completely unchanged - only internal logic modified
"""

import cv2
import torch
import numpy as np
import albumentations as A
from albumentations.pytorch import ToTensorV2
from openai import OpenAI
import base64
import io
from PIL import Image
from config import *


class DetectionCore:
    """Core detection functionality with natural OpenAI integration - API compatible"""
    
    def __init__(self, anomalib_model, hrnet_model, device='cuda'):
        self.anomalib_model = anomalib_model
        self.hrnet_model = hrnet_model
        self.device = device
        
        # Setup OpenAI 1.x client
        if OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
            self.openai_enabled = True
            print("OpenAI client initialized with natural prompts (API response unchanged)")
        else:
            self.openai_client = None
            self.openai_enabled = False
            print("Warning: OpenAI API key not found")
        
        # Preprocessing for HRNet
        self.hrnet_transform = A.Compose([
            A.Resize(*IMAGE_SIZE),
            A.Normalize(mean=NORMALIZE_MEAN, std=NORMALIZE_STD),
            ToTensorV2()
        ])
    
    def detect_anomaly(self, image_path):
        """
        Layer 1: Anomaly detection with natural OpenAI analysis
        API response structure: UNCHANGED
        """
        if not self.anomalib_model:
            raise ValueError("Anomalib model not loaded")
        
        try:
            # Run Anomalib inference
            result = self.anomalib_model.predict(image=image_path)
            
            # Process anomaly results - SAME API STRUCTURE
            if isinstance(result.pred_score, torch.Tensor):
                anomaly_score = float(result.pred_score.cpu().item())
            else:
                anomaly_score = float(result.pred_score)
                
            if isinstance(result.pred_label, torch.Tensor):
                is_anomalous = bool(result.pred_label.cpu().item())
            else:
                is_anomalous = bool(result.pred_label)
            
            # Get anomaly mask if available - SAME API STRUCTURE
            anomaly_mask = None
            if hasattr(result, 'pred_mask') and result.pred_mask is not None:
                if isinstance(result.pred_mask, torch.Tensor):
                    anomaly_mask = result.pred_mask.cpu().numpy()
                else:
                    anomaly_mask = result.pred_mask
                
                if len(anomaly_mask.shape) > 2:
                    anomaly_mask = anomaly_mask[0]
            
            # SAME API RESPONSE STRUCTURE
            base_result = {
                'is_anomalous': is_anomalous,
                'anomaly_score': anomaly_score,
                'anomaly_mask': anomaly_mask,
                'threshold_used': ANOMALY_THRESHOLD,
                'decision': 'DEFECT' if (is_anomalous and anomaly_score > ANOMALY_THRESHOLD) else 'GOOD'
            }
            
            # Natural OpenAI Layer 1 Analysis - INTERNAL ONLY
            if self.openai_enabled:
                print(f"Running natural OpenAI anomaly analysis (score: {anomaly_score:.3f})")
                openai_analysis = self._analyze_anomaly_with_natural_openai(image_path, base_result)
                base_result['openai_analysis'] = openai_analysis  # SAME API FIELD
                
                # Apply enhanced decision logic - SAME API FIELD NAMES
                enhanced_decision = self._apply_natural_anomaly_decision(base_result, openai_analysis)
                base_result['decision'] = enhanced_decision  # SAME API FIELD
            
            return base_result
            
        except Exception as e:
            print(f"Error in anomaly detection: {e}")
            return None
    
    def classify_defects(self, image_path, region_mask=None):
        """
        Layer 2: Defect classification with natural OpenAI analysis
        API response structure: UNCHANGED
        """
        if not self.hrnet_model:
            raise ValueError("HRNet model not loaded")
        
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            original_size = image_rgb.shape[:2]
            
            # Apply region mask if provided
            if region_mask is not None:
                region_mask = cv2.resize(region_mask, (original_size[1], original_size[0]))
                masked_image = image_rgb.copy()
                masked_image[region_mask < 0.5] = 0
                image_rgb = masked_image
            
            # Preprocess for HRNet
            transformed = self.hrnet_transform(image=image_rgb)
            input_tensor = transformed['image'].unsqueeze(0).to(self.device)
            
            # HRNet inference
            with torch.no_grad():
                output = self.hrnet_model(input_tensor)
                predictions = torch.softmax(output, dim=1)
                predicted_mask = torch.argmax(predictions, dim=1).squeeze().cpu().numpy()
                confidence_scores = torch.max(predictions, dim=1)[0].squeeze().cpu().numpy()
            
            # Resize predictions to original size
            predicted_mask = cv2.resize(predicted_mask.astype(np.uint8), 
                                      (original_size[1], original_size[0]), 
                                      interpolation=cv2.INTER_NEAREST)
            confidence_scores = cv2.resize(confidence_scores, 
                                         (original_size[1], original_size[0]), 
                                         interpolation=cv2.INTER_LINEAR)
            
            # Use natural enhanced detection - SAME API RESPONSE STRUCTURE
            from core.enhanced_detection import analyze_defect_predictions_enhanced
            defect_analysis = analyze_defect_predictions_enhanced(predicted_mask, confidence_scores, original_size)
            
            # SAME API RESPONSE STRUCTURE
            base_result = {
                'predicted_mask': predicted_mask,
                'confidence_scores': confidence_scores,
                'defect_analysis': defect_analysis,
                'detected_defects': defect_analysis['detected_defects'],
                'bounding_boxes': defect_analysis['bounding_boxes'],
                'class_distribution': defect_analysis['class_distribution']
            }
            
            # Natural OpenAI Layer 2 Analysis - INTERNAL LOGIC ONLY
            if self.openai_enabled and defect_analysis['detected_defects']:
                print(f"Running natural OpenAI defect classification")
                openai_analysis = self._analyze_defects_with_natural_openai(image_path, base_result)
                base_result['openai_analysis'] = openai_analysis  # SAME API FIELD
                
                # Apply OpenAI corrections if available - SAME API STRUCTURE
                if openai_analysis.get('bbox_corrections') or openai_analysis.get('type_corrections'):
                    corrections = {
                        'bbox_corrections': openai_analysis.get('bbox_corrections', {}),
                        'type_corrections': openai_analysis.get('type_corrections', {})
                    }
                    base_result = self._apply_openai_corrections(base_result, corrections)
            
            return base_result
            
        except Exception as e:
            print(f"Error in defect classification: {e}")
            return None
    
    def _analyze_anomaly_with_natural_openai(self, image_path, anomaly_result):
        """Natural OpenAI analysis for Layer 1 - no type bias"""
        try:
            if not self.openai_client:
                return {
                    'analysis': 'OpenAI client not initialized',
                    'confidence_percentage': 0,
                    'error': 'No OpenAI client'
                }
            
            # Encode image to base64
            image_base64 = self._encode_image_to_base64(image_path)
            
            # NATURAL RAG prompt - no type preference
            prompt = f"""OBJECTIVE PACKAGING QUALITY INSPECTION

MISSION: Provide unbiased assessment of packaging quality based on visual evidence.

CURRENT AI MODEL DETECTION RESULTS:
- Anomaly Score: {anomaly_result['anomaly_score']:.3f}
- Model Decision: {anomaly_result['decision']}
- Detection Threshold: {anomaly_result['threshold_used']}

NATURAL INSPECTION CRITERIA (No Type Preference):

1. STRUCTURAL INTEGRITY:
   - Look for any deformation, damage, or shape irregularities
   - Assess overall structural soundness
   - Check for any compromise in packaging strength

2. SURFACE CONDITION:
   - Examine surface quality and texture
   - Look for any marks, scratches, or discoloration
   - Assess printing/labeling quality

3. COMPLETENESS:
   - Check if all expected components are present
   - Look for missing elements or parts
   - Verify closure and sealing integrity

4. CLEANLINESS AND CONTAMINATION:
   - Assess overall cleanliness
   - Look for stains, spots, or foreign materials
   - Check for any contamination signs

5. FUNCTIONAL INTEGRITY:
   - Evaluate if packaging can perform its intended function
   - Check for any openings or breaches
   - Assess protective capability

OBJECTIVE DECISION LOGIC:
- Base assessment on what you actually observe
- Consider the anomaly score as supporting evidence
- Focus on packaging functionality and consumer acceptability
- Be neither overly strict nor overly lenient
- Consider real-world quality standards

CRITICAL INSTRUCTIONS:
- Provide honest, objective assessment
- Don't favor or avoid any particular defect type
- Focus on overall package quality
- Consider consumer and safety perspectives
- Be consistent in your evaluation standards

RESPONSE FORMAT:
Provide confidence percentage (0-100%) and detailed reasoning for your assessment.
Describe what you observe without predetermined bias toward any defect category."""

            print("Calling OpenAI API with natural RAG prompt...")
            response = self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                        ]
                    }
                ],
                max_tokens=OPENAI_MAX_TOKENS,
                temperature=0.1  # Consistent analysis
            )
            
            analysis_text = response.choices[0].message.content
            confidence = self._extract_confidence_percentage(analysis_text)
            
            print(f"Natural OpenAI anomaly analysis completed - confidence: {confidence}%")
            
            # SAME API RESPONSE STRUCTURE
            return {
                'analysis': analysis_text,
                'confidence_percentage': confidence,
                'model_used': OPENAI_MODEL,
                'layer': 'anomaly_detection',
                'natural_analysis': True
            }
            
        except Exception as e:
            print(f"Natural OpenAI anomaly analysis error: {e}")
            return {
                'analysis': f'OpenAI analysis failed: {str(e)}',
                'confidence_percentage': 0,
                'error': str(e)
            }
    
    def _analyze_defects_with_natural_openai(self, image_path, defect_result):
        """Natural OpenAI analysis for Layer 2 - unbiased defect classification"""
        try:
            if not self.openai_client:
                return {
                    'analysis': 'OpenAI client not initialized',
                    'confidence_percentage': 0,
                    'error': 'No OpenAI client'
                }
            
            image_base64 = self._encode_image_to_base64(image_path)
            
            detected_defects = defect_result['detected_defects']
            bounding_boxes = defect_result.get('bounding_boxes', {})
            
            # Create detailed bounding box information
            bbox_info = ""
            total_bboxes = 0
            for defect_type, boxes in bounding_boxes.items():
                bbox_info += f"\n{defect_type.upper()}: {len(boxes)} regions detected"
                total_bboxes += len(boxes)
                for i, bbox in enumerate(boxes):
                    x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
                    area_pct = bbox.get('area_percentage', 0)
                    conf = bbox.get('confidence', 0)
                    bbox_info += f"\n  Region {i+1}: Box({x},{y},{w},{h}) Area({area_pct:.1f}%) Conf({conf:.3f})"
            
            # NATURAL RAG prompt for defect classification - NO TYPE BIAS
            prompt = f"""EXPERT DEFECT CLASSIFICATION - OBJECTIVE ANALYSIS

MISSION: Accurately identify and classify defects based purely on visual evidence without bias.

AI MODEL DETECTION RESULTS:
DETECTED DEFECTS: {', '.join(detected_defects) if detected_defects else 'None detected'}
TOTAL BOUNDING BOXES: {total_bboxes}
DETAILED ANALYSIS:{bbox_info if bbox_info else ' None provided'}

OBJECTIVE DEFECT CLASSIFICATION GUIDE:

1. VISUAL ANALYSIS APPROACH:
   - Examine each detected region carefully
   - Base classification on actual visible characteristics
   - Don't assume or prefer any particular defect type
   - Focus on what you can clearly observe

2. DEFECT TYPE CHARACTERISTICS:

   OPEN DEFECTS:
   - Visible holes, tears, or punctures
   - Areas where interior/background shows through
   - Breach in packaging material
   Visual clues: Dark openings, see-through areas, torn edges

   SCRATCH DEFECTS:
   - Linear surface marks or abrasions
   - Scuff marks or surface texture changes
   - Scraping damage on surface
   Visual clues: Line patterns, surface disruption

   STAINED DEFECTS:
   - Discoloration or color variations
   - Spots, marks, or contamination
   - Color inconsistencies
   Visual clues: Color differences, spots, uneven appearance

   DAMAGED DEFECTS:
   - Structural deformation or crushing
   - Shape irregularities or dents
   - Physical impact damage
   Visual clues: Shape distortion, deformed areas

   MISSING_COMPONENT DEFECTS:
   - Absent parts, labels, or elements
   - Incomplete packaging components
   - Empty spaces where something should be
   Visual clues: Empty areas, missing elements

3. CLASSIFICATION PRINCIPLES:
   - Trust your visual assessment over model predictions
   - Look for distinctive characteristics of each type
   - Consider the context and overall appearance
   - Be objective and consistent
   - Don't force classifications if unclear

4. BOUNDING BOX VALIDATION:
   - Check if boxes are positioned on actual defects
   - Verify coordinates make sense for the defect type
   - Assess if box size matches the defect characteristics
   - Look for any obviously misplaced boxes

QUALITY ASSESSMENT TASKS:
1. Examine each detected region visually
2. Classify based on observable characteristics
3. Validate bounding box positioning and size
4. Provide corrections only if clearly warranted

WHAT DO YOU ACTUALLY SEE?
Describe the defects based on visual evidence:
- Physical openings or holes → "open"
- Surface marks or lines → "scratch"  
- Color variations or spots → "stained"
- Shape deformation → "damaged"
- Missing elements → "missing_component"

CORRECTION FORMAT (only if clearly needed):
CORRECT_TYPE: [actual_defect_type] - [visual reasoning]
BBOX_CORRECTION: [defect_type]: x,y,width,height - [specific reason]

Focus on objective analysis based on what you actually observe in the image."""

            print("Calling OpenAI API for natural defect classification...")
            response = self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                        ]
                    }
                ],
                max_tokens=OPENAI_MAX_TOKENS,
                temperature=0.1  # Consistent analysis
            )
            
            analysis_text = response.choices[0].message.content
            confidence = self._extract_confidence_percentage(analysis_text)
            bbox_confidence = self._extract_bbox_confidence(analysis_text)
            
            # Extract corrections from OpenAI response
            corrections = self._extract_bbox_corrections(analysis_text)
            
            print(f"Natural OpenAI defect analysis completed - confidence: {confidence}%, bbox: {bbox_confidence}%")
            
            # SAME API RESPONSE STRUCTURE
            return {
                'analysis': analysis_text,
                'confidence_percentage': confidence,
                'bbox_validation': {
                    'confidence': bbox_confidence,
                    'validated_regions': len(bounding_boxes),
                    'spatial_accuracy': 'high' if bbox_confidence > 80 else 'medium' if bbox_confidence > 60 else 'low'
                },
                'bbox_corrections': corrections.get('bbox_corrections', {}),
                'type_corrections': corrections.get('type_corrections', {}),
                'model_used': OPENAI_MODEL,
                'layer': 'defect_classification',
                'defects_analyzed': detected_defects,
                'bounding_boxes_analyzed': {k: len(v) for k, v in bounding_boxes.items()},
                'natural_analysis': True,
                'classification_validation': True,
                'spatial_validation': True,
                'type_correction_enabled': True
            }
            
        except Exception as e:
            print(f"Natural OpenAI defect analysis error: {e}")
            return {
                'analysis': f'OpenAI analysis failed: {str(e)}',
                'confidence_percentage': 0,
                'bbox_validation': {'confidence': 0, 'error': str(e)},
                'error': str(e)
            }
    
    def _apply_natural_anomaly_decision(self, model_result, openai_result):
        """Apply natural decision logic using existing config threshold"""
        try:
            model_decision = model_result['decision']
            anomaly_score = model_result['anomaly_score']
            openai_confidence = openai_result.get('confidence_percentage', 0)
            
            # Use existing ANOMALY_THRESHOLD from config - SAME API LOGIC
            if anomaly_score > ANOMALY_THRESHOLD:
                print(f"Anomaly score {anomaly_score} > {ANOMALY_THRESHOLD}, decision: DEFECT")
                return 'DEFECT'
            
            # Natural decision making without type bias
            if model_decision == 'DEFECT':
                if openai_confidence < 90:  # Slightly lower threshold for natural approach
                    print(f"Model says DEFECT, OpenAI confidence {openai_confidence}% < 90%, keeping DEFECT")
                    return 'DEFECT'
            
            print(f"Natural decision with {openai_confidence}% confidence: {model_decision}")
            return model_decision
            
        except Exception as e:
            print(f"Error in natural anomaly decision: {e}")
            return model_result['decision']
    
    def _extract_bbox_corrections(self, analysis_text):
        """Extract bounding box corrections and defect type corrections from OpenAI analysis"""
        corrections = {}
        type_corrections = {}
        
        try:
            import re
            
            # Extract defect type corrections - SAME API STRUCTURE
            type_patterns = [
                r'CORRECT_TYPE:\s*(\w+)\s*-\s*([^\n]+)',
                r'should be\s+(\w+)\s+because\s+([^\n]+)',
                r'actually\s+(\w+)\s+defect\s+([^\n]*)',
                r'correct\s+type\s+is\s+(\w+)\s+([^\n]*)',
                r'classify\s+as\s+"(\w+)"\s*-\s*([^\n]+)',
                r'this\s+is\s+(\w+)\s+not\s+[^\n]*\s+because\s+([^\n]+)'
            ]
            
            for pattern in type_patterns:
                matches = re.finditer(pattern, analysis_text, re.IGNORECASE)
                for match in matches:
                    groups = match.groups()
                    if len(groups) >= 2:
                        defect_type = groups[0].lower()
                        reason = groups[1] if len(groups) > 1 else "OpenAI correction"
                        
                        # Validate defect type
                        valid_types = ['open', 'scratch', 'missing_component', 'damaged', 'stained']
                        if defect_type in valid_types:
                            type_corrections[defect_type] = {
                                'corrected_type': defect_type,
                                'reason': reason,
                                'source': 'openai_type_correction'
                            }
            
            # Extract bounding box corrections - SAME API STRUCTURE
            bbox_patterns = [
                r'BBOX_CORRECTION:\s*(\w+):\s*(\d+),(\d+),(\d+),(\d+)\s*-\s*([^\n]+)',
                r'CORRECTION:\s*(\w+):\s*(\d+),(\d+),(\d+),(\d+)\s*\(([^)]+)\)',
                r'(\w+)\s+box\s+should\s+be\s+at\s+(\d+),(\d+)\s+size\s+(\d+)x(\d+)',
                r'move\s+(\w+)\s+to\s+(\d+),(\d+),(\d+),(\d+)'
            ]
            
            for pattern in bbox_patterns:
                matches = re.finditer(pattern, analysis_text, re.IGNORECASE)
                for match in matches:
                    groups = match.groups()
                    if len(groups) >= 5:
                        defect_type = groups[0].lower()
                        x, y = int(groups[1]), int(groups[2])
                        w, h = int(groups[3]), int(groups[4])
                        reason = groups[5] if len(groups) > 5 else "OpenAI bbox correction"
                        
                        corrections[defect_type] = {
                            'x': x, 'y': y, 'width': w, 'height': h,
                            'reason': reason,
                            'source': 'openai_validation'
                        }
            
            # Return both types of corrections - SAME API STRUCTURE
            return {
                'bbox_corrections': corrections,
                'type_corrections': type_corrections
            }
            
        except Exception as e:
            print(f"Error extracting corrections: {e}")
            return {'bbox_corrections': {}, 'type_corrections': {}}
    
    def _apply_openai_corrections(self, result, corrections):
        """Apply OpenAI bounding box and type corrections - SAME API STRUCTURE"""
        try:
            if not corrections:
                return result
            
            bbox_corrections = corrections.get('bbox_corrections', {})
            type_corrections = corrections.get('type_corrections', {})
            
            print(f"Applying {len(bbox_corrections)} bbox corrections and {len(type_corrections)} type corrections...")
            
            bounding_boxes = result.get('bounding_boxes', {})
            corrected_boxes = {}
            corrected_defects = []
            
            # Apply type corrections first
            if type_corrections:
                print("Applying defect type corrections...")
                
                # Find the most confident type correction
                best_correction = None
                for corrected_type, correction_info in type_corrections.items():
                    if not best_correction:
                        best_correction = (corrected_type, correction_info)
                
                if best_correction:
                    corrected_type, correction_info = best_correction
                    print(f"Correcting defect type to: {corrected_type} - {correction_info['reason']}")
                    
                    # Find the best existing detection to convert
                    best_existing = None
                    best_score = 0
                    
                    for existing_type, boxes in bounding_boxes.items():
                        if boxes:
                            # Score based on confidence and area reasonableness
                            box = boxes[0]
                            confidence = box.get('confidence', 0)
                            area_pct = box.get('area_percentage', 0)
                            
                            # Natural scoring without type bias
                            if 1 < area_pct < 25:  # Reasonable area range
                                score = confidence + 0.3
                            else:
                                score = confidence
                            
                            if score > best_score:
                                best_score = score
                                best_existing = (existing_type, box)
                    
                    if best_existing:
                        existing_type, existing_box = best_existing
                        print(f"Converting {existing_type} detection to {corrected_type}")
                        
                        # Create corrected box - SAME API STRUCTURE
                        corrected_box = existing_box.copy()
                        corrected_box.update({
                            'openai_type_corrected': True,
                            'original_type': existing_type,
                            'corrected_type': corrected_type,
                            'correction_reason': correction_info['reason']
                        })
                        
                        # Apply bbox correction if available for this type
                        if corrected_type in bbox_corrections:
                            bbox_correction = bbox_corrections[corrected_type]
                            print(f"Also applying bbox correction for {corrected_type}")
                            
                            corrected_box.update({
                                'x': bbox_correction['x'],
                                'y': bbox_correction['y'],
                                'width': bbox_correction['width'],
                                'height': bbox_correction['height'],
                                'center_x': bbox_correction['x'] + bbox_correction['width'] // 2,
                                'center_y': bbox_correction['y'] + bbox_correction['height'] // 2,
                                'area': bbox_correction['width'] * bbox_correction['height'],
                                'openai_bbox_corrected': True,
                                'bbox_correction_reason': bbox_correction['reason']
                            })
                            
                            # Recalculate area percentage
                            if 'predicted_mask' in result:
                                total_pixels = result['predicted_mask'].shape[0] * result['predicted_mask'].shape[1]
                                corrected_box['area_percentage'] = (corrected_box['area'] / total_pixels) * 100
                        
                        corrected_boxes[corrected_type] = [corrected_box]
                        corrected_defects.append(corrected_type)
                    else:
                        print(f"No suitable existing detection found to convert to {corrected_type}")
            
            # If no type corrections applied, apply bbox corrections to existing types
            if not corrected_boxes:
                for defect_type, boxes in bounding_boxes.items():
                    if defect_type in bbox_corrections and boxes:
                        correction = bbox_corrections[defect_type]
                        print(f"Applying bbox correction for {defect_type}: {correction['reason']}")
                        
                        corrected_box = boxes[0].copy()
                        corrected_box.update({
                            'x': correction['x'],
                            'y': correction['y'],
                            'width': correction['width'],
                            'height': correction['height'],
                            'center_x': correction['x'] + correction['width'] // 2,
                            'center_y': correction['y'] + correction['height'] // 2,
                            'area': correction['width'] * correction['height'],
                            'openai_bbox_corrected': True,
                            'correction_reason': correction['reason']
                        })
                        
                        # Recalculate area percentage
                        if 'predicted_mask' in result:
                            total_pixels = result['predicted_mask'].shape[0] * result['predicted_mask'].shape[1]
                            corrected_box['area_percentage'] = (corrected_box['area'] / total_pixels) * 100
                        
                        corrected_boxes[defect_type] = [corrected_box]
                    else:
                        corrected_boxes[defect_type] = boxes
                
                corrected_defects = list(corrected_boxes.keys())
            
            # Update result with corrections - SAME API STRUCTURE
            if corrected_boxes:
                result['bounding_boxes'] = corrected_boxes
                result['detected_defects'] = corrected_defects
                
                if 'defect_analysis' in result:
                    result['defect_analysis']['bounding_boxes'] = corrected_boxes
                    result['defect_analysis']['detected_defects'] = corrected_defects
            
            result['openai_corrections_applied'] = True
            result['corrections_summary'] = {
                'type_corrections_count': len(type_corrections),
                'bbox_corrections_count': len(bbox_corrections),
                'final_defect_types': corrected_defects
            }
            
            return result
            
        except Exception as e:
            print(f"Error applying OpenAI corrections: {e}")
            return result
    
    def _encode_image_to_base64(self, image_path):
        """Encode image to base64 for OpenAI"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _extract_confidence_percentage(self, text):
        """Extract general confidence percentage from OpenAI response"""
        import re
        matches = re.findall(r'(\d+)%', text)
        if matches:
            return max([int(match) for match in matches])
        return 75  # Default confidence
    
    def _extract_bbox_confidence(self, text):
        """Extract bounding box confidence from OpenAI response"""
        import re
        
        # Look for bounding box specific confidence patterns
        bbox_patterns = [
            r'bounding box.*?(\d+)%',
            r'spatial.*?(\d+)%',
            r'location.*?(\d+)%',
            r'bbox.*?(\d+)%',
            r'accuracy.*?(\d+)%',
            r'boxes.*?(\d+)%',
            r'positioning.*?(\d+)%'
        ]
        
        confidences = []
        for pattern in bbox_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            confidences.extend([int(match) for match in matches])
        
        if confidences:
            return max(confidences)
        
        # Fallback to general confidence if no bbox-specific found
        general_matches = re.findall(r'(\d+)%', text)
        if general_matches:
            return max([int(match) for match in general_matches])
        
        return 75  # Default confidence