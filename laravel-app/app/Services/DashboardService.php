<?php

namespace App\Services;

use App\Models\Scan;
use App\Models\RealtimeSession;
use App\Models\RealtimeScan;
use App\Models\ScanDefect;
use App\Models\RealtimeScanDefect;
use Illuminate\Support\Facades\DB;
use Carbon\Carbon;

class DashboardService
{
    /**
     * Get complete dashboard data for the authenticated user
     */
    public function getDashboardData(array $filters = []): array
    {
        return [
            'cardData' => $this->getCardDataOnly(),
            'dailyAnalysis' => $this->getDailyTrendOnly(7),
            'defectType' => $this->getDefectTypeDistribution(),
            'performanceTrend' => $this->getPerformanceTrend(30),
            'recentAnalyses' => $this->getRecentAnalysesOnly(10),
        ];
    }

    /**
     * Get card data for the top 4 statistics cards
     */
    public function getCardDataOnly(): array
    {
        $userId = auth()->id();

        // Get data for current period
        $currentData = $this->getCardDataForPeriod($userId, now()->startOfDay(), now()->endOfDay());

        // Get data for previous period (for comparison)
        $previousData = $this->getCardDataForPeriod($userId, now()->subDay()->startOfDay(), now()->subDay()->endOfDay());

        return [
            'totalDefective' => $currentData['totalDefective'],
            'totalScansImage' => $currentData['totalScansImage'],
            'totalRealtimeSessions' => $currentData['totalRealtimeSessions'],
            'totalFramesProcessed' => $currentData['totalFramesProcessed'],
            'defectiveChangeRate' => $this->calculateChangeRate($previousData['totalDefective'], $currentData['totalDefective']),
            'scansChangeRate' => $this->calculateChangeRate($previousData['totalScansImage'], $currentData['totalScansImage']),
            'sessionsChangeRate' => $this->calculateChangeRate($previousData['totalRealtimeSessions'], $currentData['totalRealtimeSessions']),
            'framesChangeRate' => $this->calculateChangeRate($previousData['totalFramesProcessed'], $currentData['totalFramesProcessed']),
        ];
    }

    /**
     * Get card data for a specific period
     */
    private function getCardDataForPeriod(int $userId, Carbon $startDate, Carbon $endDate): array
    {
        // Total defective products from image scans
        $totalDefectiveFromScans = Scan::where('user_id', $userId)
            ->where('is_defect', true)
            ->whereBetween('created_at', [$startDate, $endDate])
            ->count();

        // Total defective products from realtime scans
        $totalDefectiveFromRealtime = RealtimeScan::whereHas('realtimeSession', function ($query) use ($userId) {
            $query->where('user_id', $userId);
        })
            ->where('is_defect', true)
            ->whereBetween('created_at', [$startDate, $endDate])
            ->count();

        // Total image scans processed
        $totalScansImage = Scan::where('user_id', $userId)
            ->whereBetween('created_at', [$startDate, $endDate])
            ->count();

        // Total realtime sessions
        $totalRealtimeSessions = RealtimeSession::where('user_id', $userId)
            ->whereBetween('created_at', [$startDate, $endDate])
            ->count();

        // Total frames processed (realtime scans)
        $totalFramesProcessed = RealtimeScan::whereHas('realtimeSession', function ($query) use ($userId) {
            $query->where('user_id', $userId);
        })
            ->whereBetween('created_at', [$startDate, $endDate])
            ->count();

        return [
            'totalDefective' => $totalDefectiveFromScans + $totalDefectiveFromRealtime,
            'totalScansImage' => $totalScansImage,
            'totalRealtimeSessions' => $totalRealtimeSessions,
            'totalFramesProcessed' => $totalFramesProcessed,
        ];
    }

    /**
     * Get daily analysis trend data
     */
    public function getDailyTrendOnly(int $days = 7): array
    {
        $userId = auth()->id();
        $startDate = now()->subDays($days - 1)->startOfDay();
        $endDate = now()->endOfDay();

        $labels = [];
        $totalDefective = [];
        $totalProcessed = [];

        for ($i = 0; $i < $days; $i++) {
            $date = $startDate->copy()->addDays($i);
            $labels[] = $date->format('Y-m-d');

            // Count defective items for this date
            $defectiveFromScans = Scan::where('user_id', $userId)
                ->where('is_defect', true)
                ->whereDate('created_at', $date)
                ->count();

            $defectiveFromRealtime = RealtimeScan::whereHas('realtimeSession', function ($query) use ($userId) {
                $query->where('user_id', $userId);
            })
                ->where('is_defect', true)
                ->whereDate('created_at', $date)
                ->count();

            $totalDefective[] = $defectiveFromScans + $defectiveFromRealtime;

            // Count total processed items for this date
            $processedScans = Scan::where('user_id', $userId)
                ->whereDate('created_at', $date)
                ->count();

            $processedFrames = RealtimeScan::whereHas('realtimeSession', function ($query) use ($userId) {
                $query->where('user_id', $userId);
            })
                ->whereDate('created_at', $date)
                ->count();

            $totalProcessed[] = $processedScans + $processedFrames;
        }

        return [
            'labels' => $labels,
            'totalDefective' => $totalDefective,
            'totalProcessed' => $totalProcessed,
        ];
    }

