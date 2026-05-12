"use client";

import { useEffect, useState } from "react";
import { api } from "../api";

export interface EpisodeInfo {
    id: number;
    title: string;
    type?: string;
}

export interface CourseProgress {
    completed: number;
    total: number;
    percentage: number;
    last_episode?: EpisodeInfo | null;
    next_episode?: EpisodeInfo | null;
}

export interface ContinueWatchingCourse {
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
    progress: {
        completed: number;
        total: number;
        percentage: number;
    };
    last_episode?: EpisodeInfo;
    next_episode?: EpisodeInfo;
}

/**
 * Hook to fetch course progress for a specific course
 */
export function useCourseProgress(courseId: string | null) {
    const [progress, setProgress] = useState<CourseProgress | null>(null);
    const [isLoadingProgress, setIsLoadingProgress] = useState(false);
    const [progressError, setProgressError] = useState<string | null>(null);

    const fetchProgress = async () => {
        if (!courseId) return;

        setIsLoadingProgress(true);
        setProgressError(null);

        try {
            const response = await api.get(`/courses/${courseId}/progress/`, {
                cache: false
            });
            if (response.data.success) {
                setProgress(response.data.progress);
            } else {
                setProgressError("Failed to load progress");
            }
        } catch (err: any) {
            setProgressError(err.message || "Failed to load progress");
        } finally {
            setIsLoadingProgress(false);
        }
    };

    useEffect(() => {
        fetchProgress();
    }, [courseId]);

    return { 
        progress, 
        isLoadingProgress, 
        progressError,
        refetchProgress: fetchProgress
    };
}

/**
 * Hook to fetch continue watching list
 */
export function useContinueWatching() {
    const [continueWatchingCourses, setContinueWatchingCourses] = useState<ContinueWatchingCourse[] | null>(null);
    const [isLoadingContinueWatching, setIsLoadingContinueWatching] = useState(false);
    const [continueWatchingError, setContinueWatchingError] = useState<string | null>(null);

    const fetchContinueWatching = async () => {
        setIsLoadingContinueWatching(true);
        setContinueWatchingError(null);

        try {
            const response = await api.get("/courses/continue-watching/", {
                cache: false
            });
            if (response.data.success) {
                setContinueWatchingCourses(response.data.courses);
            } else {
                setContinueWatchingError("Failed to load continue watching list");
            }
        } catch (err: any) {
            setContinueWatchingError(err.message || "Failed to load continue watching list");
        } finally {
            setIsLoadingContinueWatching(false);
        }
    };

    useEffect(() => {
        fetchContinueWatching();
    }, []);

    return { 
        continueWatchingCourses, 
        isLoadingContinueWatching, 
        continueWatchingError,
        refetchContinueWatching: fetchContinueWatching
    };
}

/**
 * Function to mark an episode as watched
 */
export async function markEpisodeWatched(
    courseId: string, 
    episodeId: number, 
    isCompleted: boolean = true,
    watchDuration: number = 0
): Promise<{ success: boolean; progress?: CourseProgress; message: string }> {
    try {
        const response = await api.post(
            `/courses/${courseId}/episodes/${episodeId}/mark-watched/`,
            {
                is_completed: isCompleted,
                watch_duration: watchDuration,
            }
        );
        return {
            success: response.data.success,
            progress: response.data.progress,
            message: response.data.message
        };
    } catch (err: any) {
        return {
            success: false,
            message: err.response?.data?.message || "خطا در ثبت پیشرفت"
        };
    }
}
