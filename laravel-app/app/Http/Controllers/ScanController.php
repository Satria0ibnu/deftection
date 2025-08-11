<?php

namespace App\Http\Controllers;

use Exception;
use App\Models\Scan;
use Inertia\Inertia;
use App\Models\ScanDefect;
use App\Models\ScanThreat;
use App\Services\ScanHistoryService;
use App\Services\ScanDetailService;
use Illuminate\Support\Str;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Storage;
use Illuminate\Validation\ValidationException;

class ScanController extends Controller
{
    public function __construct(
        protected ScanHistoryService $scanHistoryService,
        protected ScanDetailService $scanDetailService
    ) {}

    // shows all scans
    public function index(Request $request)
    {
        try {
            // Get validated filters
            $filters = $this->scanHistoryService->filters($request);

            // Get paginated scans data
            $scans = $this->scanHistoryService->getScans($filters);

            // Get filter options with counts for current user
            $defectTypes = $this->scanHistoryService->getDefectTypesWithCounts();
            $statusCounts = $this->scanHistoryService->getStatusCounts();

            // Get user and role options only for authorized users
            $userOptions = auth()->user()->can('filterByUser', Scan::class)
                ? $this->scanHistoryService->getUsersWithCounts()
                : [];
            $rolesOptions = auth()->user()->can('filterByUser', Scan::class)
                ? $this->scanHistoryService->getRolesWithCounts()
                : [];

            // Generate initial checksum using the STABLE method
            $initialChecksum = $this->scanHistoryService->getStableDataChecksum(auth()->id());

            Log::info('Scan history index loaded', [
                'user_id' => auth()->id(),
                'filters' => $filters,
                'scans_count' => $scans->items(),
                'initial_checksum' => $initialChecksum
            ]);
            return Inertia::render('ScanHistory/Index', [
                'scans' => $scans->items(),
                'filters' => [
                    'current' => $filters,
                    'options' => [
                        'defectTypes' => $defectTypes,
                        'status' => $statusCounts,
                        'users' => $userOptions,
                        'roles' => $rolesOptions, // Fixed: pass roles correctly
                        'perPageOptions' => [5, 10, 25, 50, 100],
                    ]
                ],
                'userCan' => [
                    'viewAllScans' => auth()->user()->can('viewAny', Scan::class),
                    'filterByUser' => auth()->user()->can('filterByUser', Scan::class),
                ],
                'meta' => [
                    'total' => $scans->total(),
                    'per_page' => $scans->perPage(),
                    'current_page' => $scans->currentPage(),
                    'last_page' => $scans->lastPage(),
                    'from' => $scans->firstItem(),
                    'to' => $scans->lastItem(),
                ],
                'initialChecksum' => $initialChecksum,
            ]);
        } catch (\Exception $e) {
            // Log the error
            Log::error('Error in scan history index: ' . $e->getMessage(), [
                'user_id' => auth()->id(),
                'filters' => $request->all(),
                'trace' => $e->getTraceAsString()
            ]);

            // Return error response
            return Inertia::render('ScanHistory/Index', [
                'scans' => collect([]),
                'filters' => [
                    'current' => $this->scanHistoryService->filters($request),
                    'options' => [
                        'defectTypes' => [],
                        'status' => [],
                        'users' => [],
                        'roles' => [],
                        'perPageOptions' => [5, 10, 25, 50, 100],
                    ]
                ],
                'userCan' => [
                    'viewAllScans' => auth()->user()->can('viewAny', Scan::class),
                    'filterByUser' => auth()->user()->can('filterByUser', Scan::class),
                ],
                'error' => 'Failed to load scan history. Please try again.',
                'meta' => [
                    'total' => 0,
                    'per_page' => 10,
                    'current_page' => 1,
                    'last_page' => 1,
                    'from' => null,
                    'to' => null,
                ],
                'initialChecksum' => '',
            ]);
        }
    }


