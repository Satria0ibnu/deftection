<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Middleware\RoleMiddleware;
use Illuminate\Support\Facades\Artisan;
use App\Http\Controllers\Api\ProductApiController;

// Route::get('/user', function (Request $request) {
//     return $request->user();
// })->middleware('auth:sanctum');

// its automatically has api/ prefix



Route::middleware('auth:sanctum')->group(function () {
    Route::middleware(RoleMiddleware::class . ':uasser,adsad,user')->group(function () {
        // Route::get('/dashboard', [DashboardController::class, 'index'])->name('api.dashboard');
    });
});


Route::get('/clear-all', function () {
    Artisan::call('cache:clear');
    Artisan::call('config:clear');
    Artisan::call('config:cache');
    Artisan::call('route:clear');
    Artisan::call('view:clear');

    return response()->json(['message' => 'All caches cleared successfully!']);
});
