<?php

namespace App\Services;

use App\Models\RealtimeSession;
use App\Models\RealtimeScan;
use App\Models\RealtimeScanDefect;
use App\Models\DefectType;
use Illuminate\Support\Collection;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\File;
use Carbon\Carbon;

class RealtimeSessionReportService
{
    protected ChartGenerationService $chartService;

    public function __construct(ChartGenerationService $chartService)
    {
        $this->chartService = $chartService;
    }

    /**
     * Prepare data for realtime session report
     */
    public function prepareRealtimeSessionReport(RealtimeSession $session): array
    {
        Log::info('Starting realtime session report preparation', ['session_id' => $session->id]);

        // Load relationships
        $session->load(['user', 'realtimeScans.realtimeScanDefects']);

        // Get defect types for explanations
        $defectTypes = DefectType::all()->keyBy('slug');

        // Process session scans and defects
        $scans = $session->realtimeScans;
        Log::info('Loaded scans for session', ['session_id' => $session->id, 'scans_count' => $scans->count()]);

        $processedDefects = $this->processSessionDefects($scans, $defectTypes);

        // Generate charts data
        $chartsData = $this->generateSessionCharts($session, $scans);
        Log::info('Generated charts data', ['charts_available' => array_keys($chartsData)]);

        // Generate chart images using the chart service
        $chartImages = $this->generateChartImages($chartsData);
        Log::info('Generated chart images', [
            'images_available' => array_keys(array_filter($chartImages)),
            'total_images' => count($chartImages)
        ]);

        // Generate comprehensive statistics
        $statistics = $this->generateSessionStatistics($session, $scans);

        return [
            'session' => $session,
            'scans' => $scans,
            'defects' => $processedDefects,
            'chartsData' => $chartsData,
            'chartImages' => $chartImages,
            'statistics' => $statistics,
            'summary' => $this->generateSessionSummary($session, $scans),
            'generatedAt' => now(),
            'reportTitle' => "Realtime Session Analysis Report - Session #{$session->id}",
        ];
    }

    /**
     * Generate chart images using the chart service - with file fallback for wkhtmltopdf
     */
    private function generateChartImages(array $chartsData): array
    {
        $chartImages = [];

        try {
            Log::info('Starting chart image generation', ['charts_data' => array_keys($chartsData)]);

            // Frame trends chart
            if (!empty($chartsData['frame_trends'])) {
                Log::info('Generating frame trends chart');
                $base64Image = $this->chartService->generateDailyScanTrendsChart($chartsData['frame_trends']);
                $chartImages['frame_trends'] = $this->saveBase64ImageToTempFile($base64Image, 'frame_trends');
                Log::info('Frame trends chart generated', ['path' => $chartImages['frame_trends']]);
            }

            // Defect distribution chart
            if (!empty($chartsData['defect_distribution'])) {
                Log::info('Generating defect distribution chart');
                $base64Image = $this->chartService->generateDefectDistributionChart($chartsData['defect_distribution']);
                $chartImages['defect_distribution'] = $this->saveBase64ImageToTempFile($base64Image, 'defect_distribution');
                Log::info('Defect distribution chart generated', ['path' => $chartImages['defect_distribution']]);
            }

            // Processing performance chart
            if (!empty($chartsData['processing_performance'])) {
                Log::info('Generating processing performance chart');
                $performanceArray = collect($chartsData['processing_performance'])->map(function ($data, $stage) {
                    return [
                        'stage' => ucfirst(str_replace('_', ' ', $stage)),
                        'avg_time' => $data['avg'],
                        'max_time' => $data['max'],
                    ];
                })->values()->toArray();

                $base64Image = $this->chartService->generateProcessingPerformanceChart($performanceArray);
                $chartImages['processing_performance'] = $this->saveBase64ImageToTempFile($base64Image, 'processing_performance');
                Log::info('Processing performance chart generated', ['path' => $chartImages['processing_performance']]);
            }

            // Hourly patterns chart
            if (!empty($chartsData['hourly_patterns'])) {
                Log::info('Generating hourly patterns chart');
                $base64Image = $this->chartService->generateHourlyPatternsChart($chartsData['hourly_patterns']);
                $chartImages['hourly_patterns'] = $this->saveBase64ImageToTempFile($base64Image, 'hourly_patterns');
                Log::info('Hourly patterns chart generated', ['path' => $chartImages['hourly_patterns']]);
            }

            // Anomaly distribution chart
            if (!empty($chartsData['anomaly_distribution'])) {
                Log::info('Generating anomaly distribution chart');
                $base64Image = $this->chartService->generateAnomalyScoreChart($chartsData['anomaly_distribution']);
                $chartImages['anomaly_distribution'] = $this->saveBase64ImageToTempFile($base64Image, 'anomaly_distribution');
                Log::info('Anomaly distribution chart generated', ['path' => $chartImages['anomaly_distribution']]);
            }

            Log::info('Realtime session chart images generated', [
                'charts_generated' => array_keys(array_filter($chartImages)),
                'total_charts' => count($chartImages)
            ]);
        } catch (\Exception $e) {
            Log::error('Failed to generate realtime session chart images', [
                'error' => $e->getMessage(),
                'trace' => $e->getTraceAsString(),
                'charts_data' => array_keys($chartsData)
            ]);

            // Return empty chartImages to prevent template errors
            $chartImages = array_fill_keys(['frame_trends', 'defect_distribution', 'processing_performance', 'hourly_patterns', 'anomaly_distribution'], null);
        }

        return $chartImages;
    }

