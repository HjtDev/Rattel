"use client";

import { api } from "../api";

export interface UserProfile {
    role: string;
    gender: string | null;
    national_code: string | null;
    education: string | null;
    had_other_classes: string | null;
    memorized: string | null;
    invited_by: string | null;
    birthday: string | null;
    city: string | null;
    telegram_id: string | null;
    eitaa_id: string | null;
    instagram_id: string | null;
}

export interface UserSettings {
    profile_visible: boolean;
    email_on_login: boolean;
    email_on_payment: boolean;
    sms_on_payment: boolean;
}

export interface User {
    username: string;
    email: string | null;
    name: string;
    phone: string;
    profile_picture: string | null;
    score: number;
    profile?: UserProfile;
    settings?: UserSettings;
}

export interface AuthTokens {
    access: string;
    refresh: string;
}

class AuthManager {
    private static instance: AuthManager;
    private user: User | null = null;
    private tokens: AuthTokens | null = null;
    private refreshTimeout: NodeJS.Timeout | null = null;
    private listeners: Set<(user: User | null) => void> = new Set();

    private constructor() {
        // Load tokens and user from localStorage on initialization
        if (typeof window !== "undefined") {
            this.loadFromStorage();
        }
    }

    public static getInstance(): AuthManager {
        if (!AuthManager.instance) {
            AuthManager.instance = new AuthManager();
        }
        return AuthManager.instance;
    }

    /**
     * Subscribe to auth state changes
     */
    public subscribe(callback: (user: User | null) => void): () => void {
        this.listeners.add(callback);
        return () => this.listeners.delete(callback);
    }

    /**
     * Notify all listeners of auth state change
     */
    private notifyListeners(): void {
        this.listeners.forEach((callback) => callback(this.user));
    }

    /**
     * Load tokens and user from localStorage
     */
    private loadFromStorage(): void {
        try {
            const accessToken = localStorage.getItem("access_token");
            const refreshToken = localStorage.getItem("refresh_token");
            const userData = localStorage.getItem("user_data");

            if (accessToken && refreshToken) {
                this.tokens = {
                    access: accessToken,
                    refresh: refreshToken,
                };
                this.scheduleTokenRefresh();
            }

            if (userData) {
                this.user = JSON.parse(userData);
            }
        } catch (error) {
            console.error("Failed to load auth data from storage:", error);
            this.clearStorage();
        }
    }

    /**
     * Save tokens and user to localStorage
     */
    private saveToStorage(): void {
        try {
            if (this.tokens) {
                localStorage.setItem("access_token", this.tokens.access);
                localStorage.setItem("refresh_token", this.tokens.refresh);
            }
            if (this.user) {
                localStorage.setItem("user_data", JSON.stringify(this.user));
            }
        } catch (error) {
            console.error("Failed to save auth data to storage:", error);
        }
    }

    /**
     * Clear tokens and user from localStorage
     */
    private clearStorage(): void {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user_data");
    }

    /**
     * Decode JWT token to get expiration time
     */
    private decodeToken(token: string): { exp: number } | null {
        try {
            const base64Url = token.split(".")[1];
            const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
            const jsonPayload = decodeURIComponent(
                atob(base64)
                    .split("")
                    .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
                    .join("")
            );
            return JSON.parse(jsonPayload);
        } catch (error) {
            console.error("Failed to decode token:", error);
            return null;
        }
    }

    /**
     * Schedule automatic token refresh before expiration
     */
    private scheduleTokenRefresh(): void {
        if (this.refreshTimeout) {
            clearTimeout(this.refreshTimeout);
        }

        if (!this.tokens?.access) return;

        const decoded = this.decodeToken(this.tokens.access);
        if (!decoded?.exp) return;

        const now = Math.floor(Date.now() / 1000);
        const expiresIn = decoded.exp - now;
        
        // Refresh 1 minute before expiration
        const refreshIn = Math.max(0, (expiresIn - 60) * 1000);

        this.refreshTimeout = setTimeout(() => {
            this.refreshAccessToken();
        }, refreshIn);
    }

    /**
     * Refresh the access token using refresh token
     */
    public async refreshAccessToken(): Promise<boolean> {
        if (!this.tokens?.refresh) {
            return false;
        }

        try {
            const response = await api.post("/auth/refresh/", {
                refresh: this.tokens.refresh,
            });

            if (response.data.success) {
                this.tokens.access = response.data.access;
                
                // Update refresh token if rotated
                if (response.data.refresh) {
                    this.tokens.refresh = response.data.refresh;
                }

                this.saveToStorage();
                this.scheduleTokenRefresh();
                return true;
            }

            return false;
        } catch (error) {
            console.error("Failed to refresh token:", error);
            this.logout();
            return false;
        }
    }

