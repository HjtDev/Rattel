"use client";

import { useEffect, useState } from "react";
import { api } from "../api";

export interface CourseEpisode {
    id: string;
    title: string;
    type: string;
    file: string;
}

export interface CourseChapter {
    id: string;
    title: string;
    description: string;
    order: number;
    number_of_files: number;
    number_of_videos: number;
    is_free: boolean;
    is_visible: boolean;
    episodes: CourseEpisode[];
}

export interface CourseDetailTeacher {
    name: string;
    profile_picture: string | null;
}

export interface CourseDetail {
    id: string;
    content_type: number;
    name: string;
    image: string | null;
    teacher: CourseDetailTeacher;
    short_description: string;
    long_description: string;
    intro_video: string | null;
    price: number;
    new_price: number;
    discount: number;
    difficulty: string;
    age_group: string;
    category: string;
    rating: number;
    total_time: number;
    total_sell: number;
    number_of_episodes: number;
    chapters: CourseChapter[];
    created_at: string;
    updated_at: string;
    is_saved: boolean;
    is_owned: boolean;
    progress?: {
        completed: number;
        total: number;
        percentage: number;
        last_episode?: {
            id: number;
            title: string;
            type: string;
        } | null;
        next_episode?: any;
    } | null;
}

export function useCourseDetail(courseId: string | null) {
    const [courseDetail, setCourseDetail] = useState<CourseDetail | null>(null);
    const [isLoadingCourseDetail, setIsLoadingCourseDetail] = useState(false);
    const [courseDetailError, setCourseDetailError] = useState<string | null>(null);

    useEffect(() => {
        if (!courseId) return;

        setIsLoadingCourseDetail(true);
        setCourseDetailError(null);

        api
            .get(`/courses/${courseId}/`)
            .then((response) => {
                if (response.data.success) {
                    setCourseDetail(response.data.course);
                } else {
                    setCourseDetailError("Failed to load course details");
                }
            })
            .catch((err) => {
                setCourseDetailError(err.message || "Failed to load course details");
            })
            .finally(() => {
                setIsLoadingCourseDetail(false);
            });
    }, [courseId]);

    return { courseDetail, isLoadingCourseDetail, courseDetailError };
}
