"use client";

import {useEffect, useState, useRef} from "react";
import {getMediaUrl} from "@/src/core/utils";
import {useGallery} from "@/src/core/hooks/useGallery";
import {useGalleryDetail} from "@/src/core/hooks/useGalleryDetail";


export default function GalleryPage() {
    const [page, setPage] = useState(1);
    const [selectedGalleryId, setSelectedGalleryId] = useState<string | null>(null);
    const [currentSlide, setCurrentSlide] = useState(0);
    const mediaRefs = useRef<(HTMLVideoElement | HTMLAudioElement | null)[]>([]);
    const touchStartX = useRef<number>(0);
    const touchEndX = useRef<number>(0);
    const touchStartY = useRef<number>(0);
    const touchEndY = useRef<number>(0);
    const isTouchOnMedia = useRef<boolean>(false);
    const [isMobile, setIsMobile] = useState(false);

    const {galleryData, isLoadingGallery} = useGallery(page, 12);
    const {galleryDetail, isLoadingGalleryDetail} = useGalleryDetail(selectedGalleryId);
    const contentItems = galleryDetail?.content || [];

    useEffect(() => {
        const checkMobile = () => {
            setIsMobile(window.innerWidth < 768);
        };
        checkMobile();
        window.addEventListener("resize", checkMobile);
        return () => window.removeEventListener("resize", checkMobile);
    }, []);

    useEffect(() => {
        setCurrentSlide(0);
    }, [selectedGalleryId]);

    useEffect(() => {
        mediaRefs.current.forEach((media, index) => {
            if (media && index !== currentSlide) {
                media.pause();
                media.currentTime = 0;
            }
        });
    }, [currentSlide]);

    const handlePrevSlide = () => {
        setCurrentSlide((prev) => (prev === 0 ? contentItems.length - 1 : prev - 1));
    };

    const handleNextSlide = () => {
        setCurrentSlide((prev) => (prev === contentItems.length - 1 ? 0 : prev + 1));
    };

    const handleTouchStart = (e: React.TouchEvent) => {
        const target = e.target as HTMLElement;
        isTouchOnMedia.current = target.tagName === "VIDEO" || target.tagName === "AUDIO";
        touchStartX.current = e.touches[0].clientX;
        touchStartY.current = e.touches[0].clientY;
    };

    const handleTouchMove = (e: React.TouchEvent) => {
        touchEndX.current = e.touches[0].clientX;
        touchEndY.current = e.touches[0].clientY;
    };

    const handleTouchEnd = () => {
        if (contentItems.length <= 1 || isTouchOnMedia.current) return;

        const swipeThreshold = 50;
        const diffX = touchStartX.current - touchEndX.current;
        const diffY = Math.abs(touchStartY.current - touchEndY.current);

        // Only trigger swipe if horizontal movement is greater than vertical (to avoid interfering with scrolling)
        if (Math.abs(diffX) > swipeThreshold && Math.abs(diffX) > diffY) {
            if (diffX > 0) {
                handleNextSlide();
            } else {
                handlePrevSlide();
            }
        }
    };

    const renderPagination = () => {
        if (!galleryData?.total_pages || galleryData.total_pages <= 1) return null;

        const pages = [];
        const totalPages = galleryData.total_pages;
        const currentPage = galleryData.page;

        pages.push(
            <li key="prev" className={`page-item mb-0 ${!galleryData.has_previous ? "disabled" : ""}`}>
                <a className="page-link" href="#" onClick={(e) => {
                    e.preventDefault();
                    if (galleryData.has_previous) setPage(currentPage - 1);
                }}>
                    <i className="fas fa-angle-double-right"></i>
                </a>
            </li>
        );

        for (let i = 1; i <= totalPages; i += 1) {
            if (i === 1 || i === totalPages || (i >= currentPage - 1 && i <= currentPage + 1)) {
                pages.push(
                    <li key={i} className={`page-item mb-0 ${i === currentPage ? "active" : ""}`}>
                        <a className="page-link" href="#" onClick={(e) => {
                            e.preventDefault();
                            setPage(i);
                        }}>{i}</a>
                    </li>
                );
            } else if (i === currentPage - 2 || i === currentPage + 2) {
                pages.push(
                    <li key={i} className="page-item mb-0 disabled">
                        <span className="page-link">..</span>
                    </li>
                );
            }
        }

        pages.push(
            <li key="next" className={`page-item mb-0 ${!galleryData.has_next ? "disabled" : ""}`}>
                <a className="page-link" href="#" onClick={(e) => {
                    e.preventDefault();
                    if (galleryData.has_next) setPage(currentPage + 1);
                }}>
                    <i className="fas fa-angle-double-left"></i>
                </a>
            </li>
        );

        return pages;
    };

    return (
        <>
            <main>
                <section className="py-5">
                    <div className="container">
                        <div className="row g-4">
                            {isLoadingGallery ? (
                                <div className="col-12 text-center py-5">
                                    <div className="spinner-border text-primary" role="status">
                                        <span className="visually-hidden">Loading...</span>
                                    </div>
                                </div>
                            ) : galleryData?.items.length === 0 ? (
                                <div className="col-12 text-center py-5 text-muted">موردی یافت نشد</div>
                            ) : (
                                galleryData?.items.map((item) => (
                                    <div key={item.id} className="col-sm-6 col-lg-4 col-xl-3">
                                        <div className="card shadow h-100">
                                            <div className="position-relative"
                                                 onClick={() => setSelectedGalleryId(item.id)} role="button">
                                                <img
                                                    src={item.thumbnail ? getMediaUrl(item.thumbnail) : "/assets/images/book/01.jpg"}
                                                    className="card-img-top"
                                                    alt={item.title}
                                                />
                                            </div>
                                            <div className="card-body px-3">
                                                <h5 className="card-title mb-0">
                                                    <button
                                                        type="button"
                                                        className="btn btn-link p-0 text-start text-decoration-none stretched-link"
                                                        onClick={() => setSelectedGalleryId(item.id)}
                                                    >
                                                        {item.title}
                                                    </button>
                                                </h5>
                                            </div>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>

                        {galleryData && galleryData.total_pages && galleryData.total_pages > 1 && (
                            <nav className="mt-4 d-flex justify-content-center" aria-label="navigation">
                                <ul className="pagination pagination-primary-soft d-inline-block d-md-flex rounded mb-0">
                                    {renderPagination()}
                                </ul>
                            </nav>
                        )}
                    </div>
                </section>
            </main>

            {selectedGalleryId && (
                <>
                    <div className="modal fade show d-block" tabIndex={-1} role="dialog" aria-modal="true"
                         style={{backgroundColor: "rgba(0, 0, 0, 0.65)"}}>
                        <div
                            className="modal-dialog modal-dialog-centered"
                            role="document"
                            style={{
                                width: isMobile ? "100vw" : "75vw",
                                maxWidth: isMobile ? "100vw" : "75vw",
                                margin: isMobile ? "0" : "auto",
                                height: isMobile ? "100vh" : "auto"
                            }}
                        >
                            <div className="modal-content"
                                 style={{maxHeight: "100vh", overflow: "hidden", height: isMobile ? "100vh" : "auto"}}>
                                <div className="modal-header justify-content-start">
                                    <h5 className="modal-title">{galleryDetail?.title || "..."}</h5>
                                    <button
                                        type="button"
                                        className="btn-close ms-auto"
                                        aria-label="Close"
                                        onClick={() => setSelectedGalleryId(null)}
                                    />
                                </div>
                                <div className="modal-body pb-4"
                                     style={{maxHeight: "calc(100vh - 70px)", overflow: "hidden"}}>
                                    {isLoadingGalleryDetail ? (
                                        <div className="text-center py-5">
                                            <div className="spinner-border text-primary" role="status">
                                                <span className="visually-hidden">Loading...</span>
                                            </div>
                                        </div>
                                    ) : (
                                        <div
                                            className="bg-light rounded-3 p-4 position-relative"
                                            onTouchStart={isMobile ? handleTouchStart : undefined}
                                            onTouchMove={isMobile ? handleTouchMove : undefined}
                                            onTouchEnd={isMobile ? handleTouchEnd : undefined}
                                        >
                                            <div
                                                className="position-relative"
                                                style={{
                                                    minHeight: "calc(100vh - 250px)",
                                                    paddingLeft: isMobile ? "0" : "70px",
                                                    paddingRight: isMobile ? "0" : "70px"
                                                }}
                                            >
                                                {contentItems.map((item, index) => (
                                                    <div
                                                        key={item.id}
                                                        className={`position-absolute top-0 start-0 w-100 h-100 transition ${
                                                            index === currentSlide ? "d-block" : "d-none"
                                                        }`}
                                                        style={{
                                                            transition: "opacity 0.3s ease-in-out",
                                                            paddingLeft: isMobile ? "0" : "70px",
                                                            paddingRight: isMobile ? "0" : "70px"
                                                        }}
                                                    >
                                                        <div
                                                            className="d-flex align-items-center justify-content-center h-100">
                                                            {item.content_type === "embed" ? (
                                                                <div className="w-100"
                                                                     dangerouslySetInnerHTML={{__html: item.embed_code}}/>
                                                            ) : item.file ? (
                                                                item.content_type === "image" ? (
                                                                    <img
                                                                        src={getMediaUrl(item.file)}
                                                                        className="img-fluid rounded w-100"
                                                                        style={{
                                                                            maxHeight: "calc(100vh - 250px)",
                                                                            objectFit: "contain"
                                                                        }}
                                                                        alt={galleryDetail?.title || "gallery"}
                                                                    />
                                                                ) : item.content_type === "video" ? (
                                                                    <video
                                                                        ref={(el) => {
                                                                            mediaRefs.current[index] = el;
                                                                        }}
                                                                        src={getMediaUrl(item.file)}
                                                                        controls
                                                                        className="w-100 rounded"
                                                                        style={{
                                                                            maxHeight: "calc(100vh - 250px)",
                                                                            touchAction: "auto"
                                                                        }}
                                                                    />
                                                                ) : (
                                                                    <audio
                                                                        ref={(el) => {
                                                                            mediaRefs.current[index] = el;
                                                                        }}
                                                                        src={getMediaUrl(item.file)}
                                                                        controls
                                                                        className="w-100"
                                                                        style={{touchAction: "auto"}}
                                                                    />
                                                                )
                                                            ) : null}
                                                        </div>
                                                    </div>
                                                ))}

                                                {contentItems.length > 1 && !isMobile && (
                                                    <>
                                                        <button
                                                            type="button"
                                                            className="btn btn-primary position-absolute top-50 end-0 translate-middle-y me-3 rounded-circle d-flex align-items-center justify-content-center"
                                                            style={{width: "50px", height: "50px", zIndex: 10}}
                                                            onClick={handlePrevSlide}
                                                            aria-label="Previous"
                                                        >
                                                            <i className="fas fa-chevron-left"></i>
                                                        </button>
                                                        <button
                                                            type="button"
                                                            className="btn btn-primary position-absolute top-50 start-0 translate-middle-y ms-3 rounded-circle d-flex align-items-center justify-content-center"
                                                            style={{width: "50px", height: "50px", zIndex: 10}}
                                                            onClick={handleNextSlide}
                                                            aria-label="Next"
                                                        >
                                                            <i className="fas fa-chevron-right"></i>
                                                        </button>
                                                    </>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="modal-backdrop fade show end-0" onClick={() => setSelectedGalleryId(null)}/>
                </>
            )}
        </>
    );
}
