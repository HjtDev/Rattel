"use client";

import { useEffect, useState } from "react";
import { subscriptionManager, MySubscription } from "../subscriptions/subscriptionManager";

export type { MySubscription };

export function useMySubscription() {
    const [subscription, setSubscription] = useState<MySubscription | null>(
        subscriptionManager.getSubscription()
    );
    const [isLoading, setIsLoading] = useState(subscriptionManager.getIsLoading());

    useEffect(() => {
        const unsubscribe = subscriptionManager.subscribe(() => {
            setSubscription(subscriptionManager.getSubscription());
            setIsLoading(subscriptionManager.getIsLoading());
        });
        // Sync with any changes that happened before mount
        setSubscription(subscriptionManager.getSubscription());
        setIsLoading(subscriptionManager.getIsLoading());
        return unsubscribe;
    }, []);

    return { subscription, isLoading };
}
