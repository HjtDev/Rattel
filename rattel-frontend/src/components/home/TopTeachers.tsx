"use client";

import { useTeachers, Teacher } from "@/src/core/hooks/useTeachers";
import LoadingSkeleton from "@/src/components/skeleton/loadingSkeleton";
import { getMediaUrl } from "@/src/core/utils";

function StarRating({ rating }: { rating: number }) {
    const full = Math.floor(rating);
    const half = rating - full >= 0.5;
    const empty = 5 - full - (half ? 1 : 0);

    return (
        <ul className="list-inline hstack justify-content-center mb-0">
            <li className="list-inline-item ms-2 h6 fw-light mb-0">{rating.toFixed(1)}/5.0</li>
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
        </ul>
    );
}

function TeacherCard({ teacher }: { teacher: Teacher }) {
    return (
        <div className="col-sm-6 col-lg-4 col-xl-3">
            <div className="card text-center h-100">
                <div className="card-body text-center">
                    <div className="avatar avatar-xl mb-3 mx-auto">
                        {teacher.profile_picture ? (
                            <img
                                src={getMediaUrl(teacher.profile_picture)}
                                alt={teacher.name}
                                className="avatar-img rounded-circle"
                            />
                        ) : (
                            <div
                                className="avatar-img rounded-circle bg-secondary d-flex align-items-center justify-content-center"
                                style={{ width: 80, height: 80 }}
                            >
                                <i className="fas fa-user fa-2x text-white"></i>
                            </div>
                        )}
                    </div>
                    <h5 className="card-title">
                        <a href="#">{teacher.name}</a>
                    </h5>
                </div>
            </div>
        </div>
    );
}

interface TopTeachersSection {
    title: string;
    description: string;
    list: any[];
}

interface TopTeachersProps {
    data: TopTeachersSection | null;
    isLoading: boolean
}

export default function TopTeachers({ data, isLoading }: TopTeachersProps) {

    return (
        <section>
            <div className="container">
                <div className="row mb-4">
                    <div className="col-lg-8 mx-auto text-center">
                        <h2 className="fs-3">{data?.title}</h2>
                        <p className="mb-0">{data?.description}</p>
                    </div>
                </div>
                <LoadingSkeleton
                    isLoading={isLoading}
                    width="100%"
                    height={220}
                    count={4}
                    Content={() => (
                        <div className="row g-4">
                            {data?.list.map((teacher, index) => (
                                <TeacherCard key={index} teacher={teacher} />
                            ))}
                        </div>
                    )}
                />
            </div>
        </section>
    );
}
