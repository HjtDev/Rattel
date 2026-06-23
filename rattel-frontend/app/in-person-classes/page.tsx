"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { toast } from "react-toastify";
import {
    useInPersonClasses,
    useInPersonClassCategories,
    registerForInPersonClass,
    type InPersonClass,
} from "@/src/core/hooks/useInPersonClasses";
import { cartManager } from "@/src/core/cart/cartManager";
import { useAuth } from "@/src/core/hooks/useAuth";
import { getMediaUrl, toJalali } from "@/src/core/utils";
import { fadeInUp, staggerContainer } from "@/src/core/motionVariants";

const formatPrice = (price: number) =>
    new Intl.NumberFormat("fa-IR").format(price);

function InPersonClassesContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { isAuthenticated } = useAuth();

    const [page, setPage] = useState(Number(searchParams.get("page")) || 1);
    const [category, setCategory] = useState<string | undefined>(
        searchParams.get("category") || undefined
    );

    const [selectedClass, setSelectedClass] = useState<InPersonClass | null>(null);
    const [selectedTimeRangeId, setSelectedTimeRangeId] = useState<number | null>(null);
    const [isRegistering, setIsRegistering] = useState(false);

    const { classesData, isLoadingClasses } = useInPersonClasses({ page, count: 9, category });
    const { categories } = useInPersonClassCategories();

    const handleCategoryChange = (slug: string | undefined) => {
        setCategory(slug);
        setPage(1);
        const params = new URLSearchParams();
        if (slug) params.set("category", slug);
        router.push(`/in-person-classes${params.toString() ? `?${params}` : ""}`, { scroll: false });
    };

    const handlePageChange = (newPage: number) => {
        setPage(newPage);
        window.scrollTo({ top: 0, behavior: "smooth" });
    };

    const getBsModal = () =>
        (window as Window & { bootstrap?: { Modal: { new (el: Element): { show(): void }; getInstance(el: Element): { hide(): void } | null } } }).bootstrap?.Modal;

    const openModal = (cls: InPersonClass) => {
        if (!isAuthenticated) {
            router.push(`/auth/login?next=${encodeURIComponent("/in-person-classes/")}`);
            return;
        }
        setSelectedClass(cls);
        setSelectedTimeRangeId(null);
        const modalEl = document.getElementById("registerModal");
        if (modalEl) {
            const BootstrapModal = getBsModal();
            if (BootstrapModal) new BootstrapModal(modalEl).show();
        }
    };

    const closeModal = () => {
        const modalEl = document.getElementById("registerModal");
        if (modalEl) {
            const BootstrapModal = getBsModal();
            BootstrapModal?.getInstance(modalEl)?.hide();
        }
    };

    const handleRegisterSubmit = async () => {
        if (!selectedClass || !selectedTimeRangeId) {
            toast.warning("لطفاً یک زمان را انتخاب کنید.");
            return;
        }

        setIsRegistering(true);
        const result = await registerForInPersonClass(selectedClass.id, selectedTimeRangeId);

        if (result.success && result.id) {
            const cartResult = await cartManager.add(
                "in_person_class",
                "inpersonclassregistration",
                result.id,
                1,
                {
                    name: selectedClass.title,
                    price: selectedClass.price,
                    new_price: selectedClass.new_price,
                    picture: selectedClass.thumbnail,
                }
            );
            if (cartResult.success) {
                toast.success("با موفقیت به سبد خرید اضافه شد.");
                closeModal();
            } else {
                const cartMsg = cartResult.message?.toLowerCase() ?? "";
                const farsiMessage = cartMsg.includes("already own")
                    ? "شما قبلاً این کلاس را خریداری کرده‌اید."
                    : "خطا در افزودن به سبد خرید";
                toast.error(farsiMessage);
            }
        } else {
            toast.error(result.message || "خطا در ثبت‌نام");
        }
        setIsRegistering(false);
    };

    const renderPagination = () => {
        if (!classesData?.total_pages || classesData.total_pages <= 1) return null;

        const totalPages = classesData.total_pages;
        const currentPage = classesData.page;
        const pages = [];

        pages.push(
            <li key="prev" className={`page-item mb-0 ${!classesData.has_previous ? "disabled" : ""}`}>
                <a className="page-link" href="#" onClick={(e) => { e.preventDefault(); if (classesData.has_previous) handlePageChange(currentPage - 1); }}>
                    <i className="fas fa-angle-double-right"></i>
                </a>
            </li>
        );

        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= currentPage - 1 && i <= currentPage + 1)) {
                pages.push(
                    <li key={i} className={`page-item mb-0 ${i === currentPage ? "active" : ""}`}>
                        <a className="page-link" href="#" onClick={(e) => { e.preventDefault(); handlePageChange(i); }}>{i}</a>
                    </li>
                );
            } else if (i === currentPage - 2 || i === currentPage + 2) {
                pages.push(<li key={i} className="page-item mb-0 disabled"><span className="page-link">..</span></li>);
            }
        }

        pages.push(
            <li key="next" className={`page-item mb-0 ${!classesData.has_next ? "disabled" : ""}`}>
                <a className="page-link" href="#" onClick={(e) => { e.preventDefault(); if (classesData.has_next) handlePageChange(currentPage + 1); }}>
                    <i className="fas fa-angle-double-left"></i>
                </a>
            </li>
        );

        return pages;
    };

    return (
        <>
            <main>
                {/* Hero banner */}
                <section
                    className="bg-dark align-items-center d-flex py-5"
                    style={{
                        background: "url(/assets/images/pattern/04.png) no-repeat center center",
                        backgroundSize: "cover",
                        minHeight: "180px",
                    }}
                >
                    <div className="container">
                        <div className="row">
                            <div className="col-12">
                                <h1 className="text-white fs-2">کلاس‌های حضوری</h1>
                                <nav aria-label="breadcrumb">
                                    <ol className="breadcrumb breadcrumb-dark breadcrumb-dots mb-0">
                                        <li className="breadcrumb-item"><a href="/">صفحه اصلی</a></li>
                                        <li className="breadcrumb-item active" aria-current="page">کلاس‌های حضوری</li>
                                    </ol>
                                </nav>
                            </div>
                        </div>
                    </div>
                </section>

                <section className="pb-0 py-sm-5">
                    <div className="container">
                        <div className="row">
                            {/* Filter sidebar */}
                            <div className="col-xl-3 col-xxl-3">
                                <div className="offcanvas-xl offcanvas-end" tabIndex={-1} id="offcanvasSidebar">
                                    <div className="offcanvas-header bg-light">
                                        <h5 className="offcanvas-title">فیلتر دسته‌بندی</h5>
                                        <button type="button" className="btn-close" data-bs-dismiss="offcanvas" data-bs-target="#offcanvasSidebar" aria-label="Close"></button>
                                    </div>
                                    <div className="offcanvas-body p-3 p-xl-0">
                                        <div className="card card-body shadow p-4">
                                            <h4 className="mb-4 fs-6">دسته‌بندی</h4>
                                            <div className="d-flex flex-wrap gap-2">
                                                <button
                                                    className={`btn btn-sm ${!category ? "btn-primary" : "btn-outline-secondary"}`}
                                                    onClick={() => handleCategoryChange(undefined)}
                                                >
                                                    همه
                                                </button>
                                                {categories.map((cat) => (
                                                    <button
                                                        key={cat.id}
                                                        className={`btn btn-sm ${category === cat.slug ? "btn-primary" : "btn-outline-secondary"}`}
                                                        onClick={() => handleCategoryChange(cat.slug)}
                                                    >
                                                        {cat.name}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Card grid */}
                            <div className="col-xl-9 col-xxl-9">
                                <div className="row g-3 align-items-center justify-content-between mb-4">
                                    <div className="col-auto">
                                        <h4 className="mb-0 fs-5 fw-normal">
                                            {classesData
                                                ? `${classesData.total} کلاس یافت شد`
                                                : "در حال بارگذاری..."}
                                        </h4>
                                    </div>
                                    <div className="col-auto d-xl-none">
                                        <button
                                            className="btn btn-primary mb-0"
                                            type="button"
                                            data-bs-toggle="offcanvas"
                                            data-bs-target="#offcanvasSidebar"
                                            aria-controls="offcanvasSidebar"
                                        >
                                            <i className="fas fa-sliders-h me-1"></i>
                                            نمایش فیلتر
                                        </button>
                                    </div>
                                </div>

                                {isLoadingClasses ? (
                                    <div className="text-center py-5">
                                        <div className="spinner-border text-primary" role="status">
                                            <span className="visually-hidden">در حال بارگذاری...</span>
                                        </div>
                                    </div>
                                ) : classesData?.classes.length === 0 ? (
                                    <div className="text-center py-5">
                                        <i className="bi bi-calendar-x fs-1 text-muted mb-3 d-block"></i>
                                        <p className="text-muted fs-5">کلاسی یافت نشد</p>
                                    </div>
                                ) : (
                                    <motion.div
                                        className="row g-4"
                                        variants={staggerContainer}
                                        initial="hidden"
                                        animate="show"
                                    >
                                        {classesData?.classes.map((cls) => (
                                            <motion.div
                                                key={cls.id}
                                                className="col-sm-6 col-lg-4"
                                                variants={fadeInUp}
                                            >
                                                <div className="card shadow h-100 overflow-hidden">
                                                    {/* Thumbnail */}
                                                    <div className="position-relative" style={{ height: "200px", overflow: "hidden" }}>
                                                        <img
                                                            src={cls.thumbnail ? getMediaUrl(cls.thumbnail) : "/assets/images/courses/4by3/06.jpg"}
                                                            alt={cls.title}
                                                            className="w-100 h-100"
                                                            style={{ objectFit: "cover" }}
                                                        />
                                                        {cls.discount > 0 && (
                                                            <div className="position-absolute top-0 end-0 m-2">
                                                                <span className="badge bg-danger fs-6">{cls.discount}% تخفیف</span>
                                                            </div>
                                                        )}
                                                    </div>

                                                    <div className="card-body d-flex flex-column">
                                                        {/* Categories */}
                                                        {cls.categories.length > 0 && (
                                                            <div className="mb-2 d-flex flex-wrap gap-1">
                                                                {cls.categories.map((cat) => (
                                                                    <span key={cat.id} className="badge text-bg-primary">{cat.name}</span>
                                                                ))}
                                                            </div>
                                                        )}

                                                        <h5 className="card-title fw-normal mb-2">{cls.title}</h5>

                                                        <p
                                                            className="card-text small flex-grow-1"
                                                            style={{
                                                                display: "-webkit-box",
                                                                WebkitLineClamp: 3,
                                                                WebkitBoxOrient: "vertical",
                                                                overflow: "hidden",
                                                            }}
                                                            dangerouslySetInnerHTML={{ __html: cls.short_description }}
                                                        />

                                                        {/* Dates */}
                                                        <div className="d-flex gap-3 my-3 small">
                                                            <span><i className="bi bi-calendar-event me-1"></i>{toJalali(cls.start_date)}</span>
                                                            <span><i className="bi bi-calendar-check me-1"></i>{toJalali(cls.end_date)}</span>
                                                        </div>

                                                        {/* Price */}
                                                        <div className="d-flex align-items-center justify-content-between mb-3">
                                                            {cls.new_price > 0 ? (
                                                                <div>
                                                                    <span className="text-decoration-line-through text-muted small me-2">
                                                                        {formatPrice(cls.price)} تومان
                                                                    </span>
                                                                    <span className="h5 mb-0 text-success fw-bold">
                                                                        {formatPrice(cls.new_price)} تومان
                                                                    </span>
                                                                </div>
                                                            ) : (
                                                                <span className="h5 mb-0 text-success fw-bold">
                                                                    {formatPrice(cls.price)} تومان
                                                                </span>
                                                            )}
                                                        </div>

                                                        <button
                                                            className="btn btn-primary w-100 mt-auto"
                                                            onClick={() => openModal(cls)}
                                                        >
                                                            <i className="bi bi-person-plus me-2"></i>
                                                            ثبت‌نام
                                                        </button>
                                                    </div>
                                                </div>
                                            </motion.div>
                                        ))}
                                    </motion.div>
                                )}

                                {classesData && (classesData.total_pages ?? 0) > 1 && (
                                    <div className="col-12 mt-4">
                                        <nav className="d-flex justify-content-center" aria-label="navigation">
                                            <ul className="pagination pagination-primary-soft d-inline-block d-md-flex rounded mb-0">
                                                {renderPagination()}
                                            </ul>
                                        </nav>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </section>
            </main>

            {/* Registration Modal */}
            <div
                className="modal fade"
                id="registerModal"
                tabIndex={-1}
                aria-labelledby="registerModalLabel"
                aria-hidden="true"
            >
                <div className="modal-dialog modal-dialog-centered">
                    <div className="modal-content">
                        <div className="modal-header border-bottom">
                            <h5 className="modal-title" id="registerModalLabel">
                                انتخاب زمان کلاس
                            </h5>
                            <button type="button" className="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div className="modal-body">
                            {selectedClass && (
                                <>
                                    <p className="fw-semibold mb-3">{selectedClass.title}</p>
                                    <p className="text-muted small mb-4">یکی از زمان‌های موجود را انتخاب کنید:</p>

                                    {selectedClass.available_times.length === 0 ? (
                                        <p className="text-muted text-center">زمانی برای این کلاس تعریف نشده است.</p>
                                    ) : (
                                        <div className="d-flex flex-column gap-2">
                                            {selectedClass.available_times.map((tr) => (
                                                <div
                                                    key={tr.id}
                                                    className={`p-3 rounded border cursor-pointer ${
                                                        selectedTimeRangeId === tr.id
                                                            ? "border-primary bg-primary bg-opacity-10"
                                                            : "border-secondary"
                                                    }`}
                                                    style={{ cursor: "pointer" }}
                                                    onClick={() => setSelectedTimeRangeId(tr.id)}
                                                >
                                                    <div className="form-check mb-0">
                                                        <input
                                                            className="form-check-input"
                                                            type="radio"
                                                            name="time_range"
                                                            id={`tr-${tr.id}`}
                                                            checked={selectedTimeRangeId === tr.id}
                                                            onChange={() => setSelectedTimeRangeId(tr.id)}
                                                        />
                                                        <label className="form-check-label w-100" htmlFor={`tr-${tr.id}`} style={{ cursor: "pointer" }}>
                                                            <i className="bi bi-clock me-2 text-primary"></i>
                                                            {tr.label}
                                                        </label>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </>
                            )}
                        </div>
                        <div className="modal-footer border-top">
                            <button
                                type="button"
                                className="btn btn-outline-secondary"
                                data-bs-dismiss="modal"
                            >
                                انصراف
                            </button>
                            <button
                                type="button"
                                className="btn btn-primary"
                                onClick={handleRegisterSubmit}
                                disabled={isRegistering || !selectedTimeRangeId}
                            >
                                {isRegistering ? (
                                    <>
                                        <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                                        در حال پردازش...
                                    </>
                                ) : (
                                    <>
                                        <i className="bi bi-cart-plus me-2"></i>
                                        افزودن به سبد خرید
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
}

export default function InPersonClassesPage() {
    return (
        <Suspense fallback={null}>
            <InPersonClassesContent />
        </Suspense>
    );
}
