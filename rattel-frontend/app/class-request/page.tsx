"use client";

import { useState, useEffect } from "react";
import { motion, useReducedMotion, AnimatePresence } from "framer-motion";
import { useAuth } from "@/src/core/hooks/useAuth";
import { useAutomaticClass } from "@/src/core/hooks/useAutomaticClass";
import { toast } from "react-toastify";
import { fadeInUp, staggerContainer, scaleIn } from "@/src/core/motionVariants";

const vp = { once: true };

const STATUS_CONFIG: Record<string, { color: string; icon: string; label: string; description: string }> = {
    pending: {
        color: "warning",
        icon: "bi-hourglass-split",
        label: "در انتظار بررسی",
        description: "درخواست شما دریافت شد. استاد به زودی با شما تماس می‌گیرد.",
    },
    contacted: {
        color: "info",
        icon: "bi-telephone-fill",
        label: "تماس گرفته شد",
        description: "استاد با شما تماس گرفته است. منتظر تنظیم برنامه باشید.",
    },
    plan_created: {
        color: "success",
        icon: "bi-check-circle-fill",
        label: "برنامه ایجاد شد",
        description: "برنامه حفظ شما آماده است! از داشبورد خود آن را مشاهده کنید.",
    },
    rejected: {
        color: "danger",
        icon: "bi-x-circle-fill",
        label: "رد شده",
        description: "متأسفانه درخواست شما تأیید نشد. برای اطلاعات بیشتر تیکت ثبت کنید.",
    },
};

const HOW_IT_WORKS = [
    {
        step: "۱",
        icon: "bi-pencil-square",
        title: "ثبت درخواست",
        desc: "فرم درخواست را پر کنید. فقط به یک اکانت فعال نیاز دارید.",
        color: "primary",
    },
    {
        step: "۲",
        icon: "bi-telephone",
        title: "تماس استاد",
        desc: "استاد با شماره‌ای که ثبت کرده‌اید تماس می‌گیرد و جزئیات را بررسی می‌کند.",
        color: "info",
    },
    {
        step: "۳",
        icon: "bi-calendar2-check",
        title: "تنظیم برنامه",
        desc: "یک برنامه روزانه شخصی‌سازی شده برای شما طراحی می‌شود.",
        color: "warning",
    },
    {
        step: "۴",
        icon: "bi-graph-up-arrow",
        title: "پیشرفت روزانه",
        desc: "هر روز وظایف خود را از داشبورد ببینید، تکمیل کنید و پیشرفت‌تان را دنبال کنید.",
        color: "success",
    },
];

function StatusCard({ status }: { status: string }) {
    const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
    return (
        <motion.div
            className={`alert alert-${cfg.color} border-0 rounded-4 p-4`}
            variants={scaleIn}
            initial="hidden"
            animate="show"
        >
            <div className="d-flex align-items-center gap-3">
                <i className={`bi ${cfg.icon} fs-2`} />
                <div>
                    <h5 className="mb-1 fw-bold">{cfg.label}</h5>
                    <p className="mb-0 small">{cfg.description}</p>
                </div>
                {status === "plan_created" && (
                    <a href="/dashboard/automatic-class/" className="btn btn-success ms-auto">
                        مشاهده برنامه
                        <i className="bi bi-arrow-left ms-2" />
                    </a>
                )}
            </div>
        </motion.div>
    );
}