    /**
     * Get defect type distribution
     */
    public function getDefectTypeDistribution(): array
    {
        $userId = auth()->id();

        // Get defects from image scans
        $scanDefects = ScanDefect::whereHas('scan', function ($query) use ($userId) {
            $query->where('user_id', $userId);
        })
            ->select('label', DB::raw('count(*) as count'))
            ->groupBy('label')
            ->get();

        // Get defects from realtime scans
        $realtimeDefects = RealtimeScanDefect::whereHas('realtimeScan.realtimeSession', function ($query) use ($userId) {
            $query->where('user_id', $userId);
        })
            ->select('label', DB::raw('count(*) as count'))
            ->groupBy('label')
            ->get();

        // Combine and aggregate the results
        $combined = [];
        foreach ($scanDefects as $defect) {
            $combined[$defect->label] = ($combined[$defect->label] ?? 0) + $defect->count;
        }

        foreach ($realtimeDefects as $defect) {
            $combined[$defect->label] = ($combined[$defect->label] ?? 0) + $defect->count;
        }

        return [
            'labels' => array_keys($combined),
            'data' => array_values($combined),
        ];
    }

    /**
     * Get performance trend data
     */
    public function getPerformanceTrend(int $days = 30): array
    {
        $userId = auth()->id();
        $startDate = now()->subDays($days - 1)->startOfDay();
        $endDate = now()->endOfDay();

        $labels = [];
        $data = [];

        for ($i = 0; $i < $days; $i++) {
            $date = $startDate->copy()->addDays($i);
            $labels[] = $date->format('Y-m-d');

            // Count total defects detected for this date
            $defectiveFromScans = Scan::where('user_id', $userId)
                ->where('is_defect', true)
                ->whereDate('created_at', $date)
                ->count();

            $defectiveFromRealtime = RealtimeScan::whereHas('realtimeSession', function ($query) use ($userId) {
                $query->where('user_id', $userId);
            })
                ->where('is_defect', true)
                ->whereDate('created_at', $date)
                ->count();

            $data[] = $defectiveFromScans + $defectiveFromRealtime;
        }

        return [
            'labels' => $labels,
            'data' => $data,
        ];
    }

    /**
     * Get recent analyses
     */
    public function getRecentAnalysesOnly(int $limit = 10): array
    {
        $userId = auth()->id();

        // Get recent scans
        $recentScans = Scan::where('user_id', $userId)
            ->with(['scanDefects', 'user'])
            ->orderBy('created_at', 'desc')
            ->limit($limit)
            ->get()
            ->map(function ($scan) {
                return [
                    'id' => $scan->id,
                    'filename' => $scan->filename,
                    'status' => $scan->is_defect ? 'defect' : 'good',
                    'anomaly_score' => $scan->anomaly_score,
                    'defect_count' => $scan->scanDefects->count(),
                    'created_at' => $scan->created_at->format('Y-m-d H:i:s'),
                    'route' => route('scans.show', $scan->id),
                ];
            });

        return $recentScans->toArray();
    }

    /**
     * Get overview data for charts and widgets
     */
    public function getOverviewDataOnly(): array
    {
        $cardData = $this->getCardDataOnly();

        return [
            'totalAnalyses' => $cardData['totalScansImage'] + $cardData['totalFramesProcessed'],
            'defectRate' => $this->getDefectRate(),
            'avgProcessingTime' => $this->getAverageProcessingTime(),
            'topDefectType' => $this->getTopDefectType(),
        ];
    }

    /**
     * Calculate change rate between two values
     */
    private function calculateChangeRate(int $previous, int $current): string
    {
        if ($previous == 0) {
            return $current > 0 ? '+100%' : '+0%';
        }

        $change = (($current - $previous) / $previous) * 100;
        $sign = $change >= 0 ? '+' : '';

        return $sign . number_format($change, 1) . '%';
    }

    /**
     * Calculate overall defect rate
     */
    private function getDefectRate(): float
    {
        $userId = auth()->id();

        $totalDefective = Scan::where('user_id', $userId)->where('is_defect', true)->count() +
            RealtimeScan::whereHas('realtimeSession', function ($query) use ($userId) {
                $query->where('user_id', $userId);
            })->where('is_defect', true)->count();

        $totalProcessed = Scan::where('user_id', $userId)->count() +
            RealtimeScan::whereHas('realtimeSession', function ($query) use ($userId) {
                $query->where('user_id', $userId);
            })->count();

        return $totalProcessed > 0 ? round(($totalDefective / $totalProcessed) * 100, 2) : 0;
    }

    /**
     * Get average processing time
     */
    private function getAverageProcessingTime(): float
    {
        $userId = auth()->id();

        $scanAvg = Scan::where('user_id', $userId)
            ->selectRaw('AVG(COALESCE(preprocessing_time_ms, 0) + COALESCE(anomaly_inference_time_ms, 0) + COALESCE(classification_inference_time_ms, 0) + COALESCE(postprocessing_time_ms, 0)) as avg_time')
            ->value('avg_time') ?? 0;

        $realtimeAvg = RealtimeScan::whereHas('realtimeSession', function ($query) use ($userId) {
            $query->where('user_id', $userId);
        })
            ->selectRaw('AVG(COALESCE(preprocessing_time_ms, 0) + COALESCE(anomaly_inference_time_ms, 0) + COALESCE(classification_inference_time_ms, 0) + COALESCE(postprocessing_time_ms, 0)) as avg_time')
            ->value('avg_time') ?? 0;

        return round(($scanAvg + $realtimeAvg) / 2, 2);
    }

    /**
     * Get the most common defect type
     */
    private function getTopDefectType(): ?string
    {
        $defectDistribution = $this->getDefectTypeDistribution();

        if (empty($defectDistribution['data'])) {
            return null;
        }

        $maxIndex = array_search(max($defectDistribution['data']), $defectDistribution['data']);

        return $defectDistribution['labels'][$maxIndex] ?? null;
    }

    /**
     * Get defect trend data (legacy method for backward compatibility)
     */
    public function getDefectTrendOnly(?string $filterMonth = null): array
    {
        return $this->getDailyTrendOnly(30);
    }
}
