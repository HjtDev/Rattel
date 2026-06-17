"use client";

import { useFooter } from "@/src/core/hooks/useFooter";
import LoadingSkeleton from "@/src/components/skeleton/loadingSkeleton";

export default function Footer() {
    const { footerData, isLoadingFooter } = useFooter();
    const trustImages = [
        { src: "/assets/images/trust/enamad.png", alt: "Enamad" },
        { src: "/assets/images/trust/zibal.avif", alt: "Zibal" },
    ];

    return (
        <footer>
            <footer className="pt-5">
                <div className="container">
                    <div className="row g-4">
                        <div className="col-lg-3">
                            <LoadingSkeleton isLoading={isLoadingFooter} Content={() => (
                                <a className="me-0" href="/">
                                    <img className="light-mode-item h-40px" src={footerData?.logo} alt="Rattel Footer Logo"/>
                                </a>
                            )} width={140} height={40} />
                            <LoadingSkeleton isLoading={isLoadingFooter} Content={() => (
                                <p className="my-3">{footerData?.description}</p>
                            )} />
                            <LoadingSkeleton isLoading={isLoadingFooter} Content={() => (
                                <ul className="list-inline mb-0 mt-3">
                                    {
                                        footerData?.social_media_items.map((social_media, index) => (
                                            <li className="list-inline-item" key={index}>
                                                <a className="btn btn-white btn-sm shadow px-2 text-facebook" href={social_media.social_link.url} target="_blank">
                                                    {
                                                        ["telegram", "linkedin"].includes(social_media.social_link.platform) ? (
                                                            <i className={"fab fa-fw fa-" + social_media.social_link.platform}>
                                                            </i>
                                                        ) : (
                                                            <img src={`/assets/images/social_media/${social_media.social_link.platform}.ico`} alt={social_media.social_link.platform} width={15} height={15} />
                                                        )
                                                    }
                                                </a>
                                            </li>
                                        ))
                                    }
                                </ul>
                            )} width={250} height={40} />
                        </div>
                        <div className="col-lg-6">
                            <div className="row g-4">
                            <LoadingSkeleton isLoading={isLoadingFooter} Content={() => {
                                return footerData?.columns.map((column, index) => (
                                        <div className="col-6 col-md-4" key={index}>
                                            <h5 className="mb-2 mb-md-4">
                                                {column.title}
                                            </h5>
                                            <ul className="nav flex-column">
                                                {
                                                    column.column_links.map((link, index) => (
                                                        <li className="nav-item" key={index}>
                                                            <a className="nav-link" href={link.link.url} target="_blank">
                                                                {link.label || link.link.name}
                                                            </a>
                                                        </li>
                                                    ))
                                                }
                                            </ul>
                                        </div>
                                ))
                            }} width={190} height={206} />
                            <LoadingSkeleton
                                isLoading={isLoadingFooter}
                                Content={() => (
                                    <div className="col-6 col-md-4">
                                        <h5 className="mb-2 mb-md-4">اعتماد</h5>
                                        <ul className="list-unstyled d-flex flex-wrap gap-2 mb-0">
                                            {trustImages.map((imageItem, index) => (
                                                <li key={index}>
                                                    <a href="/about-us/#trust-section" className="d-inline-block" target="_blank">
                                                        <img
                                                            src={imageItem.src}
                                                            alt={imageItem.alt}
                                                            width={56}
                                                            height={56}
                                                            className="rounded border object-fit-cover"
                                                        />
                                                    </a>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                                width={190}
                                height={206}
                            />
                            </div>
                        </div>
                        <div className="col-lg-3">
                            <h5 className="mb-2 mb-md-4">
                                تماس با ما
                            </h5>
                            <p className="mb-2">
                                تلفن:
                                <span className="h6 fw-light ms-2">
            {footerData?.contact_phone}
          </span>
                                <span className="d-block small">
            ساعات کاری: <b className={"fw-light ms-2 h6"}>{footerData?.contact_hours}</b>
          </span>
                            </p>
                            <p className="mb-0">
                                ایمیل:
                                <span className="h6 fw-light ms-2">
            {footerData?.contact_email}
          </span>
                            </p>
                            <p className="mb-0">
                                آدرس:
                                <span className="h6 fw-light ms-2">
            {footerData?.contact_address}
          </span>
                            </p>
                        </div>
                    </div>
                    <hr className="mt-4 mb-0"/>
                    <div className="py-3">
                        <div className="container px-0">
                            <div
                                className="d-lg-flex justify-content-between align-items-center py-3 text-center text-md-left">
                                <div className="text-primary-hover">
                                    {footerData?.rights}
                                </div>
                                <div className="justify-content-center mt-3 mt-lg-0">
                                    <ul className="nav list-inline justify-content-center mb-0">
                                        <li className="list-inline-item">
                                            <a className="nav-link" href="/about-us" target="_blank">
                                                درباره ما
                                            </a>
                                        </li>
                                        <li className="list-inline-item">
                                            <a className="nav-link pe-0" href="/work-with-us" target="_blank">
                                                همکاری با ما
                                            </a>
                                        </li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </footer>
        </footer>
    );
}