    /**
     * Save base64 image to temporary file for wkhtmltopdf compatibility
     */
    private function saveBase64ImageToTempFile(?string $base64Image, string $chartName): ?string
    {
        if (!$base64Image) {
            Log::warning("No base64 image provided for {$chartName}");
            return null;
        }

        try {
            // Check if it's a proper base64 data URL
            if (!str_starts_with($base64Image, 'data:image/')) {
                Log::error("Invalid base64 image format for {$chartName}", [
                    'starts_with' => substr($base64Image, 0, 50)
                ]);
                return null;
            }

            // Extract the base64 data
            $imageData = explode(',', $base64Image);
            if (count($imageData) !== 2) {
                Log::error("Invalid base64 image structure for {$chartName}");
                return null;
            }

            $encodedImage = $imageData[1];
            $decodedImage = base64_decode($encodedImage);

            if ($decodedImage === false) {
                Log::error("Failed to decode base64 image for {$chartName}");
                return null;
            }

            // Create temp directory if it doesn't exist
            $tempDir = storage_path('app/temp/charts');
            if (!File::exists($tempDir)) {
                File::makeDirectory($tempDir, 0755, true);
            }

            // Generate unique filename
            $filename = $chartName . '_' . uniqid() . '.png';
            $filePath = $tempDir . '/' . $filename;

            // Save the file
            if (File::put($filePath, $decodedImage)) {
                Log::info("Chart image saved to temp file", [
                    'chart' => $chartName,
                    'path' => $filePath,
                    'size' => strlen($decodedImage)
                ]);
                return $filePath;
            } else {
                Log::error("Failed to save chart image to temp file", [
                    'chart' => $chartName,
                    'path' => $filePath
                ]);
                return null;
            }
        } catch (\Exception $e) {
            Log::error("Exception saving chart image to temp file", [
                'chart' => $chartName,
                'error' => $e->getMessage()
            ]);
            return null;
        }
    }

    /**
     * Process session defects with explanations
     */
    private function processSessionDefects(Collection $scans, Collection $defectTypes): Collection
    {
        $allDefects = collect();

        foreach ($scans as $scan) {
            if ($scan->realtimeScanDefects && $scan->realtimeScanDefects->isNotEmpty()) {
                foreach ($scan->realtimeScanDefects as $defect) {
                    $defectTypeSlug = str_replace(' ', '_', strtolower($defect->label ?? 'unknown'));
                    $defectType = $defectTypes->get($defectTypeSlug);

                    $allDefects->push([
                        'scan_id' => $scan->id,
                        'scan_filename' => $scan->filename,
                        'scan_captured_at' => $scan->captured_at,
                        'label' => $this->formatDefectLabel($defect->label),
                        'confidence_score' => $defect->confidence_score,
                        'severity_level' => ucfirst($defect->severity_level),
                        'area_percentage' => $defect->area_percentage,
                        'box_location' => $defect->box_location,
                        'explanation' => $defectType ? $defectType->description : 'No detailed explanation available for this defect type.',
                    ]);
                }
            }
        }

        return $allDefects;
    }

