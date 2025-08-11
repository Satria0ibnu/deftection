<?php

namespace App\Services;

use App\Models\DefectType;
use Illuminate\Support\Carbon;
use App\Models\RealtimeSession;
use Illuminate\Support\Facades\Storage;

class RealtimeSessionDetailService
{
    /**
     * Get session data in the exact format expected by the Vue component
     */
    public function getSessionData(RealtimeSession $session): array
    {
        // Load session with related data
        $session->load([
            'realtimeScans' => function ($query) {
                $query->orderBy('captured_at', 'asc');
            },
            'realtimeScans.realtimeScanDefects'
        ]);

        // Calculate session duration
        $duration = $this->calculateSessionDuration($session);

        // Process scans data in the exact format your Vue component expects
        $scans = $session->realtimeScans->map(function ($scan) {
            return [
                'id' => $scan->id,
                'filename' => $scan->filename,
                'created_at' => Carbon::parse($scan->captured_at)->toISOString(),

                'status' => $scan->is_defect ? 'defect' : 'good',
                'anomaly_score' => $scan->anomaly_score,
                'original_path' => $this->getImagePath($scan->filename, $scan->is_defect),
            ];
        });

        // Calculate defect distribution for DonutChart
        $defectDistribution = $this->calculateDefectDistribution($session->realtimeScans);

        // Return data in the exact format your Vue component expects
        return [
            'id' => $session->id,
            'date' => $session->session_start->format('d/m/Y'),
            'startTime' => $session->session_start->format('H:i:s'),
            'endTime' => $session->session_end ? $session->session_end->format('H:i:s') : null,
            'duration' => $duration,
            'total_scans' => $session->total_frames_processed ?? $session->realtimeScans->count(),
            'good_scans' => $session->good_count ?? $session->realtimeScans->where('is_defect', false)->count(),
            'defected_scans' => $session->defect_count ?? $session->realtimeScans->where('is_defect', true)->count(),
            'defect_rate' => $session->defect_rate ?? $this->calculateDefectRate($session->realtimeScans),
            'status' => ucfirst($session->session_status ?? 'Completed'),
            'scans' => $scans->toArray(),
            'defectDistribution' => $defectDistribution,
        ];
    }

    /**
     * Calculate session duration
     */
    private function calculateSessionDuration(RealtimeSession $session): string
    {
        if (!$session->session_start) {
            return 'Unknown';
        }

        $endTime = $session->session_end ?? now();
        $duration = $session->session_start->diffInSeconds($endTime);

        $hours = floor($duration / 3600);
        $minutes = floor(($duration % 3600) / 60);

        if ($hours > 0) {
            return "{$hours} hour" . ($hours > 1 ? 's' : '') . " {$minutes} minute" . ($minutes != 1 ? 's' : '');
        }

        return "{$minutes} minute" . ($minutes != 1 ? 's' : '');
    }

    /**
     * Calculate defect rate
     */
    private function calculateDefectRate($scans): float
    {
        $total = $scans->count();
        if ($total === 0) return 0.0;

        $defectCount = $scans->where('is_defect', true)->count();
        return round(($defectCount / $total) * 100, 1);
    }

    /**
     * Calculate defect distribution for charts
     */
    private function calculateDefectDistribution($scans): array
    {
        $defectScans = $scans->where('is_defect', true);

        if ($defectScans->count() === 0) {
            return [];
        }

        $distribution = [];

        foreach ($defectScans as $scan) {
            foreach ($scan->realtimeScanDefects as $defect) {
                $defectName = $this->getDefectTypeName($defect->label);
                $distribution[$defectName] = ($distribution[$defectName] ?? 0) + 1;
            }
        }

        return $distribution;
    }

    /**
     * Get defect type name from label
     */
    private function getDefectTypeName(string $label): string
    {
        // Try to get from DefectType model, fallback to formatted label
        $defectType = DefectType::where('slug', $label)->first();
        return $defectType ? $defectType->name : ucwords(str_replace('_', ' ', $label));
    }

    /**
     * Get image path with proper placeholders for good/defect status
     */
    private function getImagePath(string $filename, bool $isDefect = false): string
    {
        // Check if file exists in storage
        if (Storage::disk('public')->exists('realtime_scans/' . $filename)) {
            return Storage::url('realtime_scans/' . $filename);
        }

        // Return placeholder based on status - matching your current format
        if ($isDefect) {
            return "";
        } else {
            return "";
        }
    }
}
