"use client";

import { useCourses, Course } from "@/src/core/hooks/useCourses";
import LoadingSkeleton from "@/src/components/skeleton/loadingSkeleton";
import {getCategoryLabel, getDifficultyLabel, getMediaUrl} from "@/src/core/utils";

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
            <li className="list-inline-item ms-2 h6 fw-light mb-0">{rating.toFixed(1)}/5.0</li>
        </>
    );
}

function CourseCard({ course }: { course: Course }) {
    const effectivePrice = course.new_price > 0 ? course.new_price : course.price;
    const hasDiscount = course.new_price > 0;

    return (
        <div className="col-sm-6 col-lg-4 col-xl-3">
            <div className="card shadow h-100">
                {course.image && (
                    <img
                        src={getMediaUrl(course.image)}
                        className="card-img-top"
                        alt={course.name}
                    />
                )}
                <div className="card-body pb-0">
                    <div className="d-flex justify-content-start gap-1 mb-2">
                        <span className="badge bg-purple bg-opacity-10 text-purple">
                            {getCategoryLabel(course.category)}
                        </span>
                        <span className="badge bg-purple bg-opacity-10 text-purple">
                            {getDifficultyLabel(course.difficulty)}
                        </span>
                    </div>
                    <h5 className="card-title fw-normal">
                        <a href={`/courses/${course.id}`}>{course.name}</a>
                    </h5>
                    <p
                        className="mb-2 text-truncate-2"
                        dangerouslySetInnerHTML={{ __html: course.short_description }}
                    />
                    <ul className="list-inline mb-0">
                        <StarRating rating={course.rating} />
                    </ul>
                </div>
                <div className="card-footer pt-0 pb-3">
                    <hr />
                    <div className="d-flex justify-content-between">
                        <span className="h6 fw-light mb-0">
                            <i className="far fa-clock text-danger me-2"></i>
                            {course.total_time} ساعت
                        </span>
                        <span className="h6 fw-light mb-0">
                            <i className="fas fa-table text-orange me-2"></i>
                            {course.number_of_episodes} درس
                        </span>
                    </div>
                    <div className="d-flex justify-content-between mt-2">
                        {hasDiscount ? (
                            <>
                                <span className="text-decoration-line-through text-muted small">
                                    {course.price.toLocaleString("fa-IR")} تومان
                                </span>
                                <span className="h6 fw-bold text-success mb-0">
                                    {effectivePrice.toLocaleString("fa-IR")} تومان
                                </span>
                            </>
                        ) : (
                            <span className="h6 fw-bold mb-0">
                                {effectivePrice.toLocaleString("fa-IR")} تومان
                            </span>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function PopularCourses() {
    const { coursesData, isLoadingCourses } = useCourses({ sort: "rating", count: 8 });

    return (
        <section>
            <div className="container">
                <div className="row mb-4">
                    <div className="col-lg-8 mx-auto text-center">
                        <h2 className="fs-3">محبوب ترین دوره ها</h2>
                        <p className="mb-0">
                            هر موضوعی را در هر زمان مطالعه کنید. هزاران دوره آموزشی را با کمترین قیمت جستجو کنید!
                        </p>
                    </div>
                </div>
                <LoadingSkeleton
                    isLoading={isLoadingCourses}
                    width="100%"
                    height={320}
                    count={4}
                    Content={() => (
                        <div className="row g-4">
                            {coursesData?.courses.map((course) => (
                                <CourseCard key={course.id} course={course} />
                            ))}
                        </div>
                    )}
                />
            </div>
        </section>
    );
}
