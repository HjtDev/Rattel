"use client";

import { motion } from "framer-motion";
import { fadeInLeft, fadeInRight } from "@/src/core/motionVariants";
import LoadingSkeleton from "@/src/components/skeleton/loadingSkeleton";
import { getMediaUrl } from "@/src/core/utils";

interface Link {
    name: string;
    logo: string | null;
    url: string;
}

interface DualChoicesSection {
    choice1_title: string;
    choice1_description: string;
    choice1_image: string;
    choice1_link: Link;
    choice2_title: string;
    choice2_description: string;
    choice2_image: string;
    choice2_link: Link;
}

interface DualChoiceProps {
    data: DualChoicesSection | null;
    isLoading: boolean;
}

export default function DualChoice({ data, isLoading }: DualChoiceProps) {
    return (
        <section className="py-0 overflow-hidden">
            <div className="container">
                <div className="row g-4">
                    <motion.div
                        className="col-lg-6 position-relative overflow-hidden"
                        initial="hidden"
                        whileInView="show"
                        viewport={{ once: true, amount: 0.15 }}
                        variants={fadeInLeft}
                    >
                        <div className="bg-primary bg-opacity-10 rounded-3 p-5 h-100">
                            <div className="position-absolute bottom-0 end-0 me-3">
                                <LoadingSkeleton isLoading={isLoading} Content={() => (
                                    <img src={getMediaUrl(data?.choice1_image)} className="h-100px h-sm-200px" alt={data?.choice1_title || "Choice 1"} />
                                )} width={200} height={200} />
                            </div>
                            <div className="row">
                                <div className="col-sm-8 position-relative">
                                    <LoadingSkeleton isLoading={isLoading} Content={() => (
                                        <h2 className="mb-1 h4">
                                            {data?.choice1_title}
                                        </h2>
                                    )} width={200} height={32} />
                                    <LoadingSkeleton isLoading={isLoading} Content={() => (
                                        <p className="mb-3 h5 fw-light">
                                            {data?.choice1_description}
                                        </p>
                                    )} width={300} height={28} />
                                    <LoadingSkeleton isLoading={isLoading} Content={() => (
                                        <>
                                            {data?.choice1_link?.url && (
                                                <a href={data.choice1_link.url} className="btn btn-primary mb-0">
                                                    {data.choice1_link.name}
                                                </a>
                                            )}
                                        </>
                                    )} width={100} height={40} />
                                </div>
                            </div>
                        </div>
                    </motion.div>
                    <motion.div
                        className="col-lg-6 position-relative overflow-hidden"
                        initial="hidden"
                        whileInView="show"
                        viewport={{ once: true, amount: 0.15 }}
                        variants={fadeInRight}
                    >
                        <div className="bg-secondary rounded-3 bg-opacity-10 p-5 h-100">
                            <div className="position-absolute bottom-0 end-0 me-3">
                                <LoadingSkeleton isLoading={isLoading} Content={() => (
                                    <img src={getMediaUrl(data?.choice2_image)} className="h-100px h-sm-200px" alt={data?.choice2_title || "Choice 2"} />
                                )} width={200} height={200} />
                            </div>
                            <div className="row">
                                <div className="col-sm-8 position-relative">
                                    <LoadingSkeleton isLoading={isLoading} Content={() => (
                                        <h2 className="mb-1 h4">
                                            {data?.choice2_title}
                                        </h2>
                                    )} width={200} height={32} />
                                    <LoadingSkeleton isLoading={isLoading} Content={() => (
                                        <p className="mb-3 h5 fw-light">
                                            {data?.choice2_description}
                                        </p>
                                    )} width={300} height={28} />
                                    <LoadingSkeleton isLoading={isLoading} Content={() => (
                                        <>
                                            {data?.choice2_link?.url && (
                                                <a href={data.choice2_link.url} className="btn btn-warning mb-0">
                                                    {data.choice2_link.name}
                                                </a>
                                            )}
                                        </>
                                    )} width={100} height={40} />
                                </div>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </div>
        </section>
    )
}
