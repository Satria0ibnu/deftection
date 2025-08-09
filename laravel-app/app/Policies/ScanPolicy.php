<?php

namespace App\Policies;

use App\Models\Scan;
use App\Models\User;
use Illuminate\Auth\Access\Response;

class ScanPolicy
{
    /**
     * Determine whether the user can view any models.
     */
    public function viewAny(User $user): bool
    {
        return $user->role === 'admin';
    }

    /**
     * Determine whether the user can view the model.
     */
    public function view(User $user, Scan $scan): bool
    {
        // Admins can view any scan
        // Users can only view their own
        return $user->role === 'admin' || $scan->user_id === $user->id;
    }

    public function filterByUser(User $user): bool
    {
        return $user->role === 'admin';
    }

    /**
     * Determine whether the user can create models.
     */
    public function create(User $user): bool
    {
        return true;
    }

    /**
     * Determine whether the user can update the model.
     */
    public function update(User $user, Scan $scan): bool
    {
        return false;
    }

    /**
     * Determine whether the user can delete the model.
     */
    public function delete(User $user, Scan $scan): bool
    {
        return $user->role === 'admin' || $scan->user_id === $user->id;;
    }


    public function generateAnyReport(User $user): bool
    {
        return $user->role === 'admin';
    }

    public function generateReport(User $user, Scan $scan): bool
    {
        // Admins can generate reports for any scan, users can only generate reports for their own
        return $user->role === 'admin' || $scan->user_id === $user->id;
    }
}
