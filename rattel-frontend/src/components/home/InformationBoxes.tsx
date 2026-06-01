"use client";

import { motion } from "framer-motion";
import { fadeInLeft, fadeInRight } from "@/src/core/motionVariants";
import LoadingSkeleton from "@/src/components/skeleton/loadingSkeleton";
import { getMediaUrl } from "@/src/core/utils";

interface InformationBox {
    title: string;
    description: string;
    image: string;
    order: number;
}

interface InformationBoxesSection {
    boxes: InformationBox[];
}

interface InformationBoxesProps {
    data: InformationBoxesSection | null;
    isLoading: boolean;
}

export default function InformationBoxes({ data, isLoading }: InformationBoxesProps) {
    return (
        <LoadingSkeleton 
            isLoading={isLoading} 
            Content={() => (
                <div className={"mt-7"}>
                    {data?.boxes.map((box, index) => {
                        const isImageLeft = index % 2 === 0;
                        
                        return (
                            <section key={box.order} className={index === 0 ? "pb-0 pb-lg-5 overflow-hidden" : "overflow-hidden"}>
                                <div className="container">
                                    <div className={`row g-4 ${index === 0 ? 'g-lg-5' : ''} align-items-center`}>
                                        {isImageLeft ? (
                                            <>
                                                <motion.div
                                                    className="col-lg-6 position-relative order-2"
                                                    initial="hidden"
                                                    whileInView="show"
                                                    viewport={{ once: true, amount: 0.15 }}
                                                    variants={fadeInLeft}
                                                >
                                                    <figure className="position-absolute top-50 start-50 translate-middle ms-n8 d-none d-sm-block">
                                                        <svg width="625.8px" height="550px" viewBox="0 0 625.8 630.8">
                                                            <path className="fill-primary opacity-1"
                                                                  d="M445.8,133.5c59.7,50.3,122.9,96,149.7,161c26.5,64.6,15.9,148.6-29.9,197.7C520.3,541,439,555,364.9,578.1 c-74.5,23.1-142.1,55.2-200.4,42.3S57.2,549.7,32.6,487.3c-24.2-62-24.2-128.9-17.8-199.6C21.7,217,34.5,142.6,78.7,89.6 S198.6,5,264.4,16.7S386.1,83.2,445.8,133.5z">
                                                            </path>
                                                        </svg>
                                                    </figure>
                                                    <img src={getMediaUrl(box.image)} className="position-relative" alt={box.title} />
                                                </motion.div>
                                                <motion.div
                                                    className="col-lg-6 position-relative order-1 order-lg-2"
                                                    initial="hidden"
                                                    whileInView="show"
                                                    viewport={{ once: true, amount: 0.15 }}
                                                    variants={fadeInRight}
                                                >
                                                    <h2 className="fs-3">{box.title}</h2>
                                                    <div dangerouslySetInnerHTML={{ __html: box.description }} />
                                                </motion.div>
                                            </>
                                        ) : (
                                            <>
                                                <motion.div
                                                    className="col-md-5 position-relative z-index-9"
                                                    initial="hidden"
                                                    whileInView="show"
                                                    viewport={{ once: true, amount: 0.15 }}
                                                    variants={fadeInLeft}
                                                >
                                                    <h2 className="fs-3">{box.title}</h2>
                                                    <div dangerouslySetInnerHTML={{ __html: box.description }} />
                                                </motion.div>
                                                <motion.div
                                                    className="col-md-7 text-md-end position-relative"
                                                    initial="hidden"
                                                    whileInView="show"
                                                    viewport={{ once: true, amount: 0.15 }}
                                                    variants={fadeInRight}
                                                >
                                                    <figure className="position-absolute top-50 end-0 translate-middle-y me-n8">
                                                        <svg width="632.6px" height="540.4px" viewBox="0 0 632.6 540.4">
                                                            <path className="fill-primary opacity-1"
                                                                  d="M531.4,46.9c46.3,27.4,81.4,79.8,91.1,136.2c9.7,56.8-6.4,117.7-38.3,166s-79.4,84.2-138.6,119.3 c-59.6,35.1-130.6,69.7-201.5,62.1c-70.5-7.7-141.4-57.6-185.4-126.5C14.4,335.5-2.9,247.2,23.7,179.5 c26.2-68.1,96.7-116.5,161.6-140.2c64.9-24.2,124.5-24.6,183.3-23.4C427,17.1,485.1,19.5,531.4,46.9z">
                                                            </path>
                                                        </svg>
                                                    </figure>
                                                    <img src={getMediaUrl(box.image)} className="position-relative" alt={box.title} />
                                                </motion.div>
                                            </>
                                        )}
                                    </div>
                                </div>
                            </section>
                        );
                    })}
                </div>
            )}
            width={800}
            height={400}
        />
    );
}
