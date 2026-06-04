"use client";

import { useEffect, useState } from "react";
import { api } from "../api";

export interface Plan {
    id: string;
    name: string;
    picture: string | null;
    price: number;
    new_price: number;
    discount: number;
    duration_days: number;
    has_early_news_access: boolean;
    has_quiz_access: boolean;
    online_class_limit: 0 | 4 | 8 | 12;
    is_visible: boolean;
    created_at: string;
    updated_at: string;
}

export function useSubscriptionPlans() {
    const [plans, setPlans] = useState<Plan[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        api.get("/subscriptions/plans/")
            .then((res) => {
                if (res.data.success) {
                    setPlans(res.data.plans);
                } else {
                    setError("خطا در دریافت پلن ها");
                }
            })
            .catch((err) => {
                setError(err.message || "خطا در دریافت پلن ها");
            })
            .finally(() => setIsLoading(false));
    }, []);

    return { plans, isLoading, error };
}
