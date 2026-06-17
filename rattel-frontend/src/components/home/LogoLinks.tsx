"use client";

import { motion } from "framer-motion";
import { fadeInUp, staggerContainer } from "@/src/core/motionVariants";
import LoadingSkeleton from "@/src/components/skeleton/loadingSkeleton";
import {getMediaUrl} from "@/src/core/utils";
import {useRouter} from "next/navigation";

interface Link {
    name: string,
    logo: string | null,
    url: string,
}

interface LogoLinkSection {
    title: string;
    description: string;
    list: Link[];
}

function LogoLinkCard({logo_link}: {logo_link: Link} ) {
    const router = useRouter();
    return (
        <motion.div className="col-6 col-sm-6 col-lg-4 col-xl-3" variants={fadeInUp} whileHover={{ y: -5, transition: { duration: 0.2 } }}>
            <div className="card text-center h-100" onClick={(e) => {
                e.preventDefault();
                router.push(logo_link.url)
            }}>
                <div className="card-body text-center">
                    <div className="avatar avatar-xl mb-3 mx-auto">
                        {logo_link?.logo ? (
                            <img
                                src={getMediaUrl(logo_link.logo)}
                                alt={logo_link.name}
                                className="avatar-img rounded-circle"
                            />
                        ) : (
                            <div
                                className="avatar-img rounded-circle bg-secondary d-flex align-items-center justify-content-center"
                                style={{width: 80, height: 80}}
                            >
                                <i className="fas fa-user fa-2x text-white"></i>
                            </div>
                        )}
                    </div>
                    <h5 className="card-title">
                        <a href={logo_link.url}>{logo_link.name}</a>
                    </h5>
                </div>
            </div>
        </motion.div>
    );
}


export default function LogoLinks({data, isLoading}: { data: LogoLinkSection | null, isLoading: boolean }) {

    return data && (
        <section>
            <div className="container">
                <motion.div
                    className="row mb-4"
                    initial="hidden"
                    whileInView="show"
                    viewport={{ once: true, amount: 0.3 }}
                    variants={fadeInUp}
                >
                    <div className="col-lg-8 mx-auto text-center">
                        <h2 className="fs-3">{data?.title}</h2>
                        <p className="mb-0">{data?.description}</p>
                    </div>
                </motion.div>
                <LoadingSkeleton
                    isLoading={isLoading}
                    width="100%"
                    height={220}
                    count={4}
                    Content={() => (
                        <motion.div
                            className="row g-4"
                            variants={staggerContainer}
                            initial="hidden"
                            whileInView="show"
                            viewport={{ once: true, amount: 0.05 }}
                        >
                            {data?.list.map((logo_link, index) => (
                                <LogoLinkCard key={index} logo_link={logo_link}/>
                            ))}
                        </motion.div>
                    )}
                />
            </div>
        </section>
    );
}
