<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ $reportTitle }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'DejaVu Sans', Arial, sans-serif;
            font-size: 11px;
            line-height: 1.5;
            color: #333;
            margin: 15mm 10mm 15mm 10mm;
        }

        @page {
            margin: 15mm 10mm 15mm 10mm;
            size: A4;
        }

        .page-break {
            page-break-after: always;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px 0;
            border-bottom: 3px solid #007bff;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 8px 8px 0 0;
        }

        .header h1 {
            font-size: 24px;
            color: #007bff;
            margin-bottom: 10px;
            font-weight: 700;
        }

        .header .subtitle {
            font-size: 14px;
            color: #6c757d;
            font-weight: 500;
        }

        .section {
            margin-bottom: 30px;
        }

        .section-title {
            font-size: 18px;
            font-weight: 700;
            color: #007bff;
            margin-bottom: 15px;
            padding-bottom: 6px;
            border-bottom: 2px solid #007bff;
            position: relative;
        }

        .section-title::after {
            content: '';
            position: absolute;
            bottom: -2px;
            left: 0;
            width: 50px;
            height: 2px;
            background-color: #28a745;
        }

        /* Session Info */
        .session-info {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 20px;
        }

        .info-grid {
            display: table;
            width: 100%;
        }

        .info-row {
            display: table-row;
        }

        .info-column {
            display: table-cell;
            width: 50%;
            vertical-align: top;
            padding-right: 15px;
        }

        .info-column:last-child {
            padding-right: 0;
            padding-left: 15px;
        }

        .info-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }

        .info-item:last-child {
            border-bottom: none;
        }

        .info-label {
            font-weight: 600;
            color: #555;
        }

        .info-value {
            color: #333;
        }

        /* Dashboard */
        .summary-dashboard {
            background: #ffffff;
            border: 1px solid #ddd;
            border-radius: 6px;
            overflow: hidden;
            margin-bottom: 20px;
        }

        .summary-row {
            display: table;
            width: 100%;
        }

        .summary-cell {
            display: table-cell;
            padding: 12px;
            text-align: center;
            border-right: 1px solid #eee;
            vertical-align: middle;
        }

        .summary-cell:last-child {
            border-right: none;
        }

        .summary-cell.header {
            background: #f8f9fa;
            font-weight: 600;
            font-size: 10px;
            text-transform: uppercase;
            color: #666;
            border-bottom: 1px solid #ddd;
        }

        .summary-cell .value {
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 2px;
        }

        .summary-cell .label {
            font-size: 9px;
            color: #666;
            text-transform: uppercase;
        }

        /* Status badges */
        .status-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-weight: 500;
            font-size: 9px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            min-width: 60px;
            text-align: center;
        }

        .status-completed {
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            color: #155724;
            border: 1px solid #28a745;
        }

        .status-active {
            background: linear-gradient(135deg, #cce5ff 0%, #b3d9ff 100%);
            color: #004085;
            border: 1px solid #007bff;
        }

        .status-paused {
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
            color: #856404;
            border: 1px solid #ffc107;
        }

        .status-stopped {
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
            color: #721c24;
            border: 1px solid #dc3545;
        }

        .status-aborted {
            background: linear-gradient(135deg, #f0f0f0 0%, #e0e0e0 100%);
            color: #495057;
            border: 1px solid #6c757d;
        }

        /* Performance Grid */
        .processing-grid {
            display: table;
            width: 100%;
            margin-bottom: 20px;
        }

        .processing-row {
            display: table-row;
        }

        .processing-stage {
            display: table-cell;
            background: #f8f9fa;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            text-align: center;
            width: 25%;
        }

        .processing-stage h4 {
            font-size: 11px;
            color: #666;
            margin-bottom: 5px;
            text-transform: uppercase;
        }

        .processing-stage .time {
            font-size: 14px;
            font-weight: bold;
            color: #2c3e50;
        }

        /* Data Tables */
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15px;
            font-size: 10px;
        }

        .data-table th,
        .data-table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }

        .data-table th {
            background: #f8f9fa;
            font-weight: 600;
            color: #555;
            font-size: 9px;
            text-transform: uppercase;
        }

        .data-table tr:nth-child(even) {
            background: #f9f9f9;
        }

        /* Charts */
        .chart-container {
            text-align: center;
            margin: 15px 0;
            page-break-inside: avoid;
        }

        .chart-container img {
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
        }

        .chart-title {
            font-size: 14px;
            font-weight: 600;
            color: #495057;
            margin-bottom: 10px;
        }

        /* Highlight boxes */
        .highlight-box {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            margin: 15px 0;
            border-radius: 0 4px 4px 0;
        }

        .highlight-box h4 {
            color: #1976d2;
            margin-bottom: 8px;
            font-size: 12px;
        }

        .highlight-box p {
            margin-bottom: 5px;
            font-size: 10px;
            line-height: 1.4;
        }

        .warning-box {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 15px 0;
            border-radius: 0 4px 4px 0;
        }

        .warning-box h4 {
            color: #856404;
            margin-bottom: 8px;
            font-size: 12px;
        }

        .error-box {
            background: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 15px;
            margin: 15px 0;
            border-radius: 0 4px 4px 0;
        }

        .error-box h4 {
            color: #721c24;
            margin-bottom: 8px;
            font-size: 12px;
        }

        /* Defect Items */
        .defect-item {
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 12px;
            margin-bottom: 10px;
        }

        .defect-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }

        .defect-type {
            font-weight: 600;
            color: #dc3545;
            font-size: 12px;
        }

        .defect-confidence {
            background: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 9px;
            color: #666;
        }

        .defect-details {
            font-size: 10px;
            color: #666;
            margin-top: 5px;
        }

        /* Two column layout */
        .two-column {
            display: table;
            width: 100%;
        }

        .column {
            display: table-cell;
            width: 50%;
            vertical-align: top;
            padding-right: 15px;
        }

        .column:last-child {
            padding-right: 0;
            padding-left: 15px;
        }

        /* No data states */
        .no-data {
            text-align: center;
            padding: 30px;
            background: #f8f9fa;
            border-radius: 6px;
            color: #6c757d;
            font-style: italic;
        }

        .empty-state {
            text-align: center;
            padding: 30px;
            background: #f8f9fa;
            border-radius: 6px;
            border: 1px dashed #dee2e6;
        }

        /* Footer */
        .footer {
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #ddd;
            text-align: center;
            font-size: 9px;
            color: #666;
        }

        /* Print optimization */
        @media print {
            .section {
                page-break-inside: avoid;
            }

            .chart-container {
                page-break-inside: avoid;
            }

            .defect-item {
                page-break-inside: avoid;
            }
        }

        /* Utility classes */
        .null-value {
            color: #9ca3af;
            font-style: italic;
            font-size: 10px;
        }

        .font-bold {
            font-weight: 600;
        }

        .text-sm {
            font-size: 10px;
        }

        .mb-1 {
            margin-bottom: 8px;
        }

        .mt-1 {
            margin-top: 8px;
        }
    </style>
