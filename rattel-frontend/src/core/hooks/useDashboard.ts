"use client";

import { useEffect, useState } from "react";
import { dashboardManager, DashboardData } from "../dashboard/dashboardManager";

/**
 * useDashboard hook - Provides reactive access to user dashboard data
 * Follows the same pattern as useAuth and useTickets
 */
export function useDashboard() {
    const [dashboardData, setDashboardData] = useState<DashboardData | null>(
        dashboardManager.getDashboardData()
    );
    const [isLoading, setIsLoading] = useState(dashboardManager.getIsLoading());

    useEffect(() => {
        // Subscribe to dashboard data changes
        const unsubscribe = dashboardManager.subscribe((data) => {
            setDashboardData(data);
            setIsLoading(dashboardManager.getIsLoading());
        });

        // Initial load - fetch dashboard data if not already loaded
        const initDashboard = async () => {
            if (!dashboardManager.getDashboardData()) {
                await dashboardManager.fetchDashboard();
            }
        };

        initDashboard();

        // Cleanup subscription on unmount
        return () => {
            unsubscribe();
        };
    }, []);

    return {
        dashboardData,
        isLoadingDashboard: isLoading,
        fetchDashboard: dashboardManager.fetchDashboard.bind(dashboardManager),
        reset: dashboardManager.reset.bind(dashboardManager),
    };
}
