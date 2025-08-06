<?php

namespace App\Http\Controllers;

use Inertia\Inertia;
use App\Models\DefectType;
use Illuminate\Support\Str;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;
use App\Services\DefectTypeQueryService;


class DefectTypeController extends Controller
{

    public function __construct(protected DefectTypeQueryService $service) {}

    /**
     * Display a listing of the resource.
     */
    public function index(Request $request)
    {

        $defectTypes = $this->service->query($request);

        $filters = $this->service->filters($request);

        return Inertia::render(
            'Database/Product',
            [
                'defectTypes' => $defectTypes,
                'filters' => $filters
            ]
        );
    }

    public function indexApi(Request $request)
    {
        $defectTypes = $this->service->query($request);

        $filters = $this->service->filters($request);

        return response()->json([
            'success' => true,
            'message' => 'Defect Types retrieved successfully',
            'data' => [
                'defectTypes' => $defectTypes,
                'filters' => [
                    'search' => $filters['search'],
                    'sortBy' => $filters['sortBy'],
                    'sortDir' => $filters['sortDir'],
                    'perPage' => $filters['perPage'],
                    'page' => $filters['page'],
                ]
            ]
        ]);
    }

    public function store(Request $request)
    {
        $request->validate([
            'name' => ['required', 'string', 'max:255', 'unique:products'],
            'description' => ['nullable', 'string', 'max:1000'],
        ]);

        DefectType::create([
            'name' => $request->name,
            'slug' => Str::slug($request->name),
            'description' => $request->description ?? '',
        ]);

        return redirect()->route('defectTypes.index')->with('success', 'Defect Type created successfully.');
    }

    public function showApi(DefectType $defectType)
    {
        return response()->json([
            'success' => true,
            'message' => 'Defect Type retrieved successfully',
            'data' => $defectType
        ]);
    }

    public function update(Request $request, DefectType $defectType)
    {
        $request->validate([
            'name' => [
                'required',
                'string',
                'max:255',
                Rule::unique('defect_types', 'name')->ignore($defectType->slug, 'slug'),
            ],
            'description' => ['nullable', 'string', 'max:1000'],
        ]);

        $defectType->update([
            'name' => $request->name,
            'slug' => Str::slug($request->name),
            'description' => $request->description ?? '',
        ]);

        return redirect()->route('defectTypes.index')->with('success', 'Defect Type updated successfully.');
    }

    public function destroy(DefectType $defectType)
    {
        $defectType->delete();
        return redirect()->route('defectTypes.index')->with('success', 'Defect Type deleted successfully.');
    }
}
