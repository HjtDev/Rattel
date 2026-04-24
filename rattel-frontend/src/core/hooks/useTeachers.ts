"use client";

import { useEffect, useState } from "react";
import { api } from "../api";

export interface Teacher {
    name: string;
    profile_picture: string | null;
    number_of_courses: number;
    average_rating: number;
}

export function useTeachers() {
    const [teachersData, setTeachersData] = useState<Teacher[]>([]);
    const [isLoadingTeachers, setIsLoadingTeachers] = useState(true);
    const [teachersError, setTeachersError] = useState<string | null>(null);

    useEffect(() => {
        setIsLoadingTeachers(true);
        setTeachersError(null);

        api
            .get("/courses/teachers/")
            .then((response) => {
                if (response.data.success) {
                    setTeachersData(response.data.teachers);
                } else {
                    setTeachersError("Failed to load teachers");
                }
            })
            .catch((err) => {
                setTeachersError(err.message || "Failed to load teachers");
            })
            .finally(() => {
                setIsLoadingTeachers(false);
            });
    }, []);

    return { teachersData, isLoadingTeachers, teachersError };
}