    public function indexCheck(Request $request)
    {
        $startTime = microtime(true);

        try {
            $lastChecksum = $request->input('checksum', '');
            $userId = auth()->id();
            $currentChecksum = $this->scanHistoryService->getStableDataChecksum($userId);
            $hasChanges = $lastChecksum !== $currentChecksum;

            return response()->json([
                'has_changes' => $hasChanges,
                'checksum' => $currentChecksum,
                'timestamp' => now()->toISOString(),
                'response_time_ms' => round((microtime(true) - $startTime) * 1000, 2),
            ]);
        } catch (\Exception $e) {
            Log::error('Error checking updates: ' . $e->getMessage(), [
                'user_id' => auth()->id(),
                'last_checksum' => $request->input('checksum', ''),
                'trace' => $e->getTraceAsString()
            ]);

            return response()->json([
                'error' => 'Failed to check updates',
                'timestamp' => now()->toISOString()
            ], 500);
        }
    }

    public function indexApi(Request $request)
    {
        $startTime = microtime(true);

        try {
            // Get validated filters
            $filters = $this->scanHistoryService->filters($request);

            // Get paginated scans data
            $scans = $this->scanHistoryService->getScans($filters);

            // Get filter options with counts for current user
            $defectTypes = $this->scanHistoryService->getDefectTypesWithCounts();
            $statusCounts = $this->scanHistoryService->getStatusCounts();

            // Get user and role options only for authorized users
            $userOptions = auth()->user()->can('filterByUser', Scan::class)
                ? $this->scanHistoryService->getUsersWithCounts()
                : [];
            $rolesOptions = auth()->user()->can('filterByUser', Scan::class)
                ? $this->scanHistoryService->getRolesWithCounts()
                : [];

            // Get current STABLE checksum
            $currentChecksum = $this->scanHistoryService->getStableDataChecksum(auth()->id());

            $data = [
                'scans' => $scans->items(),
                'filters' => [
                    'current' => $filters,
                    'options' => [
                        'defectTypes' => $defectTypes,
                        'status' => $statusCounts,
                        'users' => $userOptions,
                        'roles' => $rolesOptions, // Fixed: include roles in API response
                        'perPageOptions' => [5, 10, 25, 50, 100],
                    ]
                ],
                'userCan' => [
                    'viewAllScans' => auth()->user()->can('viewAny', Scan::class),
                    'filterByUser' => auth()->user()->can('filterByUser', Scan::class),
                ],
                'meta' => [
                    'total' => $scans->total(),
                    'per_page' => $scans->perPage(),
                    'current_page' => $scans->currentPage(),
                    'last_page' => $scans->lastPage(),
                    'from' => $scans->firstItem(),
                    'to' => $scans->lastItem(),
                ],
                'checksum' => $currentChecksum,
                'timestamp' => now()->toISOString(),
                'response_time_ms' => round((microtime(true) - $startTime) * 1000, 2)
            ];

            return response()->json($data);
        } catch (\Exception $e) {
            Log::error('Error in poll data: ' . $e->getMessage(), [
                'user_id' => auth()->id(),
                'filters' => $request->all(),
                'trace' => $e->getTraceAsString()
            ]);

            return response()->json([
                'error' => 'Failed to fetch data',
                'timestamp' => now()->toISOString()
            ], 500);
        }
    }

    public function indexRefresh(Request $request)
    {
        try {
            // This is essentially the same as pollData but ensures fresh data
            return $this->indexApi($request);
        } catch (\Exception $e) {
            Log::error('Error in force refresh: ' . $e->getMessage());
            return response()->json(['error' => 'Failed to refresh data'], 500);
        }
    }

    /**
     * Display the specified scan with detailed analysis data
     */
    public function show(Scan $scan)
    {
        try {
            // Transform scan data using the service
            $analysisData = $this->scanDetailService->transformScanForAnalysis($scan);

            return Inertia::render('DetailScan/Index', [
                'analysis' => $analysisData,
                'title' => 'Scan Analysis Details',
                'scan' => $scan->only(['id', 'filename', 'created_at'])
            ]);
        } catch (\Exception $e) {
            Log::error('Error loading scan details', [
                'scan_id' => $scan->id,
                'user_id' => auth()->id(),
                'error' => $e->getMessage(),
            ]);

            return redirect()->back()->with('error', 'Failed to load scan details. Please try again.');
        }
    }

