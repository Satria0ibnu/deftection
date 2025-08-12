<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;
use App\Models\RealtimeSession;
use App\Models\RealtimeScan;
use App\Models\RealtimeScanDefect;
use Illuminate\Support\Str;
use Exception;

class RealtimeFrameController extends Controller
{
    /**
     * Process a single frame from realtime analysis
     */
    public function processFrame(Request $request)
    {
        try {
            // Validate the request - now expecting blob instead of base64
            $request->validate([
                'frame_blob' => 'required|file|mimes:jpeg,jpg,png|max:10240', // 10MB max
                'session_id' => 'required|exists:realtime_sessions,id',
                'timestamp' => 'required|string'
            ]);

            $sessionId = $request->input('session_id');
            $frameBlob = $request->file('frame_blob');
            $timestamp = $request->input('timestamp');

            // Get the session and verify it's active
            $session = RealtimeSession::findOrFail($sessionId);

            // Authorize access to this session
            $this->authorize('update', $session);

            if (!in_array($session->session_status, ['active', 'paused'])) {
                return response()->json([
                    'error' => 'Session not active',
                    'message' => 'Cannot process frames for inactive sessions'
                ], 400);
            }

            // Generate unique filename for this frame
            $filename = 'realtime_' . $sessionId . '_' . time() . '_' . Str::random(8) . '.jpg';

            Log::info('Processing realtime frame', [
                'session_id' => $sessionId,
                'filename' => $filename,
                'timestamp' => $timestamp,
                'file_size' => $frameBlob->getSize()
            ]);

            $flaskUrl = env('FLASK_API_URL', 'http://localhost:5001');

            // Send blob directly to Flask AI (fastest method)
            $response = Http::timeout(30)
                ->attach('image', file_get_contents($frameBlob->getRealPath()), $filename)
                ->post($flaskUrl . '/api/detection/frame', [
                    'filename' => $filename,
                    'source' => 'realtime_analysis'
                ]);

            if (!$response->successful()) {
                Log::error('Flask AI frame detection failed', [
                    'status' => $response->status(),
                    'body' => $response->body(),
                    'session_id' => $sessionId
                ]);

                return response()->json([
                    'error' => 'Detection failed',
                    'message' => 'Frame analysis could not be completed'
                ], 500);
            }

            $detectionData = $response->json();
            Log::info('Flask AI detection successful for realtime frame');

            // Determine if this is a defect
            $isDefect = $detectionData['final_decision'] === 'DEFECT';
            $anomalyScore = $detectionData['anomaly_score'] ?? 0;

            // Store annotated image if available (optional for realtime - only if defect for performance)
            $annotatedPath = null;
            if ($isDefect && isset($detectionData['annotated_image']) && !empty($detectionData['annotated_image'])) {
                try {
                    $annotatedData = $detectionData['annotated_image'];
                    if (strpos($annotatedData, ',') !== false) {
                        [, $annotatedData] = explode(',', $annotatedData);
                    }
                    $annotatedPath = 'images/realtime/annotated/' . $filename;
                    Storage::disk('public')->put($annotatedPath, base64_decode($annotatedData));
                } catch (Exception $e) {
                    Log::warning('Failed to store annotated frame', [
                        'error' => $e->getMessage(),
                        'session_id' => $sessionId
                    ]);
                }
            }

            // Create RealtimeScan record using existing schema
            $realtimeScan = RealtimeScan::create([
                'realtime_session_id' => $sessionId,
                'filename' => $filename,
                'captured_at' => now(),
                'annotated_path' => $annotatedPath,
                'is_defect' => $isDefect,
                'anomaly_score' => $anomalyScore,
                'anomaly_confidence_level' => $detectionData['anomaly_confidence_level'] ?? 'low',
                'anomaly_inference_time_ms' => ($detectionData['anomaly_processing_time'] ?? 0) * 1000,
                'classification_inference_time_ms' => ($detectionData['classification_processing_time'] ?? 0) * 1000,
                'preprocessing_time_ms' => ($detectionData['preprocessing_time'] ?? 0) * 1000,
                'postprocessing_time_ms' => ($detectionData['postprocessing_time'] ?? 0) * 1000,
                'anomaly_threshold' => $detectionData['anomaly_threshold'] ?? 0.3,
            ]);

            // Process defects if any using existing schema
            if ($isDefect && isset($detectionData['defects']) && is_array($detectionData['defects'])) {
                foreach ($detectionData['defects'] as $defectInfo) {
                    RealtimeScanDefect::create([
                        'realtime_scan_id' => $realtimeScan->id,
                        'label' => $defectInfo['label'] ?? 'anomaly',
                        'confidence_score' => $defectInfo['confidence_score'] ?? 0.5,
                        'severity_level' => $defectInfo['severity_level'] ?? 'moderate',
                        'area_percentage' => $defectInfo['area_percentage'] ?? 0,
                        'box_location' => $defectInfo['bounding_box'] ?? [],
                    ]);
                }
            }

            // Update session statistics atomically
            $session->increment('total_frames_processed');
            if ($isDefect) {
                $session->increment('defect_count');
            } else {
                $session->increment('good_count');
            }

            // Recalculate rates
            $session->refresh();
            $session->update([
                'defect_rate' => $session->total_frames_processed > 0
                    ? round(($session->defect_count / $session->total_frames_processed) * 100, 2)
                    : 0.00,
                'good_rate' => $session->total_frames_processed > 0
                    ? round(($session->good_count / $session->total_frames_processed) * 100, 2)
                    : 0.00
            ]);

            Log::info('Realtime frame processed successfully', [
                'session_id' => $sessionId,
                'scan_id' => $realtimeScan->id,
                'is_defect' => $isDefect,
                'anomaly_score' => $anomalyScore
            ]);

            // Prepare response data for Vue frontend
            $responseData = [
                'success' => true,
                'scan_id' => $realtimeScan->id,
                'status' => $isDefect ? 'defect' : 'good',
                'anomaly_score' => $anomalyScore,
                'confidence_level' => $detectionData['anomaly_confidence_level'] ?? 'low',
                'processing_time' => [
                    'anomaly' => $detectionData['anomaly_processing_time'] ?? 0,
                    'classification' => $detectionData['classification_processing_time'] ?? 0,
                    'preprocessing' => $detectionData['preprocessing_time'] ?? 0,
                    'postprocessing' => $detectionData['postprocessing_time'] ?? 0
                ],
                'detections' => [], // Will be populated below
                'annotated_image_url' => $annotatedPath ? Storage::url($annotatedPath) : null,
                'session_stats' => [
                    'total_frames' => $session->total_frames_processed,
                    'defect_count' => $session->defect_count,
                    'good_count' => $session->good_count,
                    'defect_rate' => $session->defect_rate
                ]
            ];

            // Convert Flask detection format to frontend bounding box format
            if (isset($detectionData['defects']) && is_array($detectionData['defects'])) {
                foreach ($detectionData['defects'] as $defect) {
                    $bbox = $defect['bounding_box'] ?? [];
                    $responseData['detections'][] = [
                        'label' => $defect['label'] ?? 'Defect',
                        'bbox' => [
                            $bbox['x'] ?? 0,
                            $bbox['y'] ?? 0,
                            $bbox['width'] ?? 50,
                            $bbox['height'] ?? 50
                        ],
                        'confidence' => $defect['confidence_score'] ?? 0.5,
                        'severity' => $defect['severity_level'] ?? 'moderate'
                    ];
                }
            }

            return response()->json($responseData, 200);
        } catch (Exception $e) {
            Log::error('Error processing realtime frame', [
                'error' => $e->getMessage(),
                'trace' => $e->getTraceAsString(),
                'session_id' => $request->input('session_id'),
                'file' => $e->getFile(),
                'line' => $e->getLine()
            ]);

            return response()->json([
                'error' => 'Processing failed',
                'message' => 'Unable to process frame. Please try again.',
                'debug' => app()->environment('local') ? $e->getMessage() : null
            ], 500);
        }
    }
}
