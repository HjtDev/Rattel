"use client";

import { useEffect, useState } from "react";
import { api } from "../api";

export interface CourseTeacher {
    name: string;
    profile_picture: string | null;
}

export interface Course {
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
    teacher: CourseTeacher;
}

export interface CoursesResponse {
    courses: Course[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number | null;
    has_next: boolean | null;
    has_previous: boolean | null;
}

export type SortOption = "rating" | "total_sell" | "has_discount" | "most_videos" | "longest" | "shortest";
export type DifficultyOption = "beginner" | "intermediate" | "advanced";
export type AgeGroupOption = "kid" | "teen" | "adult" | "all";
export type CategoryOption = "naghme" | "hafeze" | "andishe";

export interface CoursesParams {
    page?: number;
    count?: number;
    sort?: SortOption;
    age_group?: AgeGroupOption;
    difficulty?: DifficultyOption;
    category?: CategoryOption;
    teacher_name?: string;
}

export function useCourses(params: CoursesParams = {}) {
    const [coursesData, setCoursesData] = useState<CoursesResponse | null>(null);
    const [isLoadingCourses, setIsLoadingCourses] = useState(true);
    const [coursesError, setCoursesError] = useState<string | null>(null);

    const {
        page = 1,
        count = 12,
        sort,
        age_group,
        difficulty,
        category,
        teacher_name,
    } = params;

    useEffect(() => {
        setIsLoadingCourses(true);
        setCoursesError(null);

        const query = new URLSearchParams();
        query.set("page", String(page));
        query.set("count", String(count));
        if (sort) query.set("sort", sort);
        if (age_group) query.set("age_group", age_group);
        if (difficulty) query.set("difficulty", difficulty);
        if (category) query.set("category", category);
        if (teacher_name) query.set("teacher_name", teacher_name);

        api
            .get(`/courses/?${query.toString()}`)
            .then((response) => {
                if (response.data.success) {
                    setCoursesData({
                        courses: response.data.courses,
                        total: response.data.total,
                        page: response.data.page,
                        page_size: response.data.page_size,
                        total_pages: response.data.total_pages,
                        has_next: response.data.has_next,
                        has_previous: response.data.has_previous,
                    });
                } else {
                    setCoursesError("Failed to load courses");
                }
            })
            .catch((err) => {
                console.log(err.message);
                setCoursesError(err.message || "Failed to load courses");
            })
            .finally(() => {
                setIsLoadingCourses(false);
            });
    }, [page, count, sort, age_group, difficulty, category, teacher_name]);

    return { coursesData, isLoadingCourses, coursesError };
}