    /**
     * Get current access token
     */
    public getAccessToken(): string | null {
        return this.tokens?.access || null;
    }

    /**
     * Get current refresh token
     */
    public getRefreshToken(): string | null {
        return this.tokens?.refresh || null;
    }

    /**
     * Get current user
     */
    public getUser(): User | null {
        return this.user;
    }

    /**
     * Check if user is authenticated
     */
    public isAuthenticated(): boolean {
        return this.tokens !== null && this.user !== null;
    }

    /**
     * Set authentication tokens and fetch user info
     */
    public async setTokens(tokens: AuthTokens): Promise<boolean> {
        this.tokens = tokens;
        this.saveToStorage();
        this.scheduleTokenRefresh();

        // Fetch user info after setting tokens
        return await this.fetchUserInfo();
    }

    /**
     * Fetch current user information
     */
    public async fetchUserInfo(): Promise<boolean> {
        try {
            // Fetch all three endpoints in parallel
            const [infoResponse, profileResponse, settingsResponse] = await Promise.all([
                api.get("/users/info/"),
                api.get("/users/profile/?target=me"),
                api.get("/users/settings/")
            ]);

            if (infoResponse.data.success) {
                // Combine all data into one user object
                this.user = {
                    ...infoResponse.data.user,
                    profile: profileResponse.data.success ? profileResponse.data.profile : undefined,
                    settings: settingsResponse.data.success ? settingsResponse.data.settings : undefined,
                };
                
                this.saveToStorage();
                this.notifyListeners();
                return true;
            }

            return false;
        } catch (error) {
            console.error("Failed to fetch user info:", error);
            return false;
        }
    }

    /**
     * Refresh only profile data
     */
    public async refreshProfile(): Promise<boolean> {
        try {
            const response = await api.get("/users/profile/?target=me");

            if (response.data.success && this.user) {
                this.user.profile = response.data.profile;
                this.saveToStorage();
                this.notifyListeners();
                return true;
            }

            return false;
        } catch (error) {
            console.error("Failed to refresh profile:", error);
            return false;
        }
    }

    /**
     * Refresh only settings data
     */
    public async refreshSettings(): Promise<boolean> {
        try {
            const response = await api.get("/users/settings/");

            if (response.data.success && this.user) {
                this.user.settings = response.data.settings;
                this.saveToStorage();
                this.notifyListeners();
                return true;
            }

            return false;
        } catch (error) {
            console.error("Failed to fetch user info:", error);
            return false;
        }
    }

    /**
     * Update user data locally (after profile/settings update)
     */
    public updateUser(userData: Partial<User>): void {
        if (this.user) {
            this.user = { ...this.user, ...userData };
            this.saveToStorage();
            this.notifyListeners();
        }
    }

