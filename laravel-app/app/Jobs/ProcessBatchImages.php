<?php

namespace App\Jobs;

use Exception;
use App\Models\Scan;
use App\Models\ScanDefect;
use App\Models\ScanThreat;
use Illuminate\Support\Str;
use Illuminate\Bus\Queueable;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Cache;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\Storage;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Contracts\Queue\ShouldQueue;

class ProcessBatchImages implements ShouldQueue
{
    use Dispatchable, Queueable, InteractsWithQueue, SerializesModels;

    protected $batchId;
    protected $userId;

    public $timeout = 600;

    public function __construct($batchId, $userId)
    {
        $this->batchId = $batchId;
        $this->userId = $userId;
    }

    public function handle(): void
    {
        Log::info('Starting ProcessBatchImages job.', [
            'batch_id' => $this->batchId,
            'user_id' => $this->userId,
            'timeout' => $this->timeout,
        ]);

        if (!Auth::loginUsingId($this->userId)) {
            Log::error('Could not authenticate user for batch job.', ['user_id' => $this->userId]);
            return;
        }

        $files = Storage::files('temp_batches/' . $this->batchId);
        $total = count($files);

        if ($total === 0) {
            Log::warning('No files found in temporary directory for batch.', ['batch_id' => $this->batchId]);
            return;
        }

        Log::info('Found files to process.', ['batch_id' => $this->batchId, 'count' => $total]);

        foreach ($files as $index => $filePath) {
            $userImage = new \Illuminate\Http\UploadedFile(Storage::path($filePath), basename($filePath));
            Log::info('Processing file.', ['batch_id' => $this->batchId, 'file_index' => $index, 'filename' => $userImage->getClientOriginalName()]);

            try {
                $originalFilename = time() . '_' . Str::slug(pathinfo($userImage->getClientOriginalName(), PATHINFO_FILENAME)) . '.' . $userImage->getClientOriginalExtension();

                $base64Image = base64_encode(file_get_contents($userImage->getRealPath()));
                Log::info('Image encoded to Base64.', ['batch_id' => $this->batchId, 'file_index' => $index]);

                // *** CRITICAL FIX ***
                // The $request object is not available in a queued job.
                // We'll set is_scan_threat to false, matching your single store() method.
                $payload = [
                    'image_base64' => $base64Image,
                    'filename' => $originalFilename,
                    'is_scan_threat' => false,
                ];

                Log::info('Sending request to Flask API.', ['batch_id' => $this->batchId, 'url' => env('FLASK_API_URL') . '/api/detection/combined']);
                $response = Http::timeout(120)->asJson()->post(env('FLASK_API_URL') . '/api/detection/combined', $payload);
                Log::info('Received response from Flask API.', ['batch_id' => $this->batchId, 'status' => $response->status()]);

                if (!$response->ok()) {
                    throw new Exception('Flask API returned a non-OK status: ' . $response->status() . ' Body: ' . $response->body());
                }

                // Check the response structure before accessing keys
                $data = $response->json();
                Log::info('Successfully parsed JSON response from Flask.', ['batch_id' => $this->batchId]);

                // --- Database and Storage Operations ---
                $originalPath = Storage::disk('public')->putFileAs('images/original', $userImage, $originalFilename);
                Log::info('Original image stored.', ['batch_id' => $this->batchId, 'path' => $originalPath]);

                $annotatedPath = null;
                if (isset($data['annotated_image']) && !empty($data['annotated_image'])) {
                    $filedata = $data['annotated_image'];
                    if (strpos($filedata, ',') !== false) {
                        [, $filedata] = explode(',', $filedata);
                    }
                    $annotatedFilename = 'annotated_' . $originalFilename;
                    $annotatedPath = 'images/annotated/' . $annotatedFilename;
                    Storage::disk('public')->put($annotatedPath, base64_decode($filedata));
                    Log::info('Annotated image stored.', ['batch_id' => $this->batchId, 'path' => $annotatedPath]);
                }

                Log::info('Creating Scan record in the database.', ['batch_id' => $this->batchId]);
                $scan = Scan::create([
                    'user_id' => auth()->id(),
                    'filename' => $originalFilename,
                    'original_path' => $originalPath,
                    'annotated_path' => $annotatedPath,
                    'is_defect' => $data['final_decision'] === 'DEFECT' ? true : false,
                    'anomaly_score' => number_format($data['anomaly_score'] ?? 0, 5, '.', ''),
                    'anomaly_confidence_level' => $data['anomaly_confidence_level'] ?? 'N/A',
                    // Note: The new response has one 'processing_time'. We'll use it for the main inference time.
                    'anomaly_inference_time_ms' => number_format(($data['anomaly_processing_time'] ?? 0) * 1000, 3, '.', ''), // Convert seconds to ms
                    'classification_inference_time_ms' => number_format(($data['classification_processing_time'] ?? 0) * 1000, 3, '.', ''),
                    'preprocessing_time_ms' => number_format(($data['preprocessing_time'] ?? 0) * 1000, 3, '.', ''),
                    'postprocessing_time_ms' => number_format(($data['postprocessing_time'] ?? 0) * 1000, 3, '.', ''),
                    'anomaly_threshold' => number_format($data['anomaly_threshold'] ?? 0, 5, '.', ''),
                ]);
                Log::info('Scan record created successfully.', ['batch_id' => $this->batchId, 'scan_id' => $scan->id]);

                // ... (Your ScanDefect and ScanThreat creation logic would go here) ...

                if (!empty($data['defects'])) {
                    Log::info('Storing scan defects.', ['scan_id' => $scan->id, 'defect_count' => count($data['defects'])]);
                    foreach ($data['defects'] as $defect) {
                        ScanDefect::create([
                            'scan_id' => $scan->id,
                            'label' => $defect['label'] ?? 'unknown',
                            'confidence_score' => round($defect['confidence_score'] ?? 0, 6),
                            'severity_level' => $defect['severity_level'] ?? 'N/A',
                            'area_percentage' => round($defect['area_percentage'] ?? 0, 4),
                            'box_location' => $defect['bounding_box'] ?? [],
                        ]);
                    }
                    Log::info('Scan defects stored successfully.', ['scan_id' => $scan->id]);
                }

                // Store threat (assuming structure is correct if it exists)
                if (!empty($data['security_scan'])) {
                    Log::info('Storing scan threat information.', ['scan_id' => $scan->id]);
                    ScanThreat::create([
                        'scan_id' => $scan->id,
                        'hash' => $data['security_scan']['hash'] ?? null,
                        'status' => $data['security_scan']['status'] ?? null,
                        'threat_level' => $data['security_scan']['threat_level'] ?? null,
                        'qr_content' => $data['security_scan']['qr_content'] ?? null,
                        'issues' => $data['security_scan']['issues'] ?? [],
                    ]);
                    Log::info('Scan threat information stored successfully.', ['scan_id' => $scan->id]);
                }

            } catch (Exception $e) {
                Log::error('Batch scan processing failed for image', [
                    'batch_id' => $this->batchId,
                    'user_id' => auth()->id(),
                    'image_index' => $index,
                    'filename' => $userImage->getClientOriginalName(),
                    'error' => $e->getMessage(),
                    'trace' => $e->getTraceAsString() // Add trace for more detail
                ]);
            }

            sleep(0.5); // Throttle processing to avoid overwhelming the API
        }

        Log::info('Finished processing batch. Cleaning up temporary files.', ['batch_id' => $this->batchId]);
        Storage::deleteDirectory('temp_batches/' . $this->batchId);
    }
}
