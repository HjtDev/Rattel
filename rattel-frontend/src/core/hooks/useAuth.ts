"use client";

import { useEffect, useState } from "react";
import { authManager, User } from "../auth/authManager";

export function useAuth() {
    const [user, setUser] = useState<User | null>(authManager.getUser());
    const [isAuthenticated, setIsAuthenticated] = useState(authManager.isAuthenticated());
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        // Subscribe to auth state changes
        const unsubscribe = authManager.subscribe((updatedUser) => {
            setUser(updatedUser);
            setIsAuthenticated(updatedUser !== null);
        });

        // Initial load - check if we have tokens and fetch user info if needed
        const initAuth = async () => {
            if (authManager.getAccessToken() && !authManager.getUser()) {
                await authManager.fetchUserInfo();
            }
            setIsLoading(false);
        };

        initAuth();

        return () => {
            unsubscribe();
        };
    }, []);

    return {
        user,
        isAuthenticated,
        isLoading,
        login: authManager.login.bind(authManager),
        register: authManager.register.bind(authManager),
        verifyOTP: authManager.verifyOTP.bind(authManager),
        logout: authManager.logout.bind(authManager),
        refreshToken: authManager.refreshAccessToken.bind(authManager),
        refreshProfile: authManager.refreshProfile.bind(authManager),
        refreshSettings: authManager.refreshSettings.bind(authManager),
        updateUser: authManager.updateUser.bind(authManager),
    };
}
