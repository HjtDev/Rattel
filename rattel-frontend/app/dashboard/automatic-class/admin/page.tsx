"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import DashboardBase from "@/src/components/dashboard/DashboardBase";
import { useAdminClassPanel } from "@/src/core/hooks/useAdminClassPanel";
import { useAuth } from "@/src/core/hooks/useAuth";
import { toast } from "react-toastify";
import { fadeInUp, staggerContainer, scaleIn } from "@/src/core/motionVariants";
import type { AdminClassRequest, AdminPlan, CallSessionStatus, CreatePlanPayload, OnlineCallSession } from "@/src/core/automatic-class/automaticClassManager";
import DatePicker from "react-multi-date-picker";
import persian from "react-date-object/calendars/persian";
import persian_fa from "react-date-object/locales/persian_fa";

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatDate(d: string | null | undefined): string {
    if (!d) return "—";
    return new Intl.DateTimeFormat("fa-IR", { year: "numeric", month: "long", day: "numeric" }).format(new Date(d));
}

function formatDateTime(d: string): string {
    return new Intl.DateTimeFormat("fa-IR", { year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }).format(new Date(d));
}

const REQUEST_STATUS_MAP: Record<string, { color: string; label: string }> = {
    pending: { color: "warning", label: "در انتظار" },
    contacted: { color: "info", label: "تماس گرفته شد" },
    plan_created: { color: "success", label: "برنامه ایجاد شد" },
    rejected: { color: "danger", label: "رد شده" },
};

const PLAN_STATUS_MAP: Record<string, { color: string; label: string }> = {
    draft: { color: "secondary", label: "پیش‌نویس" },
    active: { color: "success", label: "فعال" },
    completed: { color: "primary", label: "تمام شده" },
    cancelled: { color: "danger", label: "لغو شده" },
};

function stepTypeColor(type: string): string {
    if (type === "memorize") return "primary";
    if (type === "review") return "warning";
    if (type === "extra_review") return "info";
    return "success";
}

function stepTypeIcon(type: string): string {
    if (type === "memorize") return "bi-book-fill";
    if (type === "review") return "bi-arrow-repeat";
    if (type === "extra_review") return "bi-arrow-counterclockwise";
    return "bi-trophy-fill";
}

function stepStatusColor(status: string): string {
    if (status === "completed") return "success";
    if (status === "delayed") return "danger";
    if (status === "skipped") return "secondary";
    return "primary";
}

function parseGregorianToDate(s: string): Date | null {
    if (!s) return null;
    const [y, m, d] = s.split("-").map(Number);
    return new Date(y, m - 1, d);
}

