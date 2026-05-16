"use client";

import { api } from "@/src/core/api";
import { toast } from "react-toastify";

// Types
export interface DashboardData {
    tickets_count: number;
    courses_count: number;
    days_since_registration: number;
    date_joined: string;
}

interface DashboardResult {
    success: boolean;
    message: string;
    data: DashboardData;
}

type DashboardSubscriber = (data: DashboardData | null) => void;

/**
 * DashboardManager - Singleton class for managing user dashboard data
 * Follows the same pattern as AuthManager and TicketManager
 */
class DashboardManager {
    private static instance: DashboardManager;
    private dashboardData: DashboardData | null = null;
    private subscribers: DashboardSubscriber[] = [];
    private isLoading: boolean = false;

    private constructor() {}

    static getInstance(): DashboardManager {
        if (!DashboardManager.instance) {
            DashboardManager.instance = new DashboardManager();
        }
        return DashboardManager.instance;
    }

    /**
     * Subscribe to dashboard data changes
     */
    subscribe(callback: DashboardSubscriber): () => void {
        this.subscribers.push(callback);
        return () => {
            this.subscribers = this.subscribers.filter((sub) => sub !== callback);
        };
    }

    /**
     * Notify all subscribers of dashboard data changes
     */
    private notify(): void {
        this.subscribers.forEach((callback) => callback(this.dashboardData));
    }

    /**
     * Get current dashboard data (synchronous)
     */
    getDashboardData(): DashboardData | null {
        return this.dashboardData;
    }

    /**
     * Check if data is currently being loaded
     */
    getIsLoading(): boolean {
        return this.isLoading;
    }

    /**
     * Fetch dashboard data from the API
     */
    async fetchDashboard(): Promise<DashboardData | null> {
        this.isLoading = true;
        this.notify();

        try {
            const response = await api.get<DashboardResult>("/users/dashboard/", {
                cache: false, // Bypass cache for fresh data
            });

            if (response.data.success && response.data.data) {
                this.dashboardData = response.data.data;
                this.notify();
                return this.dashboardData;
            } else {
                toast.error(response.data.message || "خطا در دریافت اطلاعات داشبورد");
                return null;
            }
        } catch (error: any) {
            const errorMessage =
                error.response?.data?.message || "خطا در دریافت اطلاعات داشبورد";
            toast.error(errorMessage);
            return null;
        } finally {
            this.isLoading = false;
            this.notify();
        }
    }

    /**
     * Clear dashboard data (call on logout)
     */
    reset(): void {
        this.dashboardData = null;
        this.isLoading = false;
        this.notify();
    }
}

// Export singleton instance
export const dashboardManager = DashboardManager.getInstance();
