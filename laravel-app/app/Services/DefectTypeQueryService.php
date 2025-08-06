<?php

namespace App\Services;

use App\Models\DefectType;
use Illuminate\Http\Request;
use Illuminate\Contracts\Pagination\LengthAwarePaginator;

class DefectTypeQueryService
{
    public function query(Request $request): LengthAwarePaginator
    {
        $filters = $this->filters($request);

        return DefectType::query()
            ->when(
                $filters['search'],
                fn($query) =>
                $query->where('name', 'like', '%' . $filters['search'] . '%')
            )
            ->orderBy($filters['sortBy'], $filters['sortDir'])
            ->paginate($filters['perPage'], ['*'], 'page', $filters['page'])
            ->withQueryString()
            ->through(fn($product) => [
                'id' => $product->id,
                'name' => $product->name,
                'slug' => $product->slug,
                'description' => $product->description,
            ]);
    }

    public function filters(Request $request): array
    {
        return [
            'search' => $request->get('search', ''),
            'sortBy' => in_array($request->get('sort_by'), DefectType::$sortable) ? $request->get('sort_by') : 'name',
            'sortDir' => in_array($request->get('sort_dir'), ['asc', 'desc']) ? $request->get('sort_dir') : 'asc',
            'perPage' => max(1, min((int) $request->get('per_page', 10), 100)),
            'page' => max(1, (int) $request->get('page', 1)),
        ];
    }
}
