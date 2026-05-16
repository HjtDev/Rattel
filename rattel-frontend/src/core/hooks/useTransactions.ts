"use client";

import { useEffect, useState } from "react";
import { transactionsManager, Transaction } from "../transactions/transactionsManager";

/**
 * useTransactions hook - Provides reactive access to user transactions
 */
export function useTransactions() {
    const [transactions, setTransactions] = useState<Transaction[]>(
        transactionsManager.getTransactions()
    );
    const [isLoading, setIsLoading] = useState(transactionsManager.getIsLoading());

    useEffect(() => {
        // Subscribe to transactions changes
        const unsubscribe = transactionsManager.subscribe((data) => {
            setTransactions(data);
            setIsLoading(transactionsManager.getIsLoading());
        });

        // Initial load - fetch transactions if not already loaded
        const initTransactions = async () => {
            if (transactionsManager.getTransactions().length === 0) {
                await transactionsManager.fetchTransactions();
            }
        };

        initTransactions();

        // Cleanup subscription on unmount
        return () => {
            unsubscribe();
        };
    }, []);

    return {
        transactions,
        isLoading,
        fetchTransactions: transactionsManager.fetchTransactions.bind(transactionsManager),
        reset: transactionsManager.reset.bind(transactionsManager),
    };
}