    /**
     * Update user information (name, username, email, profile_picture)
     * Calls the PATCH /api/v1/users/info/ endpoint
     */
    public async updateUserInfo(data: {
        name?: string;
        username?: string;
        email?: string;
        profile_picture?: File;
    }): Promise<{ success: boolean; message?: string; error?: number; usernameChanged?: boolean }> {
        try {
            const formData = new FormData();
            
            // Add string fields if provided
            if (data.name !== undefined) formData.append('name', data.name);
            if (data.username !== undefined) formData.append('username', data.username);
            if (data.email !== undefined) formData.append('email', data.email);
            
            // Add profile picture if provided
            if (data.profile_picture) {
                formData.append('profile_picture', data.profile_picture);
            }

            const response = await api.patch("/users/info/", formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                cache: false,
            });

            if (response.data.success && response.data.user) {
                // Check if username was changed
                const usernameChanged = data.username !== undefined && data.username !== this.user?.username;
                
                // Update local user data
                this.user = response.data.user;
                this.saveToStorage();
                this.notifyListeners();

                return {
                    success: true,
                    message: response.data.message,
                    usernameChanged,
                };
            }

            return { success: false, message: response.data.message, error: response.data.error };
        } catch (error: any) {
            return { success: false, message: error.response?.data?.message || "خطا در به‌روزرسانی اطلاعات", error: error.response?.data?.error };
        }
    }

    /**
     * Update user profile (gender, national_code, education, etc.)
     * Calls the PATCH /users/profile/?target=me endpoint
     */
    public async updateProfile(data: {
        gender?: string;
        national_code?: string;
        education?: string;
        had_other_classes?: string;
        memorized?: string;
        invited_by?: string;
        birthday?: string;
        city?: string;
        telegram_id?: string;
        eitaa_id?: string;
        instagram_id?: string;
    }): Promise<{ success: boolean; message?: string; error?: number }> {
        try {
            const response = await api.patch("/users/profile/?target=me", data, {
                cache: false,
            });

            if (response.data.success && response.data.profile) {
                // Update local user profile data
                if (this.user) {
                    this.user.profile = response.data.profile;
                    this.saveToStorage();
                    this.notifyListeners();
                }

                return {
                    success: true,
                    message: response.data.message,
                };
            }

            return { success: false, message: response.data.message, error: response.data.error };
        } catch (error: any) {
            return { 
                success: false, 
                message: error.response?.data?.message || "خطا در به‌روزرسانی پروفایل", 
                error: error.response?.data?.error 
            };
        }
    }

    /**
     * Update user settings (profile_visible, email_on_login, email_on_payment, sms_on_payment)
     * Calls the PATCH /users/settings/ endpoint
     */
    public async updateSettings(data: {
        profile_visible?: boolean;
        email_on_login?: boolean;
        email_on_payment?: boolean;
        sms_on_payment?: boolean;
    }): Promise<{ success: boolean; message?: string; error?: number }> {
        try {
            const response = await api.patch("/users/settings/", data, {
                cache: false,
            });

            if (response.data.success && response.data.settings) {
                // Update local user settings data
                if (this.user) {
                    this.user.settings = response.data.settings;
                    this.saveToStorage();
                    this.notifyListeners();
                }

                return {
                    success: true,
                    message: response.data.message,
                };
            }

            return { success: false, message: response.data.message, error: response.data.error };
        } catch (error: any) {
            return { 
                success: false, 
                message: error.response?.data?.message || "خطا در به‌روزرسانی تنظیمات", 
                error: error.response?.data?.error 
            };
        }
    }

    /**
     * Logout user and clear all data
     */
    public logout(): void {
        if (this.refreshTimeout) {
            clearTimeout(this.refreshTimeout);
            this.refreshTimeout = null;
        }

        this.tokens = null;
        this.user = null;
        this.clearStorage();
        this.notifyListeners();
    }

    /**
     * Register new user (initiates OTP session)
     */
    public async register(data: {
        username: string;
        name: string;
        phone: string;
        email?: string;
    }): Promise<{ success: boolean; message?: string; indicator?: string; error?: number }> {
        try {
            const response = await api.post("/auth/register/", data);
            return {
                success: response.data.success,
                message: response.data.message,
                indicator: response.data.indicator,
                error: response.data.error,
            };
        } catch (error: any) {
            return {
                success: false,
                message: error.response?.data?.message || "Registration failed",
                error: error.response?.data?.error,
            };
        }
    }

    /**
     * Login user (initiates OTP session)
     */
    public async login(username: string): Promise<{ success: boolean; message?: string; indicator?: string; error?: number }> {
        try {
            const response = await api.post("/auth/login/", { username });
            return {
                success: response.data.success,
                message: response.data.message,
                indicator: response.data.indicator,
                error: response.data.error,
            };
        } catch (error: any) {
            return {
                success: false,
                message: error.response?.data?.message || "Login failed",
                error: error.response?.data?.error,
            };
        }
    }

    /**
     * Verify OTP code
     */
    public async verifyOTP(
        indicator: string,
        code: string
    ): Promise<{ success: boolean; message?: string; tokens?: AuthTokens; error?: number }> {
        try {
            const response = await api.post("/auth/verify/", { indicator, token: code });

            if (response.data.success && response.data.access && response.data.refresh) {
                const tokens: AuthTokens = {
                    access: response.data.access,
                    refresh: response.data.refresh,
                };

                await this.setTokens(tokens);

                return {
                    success: true,
                    message: response.data.message,
                    tokens,
                    error: response.data.error,
                };
            }

            return {
                success: false,
                message: response.data.message || "Verification failed",
                error: response.data.error,
            };
        } catch (error: any) {
            return {
                success: false,
                message: error.response?.data?.message || "Verification failed",
                error: error.response?.data?.error,
            };
        }
    }
}

export const authManager = AuthManager.getInstance();
