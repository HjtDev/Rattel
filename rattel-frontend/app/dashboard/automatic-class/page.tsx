"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import DashboardBase from "@/src/components/dashboard/DashboardBase";
import { useAutomaticClass } from "@/src/core/hooks/useAutomaticClass";
import { toast } from "react-toastify";
import { fadeInUp, staggerContainer, scaleIn } from "@/src/core/motionVariants";
import type { PlanStep, UserCallSession } from "@/src/core/automatic-class/automaticClassManager";

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatDate(d: string | null): string {
    if (!d) return "—";
    return new Intl.DateTimeFormat("fa-IR", { year: "numeric", month: "long", day: "numeric" }).format(new Date(d));
}

function stepTypeIcon(type: string): string {
    if (type === "memorize") return "bi-book-fill";
    if (type === "review") return "bi-arrow-repeat";
    if (type === "extra_review") return "bi-arrow-counterclockwise";
    return "bi-trophy-fill";
}

function stepTypeColor(type: string): string {
    if (type === "memorize") return "primary";
    if (type === "review") return "warning";
    if (type === "extra_review") return "info";
    return "success";
}

function statusColor(status: string): string {
    if (status === "completed") return "success";
    if (status === "delayed") return "danger";
    if (status === "skipped") return "secondary";
    return "primary";
}

// Returns a label only for non-trivial statuses. pending = no badge needed.
function statusLabel(status: string): string | null {
    if (status === "completed") return "تکمیل شده";
    if (status === "delayed") return "تأخیر";
    if (status === "skipped") return "رد شده";
    return null;
}

function stepTypeLabel(type: string): string {
    if (type === "memorize") return "حفظ";
    if (type === "review") return "۱۰ درس";
    if (type === "extra_review") return "مرور";
    return "مرور نهایی";
}

// ─── Step Card ────────────────────────────────────────────────────────────────

