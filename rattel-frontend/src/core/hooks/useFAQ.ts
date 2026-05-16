"use client";

import { useEffect, useState } from "react";
import { api } from "../api";

interface FAQItem {
    question: string;
    answer: string;
    order: number;
}

export function useFAQ() {
    const [faqData, setFaqData] = useState<FAQItem[] | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        api
            .get("/site/faq/")
            .then((response) => {
                if (response.data.success) {
                    setFaqData(response.data.faqs);
                } else {
                    setError("Failed to load FAQs");
                }
            })
            .catch((err) => {
                setError(err.message || "Failed to load FAQs");
            })
            .finally(() => {
                setIsLoading(false);
            });
    }, []);

    return { faqData, isLoading, error };
}