</head>

<body>
    <!-- Header -->
    <div class="header">
        <h1>{{ $reportTitle ?? 'Realtime Session Analysis Report' }}</h1>
        <div class="subtitle">Generated on {{ ($generatedAt ?? now())->format('F j, Y \a\t g:i A T') }}</div>
    </div>

    <!-- Session Information -->
    <div class="section">
        <h2 class="section-title">Session Information</h2>
        <div class="session-info">
            <div class="info-grid">
                <div class="info-row">
                    <div class="info-column">
                        <div class="info-item">
                            <span class="info-label">Session ID:</span>
                            <span class="info-value">#{{ $summary['session_id'] ?? 'N/A' }}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">User:</span>
                            <span class="info-value">{{ $summary['user_name'] ?? 'Unknown User' }}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Email:</span>
                            <span class="info-value">{{ $summary['user_email'] ?? 'N/A' }}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Status:</span>
                            <span class="info-value">
                                <span
                                    class="status-badge status-{{ strtolower($summary['session_status'] ?? 'unknown') }}">
                                    {{ $summary['session_status'] ?? 'Unknown' }}
                                </span>
                            </span>
                        </div>
                    </div>
                    <div class="info-column">
                        <div class="info-item">
                            <span class="info-label">Camera Location:</span>
                            <span class="info-value">{{ $summary['camera_location'] ?? 'Not specified' }}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Session Start:</span>
                            <span class="info-value">
                                {{ isset($summary['session_start']) ? $summary['session_start']->format('M j, Y g:i A') : 'N/A' }}
                            </span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Session End:</span>
                            <span class="info-value">
                                {{ isset($summary['session_end']) && $summary['session_end'] ? $summary['session_end']->format('M j, Y g:i A') : 'Ongoing' }}
                            </span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Duration:</span>
                            <span class="info-value">{{ $summary['duration'] ?? 'N/A' }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Executive Summary -->
    <div class="section">
        <h2 class="section-title">Executive Summary</h2>
        <div class="summary-dashboard">
            <div class="summary-row">
                <div class="summary-cell header">Total Frames</div>
                <div class="summary-cell header">Defective</div>
                <div class="summary-cell header">Good</div>
                <div class="summary-cell header">Defect Rate</div>
                <div class="summary-cell header">Throughput</div>
            </div>
            <div class="summary-row">
                <div class="summary-cell">
                    <div class="value">{{ number_format($statistics['total_frames'] ?? 0) }}</div>
                    <div class="label">Frames</div>
                </div>
                <div class="summary-cell">
                    <div class="value">{{ number_format($statistics['defective_frames'] ?? 0) }}</div>
                    <div class="label">Defective</div>
                </div>
                <div class="summary-cell">
                    <div class="value">{{ number_format($statistics['good_frames'] ?? 0) }}</div>
                    <div class="label">Good</div>
                </div>
                <div class="summary-cell">
                    <div class="value">{{ number_format($statistics['defect_rate'] ?? 0, 1) }}%</div>
                    <div class="label">Rate</div>
                </div>
                <div class="summary-cell">
                    <div class="value">{{ number_format($statistics['throughput_fps'] ?? 0, 1) }}</div>
                    <div class="label">FPM</div>
                </div>
            </div>
        </div>

        <div class="summary-dashboard">
            <div class="summary-row">
                <div class="summary-cell header">Total Defects</div>
                <div class="summary-cell header">Avg Processing</div>
                <div class="summary-cell header">Avg Anomaly</div>
                <div class="summary-cell header">Max Anomaly</div>
                <div class="summary-cell header">Min Anomaly</div>
            </div>
            <div class="summary-row">
                <div class="summary-cell">
                    <div class="value">{{ number_format($statistics['total_defects_found'] ?? 0) }}</div>
                    <div class="label">Defects</div>
                </div>
                <div class="summary-cell">
                    <div class="value">{{ number_format($statistics['avg_processing_time'] ?? 0, 1) }}</div>
                    <div class="label">ms</div>
                </div>
                <div class="summary-cell">
                    <div class="value">{{ number_format($statistics['avg_anomaly_score'] ?? 0, 3) }}</div>
                    <div class="label">Score</div>
                </div>
                <div class="summary-cell">
                    <div class="value">{{ number_format($statistics['max_anomaly_score'] ?? 0, 3) }}</div>
                    <div class="label">Score</div>
                </div>
                <div class="summary-cell">
                    <div class="value">{{ number_format($statistics['min_anomaly_score'] ?? 0, 3) }}</div>
                    <div class="label">Score</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Performance Analysis -->
    <div class="section">
        <h2 class="section-title">Performance Analysis</h2>

        @if (!empty($chartsData['processing_performance']))
            <div class="processing-grid">
                <div class="processing-row">
                    @foreach ($chartsData['processing_performance'] as $stage => $data)
                        <div class="processing-stage">
                            <h4>{{ ucfirst(str_replace('_', ' ', $stage)) }}</h4>
                            <div class="time">{{ number_format($data['avg'] ?? 0, 1) }}ms</div>
                            <div style="font-size: 9px; color: #666; margin-top: 3px;">
                                Range: {{ number_format($data['min'] ?? 0, 1) }} -
                                {{ number_format($data['max'] ?? 0, 1) }}ms
                            </div>
                        </div>
                    @endforeach
                </div>
            </div>
        @else
            <div class="empty-state">
                <h3>No Performance Data Available</h3>
                <p>Processing performance metrics could not be calculated for this session.</p>
            </div>
        @endif

        @if (!empty($chartImages['processing_performance']))
            <div class="chart-container">
                <div class="chart-title">Processing Performance Chart</div>
                <img src="{{ $chartImages['processing_performance'] }}" alt="Processing Performance Chart">
            </div>
        @endif
    </div>

    <!-- Frame Processing Trends -->
    @if (!empty($chartImages['frame_trends']))
        <div class="section">
            <h2 class="section-title">Frame Processing Trends</h2>
            <div class="chart-container">
                <div class="chart-title">Frame Processing Trends</div>
                <img src="{{ $chartImages['frame_trends'] }}" alt="Frame Processing Trends Chart">
            </div>
        </div>
    @endif

    <!-- Defect Analysis -->
    @if (($statistics['total_defects_found'] ?? 0) > 0)
        <div class="section">
            <h2 class="section-title">Defect Analysis</h2>

            @if (!empty($chartImages['defect_distribution']))
                <div class="chart-container">
                    <div class="chart-title">Defect Distribution</div>
                    <img src="{{ $chartImages['defect_distribution'] }}" alt="Defect Distribution Chart">
                </div>
            @endif

            @if (!empty($chartsData['defect_distribution']))
                <div class="highlight-box">
                    <h4>Defect Type Distribution</h4>
                    @foreach ($chartsData['defect_distribution'] as $defect)
                        <p>• <strong>{{ $defect['label'] ?? 'Unknown' }}:</strong> {{ $defect['count'] ?? 0 }}
                            occurrences</p>
                    @endforeach
                </div>
            @endif

            @if (isset($defects) && $defects->isNotEmpty())
                <h3 style="margin: 20px 0 10px 0; font-size: 14px; color: #2c3e50;">Detected Defects</h3>
                @foreach ($defects->take(5) as $defect)
                    <div class="defect-item">
                        <div class="defect-header">
                            <span class="defect-type">{{ $defect['label'] ?? 'Unknown Defect' }}</span>
                            <span class="defect-confidence">{{ number_format($defect['confidence_score'] ?? 0, 3) }}
                                confidence</span>
                        </div>
                        <div class="defect-details">
                            <strong>Frame:</strong> {{ $defect['scan_filename'] ?? 'N/A' }} |
                            <strong>Severity:</strong> {{ $defect['severity_level'] ?? 'Unknown' }} |
                            <strong>Area:</strong> {{ number_format($defect['area_percentage'] ?? 0, 2) }}% |
                            <strong>Time:</strong>
                            {{ isset($defect['scan_captured_at']) ? Carbon\Carbon::parse($defect['scan_captured_at'])->format('H:i:s') : 'N/A' }}
                        </div>
                        @if (!empty($defect['explanation']))
                            <div class="defect-details" style="margin-top: 5px;">
                                {{ $defect['explanation'] }}
                            </div>
                        @endif
                    </div>
                @endforeach

                @if ($defects->count() > 5)
                    <div class="highlight-box">
                        <p><strong>Note:</strong> Showing first 5 defects. Total defects found:
                            {{ $defects->count() }}</p>
                    </div>
                @endif
            @endif
        </div>
    @else
        <div class="section">
            <h2 class="section-title">Defect Analysis</h2>
            <div class="no-data">
                <h3>No Defects Detected</h3>
                <p>This session completed successfully with no quality issues identified.</p>
            </div>
        </div>
    @endif

    <!-- Anomaly Score Analysis -->
    @if (!empty($chartImages['anomaly_distribution']))
        <div class="section">
            <h2 class="section-title">Anomaly Score Analysis</h2>
            <div class="chart-container">
                <div class="chart-title">Anomaly Score Distribution</div>
                <img src="{{ $chartImages['anomaly_distribution'] }}" alt="Anomaly Score Distribution Chart">
            </div>

            @if (!empty($chartsData['anomaly_distribution']))
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Score Range</th>
                            <th>Frame Count</th>
                            <th>Percentage</th>
                            <th>Risk Level</th>
                        </tr>
                    </thead>
                    <tbody>
                        @foreach ($chartsData['anomaly_distribution'] as $range)
                            <tr>
                                <td>{{ $range['range'] ?? 'N/A' }}</td>
                                <td>{{ number_format($range['count'] ?? 0) }}</td>
                                <td>{{ number_format($range['percentage'] ?? 0, 1) }}%</td>
                                <td>
                                    @if (isset($range['range']) && strpos($range['range'], '0.8-1.0') !== false)
                                        <span style="color: #dc3545;">High</span>
                                    @elseif(isset($range['range']) && strpos($range['range'], '0.6-0.8') !== false)
                                        <span style="color: #ffc107;">Medium</span>
                                    @else
                                        <span style="color: #28a745;">Low</span>
                                    @endif
                                </td>
                            </tr>
                        @endforeach
                    </tbody>
                </table>
            @endif
        </div>
    @endif

    <div class="page-break"></div>

    <!-- Hourly Processing Patterns -->
    @if (!empty($chartImages['hourly_patterns']))
        <div class="section">
            <h2 class="section-title">Hourly Processing Patterns</h2>
            <div class="chart-container">
                <div class="chart-title">Hourly Processing Patterns</div>
                <img src="{{ $chartImages['hourly_patterns'] }}" alt="Hourly Processing Patterns Chart">
            </div>
        </div>
    @endif



    {{-- <div class="page-break"></div> --}}

    <!-- Technical Details -->
    <div class="section">
        <h2 class="section-title">Technical Details</h2>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Parameter</th>
                    <th>Value</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Session Duration</td>
                    <td>{{ $summary['duration'] ?? 'N/A' }}</td>
                    <td>Total time session was active</td>
                </tr>
                <tr>
                    <td>Frames Processed</td>
                    <td>{{ number_format($statistics['total_frames'] ?? 0) }}</td>
                    <td>Total number of frames analyzed</td>
                </tr>
                <tr>
                    <td>Processing Throughput</td>
                    <td>{{ number_format($statistics['throughput_fps'] ?? 0, 1) }} FPM</td>
                    <td>Frames processed per minute</td>
                </tr>
                <tr>
                    <td>Average Processing Time</td>
                    <td>{{ number_format($statistics['avg_processing_time'] ?? 0, 1) }}ms</td>
                    <td>Average time per frame processing</td>
                </tr>
                <tr>
                    <td>Quality Control Rate</td>
                    <td>{{ number_format($statistics['good_rate'] ?? 0, 1) }}%</td>
                    <td>Percentage of frames passing quality control</td>
                </tr>
                <tr>
                    <td>Anomaly Detection Range</td>
                    <td>{{ number_format($statistics['min_anomaly_score'] ?? 0, 3) }} -
                        {{ number_format($statistics['max_anomaly_score'] ?? 0, 3) }}</td>
                    <td>Range of anomaly scores detected</td>
                </tr>
                <tr>
                    <td>Session Status</td>
                    <td>
                        <span class="status-badge status-{{ strtolower($summary['session_status'] ?? 'unknown') }}">
                            {{ $summary['session_status'] ?? 'Unknown' }}
                        </span>
                    </td>
                    <td>Final session completion status</td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- Detailed Performance Breakdown -->
    @if (!empty($chartsData['processing_performance']))
        <div class="section">
            <h2 class="section-title">Processing Performance Breakdown</h2>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Processing Stage</th>
                        <th>Avg Time (ms)</th>
                        <th>Min Time (ms)</th>
                        <th>Max Time (ms)</th>
                        <th>% of Total</th>
                    </tr>
                </thead>
                <tbody>
                    @php
                        $totalTime = array_sum(array_column($chartsData['processing_performance'], 'avg'));
                    @endphp
                    @foreach ($chartsData['processing_performance'] as $stage => $data)
                        <tr>
                            <td>{{ ucfirst(str_replace('_', ' ', $stage)) }}</td>
                            <td>{{ number_format($data['avg'] ?? 0, 1) }}</td>
                            <td>{{ number_format($data['min'] ?? 0, 1) }}</td>
                            <td>{{ number_format($data['max'] ?? 0, 1) }}</td>
                            <td>{{ $totalTime > 0 ? number_format((($data['avg'] ?? 0) / $totalTime) * 100, 1) : 0 }}%
                            </td>
                        </tr>
                    @endforeach
                </tbody>
            </table>
        </div>
    @endif

    <!-- Hourly Processing Data -->
    @if (!empty($chartsData['hourly_patterns']))
        <div class="page-break"></div>
        <div class="section">
            <h2 class="section-title">Hourly Processing Data</h2>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Hour</th>
                        <th>Total Frames</th>
                        <th>Defective</th>
                        <th>Good</th>
                        <th>Defect Rate (%)</th>
                    </tr>
                </thead>
                <tbody>
                    @foreach ($chartsData['hourly_patterns'] as $hour)
                        <tr>
                            <td>{{ $hour['hour'] ?? 'N/A' }}</td>
                            <td>{{ $hour['total'] ?? 0 }}</td>
                            <td>{{ $hour['defective'] ?? 0 }}</td>
                            <td>{{ $hour['good'] ?? 0 }}</td>
                            <td>{{ ($hour['total'] ?? 0) > 0 ? number_format((($hour['defective'] ?? 0) / $hour['total']) * 100, 1) : 0 }}%
                            </td>
                        </tr>
                    @endforeach
                </tbody>
            </table>
        </div>
    @endif

    <div class="page-break"></div>
    <!-- Report Metadata -->
    <div class="section">
        <h2 class="section-title">Report Metadata</h2>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Parameter</th>
                    <th>Value</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Report Generation Time</td>
                    <td>{{ ($generatedAt ?? now())->format('Y-m-d H:i:s T') }}</td>
                    <td>When this report was generated</td>
                </tr>
                <tr>
                    <td>Session Period</td>
                    <td>
                        {{ isset($summary['session_start']) ? $summary['session_start']->format('Y-m-d H:i') : 'N/A' }}
                        to
                        {{ isset($summary['session_end']) && $summary['session_end'] ? $summary['session_end']->format('Y-m-d H:i') : 'Ongoing' }}
                    </td>
                    <td>Session start and end times</td>
                </tr>
                <tr>
                    <td>Data Coverage</td>
                    <td>{{ ($statistics['total_defects_found'] ?? 0) > 0 ? 'Complete' : 'No Defects Found' }}</td>
                    <td>Defect detection coverage status</td>
                </tr>
                <tr>
                    <td>Chart Generation</td>
                    <td>{{ count(array_filter($chartImages ?? [])) }} / {{ count($chartImages ?? []) }}</td>
                    <td>Successfully generated charts vs total charts</td>
                </tr>
                <tr>
                    <td>Report Scope</td>
                    <td>Single Session Report</td>
                    <td>Analysis scope (session-specific)</td>
                </tr>
                <tr>
                    <td>Target Session</td>
                    <td>Session #{{ $summary['session_id'] ?? 'N/A' }} ({{ $summary['user_name'] ?? 'Unknown User' }})
                    </td>
                    <td>Specific session analysis target</td>
                </tr>
                <tr>
                    <td>Data Quality</td>
                    <td>
                        @if (($statistics['total_frames'] ?? 0) > 100)
                            High
                        @elseif (($statistics['total_frames'] ?? 0) > 20)
                            Medium
                        @elseif (($statistics['total_frames'] ?? 0) > 0)
                            Limited
                        @else
                            No Data
                        @endif
                    </td>
                    <td>Statistical significance of dataset</td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- Summary Statistics -->
    <div class="section">
        <h2 class="section-title">Executive Summary Statistics</h2>
        <div class="two-column">
            <div class="column">
                <h4 style="font-size: 12px; margin-bottom: 8px;">Quality Metrics</h4>
                <table class="data-table">
                    <tbody>
                        <tr>
                            <td><strong>Overall Quality Score</strong></td>
                            <td>{{ number_format(100 - ($statistics['defect_rate'] ?? 0), 1) }}%</td>
                        </tr>
                        <tr>
                            <td><strong>Average Anomaly Score</strong></td>
                            <td>{{ number_format($statistics['avg_anomaly_score'] ?? 0, 3) }}</td>
                        </tr>
                        <tr>
                            <td><strong>Defects per Frame</strong></td>
                            <td>{{ ($statistics['total_frames'] ?? 0) > 0 ? number_format(($statistics['total_defects_found'] ?? 0) / $statistics['total_frames'], 2) : 0 }}
                            </td>
                        </tr>
                        <tr>
                            <td><strong>Session Efficiency</strong></td>
                            <td>{{ ($statistics['avg_processing_time'] ?? 0) < 500 ? 'Excellent' : (($statistics['avg_processing_time'] ?? 0) < 1000 ? 'Good' : 'Needs Improvement') }}
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <div class="column">
                <h4 style="font-size: 12px; margin-bottom: 8px;">Performance Metrics</h4>
                <table class="data-table">
                    <tbody>
                        <tr>
                            <td><strong>Processing Efficiency</strong></td>
                            <td>{{ ($statistics['avg_processing_time'] ?? 0) < 500 ? 'Excellent' : (($statistics['avg_processing_time'] ?? 0) < 1000 ? 'Good' : 'Needs Improvement') }}
                            </td>
                        </tr>
                        <tr>
                            <td><strong>Peak Throughput</strong></td>
                            <td>{{ number_format($statistics['throughput_fps'] ?? 0, 1) }} FPM</td>
                        </tr>
                        <tr>
                            <td><strong>Total Processing Time</strong></td>
                            <td>{{ ($statistics['avg_processing_time'] ?? 0) > 0 && ($statistics['total_frames'] ?? 0) > 0 ? number_format(($statistics['avg_processing_time'] * $statistics['total_frames']) / 1000, 1) : 0 }}s
                            </td>
                        </tr>
                        <tr>
                            <td><strong>System Reliability</strong></td>
                            <td>{{ ($statistics['total_frames'] ?? 0) > 0 ? '99.9%' : 'N/A' }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <div class="footer">
        <p>Realtime Session Analysis Report | Generated on {{ ($generatedAt ?? now())->format('Y-m-d H:i:s') }} |
            Session #{{ $summary['session_id'] ?? 'N/A' }} | Total Frames:
            {{ number_format($statistics['total_frames'] ?? 0) }}
        </p>
    </div>
</body>

</html>
