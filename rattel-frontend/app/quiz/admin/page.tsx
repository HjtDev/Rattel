"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { toast } from "react-toastify";
import { useQuiz } from "@/src/core/hooks/useQuiz";
import { quizManager } from "@/src/core/quiz/quizManager";
import { useAuth } from "@/src/core/hooks/useAuth";
import { getMediaUrl } from "@/src/core/utils";
import { fadeInUp, staggerContainer } from "@/src/core/motionVariants";

const DIFFICULTY_LABELS: Record<string, string> = {
    easy: "آسان",
    medium: "متوسط",
    hard: "سخت",
};

// ─── Confirm Dialog ───────────────────────────────────────────────────────────

function ConfirmDialog({
    title,
    message,
    confirmLabel = "حذف",
    onConfirm,
    onCancel,
}: {
    title: string;
    message: string;
    confirmLabel?: string;
    onConfirm: () => void;
    onCancel: () => void;
}) {
    return (
        <motion.div
            className="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center"
            style={{ zIndex: 1060, background: "rgba(0,0,0,0.6)" }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={(e) => e.target === e.currentTarget && onCancel()}
        >
            <motion.div
                className="card border-0 shadow-lg rounded-4"
                style={{ width: "min(420px,92vw)" }}
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                transition={{ duration: 0.2 }}
            >
                <div className="card-body p-4 text-center">
                    <div className="mb-3">
                        <span
                            className="d-inline-flex align-items-center justify-content-center rounded-circle bg-danger bg-opacity-10"
                            style={{ width: 56, height: 56 }}
                        >
                            <i className="bi bi-exclamation-triangle-fill text-danger fs-4" />
                        </span>
                    </div>
                    <h6 className="fw-bold mb-2">{title}</h6>
                    <p className="small text-muted mb-4">{message}</p>
                    <div className="d-flex gap-2 justify-content-center">
                        <button className="btn btn-danger rounded-pill px-4" onClick={onConfirm}>
                            {confirmLabel}
                        </button>
                        <button className="btn btn-outline-secondary rounded-pill px-4" onClick={onCancel}>
                            انصراف
                        </button>
                    </div>
                </div>
            </motion.div>
        </motion.div>
    );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function AdminQuizListPage() {
    const router = useRouter();
    const { user, isAuthenticated } = useAuth();
    const { adminQuizzes, adminQuizzesTotal, isLoading } = useQuiz();

    const [showCreateForm, setShowCreateForm] = useState(false);
    const [creating, setCreating] = useState(false);
    const [form, setForm] = useState({
        title: "",
        difficulty: "medium",
        is_active: true,
        max_attempts_per_user: 0,
        randomize_question_order: false,
        reveal_answers_during_quiz: false,
        allow_retry_on_expiry: true,
        description: "",
    });
    const [thumbnailFile, setThumbnailFile] = useState<File | null>(null);
    const thumbnailInputRef = useRef<HTMLInputElement>(null);

    const [deleteTarget, setDeleteTarget] = useState<{ id: string; title: string } | null>(null);

    useEffect(() => {
        if (!isAuthenticated) {
            router.replace("/auth/login?next=/quiz/admin/");
            return;
        }
        if (!(user as any)?.is_staff) {
            router.replace("/dashboard");
            return;
        }
        quizManager.fetchAdminQuizzes();
    }, [isAuthenticated, user]);

    const handleCreate = async () => {
        if (!form.title.trim()) {
            toast.error("عنوان آزمون الزامی است.");
            return;
        }
        setCreating(true);
        const res = await quizManager.createQuiz({
            title: form.title,
            description: form.description,
            difficulty: form.difficulty as any,
            is_active: form.is_active,
            max_attempts_per_user: form.max_attempts_per_user,
            randomize_question_order: form.randomize_question_order,
            reveal_answers_during_quiz: form.reveal_answers_during_quiz,
            allow_retry_on_expiry: form.allow_retry_on_expiry,
            thumbnail: thumbnailFile,
        });
        setCreating(false);
        if (res.success && res.quiz) {
            toast.success("آزمون با موفقیت ایجاد شد.");
            setShowCreateForm(false);
            setForm({ title: "", difficulty: "medium", is_active: true, max_attempts_per_user: 0, randomize_question_order: false, reveal_answers_during_quiz: false, allow_retry_on_expiry: true, description: "" });
            setThumbnailFile(null);
            router.push(`/quiz/admin/${res.quiz.id}`);
        } else {
            toast.error(res.message || "خطا در ایجاد آزمون");
        }
    };

    const handleToggleActive = async (quizId: string, current: boolean) => {
        const res = await quizManager.updateQuiz(quizId, { is_active: !current });
        if (res.success) {
            toast.success(`آزمون ${!current ? "فعال" : "غیرفعال"} شد.`);
            quizManager.fetchAdminQuizzes();
        } else {
            toast.error(res.message || "خطا");
        }
    };

    const handleDeleteConfirmed = async () => {
        if (!deleteTarget) return;
        const res = await quizManager.deleteQuiz(deleteTarget.id);
        setDeleteTarget(null);
        if (res.success) {
            toast.success("آزمون حذف شد.");
        } else {
            toast.error(res.message || "خطا در حذف آزمون");
        }
    };

    return (
        <main className="py-5">
            <div className="container">
                <div className="d-flex align-items-center justify-content-between mb-4">
                    <div>
                        <h2 className="fw-bold mb-1">مدیریت آزمون‌ها</h2>
                        <p className="mb-0">
                            {new Intl.NumberFormat("fa-IR").format(adminQuizzesTotal)} آزمون در سیستم
                        </p>
                    </div>
                    <button className="btn btn-primary" onClick={() => setShowCreateForm(!showCreateForm)}>
                        <i className="bi bi-plus-lg me-2"></i>
                        آزمون جدید
                    </button>
                </div>

                {/* Create form */}
                {showCreateForm && (
                    <motion.div
                        className="card border-0 shadow-sm mb-4"
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                    >
                        <div className="card-header bg-primary text-white">
                            <h5 className="mb-0">ایجاد آزمون جدید</h5>
                        </div>
                        <div className="card-body p-4">
                            <div className="row g-3">
                                <div className="col-md-6">
                                    <label className="form-label">عنوان <span className="text-danger">*</span></label>
                                    <input
                                        type="text"
                                        className="form-control"
                                        value={form.title}
                                        onChange={(e) => setForm({ ...form, title: e.target.value })}
                                        placeholder="عنوان آزمون"
                                    />
                                </div>
                                <div className="col-md-3">
                                    <label className="form-label">سطح سختی</label>
                                    <select className="form-select" value={form.difficulty} onChange={(e) => setForm({ ...form, difficulty: e.target.value })}>
                                        <option value="easy">آسان</option>
                                        <option value="medium">متوسط</option>
                                        <option value="hard">سخت</option>
                                    </select>
                                </div>
                                <div className="col-md-3">
                                    <label className="form-label">حداکثر تلاش (۰ = نامحدود)</label>
                                    <input
                                        type="number"
                                        className="form-control"
                                        value={form.max_attempts_per_user}
                                        min={0}
                                        onChange={(e) => setForm({ ...form, max_attempts_per_user: Number(e.target.value) })}
                                    />
                                </div>
                                <div className="col-12">
                                    <label className="form-label">توضیحات</label>
                                    <textarea
                                        className="form-control"
                                        rows={3}
                                        value={form.description}
                                        onChange={(e) => setForm({ ...form, description: e.target.value })}
                                        placeholder="توضیحات آزمون (اختیاری)"
                                    />
                                </div>
                                <div className="col-md-6">
                                    <label className="form-label">بنر</label>
                                    <div
                                        className="border rounded-3 p-3 text-center"
                                        style={{ cursor: "pointer", minHeight: 80 }}
                                        onClick={() => thumbnailInputRef.current?.click()}
                                    >
                                        {thumbnailFile ? (
                                            <div className="d-flex align-items-center gap-2 justify-content-center">
                                                <img
                                                    src={URL.createObjectURL(thumbnailFile)}
                                                    alt="thumbnail"
                                                    className="rounded"
                                                    style={{ width: 56, height: 40, objectFit: "cover" }}
                                                />
                                                <span className="small text-muted">{thumbnailFile.name}</span>
                                            </div>
                                        ) : (
                                            <span className="small text-muted">
                                                <i className="bi bi-image me-2"></i>
                                                کلیک کنید تا تصویر انتخاب کنید
                                            </span>
                                        )}
                                    </div>
                                    <input
                                        type="file"
                                        ref={thumbnailInputRef}
                                        className="d-none"
                                        accept="image/*"
                                        onChange={(e) => setThumbnailFile(e.target.files?.[0] ?? null)}
                                    />
                                </div>
                                <div className="col-md-6 d-flex align-items-end">
                                    <div className="d-flex flex-wrap gap-4 w-100">
                                        <div className="form-check form-switch">
                                            <input className="form-check-input" type="checkbox" id="is_active" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
                                            <label className="form-check-label" htmlFor="is_active">فعال</label>
                                        </div>
                                        <div className="form-check form-switch">
                                            <input className="form-check-input" type="checkbox" id="randomize" checked={form.randomize_question_order} onChange={(e) => setForm({ ...form, randomize_question_order: e.target.checked })} />
                                            <label className="form-check-label" htmlFor="randomize">ترتیب تصادفی</label>
                                        </div>
                                        <div className="form-check form-switch">
                                            <input className="form-check-input" type="checkbox" id="reveal" checked={form.reveal_answers_during_quiz} onChange={(e) => setForm({ ...form, reveal_answers_during_quiz: e.target.checked })} />
                                            <label className="form-check-label" htmlFor="reveal">نمایش پاسخ حین آزمون</label>
                                        </div>
                                        <div className="form-check form-switch">
                                            <input className="form-check-input" type="checkbox" id="retry" checked={form.allow_retry_on_expiry} onChange={(e) => setForm({ ...form, allow_retry_on_expiry: e.target.checked })} />
                                            <label className="form-check-label" htmlFor="retry">تلاش مجدد پس از اتمام زمان</label>
                                        </div>
                                    </div>
                                </div>
                                <div className="col-12 d-flex gap-2 justify-content-end">
                                    <button className="btn btn-outline-secondary" onClick={() => setShowCreateForm(false)}>انصراف</button>
                                    <button className="btn btn-primary" onClick={handleCreate} disabled={creating}>
                                        {creating ? <><span className="spinner-border spinner-border-sm me-2"></span>در حال ایجاد...</> : <><i className="bi bi-check-lg me-2"></i>ایجاد آزمون</>}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* Quiz list */}
                {isLoading ? (
                    <div className="text-center py-5">
                        <div className="spinner-border text-primary" role="status">
                            <span className="visually-hidden">در حال بارگذاری...</span>
                        </div>
                    </div>
                ) : adminQuizzes.length === 0 ? (
                    <div className="text-center py-5">
                        <i className="bi bi-patch-question fs-1 mb-3 d-block"></i>
                        <p>هنوز آزمونی ایجاد نشده است</p>
                    </div>
                ) : (
                    <motion.div className="row g-3" variants={staggerContainer} initial="hidden" animate="show">
                        {adminQuizzes.map((quiz) => (
                            <motion.div key={quiz.id} className="col-12" variants={fadeInUp}>
                                <div className="card border-0 shadow-sm">
                                    <div className="card-body p-4">
                                        <div className="d-flex align-items-start gap-3">
                                            {quiz.thumbnail && (
                                                <img
                                                    src={getMediaUrl(quiz.thumbnail)}
                                                    alt={quiz.title}
                                                    className="rounded"
                                                    style={{ width: "64px", height: "48px", objectFit: "cover", flexShrink: 0 }}
                                                />
                                            )}
                                            <div className="flex-grow-1">
                                                <div className="d-flex align-items-center gap-2 mb-1">
                                                    <h5 className="mb-0">{quiz.title}</h5>
                                                    <span className={`badge ${quiz.is_active ? "bg-success" : "bg-secondary"}`}>
                                                        {quiz.is_active ? "فعال" : "غیرفعال"}
                                                    </span>
                                                    <span className="badge bg-light text-dark border">
                                                        {DIFFICULTY_LABELS[quiz.difficulty] ?? quiz.difficulty}
                                                    </span>
                                                </div>
                                                <div className="d-flex gap-3 small text-muted">
                                                    <span><i className="bi bi-list-ol me-1"></i>{new Intl.NumberFormat("fa-IR").format((quiz as any).question_count ?? 0)} سوال</span>
                                                    {quiz.categories.length > 0 && (
                                                        <span><i className="bi bi-tag me-1"></i>{quiz.categories.map((c) => c.name).join("، ")}</span>
                                                    )}
                                                </div>
                                            </div>
                                            <div className="d-flex gap-2 flex-shrink-0">
                                                <button
                                                    className={`btn btn-sm ${quiz.is_active ? "btn-outline-warning" : "btn-outline-success"}`}
                                                    onClick={() => handleToggleActive(quiz.id, quiz.is_active)}
                                                    title={quiz.is_active ? "غیرفعال کردن" : "فعال کردن"}
                                                >
                                                    <i className={`bi ${quiz.is_active ? "bi-eye-slash" : "bi-eye"}`}></i>
                                                </button>
                                                <a href={`/quiz/admin/${quiz.id}`} className="btn btn-sm btn-outline-primary" title="ویرایش">
                                                    <i className="bi bi-pencil"></i>
                                                </a>
                                                <button
                                                    className="btn btn-sm btn-outline-danger"
                                                    onClick={() => setDeleteTarget({ id: quiz.id, title: quiz.title })}
                                                    title="حذف"
                                                >
                                                    <i className="bi bi-trash"></i>
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                    </motion.div>
                )}
            </div>

            <AnimatePresence>
                {deleteTarget && (
                    <ConfirmDialog
                        title="حذف آزمون"
                        message={`آیا مطمئن هستید که می‌خواهید آزمون «${deleteTarget.title}» را حذف کنید؟ این عمل قابل بازگشت نیست.`}
                        onConfirm={handleDeleteConfirmed}
                        onCancel={() => setDeleteTarget(null)}
                    />
                )}
            </AnimatePresence>
        </main>
    );
}
