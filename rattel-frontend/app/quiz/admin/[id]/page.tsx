"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { toast } from "react-toastify";
import {
    quizManager,
    type AccessRequirement,
    type AccessRequirementPayload,
    type QuizAdmin,
    type QuestionAdmin,
    type MatchingPairAdmin,
    type CreateQuestionPayload,
    type QuizCategory,
    type QuizParticipant,
} from "@/src/core/quiz/quizManager";
import { useAuth } from "@/src/core/hooks/useAuth";
import { getMediaUrl, toJalali } from "@/src/core/utils";
import { fadeInUp } from "@/src/core/motionVariants";

// ─── Constants ────────────────────────────────────────────────────────────────

const QUESTION_TYPE_LABELS: Record<string, string> = {
    multiple_choice: "چند گزینه‌ای",
    fill_blank: "جای خالی",
    true_false: "صحیح / غلط",
    matching: "وصل کردن",
};

const EMPTY_MC_OPTIONS = [
    { text: "", is_correct: false, order: 0 },
    { text: "", is_correct: false, order: 1 },
    { text: "", is_correct: false, order: 2 },
    { text: "", is_correct: false, order: 3 },
];

const TF_OPTIONS = [
    { text: "صحیح", is_correct: true, order: 0 },
    { text: "غلط", is_correct: false, order: 1 },
];

