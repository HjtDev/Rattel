"use client";

import { useEffect, useState } from "react";
import { api } from "../api";

export interface InPersonClassTimeRange {
    id: number;
    label: string;
}

export interface InPersonClassCategory {
    id: number;
    name: string;
    slug: string;
}

export interface InPersonClass {
    id: string;
    thumbnail: string | null;
    title: string;
    short_description: string;
    price: number;
    new_price: number;
    discount: number;
    available_times: InPersonClassTimeRange[];
    categories: InPersonClassCategory[];
    start_date: string;
    end_date: string;
    meeting_url?: string | null;
}

export interface InPersonClassRegistration {
    id: string;
    in_person_class: InPersonClass;
    time_range: InPersonClassTimeRange;
    start_date: string;
    end_date: string;
    price: number;
    new_price: number;
    registered_count: number;
    created_at: string;
}

export interface InPersonClassesResponse {
    classes: InPersonClass[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number | null;
    has_next: boolean | null;
    has_previous: boolean | null;
}

export interface InPersonClassesParams {
    page?: number;
    count?: number;
    category?: string;
}

export function useInPersonClasses(params: InPersonClassesParams = {}) {
    const [classesData, setClassesData] = useState<InPersonClassesResponse | null>(null);
    const [isLoadingClasses, setIsLoadingClasses] = useState(true);
    const [classesError, setClassesError] = useState<string | null>(null);

    const { page = 1, count = 9, category } = params;

    useEffect(() => {
        setIsLoadingClasses(true);
        setClassesError(null);

        const query = new URLSearchParams();
        query.set("page", String(page));
        query.set("count", String(count));
        if (category) query.set("category", category);

        api
            .get(`/class/in-person/?${query.toString()}`)
            .then((response) => {
                if (response.data.success) {
                    setClassesData({
                        classes: response.data.classes,
                        total: response.data.total,
                        page: response.data.page,
                        page_size: response.data.page_size,
                        total_pages: response.data.total_pages,
                        has_next: response.data.has_next,
                        has_previous: response.data.has_previous,
                    });
                } else {
                    setClassesData({
                        classes: [],
                        total: 0,
                        page,
                        page_size: count,
                        total_pages: 0,
                        has_next: false,
                        has_previous: false,
                    });
                    setClassesError("Failed to load classes");
                }
            })
            .catch((err) => {
                setClassesData({
                    classes: [],
                    total: 0,
                    page,
                    page_size: count,
                    total_pages: 0,
                    has_next: false,
                    has_previous: false,
                });
                setClassesError(err.message || "Failed to load classes");
            })
            .finally(() => {
                setIsLoadingClasses(false);
            });
    }, [page, count, category]);

    return { classesData, isLoadingClasses, classesError };
}

export function useInPersonClassCategories() {
    const [categories, setCategories] = useState<InPersonClassCategory[]>([]);
    const [isLoadingCategories, setIsLoadingCategories] = useState(true);

    useEffect(() => {
        api
            .get("/class/in-person/categories/")
            .then((response) => {
                if (response.data.success) {
                    setCategories(response.data.categories);
                }
            })
            .catch(() => {})
            .finally(() => setIsLoadingCategories(false));
    }, []);

    return { categories, isLoadingCategories };
}

export function useMyInPersonClassRegistrations() {
    const [registrations, setRegistrations] = useState<InPersonClassRegistration[] | null>(null);
    const [isLoadingRegistrations, setIsLoadingRegistrations] = useState(true);
    const [registrationsError, setRegistrationsError] = useState<string | null>(null);

    const fetchRegistrations = async () => {
        setIsLoadingRegistrations(true);
        setRegistrationsError(null);
        try {
            const response = await api.get("/class/in-person/my-registrations/");
            if (response.data.success) {
                setRegistrations(response.data.registrations);
            } else {
                setRegistrationsError("Failed to load registrations");
            }
        } catch (err: any) {
            setRegistrationsError(err.message || "Failed to load registrations");
        } finally {
            setIsLoadingRegistrations(false);
        }
    };

    useEffect(() => {
        fetchRegistrations();
    }, []);

    return { registrations, isLoadingRegistrations, registrationsError, refetchRegistrations: fetchRegistrations };
}

export async function registerForInPersonClass(
    classId: string,
    timeRangeId: number
): Promise<{ success: boolean; id: string | null; message: string }> {
    try {
        const response = await api.post("/class/in-person/register/", {
            class_id: classId,
            time_range_id: timeRangeId,
        });
        return {
            success: response.data.success,
            id: response.data.id ?? null,
            message: response.data.message ?? "",
        };
    } catch (err: any) {
        return {
            success: false,
            id: null,
            message: err.response?.data?.message || "خطا در ثبت‌نام",
        };
    }
}
