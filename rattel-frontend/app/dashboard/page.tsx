"use client";

import { useState, useMemo } from "react";
import DashboardBase from "@/src/components/dashboard/DashboardBase";
import {useDashboard} from "@/src/core/hooks/useDashboard";
import {useMyCourses} from "@/src/core/hooks/useMyCourses";
import {getMediaUrl} from "@/src/core/utils";
import {useRouter} from "next/navigation";

function DashboardContent() {
    const {dashboardData, isLoadingDashboard} = useDashboard();
    const {coursesData, isLoadingCourses} = useMyCourses();
    const [searchQuery, setSearchQuery] = useState("");

    const router = useRouter()

    // Filter courses based on search query
    const filteredCourses = useMemo(() => {
        if (!searchQuery.trim()) {
            return coursesData;
        }

        const query = searchQuery.toLowerCase();
        return coursesData.filter((course) => {
            const name = course.name.toLowerCase();
            const teacher = course.teacher.name.toLowerCase();
            const description = course.short_description?.toLowerCase() || '';

            return (
                name.includes(query) ||
                teacher.includes(query) ||
                description.includes(query)
            );
        });
    }, [coursesData, searchQuery]);

    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSearchQuery(e.target.value);
    };

    const handleSearchSubmit = (e: React.FormEvent) => {
        e.preventDefault();
    };

    // Calculate progress percentage (placeholder - update when you have real progress tracking)
    const calculateProgress = () => {
        return 0; // Placeholder
    };

    return !isLoadingDashboard && (
        <div className="col-xl-9">
            <div className="row mb-4">
                <div className="col-sm-6 col-lg-4 mb-3 mb-lg-0">
                    <div
                        className="d-flex justify-content-center  align-items-center p-4 bg-orange bg-opacity-15 rounded-3">
                <span className="display-6 lh-1 text-orange mb-0">
                  <i className="fas fa-clipboard-check fa-fw">
                  </i>
                </span>
                        <div className="ms-4">
                            <div className="d-flex">
                                <h5 className="purecounter mb-0 fw-bold" data-purecounter-start="0"
                                    data-purecounter-end="9" data-purecounter-delay="200"
                                    data-purecounter-duration="0">
                                    دوره ها
                                </h5>
                            </div>
                            <p className="mb-0 h6 fw-light mt-2">
                                {dashboardData?.courses_count}
                            </p>
                        </div>
                    </div>
                </div>
                <div className="col-sm-6 col-lg-4 mb-3 mb-lg-0">
                    <div
                        className="d-flex justify-content-center align-items-center p-4 bg-purple bg-opacity-15 rounded-3"
                        onClick={(e) => {
                            e.preventDefault();
                            router.push('/dashboard/tickets/');
                        }}
                    >
                <span className="display-6 lh-1 text-purple mb-0">
                  <i className="fas fa-tv fa-fw">
                  </i>
                </span>
                        <div className="ms-4">
                            <div className="d-flex">
                                <h5 className="purecounter mb-0 fw-bold" data-purecounter-start="0"
                                    data-purecounter-end="52" data-purecounter-delay="200"
                                    data-purecounter-duration="0">
                                    تیکت ها
                                </h5>
                            </div>
                            <p className="mb-0 h6 fw-light mt-2">
                                {dashboardData?.tickets_count}
                            </p>
                        </div>
                    </div>
                </div>
                <div className="col-sm-6 col-lg-4 mb-3 mb-lg-0">
                    <div
                        className="d-flex justify-content-center align-items-center p-4 bg-success bg-opacity-10 rounded-3">
                <span className="display-6 lh-1 text-success mb-0">
                  <i className="fas fa-medal fa-fw">
                  </i>
                </span>
                        <div className="ms-4">
                            <div className="d-flex">
                                <h5 className="purecounter mb-0 fw-bold" data-purecounter-start="0"
                                    data-purecounter-end="8" data-purecounter-delay="300"
                                    data-purecounter-duration="0">
                                    عضویت
                                </h5>
                            </div>
                            <p className="mb-0 h6 fw-light mt-2">
                                {dashboardData?.days_since_registration} روز پیش
                            </p>
                        </div>
                    </div>
                </div>
            </div>
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
                    {isLoadingCourses ? (
                        <div className="text-center py-5">
                            <div className="spinner-border text-primary" role="status">
                                <span className="visually-hidden">در حال بارگذاری...</span>
                            </div>
                        </div>
                    ) : filteredCourses.length === 0 ? (
                        <div className="text-center py-5">
                            <p className="text-muted">
                                {searchQuery ? 'دوره‌ای یافت نشد' : 'هنوز دوره‌ای خریداری نکرده‌اید'}
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
                                    قسمت ها
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
                            {filteredCourses.map((course) => {
                                const progress = calculateProgress();
                                const completedEpisodes = Math.floor((progress / 100) * course.number_of_episodes);
                                return (
                            <tr key={course.id}>
                                <td>
                                    <div className="d-flex align-items-center">
                                        <div className="w-100px">
                                            <img
                                                src={course.image ? getMediaUrl(course.image) : '/assets/images/courses/4by3/08.jpg'}
                                                className="rounded" alt=""/>
                                        </div>
                                        <div className="mb-0 ms-2">
                                            <h6>
                                                <a href="/">
                                                    {course.name}
                                                </a>
                                            </h6>
                                            <div className="d-sm-flex">
                                                <p className="h6 fw-light mb-0 small me-3">
                                                    <i className="fas fa-user text-orange me-2">
                                                    </i>
                                                    {course.teacher.name}
                                                </p>
                                                <p className="h6 fw-light mb-0 small">
                                                    <i className="fas fa-check-circle text-success me-2">
                                                    </i>
                                                    {completedEpisodes} از {course.number_of_episodes}
                                                </p>
                                            </div>
                                            <div className="overflow-hidden">
                                                <div className="progress progress-sm bg-primary bg-opacity-10">
                                                    <div
                                                        className={"progress-bar bg-primary aos aos-init aos-animate"}
                                                        role={"progressbar"} data-aos={"slide-left"}
                                                        data-aos-delay={200} data-aos-duration={1000}
                                                        data-aos-easing={"ease-in-out"}
                                                        style={{width: `${progress}%`}}
                                                        aria-valuenow={progress} aria-valuemin={0}
                                                        aria-valuemax={100}
                                                    >
                                                    </div>
                                                </div>
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
                                    <a href="/"
                                       className="btn btn-sm btn-primary-soft me-1 mb-1 mb-md-0">
                                        <i className="bi bi-play-circle me-1">
                                        </i>
                                        ادامه
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
        <DashboardBase Content={<DashboardContent />} />
    )
}
