"use client";

import { api } from "../api";
import { authManager } from "../auth/authManager";
import { Plan } from "../hooks/useSubscriptionPlans";

export interface MySubscription {
    plan: Plan;
    started_at: string;
    ends_in: string;
    is_active: boolean;
}

class SubscriptionManager {
    private static instance: SubscriptionManager;
    private subscription: MySubscription | null = null;
    private isLoading: boolean = true;
    private listeners: Set<() => void> = new Set();

    private constructor() {
        if (typeof window === "undefined") return;

        authManager.subscribe((user) => {
            if (user) {
                this.fetch();
            } else {
                this.subscription = null;
                this.isLoading = false;
                this.notifyListeners();
            }
        });

        if (authManager.isAuthenticated()) {
            this.fetch();
        } else {
            this.isLoading = false;
        }
    }

    public static getInstance(): SubscriptionManager {
        if (!SubscriptionManager.instance) {
            SubscriptionManager.instance = new SubscriptionManager();
        }
        return SubscriptionManager.instance;
    }

    public subscribe(callback: () => void): () => void {
        this.listeners.add(callback);
        return () => this.listeners.delete(callback);
    }

    private notifyListeners(): void {
        this.listeners.forEach((cb) => cb());
    }

    public async fetch(): Promise<void> {
        this.isLoading = true;
        this.notifyListeners();
        try {
            const res = await api.get("/subscriptions/my/", { cache: false });
            this.subscription = res.data.success ? res.data.subscription : null;
        } catch {
            this.subscription = null;
        } finally {
            this.isLoading = false;
            this.notifyListeners();
        }
    }

    public getSubscription(): MySubscription | null {
        return this.subscription;
    }

    public getIsLoading(): boolean {
        return this.isLoading;
    }
}

export const subscriptionManager = SubscriptionManager.getInstance();