    // page for uploading images for scanning
    public function create()
    {
        return Inertia::render('ImageAnalysis/Index', [
            'title' => 'Upload Images',
            'description' => 'Upload images for scanning defects.'
        ]);
    }

    // analyze uploaded images
    public function store(Request $request)
    {
        try {
            Log::info('Scan process started.', [
                'user_id' => auth()->id(),
                'ip_address' => $request->ip()
            ]);

            // Validate the request from the frontend
            $request->validate([
                'image' => 'required|image|max:10240', // 10MB max
                'is_scan_threat' => 'sometimes|boolean'
            ]);
            Log::info('Request validation successful.');

            $userImage = $request->file('image');
            $originalFilename = time() . '_' . Str::slug(pathinfo($userImage->getClientOriginalName(), PATHINFO_FILENAME)) . '.' . $userImage->getClientOriginalExtension();

            // 1. Read the image file and encode it as a Base64 string
            $base64Image = base64_encode(file_get_contents($userImage->getRealPath()));
            Log::info('Image successfully encoded to Base64.');

            // 2. Prepare the JSON payload that Flask expects
            $payload = [
                'image_base64' => $base64Image,
                'filename' => $originalFilename,
                'is_scan_threat' => $request->boolean('is_scan_threat', false),
            ];

            // 3. Send the request as JSON
            Log::info('Sending request to Flask API.', ['url' => env('FLASK_API_URL') . '/api/detection/combined']);
            $response = Http::timeout(120) // Increased timeout for AI processing
                ->asJson() // This sets the Content-Type header to application/json
                ->post(env('FLASK_API_URL') . '/api/detection/combined', $payload);
            Log::info('Received response from Flask API.', ['status' => $response->status()]);


            if (!$response->ok()) {
                // Log the detailed error from Flask for debugging
                Log::error('Flask API returned a non-OK status.', [
                    'status' => $response->status(),
                    'body' => $response->body()
                ]);
                return Inertia::render('ImageAnalysis/Index', [ // Assuming this is the correct component
                    'error' => [
                        'message' => 'Analysis server returned an error. Please try again later.',
                        'type' => 'server_error',
                        'details' => $response->body() // Pass full details for debugging
                    ]
                ]);
            }

            $data = $response->json()['data']; // Assuming results are nested under a 'data' key
            Log::info('Successfully parsed JSON response from Flask.');

            // Store both images only now
            $originalPath = Storage::disk('public')->putFileAs('images/original', $userImage, $originalFilename);
            Log::info('Original image stored.', ['path' => $originalPath]);

            // Handle annotated image if it exists
            $annotatedPath = null;
            if (isset($data['annotated_image']['base64']) && !empty($data['annotated_image']['base64'])) {
                // The base64 string from Flask might not have the data URI prefix
                $filedata = $data['annotated_image']['base64'];
                if (strpos($filedata, ',') !== false) {
                    [, $filedata] = explode(',', $filedata);
                }
                $annotatedFilename = 'annotated_' . $originalFilename;
                $annotatedPath = 'images/annotated/' . $annotatedFilename;
                Storage::disk('public')->put($annotatedPath, base64_decode($filedata));
                Log::info('Annotated image stored.', ['path' => $annotatedPath]);
            }


            // Create Scan row and related models
            Log::info('Creating Scan record in the database.');
            $scan = Scan::create([
                'user_id' => auth()->id(),
                'filename' => $originalFilename,
                'original_path' => $originalPath,
                'annotated_path' => $annotatedPath,
                'is_defect' => $data['result_summary']['is_defective'] ?? false,
                'anomaly_score' => number_format($data['anomaly_detection']['anomaly_score'] ?? 0, 5, '.', ''),
                'anomaly_confidence_level' => $data['confidence_level'] ?? 'N/A',
                // Note: The new response has one 'processing_time'. We'll use it for the main inference time.
                'anomaly_inference_time_ms' => number_format(($data['processing_time'] ?? 0) * 1000, 3, '.', ''), // Convert seconds to ms
                'classification_interference_time_ms' => null, // Not provided in new response
                'preprocessing_time_ms' => null, // Not provided in new response
                'postprocessing_time_ms' => null, // Not provided in new response
                'anomaly_threshold' => number_format($data['anomaly_detection']['threshold_used'] ?? 0, 5, '.', ''),
            ]);
            Log::info('Scan record created successfully.', ['scan_id' => $scan->id]);

            // Store defects
            if (!empty($data['detected_defects'])) {
                Log::info('Storing scan defects.', ['scan_id' => $scan->id, 'defect_count' => count($data['detected_defects'])]);
                foreach ($data['detected_defects'] as $defect) {
                    ScanDefect::create([
                        'scan_id' => $scan->id,
                        'label' => $defect['label'] ?? 'unknown',
                        'confidence_score' => round($defect['confidence_score'] ?? 0, 6),
                        'severity_level' => $defect['severity_level'] ?? 'N/A',
                        'area_percentage' => round($defect['area_percentage'] ?? 0, 4),
                        'box_location' => $defect['box_location'] ?? [],
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

            // After successful, redirect to the results page
            Log::info('Scan process completed. Redirecting to results page.', ['scan_id' => $scan->id]);
            return Inertia::render('ImageAnalysis/Index', [
                'scanResult' => [
                    'id' => $scan->id,
                    'decision' => $data['final_decision'] ?? 'UNKNOWN',
                    'score' => $data['anomaly_detection']['anomaly_score'] ?? 0,
                    'time' => $data['processing_time'] ?? 0,
                    'defects' => count($data['detected_defects'] ?? []),
                    'originalImageUrl' => Storage::url($originalPath),
                    'annotatedImageUrl' => $annotatedPath ? asset(Storage::url($annotatedPath)) : null,
                ]
            ]);

        } catch (ValidationException $e) {
            Log::error('Request validation failed.', ['user_id' => auth()->id(), 'errors' => $e->errors()]);
            throw $e;
        } catch (Exception $e) {
            Log::error('An unexpected error occurred during scan processing.', [
                'user_id' => auth()->id(),
                'error' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);

            return Inertia::render('ImageAnalysis/Index', [
                'error' => [
                    'message' => 'Something went wrong during image analysis. Please try again.',
                    'type' => 'processing_error'
                ]
            ]);
        }
    }

    public function storeBatch(Request $request)
    {
        try {
            // Validate batch upload
            $request->validate([
                'images' => 'required|array|max:10', // Limit batch size
                'images.*' => 'required|image|max:4096'
            ]);

            $results = [];
            $errors = [];
            $successCount = 0;

            foreach ($request->file('images') as $index => $userImage) {
                try {
                    $originalFilename = time() . '_' . $index . '_' . Str::slug(pathinfo($userImage->getClientOriginalName(), PATHINFO_FILENAME)) . '.' . $userImage->getClientOriginalExtension();

                    // Send to Flask API
                    $response = Http::timeout(30)->attach('image', file_get_contents($userImage->getRealPath()), $originalFilename)
                        ->post(env('FLASK_API_URL') . '/scan');

                    if (!$response->ok()) {
                        $errors[] = [
                            'filename' => $userImage->getClientOriginalName(),
                            'error' => 'Analysis failed - server error',
                            'index' => $index
                        ];
                        continue;
                    }

                    $data = $response->json();

                    // Store images
                    $originalPath = Storage::disk('public')->putFileAs('images/original', $userImage, $originalFilename);

                    [$meta, $filedata] = explode(',', $data['annotated_image_base64']);
                    $annotatedFilename = 'annotated_' . $originalFilename;
                    $annotatedPath = 'images/annotated/' . $annotatedFilename;
                    Storage::disk('public')->put($annotatedPath, base64_decode($filedata));

                    // Create Scan record
                    $scan = Scan::create([
                        'user_id' => auth()->id(),
                        'filename' => $data['filename'],
                        'original_path' => $originalPath,
                        'annotated_path' => $annotatedPath,
                        'is_defect' => $data['is_defect'],
                        'anomaly_score' => number_format($data['anomaly_score'], 5, '.', ''),
                        'anomaly_confidence_level' => $data['anomaly_confidence_level'],
                        'anomaly_inference_time_ms' => number_format($data['processing_times']['anomaly_inference_ms'], 3, '.', ''),
                        'classification_interference_time_ms' => $data['processing_times']['classification_inference_ms'] !== null
                            ? number_format($data['processing_times']['classification_inference_ms'], 3, '.', '')
                            : null,
                        'preprocessing_time_ms' => number_format($data['processing_times']['preprocessing_ms'], 3, '.', ''),
                        'postprocessing_time_ms' => number_format($data['processing_times']['postprocessing_ms'], 3, '.', ''),
                        'anomaly_threshold' => number_format($data['anomaly_threshold'], 5, '.', ''),
                    ]);

                    // Store defects
                    foreach ($data['defects'] ?? [] as $defect) {
                        ScanDefect::create([
                            'scan_id' => $scan->id,
                            'label' => $defect['label'],
                            'confidence_score' => round($defect['confidence_score'], 6),
                            'severity_level' => $defect['severity_level'],
                            'area_percentage' => round($defect['area_percentage'], 4),
                            'box_location' => $defect['box_location'], // Pass array directly
                        ]);
                    }

                    // Store threat
                    if (!empty($data['threat_scan'])) {
                        ScanThreat::create([
                            'scan_id' => $scan->id,
                            'hash' => $data['threat_scan']['hash'],
                            'status' => $data['threat_scan']['status'],
                            'threat_level' => $data['threat_scan']['threat_level'],
                            'qr_content' => $data['threat_scan']['qr_content'],
                            'issues' => $data['threat_scan']['issues'], // Pass array directly
                        ]);
                    }

                    $results[] = [
                        'scan' => $scan->load('scanDefects', 'scanThreat'), // Use correct relationship names
                        'originalImageUrl' => Storage::url($originalPath),
                        'annotatedImageUrl' => Storage::url($annotatedPath),
                        'originalFilename' => $userImage->getClientOriginalName(),
                        'index' => $index
                    ];

                    $successCount++;
                } catch (Exception $e) {
                    Log::error('Batch scan processing failed for image', [
                        'user_id' => auth()->id(),
                        'image_index' => $index,
                        'filename' => $userImage->getClientOriginalName(),
                        'error' => $e->getMessage()
                    ]);

                    $errors[] = [
                        'filename' => $userImage->getClientOriginalName(),
                        'error' => 'Processing failed: ' . $e->getMessage(),
                        'index' => $index
                    ];
                }
            }

            // Return results
            return Inertia::render('Scan/Create', [
                'title' => 'Upload Images',
                'description' => 'Upload images for scanning defects.',
                'batchResults' => [
                    'results' => $results,
                    'errors' => $errors,
                    'summary' => [
                        'total' => count($request->file('images')),
                        'successful' => $successCount,
                        'failed' => count($errors),
                        'defectsFound' => collect($results)->where('scan.is_defect', true)->count()
                    ]
                ]
            ]);
        } catch (ValidationException $e) {
            throw $e;
        } catch (Exception $e) {
            Log::error('Batch scan failed completely', [
                'user_id' => auth()->id(),
                'error' => $e->getMessage()
            ]);

            return Inertia::render('Scan/Create', [
                'title' => 'Upload Images',
                'description' => 'Upload images for scanning defects.',
                'error' => [
                    'message' => 'Batch processing failed. Please try again.',
                    'type' => 'batch_error'
                ]
            ]);
        }
    }

    // delete a scans
    public function destroy(Scan $scan)
    {
        if (!$this->authorize('delete', $scan)) {
            abort(403, 'Unauthorized action.');
        }

        // Store scan details for logging before deletion
        $scanData = [
            'scan_id' => $scan->id,
            'filename' => $scan->filename,
            'original_path' => $scan->original_path,
            'annotated_path' => $scan->annotated_path,
            'is_defect' => $scan->is_defect,
            'anomaly_score' => $scan->anomaly_score,
            'user_id' => auth()->id(),
            'deleted_at' => now()->toISOString()
        ];

        // Delete the scan ( cascade delete related scan_defects and scan_threats)
        $scan->delete();

        // Log successful scan deletion
        Log::info('Scan deleted successfully', $scanData);

        return redirect()
            ->back()
            ->with('success', 'Scan deleted successfully.');
    }
}
