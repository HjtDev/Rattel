"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { scaleIn } from "@/src/core/motionVariants";
import { getMediaUrl } from "@/src/core/utils";

interface CoursesDemoSection {
    video: string;
}

interface CourseDemoProps {
    data: CoursesDemoSection | null;
    isLoading: boolean;
}

export default function CourseDemo({ data, isLoading }: CourseDemoProps) {
    const [isVideoModalOpen, setIsVideoModalOpen] = useState(false);

    if (isLoading || !data?.video) return null;

    const videoUrl = getMediaUrl(data.video);

    return (
        <section className="pb-0 py-sm-0 mt-5">
            <div className="container">
                <div className="row">
                    <div className="col-md-8 text-center mx-auto">
                        <motion.div
                            className="card card-body shadow p-2"
                            initial="hidden"
                            whileInView="show"
                            viewport={{ once: true, amount: 0.2 }}
                            variants={scaleIn}
                        >
                            <div className="position-relative">
                                <video
                                    src={videoUrl}
                                    preload="metadata"
                                    muted
                                    playsInline
                                    className="w-100 rounded"
                                    style={{ maxHeight: "460px", objectFit: "cover" }}
                                />
                                <div className="card-img-overlay d-flex align-items-center justify-content-center">
                                    <button
                                        type="button"
                                        className="btn btn-lg text-danger btn-round btn-white-shadow mb-0"
                                        onClick={() => setIsVideoModalOpen(true)}
                                    >
                                        <i className="fas fa-play"></i>
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    </div>
                </div>
            </div>
            {isVideoModalOpen && (
                <>
                    <div
                        className="modal fade show d-block"
                        tabIndex={-1}
                        role="dialog"
                        aria-modal="true"
                        style={{ backgroundColor: "rgba(0, 0, 0, 0.65)" }}
                    >
                        <div className="modal-dialog modal-dialog-centered modal-xl" role="document">
                            <div className="modal-content">
                                <div className="modal-header justify-content-start">
                                    <button
                                        type="button"
                                        className="btn-close"
                                        aria-label="Close"
                                        onClick={() => setIsVideoModalOpen(false)}
                                        style={{marginRight: 0}}
                                    />
                                </div>
                                <div className="modal-body p-0">
                                    <video src={videoUrl} controls autoPlay className="w-100" />
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="modal-backdrop fade show" onClick={() => setIsVideoModalOpen(false)} />
                </>
            )}
        </section>
    );
}
