"use client";

import { useEffect } from "react";
import { motion } from "framer-motion";
import { useQuiz } from "@/src/core/hooks/useQuiz";
import { quizManager } from "@/src/core/quiz/quizManager";
import { useAuth } from "@/src/core/hooks/useAuth";
import { fadeInUp, staggerContainer } from "@/src/core/motionVariants";

export default function LeaderboardPage() {
    const { leaderboard, userLeaderboardEntry, isLoading } = useQuiz();
    const { user } = useAuth();

    useEffect(() => {
        quizManager.fetchLeaderboard();
    }, []);

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
                    <div className="col-12">
                        <h1 className="text-white fs-2">
                            <i className="bi bi-trophy-fill text-warning me-3"></i>
                            جدول امتیازات
                        </h1>
                        <nav aria-label="breadcrumb">
                            <ol className="breadcrumb breadcrumb-dark breadcrumb-dots mb-0">
                                <li className="breadcrumb-item"><a href="/">صفحه اصلی</a></li>
                                <li className="breadcrumb-item"><a href="/quiz">آزمون‌ها</a></li>
                                <li className="breadcrumb-item active">جدول امتیازات</li>
                            </ol>
                        </nav>
                    </div>
                </div>
            </section>

            <section className="py-5">
                <div className="container">
                    <div className="row justify-content-center">
                        <div className="col-lg-7 col-xl-6">
                            {isLoading ? (
                                <div className="text-center py-5">
                                    <div className="spinner-border text-primary" role="status">
                                        <span className="visually-hidden">در حال بارگذاری...</span>
                                    </div>
                                </div>
                            ) : (
                                <motion.div
                                    variants={staggerContainer}
                                    initial="hidden"
                                    animate="show"
                                >
                                    <div className="card border-0 shadow-sm overflow-hidden">
                                        <div className="card-header bg-primary text-white py-3">
                                            <h5 className="mb-0">
                                                <i className="bi bi-trophy me-2"></i>
                                                برترین‌ها
                                            </h5>
                                        </div>
                                        <div className="card-body p-0">
                                            {leaderboard.length === 0 ? (
                                                <div className="text-center py-5">
                                                    <i className="bi bi-trophy fs-1 text-muted mb-3 d-block"></i>
                                                    <p className="text-muted">هنوز کسی در آزمون شرکت نکرده است</p>
                                                </div>
                                            ) : (
                                                <div className="list-group list-group-flush">
                                                    {leaderboard.map((entry, index) => {
                                                        const rank = index + 1;
                                                        const medalClass =
                                                            rank === 1 ? "text-warning" :
                                                            rank === 2 ? "text-secondary" :
                                                            rank === 3 ? "text-danger" : "text-muted";
                                                        const medalIcon =
                                                            rank === 1 ? "bi-trophy-fill" :
                                                            rank === 2 ? "bi-award-fill" :
                                                            rank === 3 ? "bi-award" : "bi-hash";
                                                        return (
                                                            <motion.div
                                                                key={entry.user__id}
                                                                className={`list-group-item d-flex align-items-center gap-3 py-3 ${entry.user__username === (user as any)?.username ? "bg-primary bg-opacity-10" : ""}`}
                                                                variants={fadeInUp}
                                                            >
                                                                <div className={`fs-4 ${medalClass}`} style={{ width: "36px", textAlign: "center" }}>
                                                                    <i className={`bi ${medalIcon}`}></i>
                                                                </div>
                                                                <div className="flex-grow-1">
                                                                    <div className="fw-semibold">{entry.user__username}</div>
                                                                </div>
                                                                <div className="text-primary fw-bold fs-5">
                                                                    {new Intl.NumberFormat("fa-IR").format(entry.total_score)}
                                                                    <small className="text-muted fw-normal fs-6 ms-1">امتیاز</small>
                                                                </div>
                                                            </motion.div>
                                                        );
                                                    })}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                    {userLeaderboardEntry && (
                                        <div className="list-group list-group-flush border-top">
                                            <div className="list-group-item text-center py-1 small">•••</div>
                                            <div className="list-group-item d-flex align-items-center gap-3 py-3 bg-primary bg-opacity-10">
                                                <div className="fs-4 text-primary fw-bold" style={{ width: "36px", textAlign: "center" }}>
                                                    {new Intl.NumberFormat("fa-IR").format(userLeaderboardEntry.rank)}
                                                </div>
                                                <div className="flex-grow-1 fw-semibold">
                                                    {userLeaderboardEntry.user__username}
                                                    <span className="badge bg-primary ms-2 small">شما</span>
                                                </div>
                                                <div className="text-primary fw-bold fs-5">
                                                    {new Intl.NumberFormat("fa-IR").format(userLeaderboardEntry.total_score)}
                                                    <small className="fw-normal fs-6 ms-1">امتیاز</small>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    <div className="text-center mt-4">
                                        <a href="/quiz" className="btn btn-outline-primary">
                                            <i className="bi bi-arrow-right me-2"></i>
                                            بازگشت به آزمون‌ها
                                        </a>
                                    </div>
                                </motion.div>
                            )}
                        </div>
                    </div>
                </div>
            </section>
        </main>
    );
}