function StepCard({
    step,
    onComplete,
    onReport,
    animDelay = 0,
}: {
    step: PlanStep;
    onComplete: (id: string, reason?: string) => void;
    onReport: (id: string, reason: string) => void;
    animDelay?: number;
}) {
    const shouldReduceMotion = useReducedMotion();
    const [showReportForm, setShowReportForm] = useState(false);
    const [reason, setReason] = useState("");
    const [completing, setCompleting] = useState(false);

    const color = stepTypeColor(step.step_type);
    const icon = stepTypeIcon(step.step_type);
    const isDone = step.status === "completed" || step.status === "skipped";

    const handleComplete = async () => {
        if (completing || isDone) return;
        setCompleting(true);
        await onComplete(step.id, reason || undefined);
        setCompleting(false);
    };

    const handleReport = async () => {
        if (!reason.trim()) { toast.warning("لطفاً دلیل تأخیر را وارد کنید"); return; }
        await onReport(step.id, reason);
        setShowReportForm(false);
        setReason("");
    };

    return (
        <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: animDelay }}
            className={`card border-0 rounded-4 shadow-sm mb-3 overflow-hidden ${isDone ? "opacity-75" : ""}`}
        >
            <div className={`border-start border-4 border-${color} p-4`}>
                <div className="d-flex align-items-start gap-3">
                    <div
                        className={`bg-${color} bg-opacity-10 text-${color} rounded-3 d-flex align-items-center justify-content-center flex-shrink-0`}
                        style={{ width: 48, height: 48 }}
                    >
                        <i className={`bi ${icon} fs-5`} />
                    </div>
                    <div className="flex-grow-1">
                        <div className="d-flex align-items-center justify-content-between flex-wrap gap-2 mb-1">
                            <h6 className="mb-0 fw-bold">{stepTypeLabel(step.step_type)}</h6>
                            <div className="d-flex gap-2 align-items-center">
                                {step.is_delayed && step.status !== "completed" && (
                                    <span className="badge bg-danger bg-opacity-10 text-danger rounded-pill">
                                        <i className="bi bi-clock-history me-1" />
                                        تأخیر داشته
                                    </span>
                                )}
                                {statusLabel(step.status) && (
                                    <span className={`badge bg-${statusColor(step.status)} bg-opacity-10 text-${statusColor(step.status)} rounded-pill`}>
                                        {statusLabel(step.status)}
                                    </span>
                                )}
                            </div>
                        </div>
                        <p className="small mb-2">
                            {step.page_start === step.page_end
                                ? `صفحه ${step.page_start}`
                                : `صفحات ${step.page_start} تا ${step.page_end}`}
                            {step.sub_part !== "full" && (
                                <span className="ms-2 badge bg-light text-dark">{step.sub_part_display}</span>
                            )}
                        </p>
                        {step.admin_note && (
                            <div className="alert alert-info alert-sm py-2 px-3 rounded-3 small mb-2">
                                <i className="bi bi-chat-quote me-1" />
                                {step.admin_note}
                            </div>
                        )}
                        {!isDone && (
                            <div className="d-flex gap-2 flex-wrap mt-3">
                                <motion.button
                                    className={`btn btn-${color} btn-sm rounded-pill px-3`}
                                    onClick={handleComplete}
                                    disabled={completing}
                                    whileTap={shouldReduceMotion ? undefined : { scale: 0.95 }}
                                >
                                    {completing ? (
                                        <span className="spinner-border spinner-border-sm" />
                                    ) : (
                                        <><i className="bi bi-check2-circle me-1" />تکمیل شد</>
                                    )}
                                </motion.button>
                                <button
                                    className="btn btn-outline-secondary btn-sm rounded-pill px-3"
                                    onClick={() => setShowReportForm(!showReportForm)}
                                >
                                    <i className="bi bi-exclamation-triangle me-1" />
                                    گزارش تأخیر
                                </button>
                            </div>
                        )}
                        {isDone && step.completed_at && (
                            <p className="text-success small mb-0 mt-2">
                                <i className="bi bi-check-circle-fill me-1" />
                                تکمیل شده در {formatDate(step.completed_at)}
                            </p>
                        )}
                    </div>
                </div>

                <AnimatePresence>
                    {showReportForm && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.25 }}
                            className="overflow-hidden mt-3"
                        >
                            <div className="border-top pt-3">
                                <label className="form-label small fw-semibold">دلیل تأخیر</label>
                                <textarea
                                    className="form-control form-control-sm rounded-3 mb-2"
                                    rows={2}
                                    value={reason}
                                    onChange={(e) => setReason(e.target.value)}
                                    placeholder="دلیل را شرح دهید..."
                                />
                                <div className="d-flex gap-2">
                                    <button className="btn btn-danger btn-sm rounded-pill px-3" onClick={handleReport}>
                                        ثبت دلیل
                                    </button>
                                    <button
                                        className="btn btn-outline-secondary btn-sm rounded-pill"
                                        onClick={() => { setShowReportForm(false); setReason(""); }}
                                    >
                                        لغو
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </motion.div>
    );
}

// ─── Progress Ring ────────────────────────────────────────────────────────────

function ProgressRing({ percent, size = 120 }: { percent: number; size?: number }) {
    const r = (size - 16) / 2;
    const circ = 2 * Math.PI * r;
    const offset = circ - (percent / 100) * circ;
    return (
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ transform: "rotate(-90deg)" }}>
            <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#e9ecef" strokeWidth={8} />
            <motion.circle
                cx={size / 2} cy={size / 2} r={r}
                fill="none" stroke="#0d6efd" strokeWidth={8}
                strokeLinecap="round"
                strokeDasharray={circ}
                initial={{ strokeDashoffset: circ }}
                animate={{ strokeDashoffset: offset }}
                transition={{ duration: 1.2, ease: "easeOut" }}
            />
        </svg>
    );
}

