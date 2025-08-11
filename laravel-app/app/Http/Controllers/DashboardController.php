<?php

namespace App\Http\Controllers;

use App\Services\DashboardService;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;
use Inertia\Inertia;
use Inertia\Response;

class DashboardController extends Controller
{
    protected DashboardService $dashboardService;

    public function __construct(DashboardService $dashboardService)
    {
        $this->dashboardService = $dashboardService;
    }

    /**
     * Display the dashboard page
     */
    public function index(): Response
    {

        $dashboardData = $this->dashboardService->getDashboardData();

        return Inertia::render('Dashboard/Index', $dashboardData);
    }

    /**
     * API endpoint for getting dashboard data (for manual refresh)
     */
    public function indexApi(): JsonResponse
    {

        $dashboardData = $this->dashboardService->getDashboardData();

        return response()->json([
            'status' => 'success',
            'data' => $dashboardData,
            'timestamp' => now()->toISOString(),
        ]);
    }
}
