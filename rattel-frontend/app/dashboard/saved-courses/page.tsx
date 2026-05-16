"use client";

import { useState, useMemo } from "react";
import DashboardBase from "@/src/components/dashboard/DashboardBase";
import {useDashboard} from "@/src/core/hooks/useDashboard";
import {getMediaUrl} from "@/src/core/utils";
import {useRouter} from "next/navigation";
import {useSavedCourses} from "@/src/core/hooks/useSavedCourses";

function SavedCoursesContent() {
    const {dashboardData, isLoadingDashboard} = useDashboard();
    const {savedCourses, isLoadingSavedCourses} = useSavedCourses();
    const [searchQuery, setSearchQuery] = useState("");

    const router = useRouter()

    // Filter courses based on search query
    const filteredCourses = useMemo(() => {
        if (!searchQuery.trim()) {
            return savedCourses;
        }

        const query = searchQuery.toLowerCase();
        return savedCourses?.filter((course) => {
            const name = course.name.toLowerCase();
            const teacher = course.teacher.name.toLowerCase();
            const description = course.short_description?.toLowerCase() || '';

            return (
                name.includes(query) ||
                teacher.includes(query) ||
                description.includes(query)
            );
        });
    }, [savedCourses, searchQuery]);

    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSearchQuery(e.target.value);
    };

    const handleSearchSubmit = (e: React.FormEvent) => {
        e.preventDefault();
    };

    return !isLoadingDashboard && (
        <div className="col-xl-9">
            <div className="card bg-transparent border rounded-3">
                <div className="card-header bg-transparent border-bottom">
                    <h3 className="mb-0 fs-5 ff-vb">
                        لیست دوره های من
                    </h3>
                </div>
                <div className="card-body">
                    <div className="row g-3 align-items-center justify-content-between mb-4">
                        <div className="col-md-12">
                            <form className="rounded position-relative" onSubmit={handleSearchSubmit}>
                                <input className="form-control pe-5 bg-transparent" type="search"
                                       placeholder="جستجوی دوره" aria-label="Search"
                                       value={searchQuery}
                                       onChange={handleSearchChange}/>
                                <button
                                    className="bg-transparent p-2 position-absolute top-50 end-0 translate-middle-y border-0 text-primary-hover text-reset"
                                    type="submit">
                                    <i className="fas fa-search fs-6 ">
                                    </i>
                                </button>
                            </form>
                        </div>
                    </div>
                    {isLoadingSavedCourses ? (
                        <div className="text-center py-5">
                            <div className="spinner-border text-primary" role="status">
                                <span className="visually-hidden">در حال بارگذاری...</span>
                            </div>
                        </div>
                    ) : filteredCourses?.length === 0 ? (
                        <div className="text-center py-5">
                            <p className="text-muted">
                                {searchQuery ? 'دوره‌ای یافت نشد' : 'هنوز دوره‌ای ذخیره نکرده‌اید'}
                            </p>
                        </div>
                    ) : (
                        <div className="table-responsive border-0">
                            <table className="table table-dark-gray align-middle p-4 mb-0 table-hover">
                                <thead>
                                <tr>
                                    <th scope="col" className="border-0 rounded-start">
                                        دوره
                                    </th>
                                    <th scope="col" className="border-0">
                                        فایل ها
                                    </th>
                                    <th scope="col" className="border-0">
                                        کیفیت
                                    </th>
                                    <th scope="col" className="border-0 rounded-end">
                                        عملیات
                                    </th>
                                </tr>
                                </thead>
                                <tbody>
                                {filteredCourses?.map((course) => {
                                    return (
                                        <tr key={course.id}>
                                            <td>
                                                <div className="d-flex align-items-center">
                                                    <div className="w-100px">
                                                        <img
                                                            src={course.image ? getMediaUrl(course.image) : '/assets/images/courses/4by3/08.jpg'}
                                                            className="rounded" alt={course.name}
                                                            onClick={(e) => {e.preventDefault(); router.push(`/courses/${course.id}`)}}
                                                        />
                                                    </div>
                                                    <div className="mb-0 ms-2">
                                                        <h6>
                                                            <a href={`/courses/${course.id}`}>
                                                                {course.name}
                                                            </a>
                                                        </h6>
                                                        <div className="d-sm-flex">
                                                            <p className="h6 fw-light mb-0 small me-3">
                                                                <i className="fas fa-user text-orange me-2">
                                                                </i>
                                                                {course.teacher.name}
                                                            </p>
                                                        </div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td>
                                                {course.number_of_episodes}
                                            </td>
                                            <td>
                                                {course.rating}/5
                                            </td>
                                            <td>
                                                <a href={`/courses/${course.id}`}
                                                   className="btn btn-sm btn-primary-soft me-1 mb-1 mb-md-0">
                                                    <i className="bi bi-play-circle me-1">
                                                    </i>
                                                    مشاهده
                                                </a>
                                            </td>
                                        </tr>
                                    );
                                })}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

export default function Dashboard() {
    return (
        <DashboardBase Content={<SavedCoursesContent />} />
    )
}