// ─── Tabs ─────────────────────────────────────────────────────────────────────

type Tab = "today" | "progress" | "plan";

function TabBar({ active, onChange }: { active: Tab; onChange: (t: Tab) => void }) {
    const shouldReduceMotion = useReducedMotion();
    const tabs: { id: Tab; icon: string; label: string }[] = [
        { id: "today", icon: "bi-sun", label: "امروز" },
        { id: "progress", icon: "bi-bar-chart-line", label: "پیشرفت" },
        { id: "plan", icon: "bi-calendar3", label: "برنامه" },
    ];
    return (
        <div className="d-flex gap-2 mb-4 flex-wrap">
            {tabs.map((t) => (
                <motion.button
                    key={t.id}
                    className={`btn rounded-pill px-4 ${active === t.id ? "btn-primary" : "btn-outline-secondary"}`}
                    onClick={() => onChange(t.id)}
                    whileTap={shouldReduceMotion ? undefined : { scale: 0.95 }}
                >
                    <i className={`bi ${t.icon} me-2`} />
                    {t.label}
                </motion.button>
            ))}
        </div>
    );
}

// ─── Main content ─────────────────────────────────────────────────────────────

function AutomaticClassContent() {
    const { plan, todayData, progressData, isLoading, noSubscription, fetchMyPlan, fetchTodaySteps, fetchProgress, completeStep, reportDelay } = useAutomaticClass();
    const shouldReduceMotion = useReducedMotion();
    const [activeTab, setActiveTab] = useState<Tab>("today");
    const [hasFetched, setHasFetched] = useState(false);

    useEffect(() => {
        if (!hasFetched) {
            setHasFetched(true);
            fetchMyPlan();
            fetchTodaySteps();
        }
    }, [hasFetched]);

    useEffect(() => {
        if (activeTab === "progress" && !progressData) {
            fetchProgress();
        }
    }, [activeTab, progressData]);

    const handleComplete = async (id: string, reason?: string) => {
        const r = await completeStep(id, reason);
        if (r.success) {
            toast.success("مرحله تکمیل شد!");
            fetchTodaySteps();
            if (progressData) fetchProgress();
        } else {
            toast.error("خطا در تکمیل مرحله");
        }
    };

    const handleReport = async (id: string, reason: string) => {
        const r = await reportDelay(id, reason);
        if (r.success) {
            toast.info("دلیل تأخیر ثبت شد.");
        } else {
            toast.error("خطا در ثبت تأخیر");
        }
    };

    const NoPlan = () => (
        <motion.div
            className="text-center py-5"
            variants={staggerContainer}
            initial={shouldReduceMotion ? false : "hidden"}
            animate="show"
        >
            <motion.div variants={scaleIn}>
                <i className="bi bi-book display-1" />
            </motion.div>
            <motion.h4 className="mt-3 fw-bold" variants={fadeInUp}>هنوز برنامه‌ای ندارید</motion.h4>
            <motion.p className="mb-4" variants={fadeInUp}>
                برای دریافت برنامه حفظ شخصی، درخواست کلاس ثبت کنید.
            </motion.p>
            <motion.a
                href="/class-request/"
                className="btn btn-primary rounded-pill px-5"
                variants={fadeInUp}
            >
                <i className="bi bi-send me-2" />
                ثبت درخواست کلاس
            </motion.a>
        </motion.div>
    );

    const NoSubscription = () => (
        <motion.div
            className="text-center py-5"
            variants={staggerContainer}
            initial={shouldReduceMotion ? false : "hidden"}
            animate="show"
        >
            <motion.div variants={scaleIn}>
                <i className="bi bi-lock-fill display-1 text-warning" />
            </motion.div>
            <motion.h4 className="mt-3 fw-bold" variants={fadeInUp}>اشتراک فعال ندارید</motion.h4>
            <motion.p className="mb-2" variants={fadeInUp}>
                برای دسترسی به پنل کلاس خودکار، باید یک اشتراک با امکان کلاس آنلاین داشته باشید.
            </motion.p>
            <motion.p className="small mb-4" variants={fadeInUp}>
                بعد از خرید اشتراک، می‌توانید درخواست کلاس ثبت کنید و برنامه شخصی خود را دریافت کنید.
            </motion.p>
            <motion.a
                href="/subscriptions/"
                className="btn btn-warning rounded-pill px-5 fw-semibold"
                variants={fadeInUp}
            >
                <i className="bi bi-star me-2" />
                مشاهده پلن‌های اشتراک
            </motion.a>
        </motion.div>
    );

    return (
        <div className="col-xl-9">
            <div className="card bg-transparent border rounded-3">
                <div className="card-header bg-transparent border-bottom">
                    <div className="d-flex align-items-center justify-content-between flex-wrap gap-3">
                        <div className="d-flex align-items-center gap-2">
                            <i className="bi bi-journal-bookmark-fill text-primary fs-5" />
                            <h3 className="mb-0 fs-5 fw-bold">کلاس خودکار حفظ</h3>
                        </div>
                        {plan && (
                            <span className="small">
                                صفحات {plan.start_page}–{plan.end_page}
                            </span>
                        )}
                    </div>
                </div>

                <div className="card-body">
                    {isLoading && !plan && !todayData && !noSubscription ? (
                        <div className="text-center py-5">
                            <div className="spinner-border text-primary" role="status" />
                        </div>
                    ) : noSubscription ? (
                        <NoSubscription />
                    ) : !plan ? (
                        <NoPlan />
                    ) : (
                        <>
                            <TabBar active={activeTab} onChange={setActiveTab} />

                            <AnimatePresence mode="wait">
                                {/* ── Today ── */}
                                {activeTab === "today" && (
                                    <motion.div
                                        key="today"
                                        initial={shouldReduceMotion ? false : { opacity: 0, x: 20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, x: -20 }}
                                        transition={{ duration: 0.25 }}
                                    >
                                        {isLoading && !todayData ? (
                                            <div className="text-center py-5">
                                                <div className="spinner-border text-primary" role="status" />
                                            </div>
                                        ) : todayData ? (
                                            <>
                                                {todayData.has_delayed && (
                                                    <div className="mb-4">
                                                        <div className="d-flex align-items-center gap-2 mb-3">
                                                            <i className="bi bi-exclamation-triangle-fill text-danger" />
                                                            <h6 className="mb-0 text-danger fw-bold">
                                                                مراحل عقب‌افتاده ({todayData.delayed_steps.length})
                                                            </h6>
                                                        </div>
                                                        <div className="alert alert-danger rounded-3 py-2 px-3 small mb-3">
                                                            <i className="bi bi-info-circle me-1" />
                                                            ابتدا مراحل عقب‌افتاده را تکمیل کنید، سپس وظایف امروز را شروع کنید.
                                                        </div>
                                                        {todayData.delayed_steps.map((step, i) => (
                                                            <StepCard key={step.id} step={step} onComplete={handleComplete} onReport={handleReport} animDelay={i * 0.08} />
                                                        ))}
                                                    </div>
                                                )}

                                                <div className="mb-4">
                                                    <div className="d-flex align-items-center gap-2 mb-3">
                                                        <i className="bi bi-sun-fill text-warning" />
                                                        <h6 className="mb-0 fw-bold">
                                                            وظایف امروز ({todayData.today_steps.length})
                                                        </h6>
                                                    </div>
                                                    {todayData.today_steps.length === 0 ? (
                                                        <div className="text-center py-4 bg-light rounded-3">
                                                            <i className="bi bi-check-circle-fill text-success fs-3 mb-2 d-block" />
                                                            <p className="mb-0">همه وظایف امروز را تکمیل کردید!</p>
                                                        </div>
                                                    ) : (
                                                        <>
                                                            {todayData.today_steps.map((step, i) => (
                                                                <StepCard key={step.id} step={step} onComplete={handleComplete} onReport={handleReport} animDelay={i * 0.08} />
                                                            ))}
                                                        </>
                                                    )}
                                                </div>

                                                {todayData.upcoming_steps.length > 0 && (
                                                    <div>
                                                        <div className="d-flex align-items-center gap-2 mb-3">
                                                            <i className="bi bi-arrow-right-circle" />
                                                            <h6 className="mb-0 fw-semibold">جلسات بعدی</h6>
                                                        </div>
                                                        {todayData.upcoming_steps.map((step) => (
                                                            <div key={step.id} className="d-flex align-items-center gap-3 p-3 bg-light rounded-3 mb-2 opacity-75">
                                                                <i className={`bi ${stepTypeIcon(step.step_type)} text-${stepTypeColor(step.step_type)}`} />
                                                                <div className="flex-grow-1">
                                                                    <span className="fw-semibold small">{stepTypeLabel(step.step_type)}</span>
                                                                    <span className="small ms-2">
                                                                        ص {step.page_start === step.page_end ? step.page_start : `${step.page_start}–${step.page_end}`}
                                                                    </span>
                                                                </div>
                                                                <span className="small">{formatDate(step.scheduled_date)}</span>
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
                                            </>
                                        ) : null}
                                    </motion.div>
                                )}

                                {/* ── Progress ── */}
                                {activeTab === "progress" && (
                                    <motion.div
                                        key="progress"
                                        initial={shouldReduceMotion ? false : { opacity: 0, x: 20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, x: -20 }}
                                        transition={{ duration: 0.25 }}
                                    >
                                        {isLoading && !progressData ? (
                                            <div className="text-center py-5">
                                                <div className="spinner-border text-primary" role="status" />
                                            </div>
                                        ) : progressData ? (
                                            <>
                                                {/* Progress summary */}
                                                <motion.div
                                                    className="row g-4 mb-5 align-items-center"
                                                    variants={staggerContainer}
                                                    initial={shouldReduceMotion ? false : "hidden"}
                                                    animate="show"
                                                >
                                                    <motion.div className="col-auto mx-auto" variants={scaleIn}>
                                                        <div className="position-relative d-inline-flex align-items-center justify-content-center">
                                                            <ProgressRing percent={progressData.stats.progress_percent} size={140} />
                                                            <div className="position-absolute text-center">
                                                                <div className="fs-4 fw-bold text-primary">{progressData.stats.progress_percent}%</div>
                                                                <div className="small">پیشرفت</div>
                                                            </div>
                                                        </div>
                                                    </motion.div>
                                                    <div className="col">
                                                        <div className="row g-3">
                                                            {[
                                                                { label: "تکمیل شده", value: progressData.stats.completed, color: "success", icon: "bi-check-circle-fill" },
                                                                { label: "در انتظار", value: progressData.stats.pending, color: "primary", icon: "bi-clock-fill" },
                                                                { label: "تأخیر دار", value: progressData.stats.delayed, color: "danger", icon: "bi-exclamation-circle-fill" },
                                                                { label: "کل مراحل", value: progressData.stats.total, color: "secondary", icon: "bi-list-check" },
                                                            ].map((stat, i) => (
                                                                <motion.div key={i} className="col-6" variants={fadeInUp}>
                                                                    <div className={`card border-0 bg-${stat.color} bg-opacity-10 rounded-3 p-3 text-center`}>
                                                                        <i className={`bi ${stat.icon} text-${stat.color} mb-1`} />
                                                                        <div className={`fs-4 fw-bold text-${stat.color}`}>{stat.value}</div>
                                                                        <div className="small">{stat.label}</div>
                                                                    </div>
                                                                </motion.div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                </motion.div>

                                                {/* Steps timeline */}
                                                <h6 className="fw-bold mb-3">تمام مراحل</h6>
                                                <div style={{ maxHeight: 420, overflowY: "auto" }} className="pe-1">
                                                    {progressData.steps.map((step, i) => (
                                                        <div
                                                            key={step.id}
                                                            className={`d-flex align-items-center gap-3 p-3 rounded-3 mb-2 border-start border-3 border-${statusColor(step.status)} ${step.status === "completed" ? "bg-success bg-opacity-5" : step.status === "delayed" ? "bg-danger bg-opacity-5" : "bg-light"}`}
                                                        >
                                                            <div
                                                                className={`bg-${stepTypeColor(step.step_type)} bg-opacity-10 text-${stepTypeColor(step.step_type)} rounded-circle d-flex align-items-center justify-content-center flex-shrink-0`}
                                                                style={{ width: 36, height: 36, fontSize: 14 }}
                                                            >
                                                                <i className={`bi ${stepTypeIcon(step.step_type)}`} />
                                                            </div>
                                                            <div className="flex-grow-1">
                                                                <div className="fw-semibold small">{stepTypeLabel(step.step_type)}</div>
                                                                <div className="" style={{ fontSize: "0.75rem" }}>
                                                                    ص {step.page_start === step.page_end ? step.page_start : `${step.page_start}–${step.page_end}`}
                                                                    {step.sub_part !== "full" && <span className="ms-1">({step.sub_part === "first_half" ? "نیمه اول" : "نیمه دوم"})</span>}
                                                                </div>
                                                            </div>
                                                            <div className="text-end">
                                                                {statusLabel(step.status) && (
                                                                    <span className={`badge bg-${statusColor(step.status)} bg-opacity-10 text-${statusColor(step.status)} rounded-pill d-block mb-1`}>
                                                                        {statusLabel(step.status)}
                                                                    </span>
                                                                )}
                                                                <div className="" style={{ fontSize: "0.7rem" }}>
                                                                    {formatDate(step.scheduled_date)}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </>
                                        ) : null}
                                    </motion.div>
                                )}

                                {/* ── Plan ── */}
                                {activeTab === "plan" && (
                                    <motion.div
                                        key="plan"
                                        initial={shouldReduceMotion ? false : { opacity: 0, x: 20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, x: -20 }}
                                        transition={{ duration: 0.25 }}
                                    >
                                        <motion.div
                                            className="row g-4"
                                            variants={staggerContainer}
                                            initial={shouldReduceMotion ? false : "hidden"}
                                            animate="show"
                                        >
                                            {[
                                                { icon: "bi-book-half", color: "primary", label: "محدوده حفظ", value: `صفحات ${plan.start_page} تا ${plan.end_page}` },
                                                { icon: "bi-calendar-check", color: "info", label: "تاریخ شروع", value: formatDate(plan.start_date) },
                                                { icon: "bi-flag-fill", color: "success", label: "هدف پایان", value: formatDate(plan.time_to_finish) },
                                                { icon: "bi-clock-history", color: "warning", label: "تناوب مطالعه", value: plan.time_freq_display },
                                                { icon: "bi-file-earmark-text", color: "secondary", label: "حجم هر جلسه", value: plan.reading_freq_display },
                                                { icon: "bi-arrow-clockwise", color: "primary", label: "مرور هر چند صفحه", value: `هر ${plan.review_freq} صفحه` },
                                                { icon: "bi-calendar-week", color: "info", label: "روزهای مطالعه", value: plan.user_day_availability_display },
                                                { icon: "bi-alarm", color: "warning", label: "بازه زمانی", value: plan.user_time_availability_display },
                                            ].map((item, i) => (
                                                <motion.div key={i} className="col-sm-6" variants={fadeInUp}>
                                                    <div className={`card border-0 bg-${item.color} bg-opacity-10 rounded-3 p-3 h-100`}>
                                                        <div className="d-flex align-items-center gap-2 mb-1">
                                                            <i className={`bi ${item.icon} text-${item.color}`} />
                                                            <span className="small">{item.label}</span>
                                                        </div>
                                                        <div className="fw-bold">{item.value}</div>
                                                    </div>
                                                </motion.div>
                                            ))}

                                            {/* Extra review range — only shown when configured */}
                                            {plan.extra_review_pages_per_session > 0 && plan.extra_review_start_page != null && plan.extra_review_end_page != null && (
                                                <motion.div className="col-12" variants={fadeInUp}>
                                                    <div className="card border-0 bg-info bg-opacity-10 rounded-3 p-3">
                                                        <div className="d-flex align-items-center gap-2 mb-2">
                                                            <i className="bi bi-arrow-counterclockwise text-info" />
                                                            <span className="small fw-semibold">بازه مرور اضافی</span>
                                                        </div>
                                                        <div className="fw-bold">
                                                            صفحات {plan.extra_review_start_page} تا {plan.extra_review_end_page}
                                                            <span className="fw-normal small ms-2">
                                                                ({plan.extra_review_pages_per_session} صفحه در هر جلسه، حلقوی)
                                                            </span>
                                                        </div>
                                                    </div>
                                                </motion.div>
                                            )}

                                            {plan.teacher_display && (
                                                <motion.div className="col-12" variants={fadeInUp}>
                                                    <div className="card border-0 bg-light rounded-3 p-3">
                                                        <div className="d-flex align-items-center gap-3">
                                                            <div className="bg-primary bg-opacity-10 text-primary rounded-circle d-flex align-items-center justify-content-center" style={{ width: 48, height: 48 }}>
                                                                <i className="bi bi-person-badge-fill fs-5" />
                                                            </div>
                                                            <div>
                                                                <div className="small">استاد شما</div>
                                                                <div className="fw-bold">{plan.teacher_display.username}</div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </motion.div>
                                            )}

                                            {/* Online call sessions — read-only view for student */}
                                            {plan.call_sessions && plan.call_sessions.length > 0 && (
                                                <motion.div className="col-12" variants={fadeInUp}>
                                                    <div className="card border-0 bg-light rounded-3 p-3">
                                                        <div className="d-flex align-items-center gap-2 mb-3">
                                                            <i className="bi bi-headset text-primary" />
                                                            <span className="fw-semibold small">جلسات تماس آنلاین</span>
                                                            <span className="small ms-auto">
                                                                {plan.call_sessions.filter((s: UserCallSession) => s.status === "completed").length}/{plan.call_sessions.length} برگزار شده
                                                            </span>
                                                        </div>
                                                        <div className="d-flex flex-wrap gap-2">
                                                            {plan.call_sessions.map((session: UserCallSession) => (
                                                                <div
                                                                    key={session.id}
                                                                    className={`d-flex align-items-center gap-2 rounded-3 px-3 py-2 small fw-semibold ${
                                                                        session.status === "completed"
                                                                            ? "bg-success bg-opacity-10 text-success"
                                                                            : session.status === "no_answer"
                                                                            ? "bg-warning bg-opacity-10 text-warning"
                                                                            : "bg-white border"
                                                                    }`}
                                                                >
                                                                    <i className={`bi ${session.status === "completed" ? "bi-check-circle-fill" : session.status === "no_answer" ? "bi-telephone-x-fill" : "bi-circle"}`} />
                                                                    جلسه {session.session_number}
                                                                    {session.status === "completed" && session.completed_at && (
                                                                        <span className="fw-normal opacity-75" style={{ fontSize: "0.7rem" }}>
                                                                            {new Intl.DateTimeFormat("fa-IR", { month: "short", day: "numeric" }).format(new Date(session.completed_at))}
                                                                        </span>
                                                                    )}
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                </motion.div>
                                            )}
                                        </motion.div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}

export default function AutomaticClassPage() {
    return <DashboardBase Content={<AutomaticClassContent />} />;
}
