"use client";

import { api } from "@/src/core/api";
import { toast } from "react-toastify";

// Types
export interface Transaction {
    tracking_id: string;
    amount: number;
    currency: string;
    transaction_status: string;
    transaction_reason: string;
    description: string;
    created_at: string;
}

interface TransactionsResult {
    success: boolean;
    message: string;
    transactions: Transaction[];
}

type TransactionsSubscriber = (transactions: Transaction[]) => void;

/**
 * TransactionsManager - Singleton class for managing user transactions
 */
class TransactionsManager {
    private static instance: TransactionsManager;
    private transactions: Transaction[] = [];
    private subscribers: TransactionsSubscriber[] = [];
    private isLoading: boolean = false;

    private constructor() {}

    static getInstance(): TransactionsManager {
        if (!TransactionsManager.instance) {
            TransactionsManager.instance = new TransactionsManager();
        }
        return TransactionsManager.instance;
    }

    /**
     * Subscribe to transactions changes
     */
    subscribe(callback: TransactionsSubscriber): () => void {
        this.subscribers.push(callback);
        return () => {
            this.subscribers = this.subscribers.filter((sub) => sub !== callback);
        };
    }

    /**
     * Notify all subscribers of transactions changes
     */
    private notify(): void {
        this.subscribers.forEach((callback) => callback(this.transactions));
    }

    /**
     * Get current transactions (synchronous)
     */
    getTransactions(): Transaction[] {
        return this.transactions;
    }

    /**
     * Check if data is currently being loaded
     */
    getIsLoading(): boolean {
        return this.isLoading;
    }

    /**
     * Fetch transactions from the API
     */
    async fetchTransactions(): Promise<Transaction[] | null> {
        this.isLoading = true;
        this.notify();

        try {
            const response = await api.get<TransactionsResult>("/payment/my-transactions/", {
                cache: false, // Bypass cache for fresh data
            });

            if (response.data.success && response.data.transactions) {
                this.transactions = response.data.transactions;
                this.notify();
                return this.transactions;
            } else {
                toast.error(response.data.message || "خطا در دریافت تراکنش‌ها");
                return null;
            }
        } catch (error: any) {
            const errorMessage =
                error.response?.data?.message || "خطا در دریافت تراکنش‌ها";
            toast.error(errorMessage);
            return null;
        } finally {
            this.isLoading = false;
            this.notify();
        }
    }

    /**
     * Clear transactions data (call on logout)
     */
    reset(): void {
        this.transactions = [];
        this.isLoading = false;
        this.notify();
    }
}

// Export singleton instance
export const transactionsManager = TransactionsManager.getInstance();
