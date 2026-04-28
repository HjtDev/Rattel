"use client";

import { useCourses, Course } from "@/src/core/hooks/useCourses";
import LoadingSkeleton from "@/src/components/skeleton/loadingSkeleton";
import { getMediaUrl } from "@/src/core/utils";

function StarRating({ rating }: { rating: number }) {
    const full = Math.floor(rating);
    const half = rating - full >= 0.5;
    const empty = 5 - full - (half ? 1 : 0);

    return (
        <>
            {Array.from({ length: full }).map((_, i) => (
                <li key={`f${i}`} className="list-inline-item me-0 small">
                    <i className="fas fa-star text-warning"></i>
                </li>
            ))}
            {half && (
                <li className="list-inline-item me-0 small">
                    <i className="fas fa-star-half-alt text-warning"></i>
                </li>
            )}
            {Array.from({ length: empty }).map((_, i) => (
                <li key={`e${i}`} className="list-inline-item me-0 small">
                    <i className="far fa-star text-warning"></i>
                </li>
            ))}
        </>
    );
}

function TrendingCourseCard({ course }: { course: Course }) {
    const effectivePrice = course.new_price > 0 ? course.new_price : course.price;
    const hasDiscount = course.new_price > 0;

    return (
        <div className="col-sm-6 col-lg-4 col-xl-3">
            <div className="card action-trigger-hover border bg-transparent">
                {course.image && (
                    <img src={getMediaUrl(course.image)} className="card-img-top" alt={course.name} />
                )}
                <div className="card-body pb-0">
                    <div className="d-flex justify-content-between mb-3">
                        <span className="hstack gap-2">
                            <span className="badge bg-primary bg-opacity-10 text-primary">{course.difficulty}</span>
                        </span>
                        <a href="#" className="h6 fw-light mb-0">
                            <i className="far fa-bookmark"></i>
                        </a>
                    </div>
                    <h5 className="card-title fw-normal">
                        <a href={`/courses/${course.id}`}>{course.name}</a>
                    </h5>
                    <div className="d-flex justify-content-between mb-2">
                        <div className="hstack gap-2">
                            <p className="text-warning m-0">
                                {course.rating.toFixed(1)}
                                <i className="fas fa-star text-warning ms-1"></i>
                            </p>
                        </div>
                        <div className="hstack gap-2">
                            <p className="h6 fw-light mb-0 m-0">{course.total_sell}</p>
                            <span className="small">(دانشجو)</span>
                        </div>
                    </div>
                    <div className="hstack gap-3">
                        <span className="h6 fw-light mb-0">
                            <i className="far fa-clock text-danger me-2"></i>
                            {course.total_time} ساعت
                        </span>
                        <span className="h6 fw-light mb-0">
                            <i className="fas fa-table text-orange me-2"></i>
                            {course.number_of_episodes} درس
                        </span>
                    </div>
                </div>
                <div className="card-footer pt-0 bg-transparent">
                    <hr />
                    <div className="d-flex justify-content-between align-items-center">
                        <div className="d-flex align-items-center">
                            <div className="avatar avatar-sm">
                                {course.teacher.profile_picture ? (
                                    <img
                                        className="avatar-img rounded-1"
                                        src={getMediaUrl(course.teacher.profile_picture)}
                                        alt={course.teacher.name}
                                    />
                                ) : (
                                    <div
                                        className="avatar-img rounded-1 bg-secondary d-flex align-items-center justify-content-center"
                                        style={{ width: 40, height: 40 }}
                                    >
                                        <i className="fas fa-user text-white"></i>
                                    </div>
                                )}
                            </div>
                            <p className="mb-0 ms-2">
                                <a href="#" className="h6 fw-light mb-0">
                                    {course.teacher.name}
                                </a>
                            </p>
                        </div>
                        <div>
                            {hasDiscount ? (
                                <>
                                    <p className="text-decoration-line-through text-muted small mb-0">
                                        {course.price.toLocaleString("fa-IR")} تومان
                                    </p>
                                    <h5 className="text-success mb-0 item-show">
                                        {effectivePrice.toLocaleString("fa-IR")} تومان
                                    </h5>
                                </>
                            ) : (
                                <h5 className="text-success mb-0 item-show">
                                    {effectivePrice.toLocaleString("fa-IR")} تومان
                                </h5>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function TrendingCourses() {
    const { coursesData, isLoadingCourses } = useCourses({ sort: "total_sell", count: 8 });

    return (
        <section>
            <div className="container">
                <div className="row mb-4">
                    <div className="col-lg-8 mx-auto text-center">
                        <h2 className="fs-3">پرفروش ترین دوره ها</h2>
                        <p className="mb-0">دوره هایی که بیشترین هنرجو را جذب کرده اند</p>
                    </div>
                </div>
                <LoadingSkeleton
                    isLoading={isLoadingCourses}
                    width="100%"
                    height={400}
                    count={4}
                    Content={() => (
                        <div className="row g-4">
                            {coursesData?.courses.map((course) => (
                                <TrendingCourseCard key={course.id} course={course} />
                            ))}
                        </div>
                    )}
                />
            </div>
        </section>
    );
}
