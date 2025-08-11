<?php

namespace App\Http\Controllers;

use App\Models\Scan;
use Inertia\Inertia;
use Illuminate\Http\Request;
use App\Models\RealtimeSession;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Storage;

class SettingsController extends Controller
{
    //
    public function index()
    {
        // Initialize default values first, in case the API call fails
        $apiDefaults = [
            'anomaly_threshold' => 0.7,
            'defect_confidence_threshold' => 0.85,
        ];

        try {
            $response = Http::timeout(5)->get(env('FLASK_API_URL') . '/api/config/thresholds');

            // Check if the request was successful (status code 2xx)
            if ($response->successful()) {
                $responseData = $response->json(); // Decode JSON only once
                Log::info('Fetched thresholds from Flask API', [
                    'status' => $response->status(),
                    'response' => $responseData
                ]);

                // Safely get values from the response, falling back to defaults if keys are missing
                $apiDefaults['anomaly_threshold'] = data_get($responseData, 'data.anomaly_threshold', 0.7);
                $apiDefaults['defect_confidence_threshold'] = data_get($responseData, 'data.defect_confidence_threshold', 0.85);

            } else {
                // Log an error if the API call failed
                Log::error('Failed to fetch thresholds from Flask API', [
                    'status' => $response->status(),
                    'body' => $response->body()
                ]);
            }
        } catch (\Exception $e) {
            // Log an error if the request couldn't be made at all (e.g., connection timeout)
            Log::error('Exception when trying to fetch thresholds from Flask API', [
                'error' => $e->getMessage()
            ]);
        }

        $defaults = [
            'detection' => [
                'anomalyThreshold' => $apiDefaults['anomaly_threshold'],
                'defectThreshold' => $apiDefaults['defect_confidence_threshold'],
                'exportFormat' => 'pdf',
            ]
        ];

        // Load settings from the JSON file, or use defaults if it's not found
        $settings = Storage::exists('settings.json')
            ? json_decode(Storage::get('settings.json'), true)
            : $defaults;

        return Inertia::render('Settings/Index', [
            'savedSettings' => $settings
        ]);
    }

    public function update(Request $request)
    {
        // 1. Validate the incoming data (your existing code is perfect)
        $validatedData = $request->validate([
            'detection.anomalyThreshold' => ['required', 'numeric', 'min:0', 'max:1'],
            'detection.defectThreshold' => ['required', 'numeric', 'min:0', 'max:1'],
            'detection.exportFormat' => ['required', 'string', 'in:pdf,json,csv'],
        ]);

        // 2. Prepare the payload for the Flask API
        //    We map the Laravel validation keys to the keys the Flask API expects.
        $payload = [
            'anomaly_threshold' => $validatedData['detection']['anomalyThreshold'],
            'defect_confidence_threshold' => $validatedData['detection']['defectThreshold'],
        ];

        try {
            // 3. Send the updated settings to the Flask API
            $response = Http::timeout(5)->put(env('FLASK_API_URL') . '/api/config/thresholds', $payload);

            // 4. Check if the API call was successful
            if (!$response->successful()) {
                // If it failed, log the error and return with an error message
                Log::error('Failed to update thresholds on Flask API', [
                    'status' => $response->status(),
                    'body' => $response->body()
                ]);
                return back()->with('error', 'Settings could not be saved to the analysis server.');
            }

            Log::info('Successfully updated thresholds on Flask API.');

            // 5. If the API call was successful, save the settings locally
            Storage::disk('local')->put('settings.json', json_encode($validatedData, JSON_PRETTY_PRINT));
            Log::info('Settings updated locally by user ID: ' . auth()->id(), $validatedData);

            // 6. Redirect back with a success message
            return back()->with('success', 'Settings saved successfully.');

        } catch (\Exception $e) {
            // Catch any connection errors and return an error message
            Log::error('Exception when trying to update thresholds on Flask API', [
                'error' => $e->getMessage()
            ]);
            return back()->with('error', 'Could not connect to the analysis server.');
        }
    }

    public function clearAllData()
    {
        Log::info('All analysis data cleared by user ID: ' . auth()->id());
        $this->authorize('deleteAny', RealtimeSession::class);
        $this->authorize('deleteAny', Scan::class);

        RealtimeSession::query()->delete();
        Scan::query()->delete();

        // Redirect back with a success message.
        return back()->with('success', 'All analysis data has been cleared.');
    }

    public function clearMyData()
    {
        Log::info('User analysis data cleared by user ID: ' . auth()->id());
        $userId = auth()->id();

        $this->authorize('delete', new RealtimeSession(['user_id' => $userId]));
        RealtimeSession::where('user_id', $userId)->delete();

        $this->authorize('delete', new Scan(['user_id' => $userId]));
        Scan::where('user_id', $userId)->delete();



        // Redirect back with a success message.
        return back()->with('success', 'Your analysis data has been cleared.');
    }

    public function reset(Request $request)
    {
        // 1. Delete the local settings file to revert to defaults
        if (Storage::disk('local')->exists('settings.json')) {
            Storage::disk('local')->delete('settings.json');
            Log::info('Local settings.json file deleted by user ID: ' . auth()->id());
        }

        try {
            // 2. Send a request to the Flask API's new reset endpoint
            //    You will need to create this '/api/config/reset' route in your Flask app.
            $response = Http::timeout(5)->put(env('FLASK_API_URL') . '/api/config/reset');

            if (!$response->successful()) {
                Log::error('Failed to reset settings on Flask API', [
                    'status' => $response->status(),
                    'body' => $response->body()
                ]);
                // Even if the API fails, we can still proceed with a local reset,
                // but you might want to return an error depending on your needs.
            } else {
                Log::info('Successfully reset settings on Flask API.');
            }

        } catch (\Exception $e) {
            Log::error('Exception when trying to reset settings on Flask API', [
                'error' => $e->getMessage()
            ]);
        }

        // 3. Redirect back with a success message
        return back()->with('success', 'Settings have been reset to their default values.');
    }
}