    /**
     * Generate charts data for session analysis
     */
    private function generateSessionCharts(RealtimeSession $session, Collection $scans): array
    {
        $chartsData = [];

        // Frame processing trends over time
        $chartsData['frame_trends'] = $this->generateFrameTrends($scans);

        // Defect type distribution
        $chartsData['defect_distribution'] = $this->generateDefectDistribution($scans);

        // Processing performance breakdown
        $chartsData['processing_performance'] = $this->generateProcessingPerformance($scans);

        // Hourly processing patterns
        $chartsData['hourly_patterns'] = $this->generateHourlyPatterns($scans);

        // Anomaly score distribution
        $chartsData['anomaly_distribution'] = $this->generateAnomalyDistribution($scans);

        return $chartsData;
    }

    /**
     * Generate frame processing trends
     */
    private function generateFrameTrends(Collection $scans): array
    {
        if ($scans->isEmpty()) {
            return [];
        }

        // Group by date for daily trends
        $trends = $scans->groupBy(function ($scan) {
            return Carbon::parse($scan->captured_at)->format('Y-m-d');
        })->map(function ($group, $date) {
            return [
                'date' => $date,
                'total' => $group->count(),
                'defective' => $group->where('is_defect', true)->count(),
                'good' => $group->where('is_defect', false)->count(),
            ];
        })->values()->toArray();

        return $trends;
    }

    /**
     * Generate defect type distribution
     */
    private function generateDefectDistribution(Collection $scans): array
    {
        $defects = collect();
        foreach ($scans as $scan) {
            if ($scan->realtimeScanDefects) {
                $defects = $defects->concat($scan->realtimeScanDefects);
            }
        }

        if ($defects->isEmpty()) {
            return [];
        }

        return $defects->groupBy('label')->map(function ($group, $label) {
            return [
                'label' => $this->formatDefectLabel($label),
                'count' => $group->count(),
                'percentage' => 0, // Will be calculated later
            ];
        })->values()->toArray();
    }

    /**
     * Generate processing performance data
     */
    private function generateProcessingPerformance(Collection $scans): array
    {
        if ($scans->isEmpty()) {
            return [];
        }

        $performance = [
            'preprocessing' => [
                'avg' => round($scans->avg('preprocessing_time_ms') ?? 0, 2),
                'min' => round($scans->min('preprocessing_time_ms') ?? 0, 2),
                'max' => round($scans->max('preprocessing_time_ms') ?? 0, 2),
            ],
            'anomaly_inference' => [
                'avg' => round($scans->avg('anomaly_inference_time_ms') ?? 0, 2),
                'min' => round($scans->min('anomaly_inference_time_ms') ?? 0, 2),
                'max' => round($scans->max('anomaly_inference_time_ms') ?? 0, 2),
            ],
            'classification_inference' => [
                'avg' => round($scans->avg('classification_inference_time_ms') ?? 0, 2),
                'min' => round($scans->min('classification_inference_time_ms') ?? 0, 2),
                'max' => round($scans->max('classification_inference_time_ms') ?? 0, 2),
            ],
            'postprocessing' => [
                'avg' => round($scans->avg('postprocessing_time_ms') ?? 0, 2),
                'min' => round($scans->min('postprocessing_time_ms') ?? 0, 2),
                'max' => round($scans->max('postprocessing_time_ms') ?? 0, 2),
            ],
        ];

        return $performance;
    }

    /**
     * Generate hourly processing patterns
     */
    private function generateHourlyPatterns(Collection $scans): array
    {
        if ($scans->isEmpty()) {
            return [];
        }

        return $scans->groupBy(function ($scan) {
            return Carbon::parse($scan->captured_at)->format('H');
        })->map(function ($group, $hour) {
            return [
                'hour' => $hour . ':00',
                'total' => $group->count(),
                'defective' => $group->where('is_defect', true)->count(),
                'good' => $group->where('is_defect', false)->count(),
            ];
        })->sortBy('hour')->values()->toArray();
    }

    /**
     * Generate anomaly score distribution
     */
    private function generateAnomalyDistribution(Collection $scans): array
    {
        if ($scans->isEmpty()) {
            return [];
        }

        $ranges = [
            '0.0-0.2' => ['min' => 0.0, 'max' => 0.2],
            '0.2-0.4' => ['min' => 0.2, 'max' => 0.4],
            '0.4-0.6' => ['min' => 0.4, 'max' => 0.6],
            '0.6-0.8' => ['min' => 0.6, 'max' => 0.8],
            '0.8-1.0' => ['min' => 0.8, 'max' => 1.0],
        ];

        return collect($ranges)->map(function ($range, $label) use ($scans) {
            $count = $scans->filter(function ($scan) use ($range) {
                $score = $scan->anomaly_score ?? 0;
                return $score >= $range['min'] && $score < $range['max'];
            })->count();

            return [
                'range' => $label,
                'count' => $count,
                'percentage' => $scans->count() > 0 ? round(($count / $scans->count()) * 100, 1) : 0,
            ];
        })->values()->toArray();
    }

