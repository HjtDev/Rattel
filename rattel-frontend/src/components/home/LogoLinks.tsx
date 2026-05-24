"use client";

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
        <div className="col-6 col-sm-6 col-lg-4 col-xl-3">
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
        </div>
    );
}


export default function LogoLinks({data, isLoading}: { data: LogoLinkSection | null, isLoading: boolean }) {

    return data && (
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
                            {data?.list.map((logo_link, index) => (
                                <LogoLinkCard key={index} logo_link={logo_link}/>
                            ))}
                        </div>
                    )}
                />
            </div>
        </section>
    );
}
