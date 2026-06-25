"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { toast } from "react-toastify";
import { useQuiz } from "@/src/core/hooks/useQuiz";
import { quizManager, type Quiz, type QuizCategory } from "@/src/core/quiz/quizManager";
import { useAuth } from "@/src/core/hooks/useAuth";
import { getMediaUrl } from "@/src/core/utils";
import { fadeInUp, staggerContainer } from "@/src/core/motionVariants";

const DIFFICULTY_LABELS: Record<string, { label: string; badge: string }> = {
    easy: { label: "آسان", badge: "bg-success" },
    medium: { label: "متوسط", badge: "bg-warning text-dark" },
    hard: { label: "سخت", badge: "bg-danger" },
};

function QuizListContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { isAuthenticated } = useAuth();

    const [page, setPage] = useState(Number(searchParams.get("page")) || 1);
    const [category, setCategory] = useState<string | undefined>(
        searchParams.get("category") || undefined
    );
    const [categories, setCategories] = useState<QuizCategory[]>([]);

    const { quizzes, quizzesTotal, quizzesTotalPages, isLoading } = useQuiz();

    useEffect(() => {
        quizManager.fetchQuizzes(page, 9, category);
        // Fetch categories for sidebar
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/quiz/categories/`)
            .then((r) => r.json())
            .then((d) => d.success && setCategories(d.categories))
            .catch(() => {});
    }, [page, category]);

    const handleCategoryChange = (slug: string | undefined) => {
        setCategory(slug);
        setPage(1);
        const params = new URLSearchParams();
        if (slug) params.set("category", slug);
        router.push(`/quiz${params.toString() ? `?${params}` : ""}`, { scroll: false });
    };

    const handlePageChange = (newPage: number) => {
        setPage(newPage);
        window.scrollTo({ top: 0, behavior: "smooth" });
    };

    const handleStartQuiz = (quiz: Quiz) => {
        if (!isAuthenticated) {
            router.push(`/auth/login?next=${encodeURIComponent("/quiz/")}`);
            return;
        }
        if (!quiz.access_met) {
            toast.warning(quiz.access_reason || "دسترسی به این آزمون برای شما فعال نیست.");
            return;
        }
        if (quiz.attempts_remaining === 0) {
            toast.warning("به حداکثر تعداد مجاز شرکت در این آزمون رسیده‌اید.");
            return;
        }
        router.push(`/quiz/${quiz.id}`);
    };

    const totalPages = quizzesTotalPages;

    const renderPagination = () => {
        if (!totalPages || totalPages <= 1) return null;
        const pages = [];

        pages.push(
            <li key="prev" className={`page-item mb-0 ${page <= 1 ? "disabled" : ""}`}>
                <a className="page-link" href="#" onClick={(e) => { e.preventDefault(); if (page > 1) handlePageChange(page - 1); }}>
                    <i className="fas fa-angle-double-right"></i>
                </a>
            </li>
        );

        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= page - 1 && i <= page + 1)) {
                pages.push(
                    <li key={i} className={`page-item mb-0 ${i === page ? "active" : ""}`}>
                        <a className="page-link" href="#" onClick={(e) => { e.preventDefault(); handlePageChange(i); }}>{i}</a>
                    </li>
                );
            } else if (i === page - 2 || i === page + 2) {
                pages.push(<li key={i} className="page-item mb-0 disabled"><span className="page-link">..</span></li>);
            }
        }

        pages.push(
            <li key="next" className={`page-item mb-0 ${page >= totalPages ? "disabled" : ""}`}>
                <a className="page-link" href="#" onClick={(e) => { e.preventDefault(); if (page < totalPages) handlePageChange(page + 1); }}>
                    <i className="fas fa-angle-double-left"></i>
                </a>
            </li>
        );

        return pages;
    };

    return (
        <main>
            {/* Hero */}
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
                            <h1 className="text-white fs-2">آزمون‌ها</h1>
                            <nav aria-label="breadcrumb">
                                <ol className="breadcrumb breadcrumb-dark breadcrumb-dots mb-0">
                                    <li className="breadcrumb-item"><a href="/">صفحه اصلی</a></li>
                                    <li className="breadcrumb-item active" aria-current="page">آزمون‌ها</li>
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

                                        <hr className="my-4" />
                                        <a href="/quiz/leaderboard" className="btn btn-outline-primary btn-sm">
                                            <i className="bi bi-trophy me-2"></i>
                                            جدول امتیازات
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Card grid */}
                        <div className="col-xl-9 col-xxl-9">
                            <div className="row g-3 align-items-center justify-content-between mb-4">
                                <div className="col-auto">
                                    <h4 className="mb-0 fs-5 fw-normal">
                                        {quizzesTotal > 0
                                            ? `${new Intl.NumberFormat("fa-IR").format(quizzesTotal)} آزمون یافت شد`
                                            : isLoading ? "در حال بارگذاری..." : "آزمونی یافت نشد"
                                        }
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

                            {isLoading ? (
                                <div className="text-center py-5">
                                    <div className="spinner-border text-primary" role="status">
                                        <span className="visually-hidden">در حال بارگذاری...</span>
                                    </div>
                                </div>
                            ) : quizzes.length === 0 ? (
                                <div className="text-center py-5">
                                    <i className="bi bi-patch-question fs-1 text-muted mb-3 d-block"></i>
                                    <p className="text-muted fs-5">آزمونی یافت نشد</p>
                                </div>
                            ) : (
                                <motion.div
                                    className="row g-4"
                                    variants={staggerContainer}
                                    initial="hidden"
                                    animate="show"
                                >
                                    {quizzes.map((quiz) => {
                                        const diff = DIFFICULTY_LABELS[quiz.difficulty] ?? { label: quiz.difficulty, badge: "bg-secondary" };
                                        const locked = !quiz.access_met;
                                        const noAttempts = quiz.attempts_remaining === 0;
                                        const lockLabel = !quiz.access_reason || quiz.access_reason.includes("اشتراک")
                                            ? "نیاز به اشتراک"
                                            : quiz.access_reason.includes("امتیاز")
                                            ? "امتیاز کافی ندارید"
                                            : quiz.access_reason.includes("آزمون")
                                            ? "پیش‌نیاز تکمیل نشده"
                                            : "دسترسی محدود";

                                        return (
                                            <motion.div
                                                key={quiz.id}
                                                className="col-sm-6 col-lg-4"
                                                variants={fadeInUp}
                                            >
                                                <div className={`card shadow h-100 overflow-hidden ${locked ? "opacity-75" : ""}`}>
                                                    {/* Thumbnail */}
                                                    <div className="position-relative" style={{ height: "180px", overflow: "hidden" }}>
                                                        <img
                                                            src={quiz.thumbnail ? getMediaUrl(quiz.thumbnail) : "/assets/images/courses/4by3/06.jpg"}
                                                            alt={quiz.title}
                                                            className="w-100 h-100"
                                                            style={{ objectFit: "cover" }}
                                                        />
                                                        <div className="position-absolute top-0 end-0 m-2 d-flex flex-column gap-1 align-items-end">
                                                            <span className={`badge ${diff.badge}`}>{diff.label}</span>
                                                            {locked && (
                                                                <span className="badge bg-dark bg-opacity-75">
                                                                    <i className="bi bi-lock-fill me-1"></i>
                                                                    {lockLabel}
                                                                </span>
                                                            )}
                                                        </div>
                                                    </div>

                                                    <div className="card-body d-flex flex-column">
                                                        {quiz.categories.length > 0 && (
                                                            <div className="mb-2 d-flex flex-wrap gap-1">
                                                                {quiz.categories.map((cat) => (
                                                                    <span key={cat.id} className="badge text-bg-light border">{cat.name}</span>
                                                                ))}
                                                            </div>
                                                        )}

                                                        <h5 className="card-title fw-normal mb-3">{quiz.title}</h5>

                                                        <div className="mt-auto d-flex align-items-center justify-content-between mb-3">
                                                            {quiz.attempts_remaining !== null ? (
                                                                <small>
                                                                    <i className="bi bi-arrow-repeat me-1"></i>
                                                                    {new Intl.NumberFormat("fa-IR").format(quiz.attempts_remaining)} تلاش باقی‌مانده
                                                                </small>
                                                            ) : (
                                                                <small>
                                                                    <i className="bi bi-infinity me-1"></i>
                                                                    تلاش نامحدود
                                                                </small>
                                                            )}
                                                            {quiz.question_count !== undefined && (
                                                                <small>
                                                                    <i className="bi bi-list-ol me-1"></i>
                                                                    {new Intl.NumberFormat("fa-IR").format(quiz.question_count)} سوال
                                                                </small>
                                                            )}
                                                        </div>

                                                        <button
                                                            className={`btn w-100 ${locked || noAttempts ? "btn-outline-secondary" : "btn-primary"}`}
                                                            onClick={() => handleStartQuiz(quiz)}
                                                            disabled={noAttempts}
                                                        >
                                                            {locked ? (
                                                                <><i className="bi bi-lock me-2"></i>{lockLabel}</>
                                                            ) : noAttempts ? (
                                                                <><i className="bi bi-x-circle me-2"></i>تلاش ندارید</>
                                                            ) : (
                                                                <><i className="bi bi-play-circle me-2"></i>شروع آزمون</>
                                                            )}
                                                        </button>
                                                    </div>
                                                </div>
                                            </motion.div>
                                        );
                                    })}
                                </motion.div>
                            )}

                            {totalPages > 1 && (
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
    );
}

export default function QuizListPage() {
    return (
        <Suspense fallback={null}>
            <QuizListContent />
        </Suspense>
    );
}