function dateObjToGregorian(dateObj: any): string {
    const d: Date = dateObj.toDate();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

// ─── Create Plan Modal ────────────────────────────────────────────────────────

const EMPTY_PLAN: CreatePlanPayload = {
    request: null,
    user: "",
    teacher: null,
    start_page: 1,
    end_page: 10,
    start_date: "",
    time_to_finish: "",
    time_freq: "per_day",
    reading_freq: "full_page",
    review_freq: 3,
    user_day_availability: "odd_days",
    user_time_availability: "morning",
    status: "draft",
    admin_notes: "",
    extra_review_start_page: null,
    extra_review_end_page: null,
    extra_review_pages_per_session: 0,
};

function CreatePlanModal({
    onClose,
    onCreate,
    prefillRequest,
}: {
    onClose: () => void;
    onCreate: (p: CreatePlanPayload) => Promise<void>;
    prefillRequest?: AdminClassRequest | null;
}) {
    const shouldReduceMotion = useReducedMotion();
    const [form, setForm] = useState<CreatePlanPayload>({
        ...EMPTY_PLAN,
        user: prefillRequest?.user ?? "",
        request: prefillRequest?.id ?? null,
    });
    const [saving, setSaving] = useState(false);

    const set = (key: keyof CreatePlanPayload, value: any) =>
        setForm((prev) => ({ ...prev, [key]: value }));

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (saving) return;
        if (!form.user || !form.start_date || !form.time_to_finish) {
            toast.warning("لطفاً تمام فیلدهای اجباری را پر کنید");
            return;
        }
        setSaving(true);
        await onCreate(form);
        setSaving(false);
    };

    return (
        <motion.div
            className="modal show d-block"
            tabIndex={-1}
            style={{ backgroundColor: "rgba(0,0,0,0.6)" }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
        >
            <motion.div
                className="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable"
                initial={shouldReduceMotion ? false : { y: 40, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: 40, opacity: 0 }}
                transition={{ duration: 0.3 }}
            >
                <div className="modal-content rounded-4 border-0 shadow-lg">
                    <div className="modal-header border-0 pb-0 px-4 pt-4">
                        <h5 className="modal-title fw-bold">
                            <i className="bi bi-plus-circle-fill text-primary me-2" />
                            ایجاد برنامه جدید
                        </h5>
                        <button type="button" className="btn-close" onClick={onClose} />
                    </div>
                    <div className="modal-body px-4">
                        {prefillRequest && (
                            <div className="alert alert-info rounded-3 small mb-4">
                                <i className="bi bi-person-fill me-2" />
                                کاربر: <strong>{prefillRequest.user_display.username}</strong>
                                {prefillRequest.user_display.phone && (
                                    <span className="ms-2 opacity-75">({prefillRequest.user_display.phone})</span>
                                )}
                            </div>
                        )}
                        <form onSubmit={handleSubmit}>
                            <div className="row g-3">
                                {!prefillRequest && (
                                    <div className="col-12">
                                        <label className="form-label fw-semibold">شناسه کاربر *</label>
                                        <input
                                            type="number"
                                            className="form-control rounded-3"
                                            value={form.user as string}
                                            onChange={(e) => set("user", e.target.value)}
                                            placeholder="ID کاربر را وارد کنید"
                                            required
                                        />
                                    </div>
                                )}
                                <div className="col-sm-6">
                                    <label className="form-label fw-semibold">صفحه شروع *</label>
                                    <input
                                        type="number"
                                        className="form-control rounded-3"
                                        min={1}
                                        value={form.start_page}
                                        onChange={(e) => set("start_page", +e.target.value)}
                                        required
                                    />
                                </div>
                                <div className="col-sm-6">
                                    <label className="form-label fw-semibold">صفحه پایان *</label>
                                    <input
                                        type="number"
                                        className="form-control rounded-3"
                                        min={form.start_page + 1}
                                        value={form.end_page}
                                        onChange={(e) => set("end_page", +e.target.value)}
                                        required
                                    />
                                </div>
                                <div className="col-sm-6">
                                    <label className="form-label fw-semibold">تاریخ شروع *</label>
                                    <DatePicker
                                        value={parseGregorianToDate(form.start_date)}
                                        onChange={(dateObj: any) => set("start_date", dateObj ? dateObjToGregorian(dateObj) : "")}
                                        calendar={persian}
                                        locale={persian_fa}
                                        format="YYYY/MM/DD"
                                        inputClass="form-control rounded-3"
                                        containerStyle={{ width: "100%" }}
                                        portal
                                        zIndex={1200}
                                    />
                                </div>
                                <div className="col-sm-6">
                                    <label className="form-label fw-semibold">هدف پایان *</label>
                                    <DatePicker
                                        value={parseGregorianToDate(form.time_to_finish)}
                                        onChange={(dateObj: any) => set("time_to_finish", dateObj ? dateObjToGregorian(dateObj) : "")}
                                        calendar={persian}
                                        locale={persian_fa}
                                        format="YYYY/MM/DD"
                                        inputClass="form-control rounded-3"
                                        containerStyle={{ width: "100%" }}
                                        portal
                                        zIndex={1200}
                                    />
                                </div>
                                <div className="col-sm-6">
                                    <label className="form-label fw-semibold">تناوب مطالعه</label>
                                    <select className="form-select rounded-3" value={form.time_freq} onChange={(e) => set("time_freq", e.target.value)}>
                                        <option value="per_day">روزانه</option>
                                        <option value="per_two_days">یک روز در میان</option>
                                    </select>
                                </div>
                                <div className="col-sm-6">
                                    <label className="form-label fw-semibold">حجم هر جلسه</label>
                                    <select className="form-select rounded-3" value={form.reading_freq} onChange={(e) => set("reading_freq", e.target.value)}>
                                        <option value="full_page">یک صفحه کامل</option>
                                        <option value="half_page">نیم صفحه</option>
                                    </select>
                                </div>
                                <div className="col-sm-6">
                                    <label className="form-label fw-semibold">مرور هر چند صفحه</label>
                                    <input
                                        type="number"
                                        className="form-control rounded-3"
                                        min={1}
                                        value={form.review_freq}
                                        onChange={(e) => set("review_freq", +e.target.value)}
                                    />
                                </div>
                                <div className="col-sm-6">
                                    <label className="form-label fw-semibold">روزهای فعال</label>
                                    <select className="form-select rounded-3" value={form.user_day_availability} onChange={(e) => set("user_day_availability", e.target.value)}>
                                        <option value="odd_days">روزهای فرد (شنبه، سه‌شنبه، پنجشنبه)</option>
                                        <option value="even_days">روزهای زوج (جمعه، دوشنبه، چهارشنبه)</option>
                                    </select>
                                </div>
                                <div className="col-sm-6">
                                    <label className="form-label fw-semibold">بازه زمانی مطالعه</label>
                                    <select className="form-select rounded-3" value={form.user_time_availability} onChange={(e) => set("user_time_availability", e.target.value)}>
                                        <option value="morning">۹ صبح تا ۱۱ صبح</option>
                                        <option value="afternoon">۳ بعدازظهر تا ۵ بعدازظهر</option>
                                        <option value="evening">۷ شب تا ۹ شب</option>
                                    </select>
                                </div>
                                <div className="col-sm-6">
                                    <label className="form-label fw-semibold">وضعیت اولیه</label>
                                    <select className="form-select rounded-3" value={form.status} onChange={(e) => set("status", e.target.value)}>
                                        <option value="draft">پیش‌نویس</option>
                                        <option value="active">فعال (مراحل تولید می‌شوند)</option>
                                    </select>
                                </div>
                                <div className="col-12">
                                    <label className="form-label fw-semibold">یادداشت مدیر</label>
                                    <textarea
                                        className="form-control rounded-3"
                                        rows={2}
                                        value={form.admin_notes}
                                        onChange={(e) => set("admin_notes", e.target.value)}
                                        placeholder="یادداشت داخلی (برای کاربر نمایش داده نمی‌شود)..."
                                    />
                                </div>

                                {/* Extra review range — optional */}
                                <div className="col-12">
                                    <div className="border rounded-3 p-3 bg-light">
                                        <div className="fw-semibold small mb-2 text-secondary">
                                            <i className="bi bi-arrow-repeat me-2" />
                                            بازه مرور اضافی (اختیاری)
                                        </div>
                                        <div className="row g-2">
                                            <div className="col-sm-4">
                                                <label className="form-label small">صفحه شروع</label>
                                                <input
                                                    type="number"
                                                    className="form-control form-control-sm rounded-3"
                                                    min={1}
                                                    value={form.extra_review_start_page ?? ""}
                                                    onChange={(e) => set("extra_review_start_page", e.target.value ? +e.target.value : null)}
                                                    placeholder="مثلاً ۱"
                                                />
                                            </div>
                                            <div className="col-sm-4">
                                                <label className="form-label small">صفحه پایان</label>
                                                <input
                                                    type="number"
                                                    className="form-control form-control-sm rounded-3"
                                                    min={form.extra_review_start_page ?? 1}
                                                    value={form.extra_review_end_page ?? ""}
                                                    onChange={(e) => set("extra_review_end_page", e.target.value ? +e.target.value : null)}
                                                    placeholder="مثلاً ۵۰"
                                                />
                                            </div>
                                            <div className="col-sm-4">
                                                <label className="form-label small">حجم مرور(صفحه)</label>
                                                <input
                                                    type="number"
                                                    className="form-control form-control-sm rounded-3"
                                                    min={0}
                                                    value={form.extra_review_pages_per_session ?? 0}
                                                    onChange={(e) => set("extra_review_pages_per_session", +e.target.value)}
                                                    placeholder="۰"
                                                />
                                            </div>
                                        </div>
                                        <div className="mt-1" style={{ fontSize: "0.72rem" }}>
                                            در صورت تنظیم، هر جلسه یک بخش مرور اضافی از این بازه صفحات دریافت می‌کند (حلقوی).
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div className="d-flex justify-content-end gap-2 mt-4">
                                <button type="button" className="btn btn-outline-secondary rounded-pill px-4" onClick={onClose}>
                                    لغو
                                </button>
                                <button type="submit" className="btn btn-primary rounded-pill px-4" disabled={saving}>
                                    {saving ? <span className="spinner-border spinner-border-sm" /> : <><i className="bi bi-check-lg me-1" />ایجاد برنامه</>}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </motion.div>
        </motion.div>
    );
}

// ─── Request Card ─────────────────────────────────────────────────────────────

function RequestCard({
    req,
    onStatusUpdate,
    onCreatePlan,
}: {
    req: AdminClassRequest;
    onStatusUpdate: (id: string, status: string) => void;
    onCreatePlan: (req: AdminClassRequest) => void;
}) {
    const shouldReduceMotion = useReducedMotion();
    const cfg = REQUEST_STATUS_MAP[req.status] || REQUEST_STATUS_MAP.pending;
    const [expanded, setExpanded] = useState(false);

    return (
        <motion.div
            layout
            className="card border-0 shadow-sm rounded-4 mb-3 overflow-hidden"
            whileHover={shouldReduceMotion ? undefined : { y: -2, transition: { duration: 0.15 } }}
        >
            <div className={`border-start border-4 border-${cfg.color}`}>
                <div className="p-4">
                    <div className="d-flex align-items-start justify-content-between gap-3 flex-wrap">
                        <div className="d-flex align-items-center gap-3">
                            <div className={`bg-${cfg.color} bg-opacity-10 text-${cfg.color} rounded-circle d-flex align-items-center justify-content-center flex-shrink-0`} style={{ width: 44, height: 44 }}>
                                <i className="bi bi-person-fill fs-5" />
                            </div>
                            <div>
                                <h6 className="mb-0 fw-bold">{req.user_display.username}</h6>
                                <div className="small d-flex align-items-center gap-2 mt-1">
                                    {req.user_display.phone && (
                                        <span><i className="bi bi-telephone me-1" />{req.user_display.phone}</span>
                                    )}
                                    <span className="opacity-50">·</span>
                                    <span>{formatDate(req.created_at)}</span>
                                </div>
                            </div>
                        </div>
                        <div className="d-flex align-items-center gap-2">
                            <span className={`badge bg-${cfg.color} bg-opacity-10 text-${cfg.color} rounded-pill px-3`}>
                                {cfg.label}
                            </span>
                            <button
                                className="btn btn-sm btn-outline-secondary rounded-circle p-1"
                                onClick={() => setExpanded(!expanded)}
                                style={{ width: 28, height: 28, lineHeight: 1 }}
                            >
                                <i className={`bi bi-chevron-${expanded ? "up" : "down"}`} style={{ fontSize: 11 }} />
                            </button>
                        </div>
                    </div>

                    <AnimatePresence>
                        {expanded && (
                            <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: "auto", opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                transition={{ duration: 0.25 }}
                                className="overflow-hidden"
                            >
                                <div className="mt-3 pt-3 border-top">
                                    {req.notes && (
                                        <div className="bg-light rounded-3 p-3 mb-3 small">
                                            <div className="mb-1 fw-semibold">یادداشت کاربر:</div>
                                            <p className="mb-0">{req.notes}</p>
                                        </div>
                                    )}
                                    {req.admin_notes && (
                                        <div className="bg-info bg-opacity-10 rounded-3 p-3 mb-3 small">
                                            <div className="text-info mb-1 fw-semibold">یادداشت مدیر:</div>
                                            <p className="mb-0">{req.admin_notes}</p>
                                        </div>
                                    )}
                                    <div className="d-flex gap-2 flex-wrap">
                                        {req.status === "pending" && (
                                            <button
                                                className="btn btn-info btn-sm rounded-pill"
                                                onClick={() => onStatusUpdate(req.id, "contacted")}
                                            >
                                                <i className="bi bi-telephone-fill me-1" />تماس گرفته شد
                                            </button>
                                        )}
                                        {(req.status === "pending" || req.status === "contacted") && (
                                            <button
                                                className="btn btn-success btn-sm rounded-pill"
                                                onClick={() => onCreatePlan(req)}
                                            >
                                                <i className="bi bi-plus-circle me-1" />ایجاد برنامه
                                            </button>
                                        )}
                                        {req.status !== "rejected" && req.status !== "plan_created" && (
                                            <button
                                                className="btn btn-outline-danger btn-sm rounded-pill"
                                                onClick={() => onStatusUpdate(req.id, "rejected")}
                                            >
                                                <i className="bi bi-x-circle me-1" />رد کردن
                                            </button>
                                        )}
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </motion.div>
    );
}

// ─── Confirm Dialog ──────────────────────────────────────────────────────────

function ConfirmDialog({
    title,
    message,
    confirmLabel,
    onConfirm,
    onCancel,
}: {
    title: string;
    message: string;
    confirmLabel: string;
    onConfirm: () => void;
    onCancel: () => void;
}) {
    const shouldReduceMotion = useReducedMotion();
    return (
        <motion.div
            className="modal show d-block"
            tabIndex={-1}
            style={{ backgroundColor: "rgba(0,0,0,0.7)", zIndex: 1060 }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
        >
            <motion.div
                className="modal-dialog modal-dialog-centered"
                style={{ maxWidth: 420 }}
                initial={shouldReduceMotion ? false : { scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                transition={{ duration: 0.2 }}
            >
                <div className="modal-content rounded-4 border-0 shadow-lg">
                    <div className="modal-body p-4 text-center">
                        <div className="mb-3">
                            <span className="d-inline-flex align-items-center justify-content-center rounded-circle bg-danger bg-opacity-10" style={{ width: 56, height: 56 }}>
                                <i className="bi bi-exclamation-triangle-fill text-danger fs-4" />
                            </span>
                        </div>
                        <h6 className="fw-bold mb-2">{title}</h6>
                        <p className="small mb-4">{message}</p>
                        <div className="d-flex gap-2 justify-content-center">
                            <button className="btn btn-outline-secondary rounded-pill px-4" onClick={onCancel}>
                                انصراف
                            </button>
                            <button className="btn btn-danger rounded-pill px-4" onClick={onConfirm}>
                                {confirmLabel}
                            </button>
                        </div>
                    </div>
                </div>
            </motion.div>
        </motion.div>
    );
}

// ─── Plan Detail Drawer ───────────────────────────────────────────────────────

function PlanDetailDrawer({
    plan,
    callLogs,
    onClose,
    onStatusChange,
    onStepUpdate,
    onLogCall,
    onUpdateCallSession,
}: {
    plan: AdminPlan;
    callLogs: any[];
    onClose: () => void;
    onStatusChange: (status: string) => void;
    onStepUpdate: (stepId: string, data: any) => void;
    onLogCall: (notes: string) => void;
    onUpdateCallSession: (sessionId: string, status: CallSessionStatus) => void;
}) {
    const shouldReduceMotion = useReducedMotion();
    const [callNotes, setCallNotes] = useState("");
    const [loggingCall, setLoggingCall] = useState(false);
    const [editingStep, setEditingStep] = useState<string | null>(null);
    const [stepNote, setStepNote] = useState("");
    const [showCancelConfirm, setShowCancelConfirm] = useState(false);

    const handleLogCall = async () => {
        if (!callNotes.trim()) { toast.warning("یادداشت تماس را وارد کنید"); return; }
        setLoggingCall(true);
        await onLogCall(callNotes);
        setCallNotes("");
        setLoggingCall(false);
    };

    const handleStepNote = async (stepId: string) => {
        await onStepUpdate(stepId, { admin_note: stepNote });
        setEditingStep(null);
        setStepNote("");
    };

    return (
        <motion.div
            className="modal show d-block"
            tabIndex={-1}
            style={{ backgroundColor: "rgba(0,0,0,0.6)" }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
        >
            <motion.div
                className="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable"
                initial={shouldReduceMotion ? false : { x: 60, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: 60, opacity: 0 }}
                transition={{ duration: 0.3 }}
            >
                <div className="modal-content rounded-4 border-0 shadow-lg">
                    <div className="modal-header border-0 px-4 pt-4 pb-2">
                        <div>
                            <h5 className="modal-title fw-bold">
                                برنامه {plan.user_display.username}
                                <span className="ms-2 badge bg-secondary text-white rounded-pill" style={{ fontSize: "0.7rem" }}>
                                    ص {plan.start_page}–{plan.end_page}
                                </span>
                            </h5>
                            <div className="d-flex align-items-center gap-3 flex-wrap small mt-1">
                                {plan.user_display.phone && <span><i className="bi bi-telephone me-1" />{plan.user_display.phone}</span>}
                                {plan.subscription_info && (
                                    <span className={`badge rounded-pill ${plan.subscription_info.is_active ? "bg-success" : "bg-secondary"} bg-opacity-15 text-${plan.subscription_info.is_active ? "success" : "secondary"} border border-${plan.subscription_info.is_active ? "success" : "secondary"} border-opacity-25`}>
                                        <i className="bi bi-award me-1" />
                                        {plan.subscription_info.plan_name}
                                        {" · "}
                                        {plan.subscription_info.online_class_limit} جلسه آنلاین
                                    </span>
                                )}
                            </div>
                        </div>
                        <button type="button" className="btn-close" onClick={onClose} />
                    </div>

                    <div className="modal-body px-4">
                        <div className="row g-4">
                            {/* Left: Steps */}
                            <div className="col-lg-7">
                                <div className="d-flex align-items-center justify-content-between mb-3">
                                    <h6 className="fw-bold mb-0">مراحل ({plan.steps?.length ?? 0})</h6>
                                    <div className="d-flex gap-2">
                                        {plan.status === "draft" && (
                                            <button className="btn btn-success btn-sm rounded-pill" onClick={() => onStatusChange("active")}>
                                                <i className="bi bi-play-fill me-1" />فعال‌سازی
                                            </button>
                                        )}
                                        {plan.status === "active" && (
                                            <button className="btn btn-outline-danger btn-sm rounded-pill" onClick={() => setShowCancelConfirm(true)}>
                                                <i className="bi bi-stop-fill me-1" />لغو
                                            </button>
                                        )}
                                    </div>
                                </div>

                                {!plan._steps_generated && plan.status === "draft" && (
                                    <div className="alert alert-warning rounded-3 small">
                                        <i className="bi bi-info-circle me-1" />
                                        مراحل پس از فعال‌سازی برنامه تولید می‌شوند.
                                    </div>
                                )}

                                <div style={{ maxHeight: 460, overflowY: "auto" }} className="pe-1">
                                    {(plan.steps || []).map((step) => (
                                        <div
                                            key={step.id}
                                            className={`card border-0 rounded-3 mb-2 border-start border-3 border-${stepTypeColor(step.step_type)}`}
                                        >
                                            <div className="card-body py-2 px-3">
                                                <div className="d-flex align-items-center gap-2">
                                                    <i className={`bi ${stepTypeIcon(step.step_type)} text-${stepTypeColor(step.step_type)} flex-shrink-0`} />
                                                    <div className="flex-grow-1">
                                                        <div className="d-flex align-items-center gap-2 flex-wrap">
                                                            <span className="small fw-semibold">{step.step_type_display}</span>
                                                            <span className="" style={{ fontSize: "0.72rem" }}>ص {step.page_start}–{step.page_end}</span>
                                                            <span className={`badge bg-${stepStatusColor(step.status)} bg-opacity-10 text-${stepStatusColor(step.status)} rounded-pill`} style={{ fontSize: "0.65rem" }}>{step.status_display}</span>
                                                        </div>
                                                        {step.admin_note && (
                                                            <div className="mt-1" style={{ fontSize: "0.72rem" }}>
                                                                <i className="bi bi-chat-square-text me-1" />{step.admin_note}
                                                            </div>
                                                        )}
                                                        {step.delay_reason && (
                                                            <div className="text-danger mt-1" style={{ fontSize: "0.72rem" }}>
                                                                <i className="bi bi-exclamation-triangle me-1" />{step.delay_reason}
                                                            </div>
                                                        )}
                                                    </div>
                                                    <div className="d-flex gap-1 align-items-center flex-shrink-0">
                                                        <span className="fw-bold" style={{ fontSize: "0.7rem" }}>{formatDate(step.scheduled_date)}</span>
                                                        <button
                                                            className="btn btn-sm btn-outline-secondary rounded-circle p-0 d-flex align-items-center justify-content-center"
                                                            style={{ width: 24, height: 24 }}
                                                            onClick={() => { setEditingStep(editingStep === step.id ? null : step.id); setStepNote(step.admin_note || ""); }}
                                                            title="یادداشت مدیر"
                                                        >
                                                            <i className="bi bi-pencil" style={{ fontSize: 10 }} />
                                                        </button>
                                                    </div>
                                                </div>
                                                <AnimatePresence>
                                                    {editingStep === step.id && (
                                                        <motion.div
                                                            initial={{ height: 0, opacity: 0 }}
                                                            animate={{ height: "auto", opacity: 1 }}
                                                            exit={{ height: 0, opacity: 0 }}
                                                            className="overflow-hidden mt-2"
                                                        >
                                                            <div className="d-flex gap-2">
                                                                <input
                                                                    type="text"
                                                                    className="form-control form-control-sm rounded-3"
                                                                    value={stepNote}
                                                                    onChange={(e) => setStepNote(e.target.value)}
                                                                    placeholder="یادداشت برای این مرحله..."
                                                                />
                                                                <button className="btn btn-primary btn-sm rounded-pill px-3" onClick={() => handleStepNote(step.id)}>ثبت</button>
                                                            </div>
                                                        </motion.div>
                                                    )}
                                                </AnimatePresence>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Right: Info + Call log */}
                            <div className="col-lg-5">
                                {/* Plan info */}
                                <div className="card border-0 bg-light rounded-4 p-3 mb-4">
                                    <h6 className="fw-bold mb-3">جزئیات برنامه</h6>
                                    <div className="row g-2 text-center">
                                        {[
                                            { l: "شروع", v: formatDate(plan.start_date) },
                                            { l: "پایان هدف", v: formatDate(plan.time_to_finish) },
                                            { l: "تناوب مطالعه", v: plan.time_freq_display },
                                            { l: "حجم هر جلسه", v: plan.reading_freq_display },
                                            { l: "مرور هر چند صفحه", v: `هر ${plan.review_freq} صفحه` },
                                            { l: "روزهای مطالعه", v: plan.user_day_availability_display },
                                            { l: "بازه زمانی", v: plan.user_time_availability_display },
                                            { l: "محدوده حفظ", v: `ص ${plan.start_page}–${plan.end_page}` },
                                        ].map((i, idx) => (
                                            <div key={idx} className="col-6">
                                                <div className="bg-white rounded-3 p-2">
                                                    <div className="small">{i.l}</div>
                                                    <div className="fw-semibold small">{i.v || "—"}</div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                    {plan.extra_review_pages_per_session > 0 && plan.extra_review_start_page != null && plan.extra_review_end_page != null && (
                                        <div className="mt-2 bg-white rounded-3 p-2 text-center">
                                            <div className="small">مرور اضافی</div>
                                            <div className="fw-semibold small">
                                                ص {plan.extra_review_start_page}–{plan.extra_review_end_page}
                                                <span className="fw-normal ms-1">({plan.extra_review_pages_per_session} صفحه/جلسه)</span>
                                            </div>
                                        </div>
                                    )}
                                    {/* Progress bar */}
                                    <div className="mt-3">
                                        <div className="d-flex justify-content-between small mb-1">
                                            <span className="">پیشرفت</span>
                                            <span className="fw-bold text-primary">{plan.progress_percent}%</span>
                                        </div>
                                        <div className="progress rounded-pill" style={{ height: 8 }}>
                                            <motion.div
                                                className="progress-bar bg-primary rounded-pill"
                                                initial={{ width: 0 }}
                                                animate={{ width: `${plan.progress_percent}%` }}
                                                transition={{ duration: 1, ease: "easeOut" }}
                                            />
                                        </div>
                                        <div className="small mt-1">
                                            {plan.completed_steps} از {plan.total_steps} مرحله تکمیل شده
                                        </div>
                                    </div>
                                </div>

                                {/* Online call sessions */}
                                <div className="mb-4">
                                    <h6 className="fw-bold mb-3">
                                        <i className="bi bi-headset me-2 text-primary" />
                                        جلسات تماس آنلاین
                                        {plan.call_sessions && plan.call_sessions.length > 0 && (
                                            <span className="ms-2 fw-normal small">
                                                ({plan.call_sessions.filter(s => s.status === "completed").length}/{plan.call_sessions.length})
                                            </span>
                                        )}
                                    </h6>
                                    {plan.call_sessions && plan.call_sessions.length > 0 ? (
                                        <div className="d-flex flex-column gap-2">
                                            {plan.call_sessions.map((session) => (
                                                <div key={session.id} className={`card border-0 rounded-3 p-2 ${session.status === "completed" ? "bg-success bg-opacity-10" : session.status === "no_answer" ? "bg-warning bg-opacity-10" : "bg-light"}`}>
                                                    <div className="d-flex align-items-center gap-2">
                                                        <span className="small fw-semibold" style={{ minWidth: 24 }}>#{session.session_number}</span>
                                                        <div className="flex-grow-1">
                                                            {session.status !== "pending" && session.completed_at && (
                                                                <div className="" style={{ fontSize: "0.7rem" }}>
                                                                    {formatDateTime(session.completed_at)}
                                                                    {session.marked_by_display && <span className="ms-1">· {session.marked_by_display}</span>}
                                                                </div>
                                                            )}
                                                        </div>
                                                        <div className="d-flex gap-1">
                                                            <button
                                                                className={`btn btn-sm rounded-pill px-2 py-0 ${session.status === "completed" ? "btn-success" : "btn-outline-success"}`}
                                                                style={{ fontSize: "0.7rem" }}
                                                                onClick={() => onUpdateCallSession(session.id, "completed")}
                                                                title="تماس برقرار شد"
                                                            >
                                                                <i className="bi bi-check-lg" />
                                                            </button>
                                                            <button
                                                                className={`btn btn-sm rounded-pill px-2 py-0 ${session.status === "no_answer" ? "btn-warning" : "btn-outline-warning"}`}
                                                                style={{ fontSize: "0.7rem" }}
                                                                onClick={() => onUpdateCallSession(session.id, "no_answer")}
                                                                title="بی‌پاسخ"
                                                            >
                                                                <i className="bi bi-telephone-x" />
                                                            </button>
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <div className="small bg-light rounded-3 p-3">
                                            <i className="bi bi-info-circle me-2" />
                                            {plan.subscription_info
                                                ? plan.subscription_info.online_class_limit > 0
                                                    ? `اشتراک کاربر ${plan.subscription_info.online_class_limit} جلسه آنلاین دارد. جلسات پس از فعال‌سازی برنامه ایجاد می‌شوند.`
                                                    : "اشتراک کاربر شامل جلسه تماس آنلاین نمی‌شود."
                                                : "جلسه تماس آنلاین برای این برنامه ثبت نشده است."
                                            }
                                        </div>
                                    )}
                                </div>

                                {/* Call log */}
                                <div>
                                    <h6 className="fw-bold mb-3">ثبت تماس</h6>
                                    <div className="mb-3">
                                        <textarea
                                            className="form-control rounded-3 small"
                                            rows={3}
                                            value={callNotes}
                                            onChange={(e) => setCallNotes(e.target.value)}
                                            placeholder="خلاصه مکالمه، توصیه‌ها، وضعیت کاربر..."
                                        />
                                        <div className="d-flex gap-2 mt-2">
                                            <button
                                                className="btn btn-primary btn-sm rounded-pill px-4"
                                                onClick={handleLogCall}
                                                disabled={loggingCall}
                                            >
                                                {loggingCall ? <span className="spinner-border spinner-border-sm" /> : <><i className="bi bi-telephone-plus me-1" />ثبت تماس</>}
                                            </button>
                                            {plan.user_display?.phone && (
                                                <a
                                                    href={`tel:${plan.user_display.phone}`}
                                                    className="btn btn-success btn-sm rounded-pill px-3"
                                                    title={plan.user_display.phone}
                                                >
                                                    <i className="bi bi-telephone-fill me-1" />
                                                    {plan.user_display.phone}
                                                </a>
                                            )}
                                        </div>
                                    </div>

                                    {callLogs.length > 0 && (
                                        <div style={{ maxHeight: 220, overflowY: "auto" }}>
                                            {callLogs.map((log) => (
                                                <div key={log.id} className="card border-0 bg-light rounded-3 p-3 mb-2 small">
                                                    <div className="d-flex justify-content-between mb-1">
                                                        <span><i className="bi bi-person-fill me-1" />{log.called_by_display || "استاد"}</span>
                                                        <span>{formatDateTime(log.call_date)}</span>
                                                    </div>
                                                    <p className="mb-0">{log.notes}</p>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </motion.div>

            <AnimatePresence>
                {showCancelConfirm && (
                    <ConfirmDialog
                        title="لغو برنامه"
                        message="آیا مطمئن هستید که می‌خواهید این برنامه را لغو کنید؟ کاربر دیگر نمی‌تواند پیشرفتی ثبت کند."
                        confirmLabel="بله، لغو شود"
                        onConfirm={() => { setShowCancelConfirm(false); onStatusChange("cancelled"); }}
                        onCancel={() => setShowCancelConfirm(false)}
                    />
                )}
            </AnimatePresence>
        </motion.div>
    );
}

// ─── Filter Chips ─────────────────────────────────────────────────────────────

function FilterChips({ options, active, onChange }: { options: { value: string; label: string }[]; active: string; onChange: (v: string) => void }) {
    const shouldReduceMotion = useReducedMotion();
    return (
        <div className="d-flex gap-2 flex-wrap mb-4">
            {options.map((opt) => (
                <motion.button
                    key={opt.value}
                    className={`btn btn-sm rounded-pill ${active === opt.value ? "btn-primary" : "btn-outline-secondary"}`}
                    onClick={() => onChange(opt.value)}
                    whileTap={shouldReduceMotion ? undefined : { scale: 0.93 }}
                >
                    {opt.label}
                </motion.button>
            ))}
        </div>
    );
}

// ─── Admin Panel Content ──────────────────────────────────────────────────────

type AdminTab = "requests" | "plans" | "calls";

function AdminClassContent() {
    const { user } = useAuth();
    const {
        adminRequests, adminPlans, activePlan, callLogs, isLoading,
        fetchAdminRequests, updateAdminRequest, fetchAdminPlans,
        fetchAdminPlanDetail, createPlan, updatePlan, updateAdminStep,
        logCall, updateCallSession, clearActivePlan,
    } = useAdminClassPanel();
    const shouldReduceMotion = useReducedMotion();

    const [activeTab, setActiveTab] = useState<AdminTab>("requests");
    const [reqStatusFilter, setReqStatusFilter] = useState("all");
    const [planStatusFilter, setPlanStatusFilter] = useState("all");
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [createFromRequest, setCreateFromRequest] = useState<AdminClassRequest | null>(null);
    const [hasFetched, setHasFetched] = useState(false);

    useEffect(() => {
        if (!hasFetched) {
            setHasFetched(true);
            fetchAdminRequests();
            fetchAdminPlans();
        }
    }, [hasFetched]);

    useEffect(() => {
        const filter = reqStatusFilter === "all" ? undefined : reqStatusFilter;
        fetchAdminRequests(filter);
    }, [reqStatusFilter]);

    useEffect(() => {
        const filter = planStatusFilter === "all" ? undefined : planStatusFilter;
        fetchAdminPlans(filter);
    }, [planStatusFilter]);

    const handleCreatePlan = async (payload: CreatePlanPayload) => {
        const result = await createPlan(payload);
        if (result.success) {
            toast.success("برنامه با موفقیت ایجاد شد");
            setShowCreateModal(false);
            setCreateFromRequest(null);
            // Refresh requests so the linked request card reflects plan_created status
            fetchAdminRequests(reqStatusFilter === "all" ? undefined : reqStatusFilter);
        } else {
            toast.error("خطا در ایجاد برنامه");
        }
    };

    const handleRequestStatusUpdate = async (id: string, status: string) => {
        const result = await updateAdminRequest(id, { status });
        if (result.success) {
            toast.success("وضعیت درخواست به‌روز شد");
        } else {
            toast.error("خطا در به‌روزرسانی وضعیت درخواست");
        }
    };

    const handleOpenCreateFromRequest = (req: AdminClassRequest) => {
        setCreateFromRequest(req);
        setShowCreateModal(true);
    };

    const handlePlanStatusChange = async (status: string) => {
        if (!activePlan) return;
        const result = await updatePlan(activePlan.id, { status } as any);
        if (result.success) {
            toast.success("وضعیت برنامه به‌روز شد");
            fetchAdminPlanDetail(activePlan.id);
        } else {
            toast.error("خطا در به‌روزرسانی وضعیت برنامه");
        }
    };

    const handleStepUpdate = async (stepId: string, data: any) => {
        const result = await updateAdminStep(stepId, data);
        if (result.success) {
            toast.success("مرحله به‌روز شد");
        } else {
            toast.error("خطا در به‌روزرسانی مرحله");
        }
    };

    const handleLogCall = async (notes: string) => {
        if (!activePlan) return;
        const result = await logCall(activePlan.id, notes);
        if (result.success) {
            toast.success("تماس ثبت شد");
        } else {
            toast.error("خطا در ثبت تماس");
        }
    };

    const handleUpdateCallSession = async (sessionId: string, status: CallSessionStatus) => {
        const result = await updateCallSession(sessionId, status);
        if (result.success) {
            toast.success("جلسه تماس به‌روز شد");
        } else {
            toast.error("خطا در به‌روزرسانی جلسه تماس");
        }
    };

    const TABS: { id: AdminTab; icon: string; label: string; count?: number }[] = [
        { id: "requests", icon: "bi-inbox", label: "درخواست‌ها", count: adminRequests.length },
        { id: "plans", icon: "bi-journal-bookmark", label: "برنامه‌ها", count: adminPlans.length },
        { id: "calls", icon: "bi-telephone-outbound", label: "ثبت تماس سریع" },
    ];

    return (
        <div className="col-xl-9">
            <div className="card bg-transparent border rounded-3">
                <div className="card-header bg-transparent border-bottom">
                    <div className="d-flex align-items-center justify-content-between flex-wrap gap-3">
                        <div className="d-flex align-items-center gap-2">
                            <i className="bi bi-shield-check text-primary fs-5" />
                            <h3 className="mb-0 fs-5 fw-bold">پنل مدیریت کلاس</h3>
                        </div>
                        <button
                            className="btn btn-primary btn-sm rounded-pill px-3"
                            onClick={() => { setCreateFromRequest(null); setShowCreateModal(true); }}
                        >
                            <i className="bi bi-plus-circle me-2" />
                            برنامه جدید
                        </button>
                    </div>
                </div>

                <div className="card-body">
                    {/* Tab bar */}
                    <div className="d-flex gap-2 mb-4 flex-wrap border-bottom pb-3">
                        {TABS.map((t) => (
                            <motion.button
                                key={t.id}
                                className={`btn rounded-pill px-4 d-flex align-items-center gap-2 ${activeTab === t.id ? "btn-primary" : "btn-outline-secondary"}`}
                                onClick={() => setActiveTab(t.id)}
                                whileTap={shouldReduceMotion ? undefined : { scale: 0.95 }}
                            >
                                <i className={`bi ${t.icon}`} />
                                {t.label}
                                {t.count !== undefined && (
                                    <span className={`badge rounded-pill ${activeTab === t.id ? "bg-white text-primary" : "bg-secondary"}`} style={{ fontSize: "0.65rem" }}>
                                        {t.count}
                                    </span>
                                )}
                            </motion.button>
                        ))}
                    </div>

                    <AnimatePresence mode="wait">
                        {/* ── Requests ── */}
                        {activeTab === "requests" && (
                            <motion.div
                                key="requests"
                                initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                transition={{ duration: 0.2 }}
                            >
                                <FilterChips
                                    active={reqStatusFilter}
                                    onChange={setReqStatusFilter}
                                    options={[
                                        { value: "all", label: "همه" },
                                        { value: "pending", label: "در انتظار" },
                                        { value: "contacted", label: "تماس گرفته شد" },
                                        { value: "plan_created", label: "برنامه ایجاد شد" },
                                        { value: "rejected", label: "رد شده" },
                                    ]}
                                />
                                {isLoading ? (
                                    <div className="text-center py-5"><div className="spinner-border text-primary" /></div>
                                ) : adminRequests.length === 0 ? (
                                    <div className="text-center py-5">
                                        <i className="bi bi-inbox display-4 d-block mb-3" />
                                        درخواستی یافت نشد
                                    </div>
                                ) : (
                                    <motion.div variants={staggerContainer} initial={shouldReduceMotion ? false : "hidden"} animate="show">
                                        {adminRequests.map((req, i) => (
                                            <motion.div key={req.id} variants={fadeInUp} transition={{ delay: i * 0.05 }}>
                                                <RequestCard
                                                    req={req}
                                                    onStatusUpdate={handleRequestStatusUpdate}
                                                    onCreatePlan={handleOpenCreateFromRequest}
                                                />
                                            </motion.div>
                                        ))}
                                    </motion.div>
                                )}
                            </motion.div>
                        )}

                        {/* ── Plans ── */}
                        {activeTab === "plans" && (
                            <motion.div
                                key="plans"
                                initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                transition={{ duration: 0.2 }}
                            >
                                <FilterChips
                                    active={planStatusFilter}
                                    onChange={setPlanStatusFilter}
                                    options={[
                                        { value: "all", label: "همه" },
                                        { value: "draft", label: "پیش‌نویس" },
                                        { value: "active", label: "فعال" },
                                        { value: "completed", label: "تمام شده" },
                                        { value: "cancelled", label: "لغو شده" },
                                    ]}
                                />
                                {isLoading ? (
                                    <div className="text-center py-5"><div className="spinner-border text-primary" /></div>
                                ) : adminPlans.length === 0 ? (
                                    <div className="text-center py-5">
                                        <i className="bi bi-journal-x display-4 d-block mb-3" />
                                        برنامه‌ای یافت نشد
                                    </div>
                                ) : (
                                    <div className="table-responsive">
                                        <table className="table table-hover align-middle">
                                            <thead className="table-light">
                                                <tr>
                                                    <th>کاربر</th>
                                                    <th>صفحات</th>
                                                    <th>وضعیت</th>
                                                    <th>پیشرفت</th>
                                                    <th>شروع</th>
                                                    <th></th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {adminPlans.map((plan) => {
                                                    const cfg = PLAN_STATUS_MAP[plan.status] || PLAN_STATUS_MAP.draft;
                                                    return (
                                                        <tr key={plan.id}>
                                                            <td>
                                                                <div className="fw-semibold">{plan.user_display?.username || "—"}</div>
                                                                <div className="small">{plan.user_display?.phone || ""}</div>
                                                            </td>
                                                            <td className="small">{plan.start_page}–{plan.end_page}</td>
                                                            <td>
                                                                <span className={`badge bg-${cfg.color} bg-opacity-10 text-${cfg.color} rounded-pill`}>
                                                                    {cfg.label}
                                                                </span>
                                                            </td>
                                                            <td style={{ minWidth: 100 }}>
                                                                <div className="progress rounded-pill" style={{ height: 6 }}>
                                                                    <div
                                                                        className="progress-bar bg-primary rounded-pill"
                                                                        style={{ width: `${plan.progress_percent}%` }}
                                                                    />
                                                                </div>
                                                                <div className="" style={{ fontSize: "0.7rem" }}>{plan.progress_percent}%</div>
                                                            </td>
                                                            <td className="small">{formatDate(plan.start_date)}</td>
                                                            <td>
                                                                <button
                                                                    className="btn btn-sm btn-outline-primary rounded-pill"
                                                                    onClick={() => fetchAdminPlanDetail(plan.id)}
                                                                >
                                                                    <i className="bi bi-eye me-1" />جزئیات
                                                                </button>
                                                            </td>
                                                        </tr>
                                                    );
                                                })}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </motion.div>
                        )}

                        {/* ── Quick Call ── */}
                        {activeTab === "calls" && (
                            <motion.div
                                key="calls"
                                initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                transition={{ duration: 0.2 }}
                            >
                                <div className="row g-4">
                                    <div className="col-lg-6">
                                        <div className="card border-0 shadow-sm rounded-4 p-4">
                                            <h6 className="fw-bold mb-3">
                                                <i className="bi bi-telephone-plus text-primary me-2" />
                                                ثبت تماس جدید
                                            </h6>
                                            <QuickCallForm plans={adminPlans} onLog={logCall} />
                                        </div>
                                    </div>
                                    <div className="col-lg-6">
                                        <div className="card border-0 shadow-sm rounded-4 p-4">
                                            <h6 className="fw-bold mb-3">
                                                <i className="bi bi-clock-history me-2" />
                                                آخرین تماس‌ها
                                            </h6>
                                            <RecentCallsSummary plans={adminPlans} />
                                        </div>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>

            {/* Modals */}
            <AnimatePresence>
                {showCreateModal && (
                    <CreatePlanModal
                        onClose={() => { setShowCreateModal(false); setCreateFromRequest(null); }}
                        onCreate={handleCreatePlan}
                        prefillRequest={createFromRequest}
                    />
                )}
                {activePlan && (
                    <PlanDetailDrawer
                        plan={activePlan}
                        callLogs={callLogs}
                        onClose={clearActivePlan}
                        onStatusChange={handlePlanStatusChange}
                        onStepUpdate={handleStepUpdate}
                        onLogCall={handleLogCall}
                        onUpdateCallSession={handleUpdateCallSession}
                    />
                )}
            </AnimatePresence>
        </div>
    );
}

// ─── Quick Call Form (standalone in calls tab) ────────────────────────────────

function QuickCallForm({ plans, onLog }: { plans: AdminPlan[]; onLog: (planId: string, notes: string) => Promise<any> }) {
    const [planId, setPlanId] = useState("");
    const [notes, setNotes] = useState("");
    const [saving, setSaving] = useState(false);
    const selectedPhone = plans.find(p => p.id === planId)?.user_display?.phone ?? null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!planId || !notes.trim()) { toast.warning("برنامه و یادداشت را وارد کنید"); return; }
        setSaving(true);
        const result = await onLog(planId, notes);
        if (result.success) {
            toast.success("تماس ثبت شد");
            setNotes("");
        } else {
            toast.error("خطا در ثبت تماس");
        }
        setSaving(false);
    };

    return (
        <form onSubmit={handleSubmit}>
            <div className="mb-3">
                <label className="form-label small fw-semibold">برنامه (کاربر)</label>
                <select className="form-select rounded-3" value={planId} onChange={(e) => setPlanId(e.target.value)} required>
                    <option value="">انتخاب کنید...</option>
                    {plans.filter(p => p.status === "active").map((p) => (
                        <option key={p.id} value={p.id}>
                            {p.user_display?.username} — ص {p.start_page}–{p.end_page}
                        </option>
                    ))}
                </select>
            </div>
            <div className="mb-3">
                <label className="form-label small fw-semibold">یادداشت تماس</label>
                <textarea
                    className="form-control rounded-3"
                    rows={4}
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="خلاصه مکالمه، وضعیت کاربر، توصیه‌ها..."
                    required
                />
            </div>
            <div className="d-flex gap-2">
                <button type="submit" className="btn btn-primary rounded-pill px-4" disabled={saving}>
                    {saving ? <span className="spinner-border spinner-border-sm" /> : <><i className="bi bi-telephone-plus me-1" />ثبت</>}
                </button>
                {selectedPhone && (
                    <a href={`tel:${selectedPhone}`} className="btn btn-success rounded-pill px-3" title={selectedPhone}>
                        <i className="bi bi-telephone-fill me-1" />
                        {selectedPhone}
                    </a>
                )}
            </div>
        </form>
    );
}

function RecentCallsSummary({ plans }: { plans: AdminPlan[] }) {
    if (plans.length === 0) return <p className="small">ابتدا برنامه‌ای فعال کنید.</p>;
    return (
        <p className="small">
            برای مشاهده تاریخچه تماس‌ها، از تب «برنامه‌ها» روی دکمه «جزئیات» کلیک کنید.
        </p>
    );
}

export default function AdminClassPage() {
    return <DashboardBase Content={<AdminClassContent />} />;
}
