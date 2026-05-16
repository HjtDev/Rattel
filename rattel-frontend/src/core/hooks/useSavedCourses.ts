"use client";

import { useEffect, useState } from "react";
import { api } from "../api";

export interface SavedCourse {
    id: string;
    name: string;
    image: string | null;
    price: number;
    new_price: number;
    difficulty: string;
    category: string;
    short_description: string;
    number_of_episodes: number;
    total_time: number;
    rating: number;
    total_sell: number;
    teacher: {
        name: string;
        profile_picture: string | null;
    };
    is_saved: boolean;
}

export function useSavedCourses() {
    const [savedCourses, setSavedCourses] = useState<SavedCourse[] | null>(null);
    const [isLoadingSavedCourses, setIsLoadingSavedCourses] = useState(false);
    const [savedCoursesError, setSavedCoursesError] = useState<string | null>(null);

    const fetchSavedCourses = async () => {
        setIsLoadingSavedCourses(true);
        setSavedCoursesError(null);

        try {
            const response = await api.get("/courses/saved-courses/");
            if (response.data.success) {
                setSavedCourses(response.data.courses);
            } else {
                setSavedCoursesError("Failed to load saved courses");
            }
        } catch (err: any) {
            setSavedCoursesError(err.message || "Failed to load saved courses");
        } finally {
            setIsLoadingSavedCourses(false);
        }
    };

    useEffect(() => {
        fetchSavedCourses();
    }, []);

    return { 
        savedCourses, 
        isLoadingSavedCourses, 
        savedCoursesError,
        refetchSavedCourses: fetchSavedCourses
    };
}

export async function toggleSaveCourse(courseId: string): Promise<{ success: boolean; is_saved: boolean; message: string }> {
    try {
        const response = await api.post(`/courses/${courseId}/toggle-save/`);
        return {
            success: response.data.success,
            is_saved: response.data.is_saved,
            message: response.data.message
        };
    } catch (err: any) {
        return {
            success: false,
            is_saved: false,
            message: err.response?.data?.message || "خطا در ذخیره دوره"
        };
    }
}