const REQ_TYPE_LABELS: Record<string, string> = {
    free: "آزاد (بدون محدودیت)",
    subscription: "نیاز به اشتراک فعال",
    completed_quiz: "تکمیل آزمون دیگر",
    min_score: "حداقل امتیاز کل کاربر",
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

const EMPTY_PAIRS = [
    { left_text: "", right_text: "" },
    { left_text: "", right_text: "" },
    { left_text: "", right_text: "" },
    { left_text: "", right_text: "" },
];

interface QuestionFormState {
    type: "multiple_choice" | "fill_blank" | "true_false" | "matching";
    text: string;
    score: number;
    time_to_answer: number;
    options: { text: string; is_correct: boolean; order: number }[];
    pairs: { left_text: string; right_text: string }[];
    imageFile: File | null;
}

function buildDefaultOptions(type: string) {
    if (type === "true_false") return TF_OPTIONS.map((o) => ({ ...o }));
    return EMPTY_MC_OPTIONS.map((o) => ({ ...o }));
}

// ─── Confirm Dialog ───────────────────────────────────────────────────────────

function ConfirmDialog({
    title,
    message,
    onConfirm,
    onCancel,
}: {
    title: string;
    message: string;
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
                        <span className="d-inline-flex align-items-center justify-content-center rounded-circle bg-danger bg-opacity-10" style={{ width: 56, height: 56 }}>
                            <i className="bi bi-exclamation-triangle-fill text-danger fs-4" />
                        </span>
                    </div>
                    <h6 className="fw-bold mb-2">{title}</h6>
                    <p className="small mb-4">{message}</p>
                    <div className="d-flex gap-2 justify-content-center">
                        <button className="btn btn-danger rounded-pill px-4" onClick={onConfirm}>حذف</button>
                        <button className="btn btn-outline-secondary rounded-pill px-4" onClick={onCancel}>انصراف</button>
                    </div>
                </div>
            </motion.div>
        </motion.div>
    );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function AdminQuizBuilderPage() {
    const params = useParams();
    const router = useRouter();
    const quizId = params.id as string;
    const { user, isAuthenticated } = useAuth();

    const [quiz, setQuiz] = useState<QuizAdmin | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);

    const [editForm, setEditForm] = useState({
        title: "",
        description: "",
        difficulty: "medium",
        is_active: true,
        max_attempts_per_user: 0,
        randomize_question_order: false,
        reveal_answers_during_quiz: false,
        allow_retry_on_expiry: true,
    });
    const [thumbnailFile, setThumbnailFile] = useState<File | null>(null);
    const thumbnailInputRef = useRef<HTMLInputElement>(null);

    // Category state
    const [allCategories, setAllCategories] = useState<QuizCategory[]>([]);
    const [selectedCategoryIds, setSelectedCategoryIds] = useState<number[]>([]);
    const [savingCategories, setSavingCategories] = useState(false);
    const [newCatName, setNewCatName] = useState("");
    const [newCatSlug, setNewCatSlug] = useState("");
    const [creatingCat, setCreatingCat] = useState(false);

    // Question form
    const [showQuestionForm, setShowQuestionForm] = useState(false);
    const [editingQuestionId, setEditingQuestionId] = useState<string | null>(null);
    const [questionForm, setQuestionForm] = useState<QuestionFormState>({
        type: "multiple_choice",
        text: "",
        score: 1,
        time_to_answer: 30,
        options: EMPTY_MC_OPTIONS.map((o) => ({ ...o })),
        pairs: EMPTY_PAIRS.map((p) => ({ ...p })),
        imageFile: null,
    });
    const [savingQuestion, setSavingQuestion] = useState(false);
    const imageInputRef = useRef<HTMLInputElement>(null);
    const [deleteQuestionTarget, setDeleteQuestionTarget] = useState<string | null>(null);

    // Access requirements
    const [reqForm, setReqForm] = useState<AccessRequirementPayload>({ type: "free" });
    const [savingReq, setSavingReq] = useState(false);
    const [deletingReqId, setDeletingReqId] = useState<number | null>(null);

    // Participants
    const [participants, setParticipants] = useState<QuizParticipant[]>([]);

    useEffect(() => {
        if (!isAuthenticated) {
            router.replace(`/auth/login?next=/quiz/admin/${quizId}`);
            return;
        }
        if (!(user as any)?.is_staff) {
            router.replace("/dashboard");
            return;
        }
        loadQuiz();
        quizManager.fetchAdminCategories().then((res) => {
            if (res.success && res.categories) setAllCategories(res.categories);
        });
        quizManager.fetchQuizParticipants(quizId).then((res) => {
            if (res.success && res.participants) setParticipants(res.participants);
        });
    }, [isAuthenticated, user]);

    const loadQuiz = async () => {
        setIsLoading(true);
        const res = await quizManager.fetchAdminQuizDetail(quizId);
        if (res.success && res.quiz) {
            setQuiz(res.quiz);
            setEditForm({
                title: res.quiz.title,
                description: res.quiz.description || "",
                difficulty: res.quiz.difficulty,
                is_active: res.quiz.is_active,
                max_attempts_per_user: res.quiz.max_attempts_per_user ?? 0,
                randomize_question_order: res.quiz.randomize_question_order ?? false,
                reveal_answers_during_quiz: res.quiz.reveal_answers_during_quiz ?? false,
                allow_retry_on_expiry: res.quiz.allow_retry_on_expiry ?? true,
            });
            setSelectedCategoryIds(res.quiz.categories.map((c) => c.id));
        } else {
            toast.error("آزمون یافت نشد.");
            router.push("/quiz/admin");
        }
        setIsLoading(false);
    };

    // ── Quiz settings save ─────────────────────────────────────────────────────

    const handleSaveQuiz = async () => {
        setIsSaving(true);
        const res = await quizManager.updateQuiz(quizId, {
            ...(editForm as any),
            thumbnail: thumbnailFile ?? undefined,
        });
        setIsSaving(false);
        if (res.success) {
            toast.success("تغییرات ذخیره شد.");
            setThumbnailFile(null);
            if (res.quiz) {
                setQuiz(res.quiz);
                setEditForm({
                    title: res.quiz.title,
                    description: res.quiz.description || "",
                    difficulty: res.quiz.difficulty,
                    is_active: res.quiz.is_active,
                    max_attempts_per_user: res.quiz.max_attempts_per_user ?? 0,
                    randomize_question_order: res.quiz.randomize_question_order ?? false,
                    reveal_answers_during_quiz: res.quiz.reveal_answers_during_quiz ?? false,
                    allow_retry_on_expiry: res.quiz.allow_retry_on_expiry ?? true,
                });
            }
        } else {
            toast.error(res.message || "خطا در ذخیره");
        }
    };

    // ── Category handlers ──────────────────────────────────────────────────────

    const handleSaveCategories = async () => {
        setSavingCategories(true);
        const res = await quizManager.updateQuiz(quizId, { categories: selectedCategoryIds });
        setSavingCategories(false);
        if (res.success) {
            toast.success("دسته‌بندی‌ها ذخیره شد.");
            if (res.quiz) {
                setQuiz((prev) => prev ? { ...prev, categories: res.quiz!.categories } : prev);
                setSelectedCategoryIds(res.quiz.categories.map((c) => c.id));
            }
        } else {
            toast.error(res.message || "خطا در ذخیره دسته‌بندی‌ها");
        }
    };

    const handleCreateCategory = async () => {
        if (!newCatName.trim() || !newCatSlug.trim()) {
            toast.error("نام و اسلاگ الزامی است.");
            return;
        }
        setCreatingCat(true);
        const res = await quizManager.createAdminCategory(newCatName.trim(), newCatSlug.trim());
        setCreatingCat(false);
        if (res.success && res.category) {
            setAllCategories((prev) => [...prev, res.category!]);
            setNewCatName("");
            setNewCatSlug("");
            toast.success("دسته‌بندی ایجاد شد.");
        } else {
            const errMsg = typeof res.message === "object"
                ? (Object.values(res.message as any)[0] as string)
                : (res.message || "خطا در ایجاد دسته‌بندی");
            toast.error(errMsg);
        }
    };

    // ── Question form ──────────────────────────────────────────────────────────

    const openNewQuestion = () => {
        setEditingQuestionId(null);
        setQuestionForm({
            type: "multiple_choice",
            text: "",
            score: 1,
            time_to_answer: 30,
            options: EMPTY_MC_OPTIONS.map((o) => ({ ...o })),
            pairs: EMPTY_PAIRS.map((p) => ({ ...p })),
            imageFile: null,
        });
        setShowQuestionForm(true);
    };

    const openEditQuestion = (q: QuestionAdmin) => {
        setEditingQuestionId(q.id);
        setQuestionForm({
            type: q.type as any,
            text: q.text,
            score: q.score,
            time_to_answer: q.time_to_answer,
            options: q.options.map((o) => ({ text: o.text, is_correct: (o as any).is_correct, order: o.order })),
            pairs: q.pairs && q.pairs.length > 0
                ? q.pairs.map((p: MatchingPairAdmin) => ({ left_text: p.left_text, right_text: p.right_text }))
                : EMPTY_PAIRS.map((p) => ({ ...p })),
            imageFile: null,
        });
        setShowQuestionForm(true);
    };

    const handleTypeChange = (newType: string) => {
        setQuestionForm((prev) => ({
            ...prev,
            type: newType as any,
            options: buildDefaultOptions(newType),
            pairs: newType === "matching" ? EMPTY_PAIRS.map((p) => ({ ...p })) : prev.pairs,
        }));
    };

    const handlePairText = (idx: number, side: "left_text" | "right_text", text: string) => {
        setQuestionForm((prev) => ({
            ...prev,
            pairs: prev.pairs.map((p, i) => i === idx ? { ...p, [side]: text } : p),
        }));
    };

    const handleAddPair = () => {
        setQuestionForm((prev) => ({
            ...prev,
            pairs: [...prev.pairs, { left_text: "", right_text: "" }],
        }));
    };

    const handleRemovePair = (idx: number) => {
        setQuestionForm((prev) => ({
            ...prev,
            pairs: prev.pairs.filter((_, i) => i !== idx),
        }));
    };

    const handleSetCorrect = (idx: number) => {
        setQuestionForm((prev) => ({
            ...prev,
            options: prev.options.map((o, i) => ({ ...o, is_correct: i === idx })),
        }));
    };

    const handleOptionText = (idx: number, text: string) => {
        setQuestionForm((prev) => ({
            ...prev,
            options: prev.options.map((o, i) => (i === idx ? { ...o, text } : o)),
        }));
    };

    const handleSaveQuestion = async () => {
        if (!questionForm.text.trim()) { toast.error("متن سوال الزامی است."); return; }
        if (questionForm.type === "matching") {
            if (questionForm.pairs.length < 2) { toast.error("حداقل ۲ جفت لازم است."); return; }
            if (questionForm.pairs.some((p) => !p.left_text.trim() || !p.right_text.trim())) {
                toast.error("متن همه جفت‌ها الزامی است."); return;
            }
        } else {
            if (questionForm.type !== "true_false" && questionForm.options.some((o) => !o.text.trim())) {
                toast.error("متن همه گزینه‌ها الزامی است."); return;
            }
            if (!questionForm.options.some((o) => o.is_correct)) {
                toast.error("باید یک گزینه صحیح انتخاب شود."); return;
            }
        }

        setSavingQuestion(true);
        const payload: CreateQuestionPayload = {
            type: questionForm.type,
            text: questionForm.text,
            score: questionForm.score,
            time_to_answer: questionForm.time_to_answer,
            options: questionForm.type === "matching" ? [] : questionForm.options,
            pairs: questionForm.type === "matching" ? questionForm.pairs : undefined,
            image: questionForm.imageFile,
        };

        const res = editingQuestionId
            ? await quizManager.updateQuestion(editingQuestionId, payload)
            : await quizManager.createQuestion(quizId, payload);

        setSavingQuestion(false);
        if (res.success) {
            toast.success(editingQuestionId ? "سوال ویرایش شد." : "سوال اضافه شد.");
            setShowQuestionForm(false);
            if (res.question) {
                const savedId = editingQuestionId;
                setQuiz((prev) => {
                    if (!prev) return prev;
                    const qs = prev.questions || [];
                    return {
                        ...prev,
                        questions: savedId
                            ? qs.map((q) => q.id === savedId ? res.question! : q)
                            : [...qs, res.question!],
                    };
                });
            }
        } else {
            toast.error(res.message || "خطا در ذخیره سوال");
        }
    };

    const handleDeleteQuestionConfirmed = async () => {
        if (!deleteQuestionTarget) return;
        const qid = deleteQuestionTarget;
        const res = await quizManager.deleteQuestion(qid);
        setDeleteQuestionTarget(null);
        if (res.success) {
            toast.success("سوال حذف شد.");
            setQuiz((prev) => prev ? { ...prev, questions: (prev.questions || []).filter((q) => q.id !== qid) } : prev);
        } else {
            toast.error(res.message || "خطا در حذف سوال");
        }
    };

    const handleMoveQuestion = async (questions: QuestionAdmin[], idx: number, dir: -1 | 1) => {
        const newIdx = idx + dir;
        if (newIdx < 0 || newIdx >= questions.length) return;
        const reordered = [...questions];
        [reordered[idx], reordered[newIdx]] = [reordered[newIdx], reordered[idx]];
        const items = reordered.map((q, i) => ({ id: q.id, order: i }));
        const res = await quizManager.reorderQuestions(items);
        if (res.success) {
            const updatedQuestions = reordered.map((q, i) => ({ ...q, order: i }));
            setQuiz((prev) => prev ? { ...prev, questions: updatedQuestions } : prev);
        } else {
            toast.error("خطا در ترتیب‌بندی سوالات");
        }
    };

    // ── Access requirements ────────────────────────────────────────────────────

    const handleAddRequirement = async () => {
        const requirements: AccessRequirement[] = (quiz?.access_requirements || []);
        if (requirements.some((r) => r.type === reqForm.type)) {
            toast.warning("این نوع شرط دسترسی قبلاً تعریف شده است.");
            return;
        }
        setSavingReq(true);
        const res = await quizManager.createAccessRequirement(quizId, reqForm);
        setSavingReq(false);
        if (res.success) {
            toast.success("شرط دسترسی اضافه شد.");
            setReqForm({ type: "free" });
            if (res.requirement) {
                setQuiz((prev) => prev ? {
                    ...prev,
                    access_requirements: [...(prev.access_requirements || []), res.requirement!],
                } : prev);
            }
        } else {
            const errMsg = typeof res.message === "object"
                ? (Object.values(res.message as any)[0] as string)
                : (res.message || "خطا در افزودن شرط دسترسی");
            toast.error(errMsg);
        }
    };

    const handleDeleteRequirement = async (reqId: number) => {
        setDeletingReqId(reqId);
        const res = await quizManager.deleteAccessRequirement(reqId);
        setDeletingReqId(null);
        if (res.success) {
            toast.success("شرط دسترسی حذف شد.");
            setQuiz((prev) => prev ? {
                ...prev,
                access_requirements: (prev.access_requirements || []).filter((r) => r.id !== reqId),
            } : prev);
        } else {
            toast.error(res.message || "خطا در حذف شرط دسترسی");
        }
    };

    // ── Render ─────────────────────────────────────────────────────────────────

    if (isLoading) {
        return (
            <div className="d-flex justify-content-center align-items-center" style={{ minHeight: "60vh" }}>
                <div className="spinner-border text-primary" role="status">
                    <span className="visually-hidden">در حال بارگذاری...</span>
                </div>
            </div>
        );
    }
    if (!quiz) return null;

    const questions: QuestionAdmin[] = (quiz.questions || []).slice().sort((a, b) => a.order - b.order);
    const requirements: AccessRequirement[] = (quiz.access_requirements || []);
    const otherQuizzes = quizManager.getAdminQuizzes().filter((q) => q.id !== quizId);

    return (
        <main className="py-5">
            <div className="container">
                <div className="d-flex align-items-center gap-3 mb-4">
                    <a href="/quiz/admin" className="btn btn-outline-secondary btn-sm">
                        <i className="bi bi-arrow-right me-1"></i>بازگشت
                    </a>
                    <h2 className="fw-bold mb-0 fs-4">{quiz.title}</h2>
                </div>

                <div className="row g-4">
                    {/* ── Quiz settings ─────────────────────────────────────── */}
                    <div className="col-lg-5">
                        <div className="card border-0 shadow-sm">
                            <div className="card-header bg-transparent border-bottom">
                                <h5 className="mb-0">تنظیمات آزمون</h5>
                            </div>
                            <div className="card-body p-4">
                                <div className="mb-3">
                                    <label className="form-label">عنوان</label>
                                    <input type="text" className="form-control" value={editForm.title} onChange={(e) => setEditForm({ ...editForm, title: e.target.value })} />
                                </div>
                                <div className="mb-3">
                                    <label className="form-label">توضیحات</label>
                                    <textarea className="form-control" rows={3} value={editForm.description} onChange={(e) => setEditForm({ ...editForm, description: e.target.value })} />
                                </div>

                                {/* Thumbnail */}
                                <div className="mb-3">
                                    <label className="form-label">بنر</label>
                                    <div
                                        className="border rounded-3 p-3 text-center"
                                        style={{ cursor: "pointer", minHeight: 72 }}
                                        onClick={() => thumbnailInputRef.current?.click()}
                                    >
                                        {thumbnailFile ? (
                                            <div className="d-flex align-items-center gap-2 justify-content-center">
                                                <img src={URL.createObjectURL(thumbnailFile)} alt="" className="rounded" style={{ width: 56, height: 40, objectFit: "cover" }} />
                                                <span className="small">{thumbnailFile.name}</span>
                                            </div>
                                        ) : quiz.thumbnail ? (
                                            <div className="d-flex align-items-center gap-2 justify-content-center">
                                                <img src={getMediaUrl(quiz.thumbnail)} alt="" className="rounded" style={{ width: 56, height: 40, objectFit: "cover" }} />
                                                <span className="small">کلیک برای تغییر</span>
                                            </div>
                                        ) : (
                                            <span className="small"><i className="bi bi-image me-2"></i>کلیک کنید تا تصویر انتخاب کنید</span>
                                        )}
                                    </div>
                                    <input type="file" ref={thumbnailInputRef} className="d-none" accept="image/*" onChange={(e) => setThumbnailFile(e.target.files?.[0] ?? null)} />
                                </div>

                                <div className="row g-3 mb-3">
                                    <div className="col-6">
                                        <label className="form-label">سختی</label>
                                        <select className="form-select" value={editForm.difficulty} onChange={(e) => setEditForm({ ...editForm, difficulty: e.target.value })}>
                                            <option value="easy">آسان</option>
                                            <option value="medium">متوسط</option>
                                            <option value="hard">سخت</option>
                                        </select>
                                    </div>
                                    <div className="col-6">
                                        <label className="form-label">حداکثر تلاش</label>
                                        <input type="number" className="form-control" min={0} value={editForm.max_attempts_per_user} onChange={(e) => setEditForm({ ...editForm, max_attempts_per_user: Number(e.target.value) })} />
                                        <small>۰ = نامحدود</small>
                                    </div>
                                </div>
                                <div className="d-flex flex-column gap-2 mb-4">
                                    <div className="form-check form-switch">
                                        <input className="form-check-input" type="checkbox" id="ea_active" checked={editForm.is_active} onChange={(e) => setEditForm({ ...editForm, is_active: e.target.checked })} />
                                        <label className="form-check-label" htmlFor="ea_active">فعال</label>
                                    </div>
                                    <div className="form-check form-switch">
                                        <input className="form-check-input" type="checkbox" id="ea_rand" checked={editForm.randomize_question_order} onChange={(e) => setEditForm({ ...editForm, randomize_question_order: e.target.checked })} />
                                        <label className="form-check-label" htmlFor="ea_rand">ترتیب تصادفی سوالات</label>
                                    </div>
                                    <div className="form-check form-switch">
                                        <input className="form-check-input" type="checkbox" id="ea_rev" checked={editForm.reveal_answers_during_quiz} onChange={(e) => setEditForm({ ...editForm, reveal_answers_during_quiz: e.target.checked })} />
                                        <label className="form-check-label" htmlFor="ea_rev">نمایش پاسخ حین آزمون</label>
                                    </div>
                                    <div className="form-check form-switch">
                                        <input className="form-check-input" type="checkbox" id="ea_retry" checked={editForm.allow_retry_on_expiry} onChange={(e) => setEditForm({ ...editForm, allow_retry_on_expiry: e.target.checked })} />
                                        <label className="form-check-label" htmlFor="ea_retry">تلاش مجدد پس از اتمام زمان</label>
                                    </div>
                                </div>
                                <button className="btn btn-primary w-100" onClick={handleSaveQuiz} disabled={isSaving}>
                                    {isSaving ? <><span className="spinner-border spinner-border-sm me-2"></span>در حال ذخیره...</> : <><i className="bi bi-check-lg me-2"></i>ذخیره تغییرات</>}
                                </button>
                            </div>
                        </div>

                        {/* ── Categories ───────────────────────────────────── */}
                        <div className="card border-0 shadow-sm mt-4">
                            <div className="card-header bg-transparent border-bottom">
                                <h5 className="mb-0">دسته‌بندی‌ها</h5>
                            </div>
                            <div className="card-body p-4">
                                {allCategories.length > 0 ? (
                                    <div className="d-flex flex-column gap-2 mb-3">
                                        {allCategories.map((cat) => (
                                            <div key={cat.id} className="form-check">
                                                <input
                                                    type="checkbox"
                                                    className="form-check-input"
                                                    id={`cat-${cat.id}`}
                                                    checked={selectedCategoryIds.includes(cat.id)}
                                                    onChange={(e) => {
                                                        if (e.target.checked) {
                                                            setSelectedCategoryIds((prev) => [...prev, cat.id]);
                                                        } else {
                                                            setSelectedCategoryIds((prev) => prev.filter((id) => id !== cat.id));
                                                        }
                                                    }}
                                                />
                                                <label className="form-check-label" htmlFor={`cat-${cat.id}`}>{cat.name}</label>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="small mb-3">هیچ دسته‌بندی‌ای وجود ندارد</p>
                                )}

                                <button className="btn btn-sm btn-outline-primary w-100 mb-3" onClick={handleSaveCategories} disabled={savingCategories}>
                                    {savingCategories ? <><span className="spinner-border spinner-border-sm me-2"></span>در حال ذخیره...</> : <><i className="bi bi-check-lg me-1"></i>ذخیره دسته‌بندی‌ها</>}
                                </button>

                                <div className="border rounded-3 p-3 bg-light">
                                    <div className="small fw-semibold mb-2">دسته‌بندی جدید</div>
                                    <div className="mb-2">
                                        <input
                                            type="text"
                                            className="form-control form-control-sm"
                                            placeholder="نام دسته‌بندی"
                                            value={newCatName}
                                            onChange={(e) => setNewCatName(e.target.value)}
                                        />
                                    </div>
                                    <div className="mb-2">
                                        <input
                                            type="text"
                                            className="form-control form-control-sm"
                                            placeholder="اسلاگ (انگلیسی، مثال: programming)"
                                            value={newCatSlug}
                                            onChange={(e) => setNewCatSlug(e.target.value)}
                                        />
                                    </div>
                                    <button className="btn btn-sm btn-success w-100" onClick={handleCreateCategory} disabled={creatingCat}>
                                        {creatingCat ? <span className="spinner-border spinner-border-sm"></span> : <><i className="bi bi-plus-lg me-1"></i>ایجاد دسته‌بندی</>}
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* ── Access requirements ──────────────────────────── */}
                        <div className="card border-0 shadow-sm mt-4">
                            <div className="card-header bg-transparent border-bottom">
                                <h5 className="mb-0">شرایط دسترسی</h5>
                            </div>
                            <div className="card-body p-4">
                                {requirements.length === 0 ? (
                                    <p className="small mb-3">هیچ شرطی تعریف نشده (آزاد برای همه)</p>
                                ) : (
                                    <div className="d-flex flex-column gap-2 mb-3">
                                        {requirements.map((req) => (
                                            <div key={req.id} className="d-flex align-items-center justify-content-between border rounded-3 px-3 py-2 small">
                                                <div>
                                                    <span className="badge bg-primary bg-opacity-10 text-primary me-2">{REQ_TYPE_LABELS[req.type] ?? req.type}</span>
                                                    {req.required_quiz && <span>{req.required_quiz.title}</span>}
                                                    {req.required_score != null && <span className="ms-1">(حداقل {new Intl.NumberFormat("fa-IR").format(req.required_score)} امتیاز)</span>}
                                                </div>
                                                <button
                                                    className="btn btn-sm btn-outline-danger py-0 px-2"
                                                    onClick={() => handleDeleteRequirement(req.id)}
                                                    disabled={deletingReqId === req.id}
                                                >
                                                    {deletingReqId === req.id ? <span className="spinner-border spinner-border-sm"></span> : <i className="bi bi-x-lg"></i>}
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {/* Add requirement form */}
                                <div className="border rounded-3 p-3 bg-light">
                                    <div className="small fw-semibold mb-2">افزودن شرط جدید</div>
                                    <div className="mb-2">
                                        <select
                                            className="form-select form-select-sm"
                                            value={reqForm.type}
                                            onChange={(e) => setReqForm({ type: e.target.value as any })}
                                        >
                                            <option value="free">آزاد</option>
                                            <option value="subscription">نیاز به اشتراک فعال</option>
                                            <option value="completed_quiz">تکمیل آزمون دیگر</option>
                                            <option value="min_score">حداقل امتیاز کل کاربر</option>
                                        </select>
                                    </div>
                                    {reqForm.type === "completed_quiz" && (
                                        <div className="mb-2">
                                            <select
                                                className="form-select form-select-sm"
                                                value={reqForm.required_quiz_id ?? ""}
                                                onChange={(e) => setReqForm({ ...reqForm, required_quiz_id: e.target.value || null })}
                                            >
                                                <option value="">انتخاب آزمون پیش‌نیاز...</option>
                                                {otherQuizzes.map((q) => (
                                                    <option key={q.id} value={q.id}>{q.title}</option>
                                                ))}
                                            </select>
                                        </div>
                                    )}
                                    {reqForm.type === "min_score" && (
                                        <div className="mb-2">
                                            <input
                                                type="number"
                                                className="form-control form-control-sm"
                                                placeholder="حداقل امتیاز کل کاربر"
                                                min={1}
                                                value={reqForm.required_score ?? ""}
                                                onChange={(e) => setReqForm({ ...reqForm, required_score: e.target.value ? Number(e.target.value) : null })}
                                            />
                                        </div>
                                    )}
                                    <button className="btn btn-sm btn-primary w-100" onClick={handleAddRequirement} disabled={savingReq}>
                                        {savingReq ? <span className="spinner-border spinner-border-sm me-2"></span> : <i className="bi bi-plus-lg me-1"></i>}
                                        افزودن شرط
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* ── Questions ─────────────────────────────────────────── */}
                    <div className="col-lg-7">
                        <div className="card border-0 shadow-sm">
                            <div className="card-header bg-transparent border-bottom d-flex align-items-center justify-content-between">
                                <h5 className="mb-0">
                                    سوالات
                                    <span className="badge bg-primary ms-2">{new Intl.NumberFormat("fa-IR").format(questions.length)}</span>
                                </h5>
                                <button className="btn btn-sm btn-primary" onClick={openNewQuestion}>
                                    <i className="bi bi-plus-lg me-1"></i>افزودن سوال
                                </button>
                            </div>
                            <div className="card-body p-3">
                                {questions.length === 0 ? (
                                    <div className="text-center py-5">
                                        <i className="bi bi-question-circle fs-1 mb-3 d-block"></i>
                                        <p>هنوز سوالی اضافه نشده است</p>
                                    </div>
                                ) : (
                                    <div className="d-flex flex-column gap-2">
                                        {questions.map((q, idx) => (
                                            <motion.div key={q.id} className="border rounded-3 p-3" variants={fadeInUp} initial="hidden" animate="show">
                                                <div className="d-flex align-items-start gap-2">
                                                    <div className="d-flex flex-column gap-1">
                                                        <button className="btn btn-outline-secondary btn-sm py-0 px-1" onClick={() => handleMoveQuestion(questions, idx, -1)} disabled={idx === 0}>
                                                            <i className="bi bi-chevron-up small"></i>
                                                        </button>
                                                        <button className="btn btn-outline-secondary btn-sm py-0 px-1" onClick={() => handleMoveQuestion(questions, idx, 1)} disabled={idx === questions.length - 1}>
                                                            <i className="bi bi-chevron-down small"></i>
                                                        </button>
                                                    </div>
                                                    <div className="flex-grow-1">
                                                        <div className="d-flex align-items-center gap-2 mb-1 flex-wrap">
                                                            <span className="badge bg-secondary bg-opacity-25 text-dark small">{QUESTION_TYPE_LABELS[q.type] ?? q.type}</span>
                                                            <span className="small"><i className="bi bi-star me-1"></i>{new Intl.NumberFormat("fa-IR").format(q.score)} امتیاز</span>
                                                            <span className="small"><i className="bi bi-clock me-1"></i>{new Intl.NumberFormat("fa-IR").format(q.time_to_answer)} ثانیه</span>
                                                            {(q as any).image && <span className="badge bg-info bg-opacity-10 text-info small"><i className="bi bi-image me-1"></i>تصویر</span>}
                                                        </div>
                                                        <p className="mb-1 small">{q.text.length > 120 ? q.text.slice(0, 120) + "..." : q.text}</p>
                                                        <div className="d-flex flex-wrap gap-1">
                                                            {q.type === "matching" ? (
                                                                q.pairs && q.pairs.length > 0 ? (
                                                                    <span className="badge bg-info bg-opacity-15 text-info small">
                                                                        <i className="bi bi-arrow-left-right me-1"></i>
                                                                        {new Intl.NumberFormat("fa-IR").format(q.pairs.length)} جفت
                                                                    </span>
                                                                ) : (
                                                                    <span className="badge bg-warning bg-opacity-15 text-warning small">بدون جفت</span>
                                                                )
                                                            ) : (
                                                                q.options.map((o) => (
                                                                    <span key={o.id} className={`badge ${(o as any).is_correct ? "bg-success" : "bg-light text-dark border"} small`}>
                                                                        {o.text.length > 30 ? o.text.slice(0, 30) + "…" : o.text}
                                                                        {(o as any).is_correct && <i className="bi bi-check-lg ms-1"></i>}
                                                                    </span>
                                                                ))
                                                            )}
                                                        </div>
                                                    </div>
                                                    <div className="d-flex gap-1 flex-shrink-0">
                                                        <button className="btn btn-sm btn-outline-primary" onClick={() => openEditQuestion(q)}><i className="bi bi-pencil"></i></button>
                                                        <button className="btn btn-sm btn-outline-danger" onClick={() => setDeleteQuestionTarget(q.id)}><i className="bi bi-trash"></i></button>
                                                    </div>
                                                </div>
                                            </motion.div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* ── Participants ───────────────────────────────────── */}
                        <div className="card border-0 shadow-sm mt-4">
                            <div className="card-header bg-transparent border-bottom d-flex align-items-center justify-content-between">
                                <h5 className="mb-0">
                                    <i className="bi bi-people me-2 text-primary"></i>
                                    شرکت‌کنندگان
                                    <span className="badge bg-secondary ms-2">{participants.length}</span>
                                </h5>
                            </div>
                            <div className="card-body">
                                {participants.length === 0 ? (
                                    <div className="text-center py-5">
                                        <i className="bi bi-people fs-1 text-muted mb-3 d-block"></i>
                                        <p className="text-muted">هنوز کسی در این آزمون شرکت نکرده است</p>
                                    </div>
                                ) : (
                                    <div className="table-responsive border-0">
                                        <table className="table table-dark-gray align-middle p-4 mb-0 table-hover">
                                            <thead>
                                                <tr>
                                                    <th scope="col" className="border-0 rounded-start">کاربر</th>
                                                    <th scope="col" className="border-0">امتیاز</th>
                                                    <th scope="col" className="border-0">درست / غلط</th>
                                                    <th scope="col" className="border-0">مدت زمان</th>
                                                    <th scope="col" className="border-0 rounded-end">تاریخ</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {participants.map((p, idx) => (
                                                    <tr key={`${p.user_id}-${idx}`}>
                                                        <td>
                                                            <div className="fw-semibold">{p.username}</div>
                                                        </td>
                                                        <td>
                                                            <span className="text-primary fw-bold">
                                                                {new Intl.NumberFormat("fa-IR").format(p.score)}
                                                            </span>
                                                        </td>
                                                        <td>
                                                            <span className="text-success me-1">
                                                                <i className="bi bi-check-circle me-1"></i>
                                                                {new Intl.NumberFormat("fa-IR").format(p.correct_count)}
                                                            </span>
                                                            <span className="text-muted">/</span>
                                                            <span className="text-danger ms-1">
                                                                <i className="bi bi-x-circle me-1"></i>
                                                                {new Intl.NumberFormat("fa-IR").format(p.incorrect_count)}
                                                            </span>
                                                        </td>
                                                        <td className="text-nowrap">
                                                            <i className="bi bi-clock me-1 text-muted"></i>
                                                            {Math.floor(p.time_spent / 60)}:{String(p.time_spent % 60).padStart(2, "0")}
                                                        </td>
                                                        <td className="text-nowrap">
                                                            {p.finished_at
                                                                ? toJalali(p.finished_at.split("T")[0])
                                                                : "—"
                                                            }
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* ── Question form modal ────────────────────────────────────────── */}
            <AnimatePresence>
                {showQuestionForm && (
                    <motion.div
                        className="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center"
                        style={{ zIndex: 1050, background: "rgba(0,0,0,0.5)" }}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={(e) => e.target === e.currentTarget && setShowQuestionForm(false)}
                    >
                        <motion.div
                            className="card border-0 shadow-lg"
                            style={{ width: "min(700px, 95vw)", maxHeight: "90vh", overflowY: "auto" }}
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                        >
                            <div className="card-header bg-primary text-white d-flex align-items-center justify-content-between">
                                <h5 className="mb-0">{editingQuestionId ? "ویرایش سوال" : "افزودن سوال جدید"}</h5>
                                <button className="btn btn-close btn-close-white" onClick={() => setShowQuestionForm(false)}></button>
                            </div>
                            <div className="card-body p-4">
                                <div className="row g-3 mb-3">
                                    <div className="col-md-4">
                                        <label className="form-label">نوع سوال</label>
                                        <select className="form-select" value={questionForm.type} onChange={(e) => handleTypeChange(e.target.value)}>
                                            <option value="multiple_choice">چند گزینه‌ای</option>
                                            <option value="fill_blank">جای خالی</option>
                                            <option value="true_false">صحیح / غلط</option>
                                            <option value="matching">وصل کردن</option>
                                        </select>
                                    </div>
                                    <div className="col-md-4">
                                        <label className="form-label">امتیاز</label>
                                        <input type="number" className="form-control" min={1} value={questionForm.score} onChange={(e) => setQuestionForm({ ...questionForm, score: Number(e.target.value) })} />
                                    </div>
                                    <div className="col-md-4">
                                        <label className="form-label">زمان (ثانیه)</label>
                                        <input type="number" className="form-control" min={5} value={questionForm.time_to_answer} onChange={(e) => setQuestionForm({ ...questionForm, time_to_answer: Number(e.target.value) })} />
                                    </div>
                                </div>
                                <div className="mb-3">
                                    <label className="form-label">متن سوال <span className="text-danger">*</span></label>
                                    <textarea
                                        className="form-control"
                                        rows={3}
                                        value={questionForm.text}
                                        onChange={(e) => setQuestionForm({ ...questionForm, text: e.target.value })}
                                        placeholder="متن سوال را وارد کنید..."
                                    />
                                </div>

                                {/* Question image */}
                                <div className="mb-3">
                                    <label className="form-label">تصویر سوال (اختیاری)</label>
                                    <div
                                        className="border rounded-3 p-3 text-center"
                                        style={{ cursor: "pointer", minHeight: 64 }}
                                        onClick={() => imageInputRef.current?.click()}
                                    >
                                        {questionForm.imageFile ? (
                                            <div className="d-flex align-items-center gap-2 justify-content-center">
                                                <img src={URL.createObjectURL(questionForm.imageFile)} alt="" className="rounded" style={{ width: 80, height: 52, objectFit: "cover" }} />
                                                <span className="small">{questionForm.imageFile.name}</span>
                                            </div>
                                        ) : editingQuestionId && (quiz.questions?.find((q) => q.id === editingQuestionId) as any)?.image ? (
                                            <div className="d-flex align-items-center gap-2 justify-content-center">
                                                <img src={getMediaUrl((quiz.questions?.find((q) => q.id === editingQuestionId) as any).image)} alt="" className="rounded" style={{ width: 80, height: 52, objectFit: "cover" }} />
                                                <span className="small">کلیک برای تغییر</span>
                                            </div>
                                        ) : (
                                            <span className="small"><i className="bi bi-image me-2"></i>کلیک کنید تا تصویر انتخاب کنید</span>
                                        )}
                                    </div>
                                    <input type="file" ref={imageInputRef} className="d-none" accept="image/*" onChange={(e) => setQuestionForm({ ...questionForm, imageFile: e.target.files?.[0] ?? null })} />
                                </div>

                                {/* Options / Pairs */}
                                {questionForm.type === "matching" ? (
                                    <div className="mb-3">
                                        <label className="form-label mb-2">
                                            جفت‌ها
                                            <small className="ms-2">(هر سطر یک جفت: سمت راست ↔ سمت چپ)</small>
                                        </label>
                                        <div className="d-flex flex-column gap-2">
                                            {questionForm.pairs.map((pair, idx) => (
                                                <div key={idx} className="d-flex align-items-center gap-2">
                                                    <input
                                                        type="text"
                                                        className="form-control form-control-sm"
                                                        placeholder={`سمت راست ${idx + 1}`}
                                                        value={pair.left_text}
                                                        onChange={(e) => handlePairText(idx, "left_text", e.target.value)}
                                                    />
                                                    <i className="bi bi-arrows-expand-vertical text-muted flex-shrink-0" />
                                                    <input
                                                        type="text"
                                                        className="form-control form-control-sm"
                                                        placeholder={`سمت چپ ${idx + 1}`}
                                                        value={pair.right_text}
                                                        onChange={(e) => handlePairText(idx, "right_text", e.target.value)}
                                                    />
                                                    <button
                                                        className="btn btn-outline-danger btn-sm flex-shrink-0"
                                                        onClick={() => handleRemovePair(idx)}
                                                        disabled={questionForm.pairs.length <= 2}
                                                        title="حذف جفت"
                                                    >
                                                        <i className="bi bi-trash" />
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                        <button className="btn btn-outline-primary btn-sm mt-2" onClick={handleAddPair}>
                                            <i className="bi bi-plus-circle me-1" />افزودن جفت
                                        </button>
                                    </div>
                                ) : (
                                    <div className="mb-3">
                                        <label className="form-label mb-2">
                                            گزینه‌ها
                                            <small className="ms-2">(گزینه صحیح را علامت‌گذاری کنید)</small>
                                        </label>
                                        <div className="d-flex flex-column gap-2">
                                            {questionForm.options.map((opt, idx) => (
                                                <div key={idx} className="d-flex align-items-center gap-2">
                                                    <div className="form-check mb-0">
                                                        <input
                                                            type="radio"
                                                            className="form-check-input"
                                                            name="correct_option"
                                                            id={`opt-${idx}`}
                                                            checked={opt.is_correct}
                                                            onChange={() => handleSetCorrect(idx)}
                                                        />
                                                    </div>
                                                    <input
                                                        type="text"
                                                        className={`form-control form-control-sm ${opt.is_correct ? "border-success" : ""}`}
                                                        placeholder={`گزینه ${idx + 1}`}
                                                        value={opt.text}
                                                        readOnly={questionForm.type === "true_false"}
                                                        onChange={(e) => handleOptionText(idx, e.target.value)}
                                                    />
                                                    {opt.is_correct && <span className="badge bg-success flex-shrink-0">صحیح</span>}
                                                </div>
                                            ))}
                                        </div>
                                        {questionForm.type === "true_false" && (
                                            <small>برای سوال صحیح/غلط، گزینه‌ها ثابت هستند.</small>
                                        )}
                                    </div>
                                )}

                                <div className="d-flex gap-2 justify-content-end">
                                    <button className="btn btn-outline-secondary" onClick={() => setShowQuestionForm(false)}>انصراف</button>
                                    <button className="btn btn-primary" onClick={handleSaveQuestion} disabled={savingQuestion}>
                                        {savingQuestion ? <><span className="spinner-border spinner-border-sm me-2"></span>در حال ذخیره...</> : <><i className="bi bi-check-lg me-2"></i>ذخیره سوال</>}
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    </motion.div>
                )}

                {deleteQuestionTarget && (
                    <ConfirmDialog
                        title="حذف سوال"
                        message="آیا مطمئن هستید که می‌خواهید این سوال را حذف کنید؟"
                        onConfirm={handleDeleteQuestionConfirmed}
                        onCancel={() => setDeleteQuestionTarget(null)}
                    />
                )}
            </AnimatePresence>
        </main>
    );
}
