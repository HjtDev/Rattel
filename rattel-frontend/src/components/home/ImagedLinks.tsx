"use client";

import { motion } from "framer-motion";
import { scaleIn } from "@/src/core/motionVariants";
import LoadingSkeleton from "@/src/components/skeleton/loadingSkeleton";
import {getMediaUrl} from "@/src/core/utils";

interface ImagedLink {
    name: string;
    logo: string | null;
    url: string;
}

interface ImagedLinksSection {
    links: ImagedLink[];
}

interface ImagedLinksProps {
    data: ImagedLinksSection | null;
    isLoading: boolean;
}

export default function ImagedLinks({data, isLoading}: ImagedLinksProps) {
    return (
        <section>
            <div className="container">
                <div className="row">
                    <div className="col-md-12">
                        <motion.div
                            className="bg-light rounded-3 p-4"
                            initial="hidden"
                            whileInView="show"
                            viewport={{ once: true, amount: 0.2 }}
                            variants={scaleIn}
                        >
                            <div className="tiny-slider arrow-round arrow-creative arrow-blur arrow-hover py-1">
                                <div className="tns-outer" id="tns1-ow">
                                    <div className="tns-liveregion tns-visually-hidden" aria-live="polite"
                                         aria-atomic="true">
                                        slide
                                        <span className="current">
                  16 to 20
                </span>
                                        of 6
                                    </div>
                                    <div id="tns1-mw" className="tns-ovh">
                                        <div className="tns-inner" id="tns1-iw">
                                            <div
                                                className="tiny-slider-inner  tns-slider tns-carousel tns-subpixel tns-calc tns-horizontal"
                                                data-autoplay="true" data-gutter="80" data-arrow="true"
                                                data-dots="false"
                                                data-items="5" data-items-lg="3" data-items-md="2" data-items-xs="1"
                                                id="tns1"
                                                style={{transform: 'translate3d(57.6923%, 0px, 0px)'}}>
                                                <LoadingSkeleton isLoading={isLoading} Content={() => (
                                                    <>
                                                        {data?.links.map((link, index) => (
                                                            <div key={index} className="tns-item">
                                                                <div
                                                                    className="bg-body text-center rounded-2 border py-2 px-1 position-relative">
                                                                    {link.logo && (
                                                                        <img src={getMediaUrl(link.logo)}
                                                                             className="h-40px" alt={link.name}/>
                                                                    )}
                                                                    <a href={link.url}
                                                                       className="text-primary-hover stretched-link">
                                                                        <span className="h6 ms-2">{link.name}</span>
                                                                    </a>
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </>
                                                )} width={120} height={60} count={5}/>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="tns-controls" aria-label="Carousel Navigation" tabIndex={0}>
                                        <button type="button" data-controls="prev" tabIndex={-1} aria-controls="tns1">
                                            <i className="fas fa-chevron-left">
                                            </i>
                                        </button>
                                        <button type="button" data-controls="next" tabIndex={-1} aria-controls="tns1">
                                            <i className="fas fa-chevron-right">
                                            </i>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    </div>
                </div>
            </div>
        </section>
    )
}