export default function ClassRequestPage() {
    const { user, isAuthenticated, isLoading: authLoading } = useAuth();
    const { classRequest, isLoading, fetchClassRequest, submitClassRequest } = useAutomaticClass();
    const shouldReduceMotion = useReducedMotion();
    const initial = shouldReduceMotion ? false : "hidden";

    const [notes, setNotes] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [hasFetched, setHasFetched] = useState(false);

    useEffect(() => {
        if (isAuthenticated && !hasFetched) {
            setHasFetched(true);
            fetchClassRequest();
        }
    }, [isAuthenticated, hasFetched]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (submitting) return;
        setSubmitting(true);
        const result = await submitClassRequest(notes);
        if (result.success) {
            toast.success(result.message || "درخواست شما با موفقیت ثبت شد");
            setNotes("");
        } else if (result.error === -1) {
            toast.warning("شما قبلاً یک درخواست فعال ثبت کرده‌اید.");
        } else {
            toast.error(result.message || "خطا در ثبت درخواست");
        }
        setSubmitting(false);
    };

    const canRequest = !classRequest || classRequest.status === "rejected" || classRequest.plan_is_cancelled;

    return (
        <main>
            {/* ── Hero ── */}
            <section
                className="py-5 py-lg-7"
                style={{
                    background: "linear-gradient(135deg, #0d6efd15 0%, #6610f215 50%, #0d6efd08 100%)",
                }}
            >
                <div className="container">
                    <motion.div
                        className="row justify-content-center text-center"
                        variants={staggerContainer}
                        initial={initial}
                        animate="show"
                    >
                        <div className="col-lg-8">
                            <motion.span
                                className="badge bg-primary bg-opacity-10 text-primary border border-primary rounded-pill px-3 py-2 mb-3 d-inline-block"
                                variants={fadeInUp}
                            >
                                <i className="bi bi-stars me-2" />
                                کلاس هوشمند حفظ قرآن
                            </motion.span>
                            <motion.h1 className="display-5 fw-bold mb-3" variants={fadeInUp}>
                                برنامه حفظ شخصی‌سازی شده
                            </motion.h1>
                            <motion.p className="lead mb-4" variants={fadeInUp}>
                                با ثبت درخواست، استاد با شما تماس می‌گیرد و یک برنامه روزانه متناسب با
                                توانایی‌ها و زمان‌بندی شما طراحی می‌کند.
                            </motion.p>
                            {!isAuthenticated && !authLoading && (
                                <motion.a
                                    href="/auth/login/?next=/class-request/"
                                    className="btn btn-primary btn-lg rounded-pill px-5"
                                    variants={fadeInUp}
                                >
                                    <i className="bi bi-box-arrow-in-left me-2" />
                                    ورود به حساب کاربری
                                </motion.a>
                            )}
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* ── How it works ── */}
            <section className="py-5">
                <div className="container">
                    <motion.div
                        className="text-center mb-5"
                        variants={fadeInUp}
                        initial={initial}
                        whileInView="show"
                        viewport={vp}
                    >
                        <h2 className="fs-3 fw-bold">چطور کار می‌کند؟</h2>
                        <p>در چهار مرحله ساده، برنامه حفظ خود را شروع کنید</p>
                    </motion.div>

                    <motion.div
                        className="row g-4"
                        variants={staggerContainer}
                        initial={initial}
                        whileInView="show"
                        viewport={vp}
                    >
                        {HOW_IT_WORKS.map((item, i) => (
                            <motion.div key={i} className="col-sm-6 col-xl-3" variants={fadeInUp}>
                                <motion.div
                                    className="card border-0 shadow-sm h-100 rounded-4 text-center p-4"
                                    whileHover={shouldReduceMotion ? undefined : { y: -6, transition: { duration: 0.2 } }}
                                >
                                    <div
                                        className={`icon-xl bg-${item.color} bg-opacity-10 text-${item.color} rounded-circle mx-auto mb-3 d-flex align-items-center justify-content-center`}
                                        style={{ width: 64, height: 64 }}
                                    >
                                        <i className={`bi ${item.icon} fs-4`} />
                                    </div>
                                    <span
                                        className={`badge bg-${item.color} bg-opacity-10 text-${item.color} rounded-pill mb-2`}
                                        style={{ fontSize: "0.7rem" }}
                                    >
                                        مرحله {item.step}
                                    </span>
                                    <h5 className="fw-bold mb-2">{item.title}</h5>
                                    <p className="small mb-0">{item.desc}</p>
                                </motion.div>
                            </motion.div>
                        ))}
                    </motion.div>
                </div>
            </section>

            {/* ── Request form / status ── */}
            <section className="py-5 pb-7">
                <div className="container">
                    <div className="row justify-content-center">
                        <div className="col-lg-7">
                            <AnimatePresence mode="wait">
                                {authLoading || isLoading ? (
                                    <motion.div
                                        key="skeleton"
                                        className="card border-0 shadow-sm rounded-4 p-5 text-center"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        exit={{ opacity: 0 }}
                                    >
                                        <div className="spinner-border text-primary mx-auto mb-3" role="status" />
                                        <p className="mb-0">در حال بارگذاری...</p>
                                    </motion.div>
                                ) : !isAuthenticated ? (
                                    <motion.div
                                        key="login-cta"
                                        className="card border-0 shadow-sm rounded-4 p-5 text-center"
                                        variants={scaleIn}
                                        initial="hidden"
                                        animate="show"
                                    >
                                        <i className="bi bi-lock-fill fs-1 mb-3" />
                                        <h4 className="fw-bold mb-2">برای ثبت درخواست وارد شوید</h4>
                                        <p className="mb-4">
                                            فقط کاربران ثبت‌نام شده می‌توانند درخواست کلاس ثبت کنند.
                                        </p>
                                        <a href="/auth/login/?next=/class-request/" className="btn btn-primary btn-lg rounded-pill px-5">
                                            <i className="bi bi-box-arrow-in-left me-2" />
                                            ورود / ثبت نام
                                        </a>
                                    </motion.div>
                                ) : classRequest && !canRequest ? (
                                    <motion.div
                                        key="status"
                                        variants={scaleIn}
                                        initial="hidden"
                                        animate="show"
                                        className="card border-0 shadow-sm rounded-4 p-4"
                                    >
                                        <div className="d-flex align-items-center gap-2 mb-4">
                                            <i className="bi bi-person-lines-fill text-primary fs-5" />
                                            <h4 className="mb-0 fw-bold">وضعیت درخواست شما</h4>
                                        </div>
                                        <StatusCard status={classRequest.status} />
                                        <div className="mt-3 small text-center">
                                            ثبت شده در:{" "}
                                            {new Intl.DateTimeFormat("fa-IR", {
                                                year: "numeric",
                                                month: "long",
                                                day: "numeric",
                                            }).format(new Date(classRequest.created_at))}
                                        </div>
                                    </motion.div>
                                ) : (
                                    <motion.div
                                        key="form"
                                        className="card border-0 shadow-sm rounded-4 p-4 p-sm-5"
                                        variants={scaleIn}
                                        initial="hidden"
                                        animate="show"
                                    >
                                        <div className="d-flex align-items-center gap-2 mb-4">
                                            <i className="bi bi-send-fill text-primary fs-5" />
                                            <h4 className="mb-0 fw-bold">ثبت درخواست کلاس</h4>
                                        </div>

                                        {classRequest?.status === "rejected" && (
                                            <div className="alert alert-warning rounded-3 small mb-4">
                                                <i className="bi bi-exclamation-triangle me-2" />
                                                درخواست قبلی شما رد شده است. می‌توانید درخواست جدید ثبت کنید.
                                            </div>
                                        )}
                                        {classRequest?.plan_is_cancelled && (
                                            <div className="alert alert-warning rounded-3 small mb-4">
                                                <i className="bi bi-x-circle me-2" />
                                                برنامه قبلی شما لغو شده است. می‌توانید درخواست جدید ثبت کنید.
                                            </div>
                                        )}

                                        <div className="d-flex align-items-center gap-3 p-3 bg-light rounded-3 mb-4">
                                            <img
                                                src={user?.profile_picture || "/assets/images/auth/default_profile.png"}
                                                alt={user?.name}
                                                className="rounded-circle border"
                                                style={{ width: 48, height: 48, objectFit: "cover" }}
                                            />
                                            <div>
                                                <div className="fw-semibold">{user?.name}</div>
                                                <div className="small">{user?.phone}</div>
                                            </div>
                                        </div>

                                        <form onSubmit={handleSubmit}>
                                            <div className="mb-4">
                                                <label className="form-label fw-semibold">
                                                    توضیحات (اختیاری)
                                                </label>
                                                <textarea
                                                    className="form-control rounded-3"
                                                    rows={4}
                                                    value={notes}
                                                    onChange={(e) => setNotes(e.target.value)}
                                                    placeholder="اگر نکته‌ای دارید (سطح حفظ، اهداف، محدودیت زمانی) اینجا بنویسید..."
                                                    maxLength={500}
                                                />
                                                <div className="small text-end mt-1">
                                                    {notes.length} / ۵۰۰
                                                </div>
                                            </div>

                                            <div className="alert alert-info rounded-3 small mb-4">
                                                <i className="bi bi-info-circle me-2" />
                                                شماره تماس{" "}
                                                <strong>{user?.phone}</strong> برای تماس استاد استفاده
                                                می‌شود. مطمئن شوید در دسترس هستید.
                                            </div>

                                            <motion.button
                                                type="submit"
                                                className="btn btn-primary btn-lg w-100 rounded-3"
                                                disabled={submitting}
                                                whileTap={shouldReduceMotion ? undefined : { scale: 0.97 }}
                                            >
                                                {submitting ? (
                                                    <>
                                                        <span className="spinner-border spinner-border-sm me-2" />
                                                        در حال ارسال...
                                                    </>
                                                ) : (
                                                    <>
                                                        <i className="bi bi-send me-2" />
                                                        ثبت درخواست
                                                    </>
                                                )}
                                            </motion.button>
                                        </form>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    </div>
                </div>
            </section>
        </main>
    );
}
