import { useState, useEffect } from 'react';
import {api} from "@/src/core/api";

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
    short_description: string;
    number_of_episodes: number;
    total_time: number;
    rating: number;
    total_sell: number;
    teacher: CourseTeacher;
    progress?: {
        completed: number;
        total: number;
        percentage: number;
    } | null;
}

export interface MyCoursesResponse {
    success: boolean;
    message: string;
    courses: Course[];
    total: number;
}

export const useMyCourses = (autoFetch: boolean = true) => {
    const [coursesData, setCoursesData] = useState<Course[]>([]);
    const [total, setTotal] = useState<number>(0);
    const [isLoadingCourses, setIsLoadingCourses] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    const fetchMyCourses = async () => {
        setIsLoadingCourses(true);
        setError(null);

        try {
            const response = await api.get<MyCoursesResponse>('/courses/my-courses/', {
                cache: false
            });

            if (response.data.success) {
                setCoursesData(response.data.courses);
                setTotal(response.data.total);
            } else {
                setError(response.data.message);
            }
        } catch (err: any) {
            if (err.response?.status === 401) {
                setError('لطفاً وارد حساب کاربری خود شوید');
            } else {
                setError(err.response?.data?.message || 'خطا در دریافت دوره‌های خریداری شده');
            }
        } finally {
            setIsLoadingCourses(false);
        }
    };

    useEffect(() => {
        if (autoFetch) {
            fetchMyCourses();
        }
    }, [autoFetch]);

    return {
        coursesData: coursesData,
        total,
        isLoadingCourses: isLoadingCourses,
        error,
        refetch: fetchMyCourses,
    };
};
