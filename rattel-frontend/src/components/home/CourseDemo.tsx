"use client";

import { getMediaUrl } from "@/src/core/utils";

interface CoursesDemoSection {
    video: string;
}

interface CourseDemoProps {
    data: CoursesDemoSection | null;
    isLoading: boolean;
}

export default function CourseDemo({ data, isLoading }: CourseDemoProps) {
    if (isLoading || !data?.video) return null;

    const videoUrl = getMediaUrl(data.video);

    return (
        <section className="pb-0 py-sm-0 mt-5">
            <div className="container">
                <div className="row">
                    <div className="col-md-8 text-center mx-auto">
                        <div className="card card-body shadow p-2">
                            <div className="position-relative">
                                <div className="card-img-overlay d-flex align-items-center justify-content-center">
                                    <a
                                        href={videoUrl}
                                        className="btn btn-lg text-danger btn-round btn-white-shadow mb-0"
                                        data-glightbox
                                        data-gallery="video-tour"
                                    >
                                        <i className="fas fa-play"></i>
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
