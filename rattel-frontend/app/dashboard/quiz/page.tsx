"use client";

import { useEffect } from "react";
import DashboardBase from "@/src/components/dashboard/DashboardBase";
import { useDashboard } from "@/src/core/hooks/useDashboard";
import { useQuiz } from "@/src/core/hooks/useQuiz";
import { quizManager } from "@/src/core/quiz/quizManager";
import { toJalali } from "@/src/core/utils";

const STATUS_CONFIG: Record<string, { label: string; badge: string }> = {
    completed: { label: "تکمیل شده", badge: "bg-success" },
    expired: { label: "منقضی شده", badge: "bg-danger" },
    in_progress: { label: "در حال انجام", badge: "bg-warning text-dark" },
};

const formatTime = (seconds: number): string => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
};

function MyQuizContent() {
    const { isLoadingDashboard } = useDashboard();
    const { myAttempts, isLoading } = useQuiz();

    useEffect(() => {
        quizManager.fetchMyAttempts();
    }, []);

    return !isLoadingDashboard ? (
        <div className="col-xl-9">
            <div className="card bg-transparent border rounded-3">
                <div className="card-header bg-transparent border-bottom d-flex align-items-center justify-content-between">
                    <h3 className="mb-0 fs-5 ff-vb">
                        <i className="bi bi-patch-question me-2 text-primary"></i>
                        آزمون‌های من
                    </h3>
                    <a href="/quiz" className="btn btn-sm btn-outline-primary">
                        مشاهده آزمون‌ها
                    </a>
                </div>

                <div className="card-body">
                    {isLoading ? (
                        <div className="text-center py-5">
                            <div className="spinner-border text-primary" role="status">
                                <span className="visually-hidden">در حال بارگذاری...</span>
                            </div>
                        </div>
                    ) : !myAttempts || myAttempts.length === 0 ? (
                        <div className="text-center py-5">
                            <i className="bi bi-patch-question fs-1 text-muted mb-3 d-block"></i>
                            <p className="text-muted">هنوز در هیچ آزمونی شرکت نکرده‌اید</p>
                            <a href="/quiz" className="btn btn-primary btn-sm mt-2">
                                <i className="bi bi-play-circle me-2"></i>
                                شروع آزمون
                            </a>
                        </div>
                    ) : (
                        <div className="table-responsive border-0">
                            <table className="table table-dark-gray align-middle p-4 mb-0 table-hover">
                                <thead>
                                    <tr>
                                        <th scope="col" className="border-0 rounded-start">آزمون</th>
                                        <th scope="col" className="border-0">امتیاز</th>
                                        <th scope="col" className="border-0">درست / غلط</th>
                                        <th scope="col" className="border-0">مدت زمان</th>
                                        <th scope="col" className="border-0">تاریخ</th>
                                        <th scope="col" className="border-0 rounded-end">وضعیت</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {myAttempts.map((attempt) => {
                                        const cfg = STATUS_CONFIG[attempt.status] ?? { label: attempt.status_display, badge: "bg-secondary" };
                                        return (
                                            <tr key={attempt.id}>
                                                <td>
                                                    <div className="fw-semibold">{attempt.quiz.title}</div>
                                                </td>
                                                <td>
                                                    <span className="text-primary fw-bold">
                                                        {new Intl.NumberFormat("fa-IR").format(attempt.score)}
                                                    </span>
                                                </td>
                                                <td>
                                                    <span className="text-success me-1">
                                                        <i className="bi bi-check-circle me-1"></i>
                                                        {new Intl.NumberFormat("fa-IR").format(attempt.correct_count)}
                                                    </span>
                                                    <span className="text-muted">/</span>
                                                    <span className="text-danger ms-1">
                                                        <i className="bi bi-x-circle me-1"></i>
                                                        {new Intl.NumberFormat("fa-IR").format(attempt.incorrect_count)}
                                                    </span>
                                                </td>
                                                <td className="text-nowrap">
                                                    <i className="bi bi-clock me-1 text-muted"></i>
                                                    {formatTime(attempt.time_spent)}
                                                </td>
                                                <td className="text-nowrap">
                                                    {attempt.finished_at
                                                        ? toJalali(attempt.finished_at.split("T")[0])
                                                        : toJalali(attempt.created_at.split("T")[0])
                                                    }
                                                </td>
                                                <td>
                                                    <span className={`badge ${cfg.badge}`}>{cfg.label}</span>
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>
        </div>
    ) : null;
}

export default function MyQuizPage() {
    return <DashboardBase Content={<MyQuizContent />} />;
}