    /**
     * Generate comprehensive session statistics
     */
    private function generateSessionStatistics(RealtimeSession $session, Collection $scans): array
    {
        $totalScans = $scans->count();
        $defectiveScans = $scans->where('is_defect', true)->count();
        $goodScans = $totalScans - $defectiveScans;

        // Calculate total defects across all scans
        $totalDefects = $scans->sum(function ($scan) {
            return $scan->realtimeScanDefects ? $scan->realtimeScanDefects->count() : 0;
        });

        return [
            'total_frames' => $totalScans,
            'defective_frames' => $defectiveScans,
            'good_frames' => $goodScans,
            'defect_rate' => $totalScans > 0 ? round(($defectiveScans / $totalScans) * 100, 2) : 0,
            'good_rate' => $totalScans > 0 ? round(($goodScans / $totalScans) * 100, 2) : 0,
            'total_defects_found' => $totalDefects,
            'avg_processing_time' => $this->calculateAverageProcessingTime($scans),
            'session_duration' => $session->duration_seconds ?? $this->calculateSessionDuration($session),
            'throughput_fps' => $session->throughput_fps ?? $this->calculateThroughput($session, $scans),
            'avg_anomaly_score' => round($scans->avg('anomaly_score') ?? 0, 3),
            'max_anomaly_score' => round($scans->max('anomaly_score') ?? 0, 3),
            'min_anomaly_score' => round($scans->min('anomaly_score') ?? 0, 3),
        ];
    }

    /**
     * Generate session summary
     */
    private function generateSessionSummary(RealtimeSession $session, Collection $scans): array
    {
        return [
            'session_id' => $session->id,
            'user_name' => $session->user->name ?? 'Unknown User',
            'user_email' => $session->user->email ?? 'N/A',
            'session_status' => ucfirst($session->session_status),
            'camera_location' => $session->camera_location ?? 'Not specified',
            'session_start' => $session->session_start,
            'session_end' => $session->session_end,
            'duration' => $this->formatDuration($session->duration_seconds ?? $this->calculateSessionDuration($session)),
            'total_frames' => $scans->count(),
            'defect_rate' => $session->defect_rate ?? 0,
            'throughput' => $session->throughput_fps ?? 0,
        ];
    }

    /**
     * Helper methods
     */
    private function formatDefectLabel(?string $label): string
    {
        return ucwords(str_replace(['_', '-'], ' ', $label ?? 'Unknown'));
    }

    private function calculateAverageProcessingTime(Collection $scans): float
    {
        if ($scans->isEmpty()) {
            return 0;
        }

        $totalTimes = $scans->map(function ($scan) {
            return ($scan->preprocessing_time_ms ?? 0) +
                ($scan->anomaly_inference_time_ms ?? 0) +
                ($scan->classification_inference_time_ms ?? 0) +
                ($scan->postprocessing_time_ms ?? 0);
        });

        return round($totalTimes->avg(), 2);
    }

    private function calculateSessionDuration(RealtimeSession $session): int
    {
        if ($session->session_end) {
            return $session->session_start->diffInSeconds($session->session_end);
        }

        return $session->session_start->diffInSeconds(now());
    }

    private function calculateThroughput(RealtimeSession $session, Collection $scans): float
    {
        $duration = $this->calculateSessionDuration($session);

        if ($duration <= 0) {
            return 0;
        }

        return round($scans->count() / ($duration / 60), 3); // frames per minute
    }

    private function formatDuration(?int $seconds): string
    {
        if (!$seconds) {
            return '0 seconds';
        }

        $hours = floor($seconds / 3600);
        $minutes = floor(($seconds % 3600) / 60);
        $remainingSeconds = $seconds % 60;

        $parts = [];
        if ($hours > 0) $parts[] = "{$hours}h";
        if ($minutes > 0) $parts[] = "{$minutes}m";
        if ($remainingSeconds > 0) $parts[] = "{$remainingSeconds}s";

        return implode(' ', $parts);
    }
}
