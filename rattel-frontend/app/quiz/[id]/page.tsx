"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { toast } from "react-toastify";
import { useQuiz } from "@/src/core/hooks/useQuiz";
import { quizManager, type ActiveAttempt, type FinishResult, type Question } from "@/src/core/quiz/quizManager";
import { useAuth } from "@/src/core/hooks/useAuth";
import { getMediaUrl } from "@/src/core/utils";
import { fadeInUp, scaleIn } from "@/src/core/motionVariants";

type Phase = "loading" | "idle" | "in_progress" | "finished";

const formatTime = (seconds: number): string => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
};

const DIFFICULTY_LABELS: Record<string, string> = {
    easy: "آسان",
    medium: "متوسط",
    hard: "سخت",
};

const QUESTION_TYPE_LABELS: Record<string, string> = {
    multiple_choice: "چند گزینه‌ای",
    fill_blank: "جای خالی",
    true_false: "صحیح / غلط",
    matching: "وصل کردن",
};

const PAIR_COLORS: Array<{ bg: string; text: string; border: string }> = [
    { bg: "#198754", text: "#fff", border: "#198754" },   // green
    { bg: "#0d6efd", text: "#fff", border: "#0d6efd" },   // blue
    { bg: "#e6820a", text: "#fff", border: "#e6820a" },   // orange
    { bg: "#dc3545", text: "#fff", border: "#dc3545" },   // red
    { bg: "#6f42c1", text: "#fff", border: "#6f42c1" },   // purple
    { bg: "#0dcaf0", text: "#000", border: "#0dcaf0" },   // cyan
    { bg: "#d63384", text: "#fff", border: "#d63384" },   // pink
    { bg: "#20c997", text: "#fff", border: "#20c997" },   // teal
    { bg: "#6c757d", text: "#fff", border: "#6c757d" },   // gray
    { bg: "#795548", text: "#fff", border: "#795548" },   // brown
    { bg: "#0a58ca", text: "#fff", border: "#0a58ca" },   // dark blue
    { bg: "#146c43", text: "#fff", border: "#146c43" },   // dark green
    { bg: "#483d8b", text: "#fff", border: "#483d8b" },   // slate purple
    { bg: "#008b8b", text: "#fff", border: "#008b8b" },   // dark cyan
    { bg: "#b5451b", text: "#fff", border: "#b5451b" },   // rust
];

function QuizPlayPage() {
    const params = useParams();
    const router = useRouter();
    const quizId = params.id as string;
    const { isAuthenticated } = useAuth();
    const { currentQuiz, isLoading } = useQuiz();

    const [phase, setPhase] = useState<Phase>("loading");
    const [attempt, setAttempt] = useState<ActiveAttempt | null>(null);
    const [currentQIdx, setCurrentQIdx] = useState(0);
    const [selectedOptionId, setSelectedOptionId] = useState<string | null>(null);
    const [confirmedOptionId, setConfirmedOptionId] = useState<string | null>(null);
    const [revealResult, setRevealResult] = useState<{ is_correct: boolean; correct_option_id: string | null } | null>(null);
    const [timeLeft, setTimeLeft] = useState(0);
    const [totalTime, setTotalTime] = useState(0);
    const [finishResult, setFinishResult] = useState<FinishResult | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isStarting, setIsStarting] = useState(false);
    const [direction, setDirection] = useState(1);

    // Matching question state — array preserves insertion order for stable color assignment
    const [connectionPairs, setConnectionPairs] = useState<Array<{ leftId: string; rightId: string }>>([]);
    const [selectedLeftId, setSelectedLeftId] = useState<string | null>(null);

    const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const questionStartTimeRef = useRef<number>(Date.now());
    const isFinishingRef = useRef(false);

    useEffect(() => {
        quizManager.fetchQuizDetail(quizId).then((res) => {
            if (res.success) {
                setPhase("idle");
            } else {
                toast.error("آزمون یافت نشد.");
                router.push("/quiz");
            }
        });
    }, [quizId]);

    useEffect(() => {
        if (phase !== "in_progress" || !attempt) return;

        timerRef.current = setInterval(() => {
            setTimeLeft((t) => {
                if (t <= 1) {
                    clearInterval(timerRef.current!);
                    timerRef.current = null;
                    return 0;
                }
                return t - 1;
            });
        }, 1000);

        return () => {
            if (timerRef.current) clearInterval(timerRef.current);
        };
    }, [phase, attempt]);

    // Detect timer expiry outside of the state updater to avoid React double-invoke issues
    useEffect(() => {
        if (phase === "in_progress" && timeLeft === 0 && totalTime > 0 && attempt) {
            handleFinish(attempt, true);
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [timeLeft]);

    const handleStart = async () => {
        if (!isAuthenticated) {
            router.push(`/auth/login?next=${encodeURIComponent(`/quiz/${quizId}`)}`);
            return;
        }
        setIsStarting(true);
        const res = await quizManager.startQuiz(quizId);
        setIsStarting(false);
        if (res.success && res.attempt) {
            isFinishingRef.current = false;
            setAttempt(res.attempt);
            setTimeLeft(res.attempt.total_time_seconds);
            setTotalTime(res.attempt.total_time_seconds);
            setCurrentQIdx(0);
            setSelectedOptionId(null);
            setConfirmedOptionId(null);
            setRevealResult(null);
            setConnectionPairs([]);
            setSelectedLeftId(null);
            questionStartTimeRef.current = Date.now();
            setPhase("in_progress");
        } else {
            const msg = res.message || "خطا در شروع آزمون";
            if (res.error === -4) {
                toast.warning("آزمون در حال اجرا دارید. لطفاً تلاش قبلی را تکمیل کنید.");
            } else if (res.error === -5) {
                toast.warning("به حداکثر تعداد مجاز شرکت در این آزمون رسیده‌اید.");
            } else if (res.error === -6) {
                toast.error(msg);
            } else {
                toast.error(msg);
            }
        }
    };

    const handleOptionSelect = (optionId: string) => {
        if (confirmedOptionId !== null) return;
        setSelectedOptionId(optionId);
    };

    const handleLeftClick = (leftId: string) => {
        if (confirmedOptionId !== null) return;
        // Toggle selection: clicking selected left item deselects
        setSelectedLeftId((prev) => prev === leftId ? null : leftId);
    };

    const handleRightClick = (rightId: string) => {
        if (confirmedOptionId !== null) return;
        if (!selectedLeftId) return;
        setConnectionPairs((prev) => {
            // Remove any existing entry for this leftId or this rightId
            const filtered = prev.filter((p) => p.leftId !== selectedLeftId && p.rightId !== rightId);
            return [...filtered, { leftId: selectedLeftId, rightId }];
        });
        setSelectedLeftId(null);
    };

    const handleConfirm = async () => {
        const currentQuestion = attempt?.questions[currentQIdx];
        if (!attempt || !currentQuestion || confirmedOptionId !== null || isSubmitting) return;

        const timeTaken = Math.floor((Date.now() - questionStartTimeRef.current) / 1000);
        setIsSubmitting(true);

        if (currentQuestion.type === "matching") {
            const leftCount = (currentQuestion.left_items ?? []).length;
            if (connectionPairs.length < leftCount) return;
            setConfirmedOptionId("matching_submitted");
            const connectionsMap = Object.fromEntries(connectionPairs.map((p) => [p.leftId, p.rightId]));
            const res = await quizManager.submitAnswer(
                quizId,
                attempt.attempt_id,
                currentQuestion.id,
                null,
                timeTaken,
                connectionsMap,
            );
            setIsSubmitting(false);
            if (attempt.reveal_answers_during_quiz && res.success) {
                setRevealResult({ is_correct: res.is_correct ?? false, correct_option_id: null });
                setTimeout(() => advanceToNext(attempt), 1800);
            } else {
                advanceToNext(attempt);
            }
            return;
        }

        if (!selectedOptionId) { setIsSubmitting(false); return; }
        setConfirmedOptionId(selectedOptionId);

        const res = await quizManager.submitAnswer(
            quizId,
            attempt.attempt_id,
            currentQuestion.id,
            selectedOptionId,
            timeTaken,
        );
        setIsSubmitting(false);

        if (attempt.reveal_answers_during_quiz && res.success) {
            setRevealResult({
                is_correct: res.is_correct ?? false,
                correct_option_id: res.correct_option_id ?? null,
            });
            // Auto-advance after 1.5s
            setTimeout(() => {
                advanceToNext(attempt);
            }, 1500);
        } else {
            advanceToNext(attempt);
        }
    };

    const advanceToNext = (currentAttempt: ActiveAttempt) => {
        const nextIdx = currentQIdx + 1;
        if (nextIdx >= currentAttempt.questions.length) {
            handleFinish(currentAttempt, false);
        } else {
            setDirection(1);
            setCurrentQIdx(nextIdx);
            setSelectedOptionId(null);
            setConfirmedOptionId(null);
            setRevealResult(null);
            setConnectionPairs([]);
            setSelectedLeftId(null);
            questionStartTimeRef.current = Date.now();
        }
    };

    const handleFinish = async (currentAttempt: ActiveAttempt, fromTimer: boolean) => {
        if (isFinishingRef.current) return;
        isFinishingRef.current = true;
        if (timerRef.current) {
            clearInterval(timerRef.current);
            timerRef.current = null;
        }
        setPhase("loading");
        const res = await quizManager.finishQuiz(quizId, currentAttempt.attempt_id);
        isFinishingRef.current = false;
        if (res.success && res.result) {
            setFinishResult(res.result);
            if (fromTimer || res.result.status === "expired") {
                toast.warning("زمان آزمون به پایان رسید.");
            }
            setPhase("finished");
        } else {
            toast.error(res.message || "خطا در پایان دادن به آزمون");
            if (fromTimer) {
                // Time ran out — can't safely resume, send user back to quiz list
                router.push("/quiz");
            } else {
                setPhase("in_progress");
            }
        }
    };

    const getOptionStyle = (optionId: string) => {
        if (!confirmedOptionId) {
            return selectedOptionId === optionId
                ? "border-primary bg-primary bg-opacity-10"
                : "border-secondary";
        }
        if (!revealResult) return "border-secondary";
        if (optionId === revealResult.correct_option_id) return "border-success bg-success bg-opacity-10";
        if (optionId === confirmedOptionId && !revealResult.is_correct) return "border-danger bg-danger bg-opacity-10";
        return "border-secondary opacity-50";
    };

    if (phase === "loading") {
        return (
            <div className="d-flex justify-content-center align-items-center" style={{ minHeight: "60vh" }}>
                <div className="spinner-border text-primary" role="status">
                    <span className="visually-hidden">در حال بارگذاری...</span>
                </div>
            </div>
        );
    }

    if (phase === "finished" && finishResult) {
        const pct = finishResult.total_questions > 0
            ? Math.round((finishResult.correct_count / finishResult.total_questions) * 100)
            : 0;
        return (
            <main className="py-5">
                <div className="container">
                    <motion.div
                        className="row justify-content-center"
                        variants={fadeInUp}
                        initial="hidden"
                        animate="show"
                    >
                        <div className="col-lg-7 col-xl-6">
                            <div className="card shadow-lg border-0 text-center p-5">
                                <div className="mb-4">
                                    {finishResult.status === "expired" ? (
                                        <i className="bi bi-clock-history fs-1 text-warning d-block mb-3"></i>
                                    ) : pct >= 70 ? (
                                        <i className="bi bi-trophy-fill fs-1 text-warning d-block mb-3"></i>
                                    ) : (
                                        <i className="bi bi-patch-check-fill fs-1 text-primary d-block mb-3"></i>
                                    )}
                                    <h2 className="fw-bold mb-2">
                                        {finishResult.status === "expired" ? "وقت تمام شد!" : "آزمون تمام شد!"}
                                    </h2>
                                    {finishResult.status === "expired" && (
                                        <p className="text-warning small">زمان آزمون به پایان رسید و نتایج ثبت شد.</p>
                                    )}
                                </div>

                                <div className="row g-3 mb-4 text-center">
                                    <div className="col-6 col-md-3">
                                        <div className="bg-primary bg-opacity-10 rounded-3 p-3">
                                            <div className="h3 fw-bold text-primary mb-0">
                                                {new Intl.NumberFormat("fa-IR").format(finishResult.score)}
                                            </div>
                                            <small>امتیاز</small>
                                        </div>
                                    </div>
                                    <div className="col-6 col-md-3">
                                        <div className="bg-success bg-opacity-10 rounded-3 p-3">
                                            <div className="h3 fw-bold text-success mb-0">
                                                {new Intl.NumberFormat("fa-IR").format(finishResult.correct_count)}
                                            </div>
                                            <small>درست</small>
                                        </div>
                                    </div>
                                    <div className="col-6 col-md-3">
                                        <div className="bg-danger bg-opacity-10 rounded-3 p-3">
                                            <div className="h3 fw-bold text-danger mb-0">
                                                {new Intl.NumberFormat("fa-IR").format(finishResult.incorrect_count)}
                                            </div>
                                            <small>غلط</small>
                                        </div>
                                    </div>
                                    <div className="col-6 col-md-3">
                                        <div className="bg-secondary bg-opacity-10 rounded-3 p-3">
                                            <div className="h3 fw-bold mb-0">{formatTime(finishResult.time_spent)}</div>
                                            <small>زمان</small>
                                        </div>
                                    </div>
                                </div>

                                {/* Score bar */}
                                <div className="mb-4">
                                    <div className="d-flex justify-content-between mb-1">
                                        <small>
                                            {pct >= 90 ? "عالی" :
                                             pct >= 70 ? "خیلی خوب" :
                                             pct >= 50 ? "خوب" :
                                             pct >= 30 ? "قابل قبول" : "باید بیشتر مطالعه کنی"}
                                        </small>
                                        <small className="fw-bold">{new Intl.NumberFormat("fa-IR").format(pct)}٪</small>
                                    </div>
                                    <div className="progress" style={{ height: "10px", direction: "rtl" }}>
                                        <div
                                            className={`progress-bar ${pct >= 70 ? "bg-success" : pct >= 40 ? "bg-warning" : "bg-danger"}`}
                                            style={{ width: `${pct}%`, transition: "width 1s ease-out" }}
                                        ></div>
                                    </div>
                                </div>

                                <div className="d-flex gap-3 justify-content-center flex-wrap">
                                    <a href="/quiz/leaderboard" className="btn btn-outline-primary">
                                        <i className="bi bi-trophy me-2"></i>
                                        جدول امتیازات
                                    </a>
                                    <a href="/quiz" className="btn btn-primary">
                                        <i className="bi bi-arrow-right me-2"></i>
                                        بازگشت به آزمون‌ها
                                    </a>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </main>
        );
    }

    if (phase === "idle" && currentQuiz) {
        const diff = DIFFICULTY_LABELS[currentQuiz.difficulty] ?? currentQuiz.difficulty;
        return (
            <main className="py-5">
                <div className="container">
                    <motion.div
                        className="row justify-content-center"
                        variants={fadeInUp}
                        initial="hidden"
                        animate="show"
                    >
                        <div className="col-lg-8 col-xl-7">
                            <div className="card shadow-lg border-0 overflow-hidden">
                                {currentQuiz.thumbnail && (
                                    <div style={{ height: "240px", overflow: "hidden" }}>
                                        <img
                                            src={getMediaUrl(currentQuiz.thumbnail)}
                                            alt={currentQuiz.title}
                                            className="w-100 h-100"
                                            style={{ objectFit: "cover" }}
                                        />
                                    </div>
                                )}
                                <div className="card-body p-4 p-lg-5">
                                    <div className="d-flex flex-wrap gap-2 mb-3">
                                        <span className="badge bg-primary">{diff}</span>
                                        {currentQuiz.categories.map((c) => (
                                            <span key={c.id} className="badge text-bg-light border">{c.name}</span>
                                        ))}
                                        {currentQuiz.question_count !== undefined && (
                                            <span className="badge bg-secondary bg-opacity-25 text-dark">
                                                {new Intl.NumberFormat("fa-IR").format(currentQuiz.question_count)} سوال
                                            </span>
                                        )}
                                    </div>

                                    <h2 className="fw-bold mb-3">{currentQuiz.title}</h2>

                                    {currentQuiz.description && (
                                        <div
                                            className="text-muted mb-4"
                                            dangerouslySetInnerHTML={{ __html: currentQuiz.description }}
                                        />
                                    )}

                                    <div className="row g-3 mb-4">
                                        <div className="col-6 col-md-4">
                                            <div className="d-flex align-items-center gap-2">
                                                <i className="bi bi-arrow-repeat text-primary fs-5"></i>
                                                <div>
                                                    <div className="small text-muted">تعداد تلاش</div>
                                                    <div className="fw-semibold">
                                                        {currentQuiz.attempts_remaining === null
                                                            ? "نامحدود"
                                                            : `${new Intl.NumberFormat("fa-IR").format(currentQuiz.attempts_remaining)} باقی‌مانده`
                                                        }
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        {currentQuiz.reveal_answers_during_quiz && (
                                            <div className="col-6 col-md-4">
                                                <div className="d-flex align-items-center gap-2">
                                                    <i className="bi bi-eye text-success fs-5"></i>
                                                    <div>
                                                        <div className="small text-muted">نمایش پاسخ</div>
                                                        <div className="fw-semibold">بله</div>
                                                    </div>
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    {!currentQuiz.access_met ? (
                                        <div className="alert alert-warning d-flex align-items-center gap-3">
                                            <i className="bi bi-lock-fill fs-4"></i>
                                            <div>
                                                <strong>نیاز به اشتراک</strong>
                                                <p className="mb-0 small">برای شرکت در این آزمون باید اشتراک فعال داشته باشید.</p>
                                            </div>
                                        </div>
                                    ) : currentQuiz.attempts_remaining === 0 ? (
                                        <div className="alert alert-secondary">تلاش شما برای این آزمون تمام شده است.</div>
                                    ) : (
                                        <button
                                            className="btn btn-primary btn-lg w-100"
                                            onClick={handleStart}
                                            disabled={isStarting}
                                        >
                                            {isStarting ? (
                                                <><span className="spinner-border spinner-border-sm me-2" role="status"></span>در حال آماده‌سازی...</>
                                            ) : (
                                                <><i className="bi bi-play-circle-fill me-2"></i>شروع آزمون</>
                                            )}
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </main>
        );
    }

    if (phase === "in_progress" && attempt) {
        const currentQuestion = attempt.questions[currentQIdx];
        const totalQuestions = attempt.questions.length;
        const timerPct = totalTime > 0 ? (timeLeft / totalTime) * 100 : 0;
        const timerDanger = totalTime > 0 && (timeLeft / totalTime) * 100 < 10;

        return (
            <main className="py-4 py-md-5">
                <div className="container">
                    <div className="row justify-content-center">
                        <div className="col-lg-8 col-xl-7">
                            {/* Question counter */}
                            <div className="d-flex align-items-center mb-3">
                                <span className="small">
                                    سوال {new Intl.NumberFormat("fa-IR").format(currentQIdx + 1)} از {new Intl.NumberFormat("fa-IR").format(totalQuestions)}
                                </span>
                            </div>

                            {/* Question card */}
                            <AnimatePresence mode="wait">
                                <motion.div
                                    key={currentQuestion.id}
                                    initial={{ opacity: 0, x: direction > 0 ? 60 : -60 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: direction > 0 ? -60 : 60 }}
                                    transition={{ duration: 0.3, ease: "easeOut" }}
                                >
                                    {/* Question text card */}
                                    <div className="card border-0 shadow-sm mb-4" style={{ minHeight: "140px" }}>
                                        <div className="card-body p-4">
                                            <div className="d-flex align-items-center gap-2 mb-3">
                                                <span className="badge bg-primary bg-opacity-15 text-primary">
                                                    {QUESTION_TYPE_LABELS[currentQuestion.type] ?? currentQuestion.type}
                                                </span>
                                                <span className="badge bg-secondary bg-opacity-15 text-secondary">
                                                    {new Intl.NumberFormat("fa-IR").format(currentQuestion.score)} امتیاز
                                                </span>
                                            </div>
                                            <p className="fs-5 mb-0 lh-lg">{currentQuestion.text}</p>
                                            {(currentQuestion as any).image && (
                                                <div className="mt-3 text-center">
                                                    <img
                                                        src={getMediaUrl((currentQuestion as any).image)}
                                                        alt=""
                                                        className="rounded-3 img-fluid"
                                                        style={{ maxHeight: "260px", objectFit: "contain" }}
                                                    />
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {/* Timer bar + clock — between question and options */}
                                    <div className="mb-4">
                                        <div className="progress" style={{ height: "12px", transform: "scaleX(-1)" }}>
                                            <div
                                                className={`progress-bar ${timerDanger ? "bg-danger" : "bg-success"}`}
                                                role="progressbar"
                                                style={{ width: `${timerPct}%`, transition: "width 1s linear" }}
                                            ></div>
                                        </div>
                                        <div className="d-flex justify-content-end mt-1">
                                            <span className={`small fw-bold ${timerDanger ? "text-danger" : "text-success"}`}>
                                                <i className={`bi bi-${timerDanger ? "alarm" : "clock"} me-1`}></i>
                                                {formatTime(timeLeft)}
                                            </span>
                                        </div>
                                    </div>

                                    {/* Options / Matching UI */}
                                    {currentQuestion.type === "matching" ? (() => {
                                        const getPairColor = (leftId: string) => {
                                            const idx = connectionPairs.findIndex((p) => p.leftId === leftId);
                                            return idx >= 0 ? PAIR_COLORS[idx % PAIR_COLORS.length] : null;
                                        };
                                        const getRightColor = (rightId: string) => {
                                            const pair = connectionPairs.find((p) => p.rightId === rightId);
                                            return pair ? getPairColor(pair.leftId) : null;
                                        };
                                        return (
                                        <div>
                                            {revealResult && (
                                                <div className={`alert ${revealResult.is_correct ? "alert-success" : "alert-danger"} py-2 mb-3`}>
                                                    <i className={`bi bi-${revealResult.is_correct ? "check-circle" : "x-circle"} me-2`}></i>
                                                    {revealResult.is_correct ? "تمام موارد درست وصل شدند!" : "برخی موارد اشتباه وصل شده بودند."}
                                                </div>
                                            )}
                                            {!revealResult && confirmedOptionId === null && (
                                                <p className="small text-muted mb-2">
                                                    <i className="bi bi-info-circle me-1"></i>
                                                    یک گزینه از سمت چپ انتخاب کنید، سپس جفت آن را از سمت راست بزنید.
                                                </p>
                                            )}
                                            <div className="row g-2">
                                                <div className="col-6">
                                                    {(currentQuestion.left_items ?? []).map((item) => {
                                                        const color = getPairColor(item.id);
                                                        const isSelected = selectedLeftId === item.id;
                                                        return (
                                                            <button
                                                                key={item.id}
                                                                className="btn w-100 mb-2 text-end rounded-3 border-2 fw-semibold"
                                                                style={{
                                                                    minHeight: "52px",
                                                                    fontSize: "0.9rem",
                                                                    backgroundColor: isSelected
                                                                        ? "#0d6efd"
                                                                        : color
                                                                        ? color.bg
                                                                        : "transparent",
                                                                    color: isSelected
                                                                        ? "#fff"
                                                                        : color
                                                                        ? color.text
                                                                        : "inherit",
                                                                    borderColor: isSelected
                                                                        ? "#0d6efd"
                                                                        : color
                                                                        ? color.border
                                                                        : "#6c757d",
                                                                    opacity: confirmedOptionId !== null ? 1 : undefined,
                                                                    transition: "all 0.2s",
                                                                }}
                                                                onClick={() => handleLeftClick(item.id)}
                                                                disabled={confirmedOptionId !== null}
                                                            >
                                                                {item.text}
                                                                {color && <i className="bi bi-link-45deg ms-2 small"></i>}
                                                            </button>
                                                        );
                                                    })}
                                                </div>
                                                <div className="col-6">
                                                    {(currentQuestion.right_items ?? []).map((item) => {
                                                        const color = getRightColor(item.id);
                                                        return (
                                                            <button
                                                                key={item.id}
                                                                className="btn w-100 mb-2 text-end rounded-3 border-2 fw-semibold"
                                                                style={{
                                                                    minHeight: "52px",
                                                                    fontSize: "0.9rem",
                                                                    backgroundColor: color
                                                                        ? color.bg
                                                                        : "transparent",
                                                                    color: color
                                                                        ? color.text
                                                                        : "inherit",
                                                                    borderColor: color
                                                                        ? color.border
                                                                        : selectedLeftId
                                                                        ? "#0d6efd"
                                                                        : "#6c757d",
                                                                    transition: "all 0.2s",
                                                                }}
                                                                onClick={() => handleRightClick(item.id)}
                                                                disabled={confirmedOptionId !== null}
                                                            >
                                                                {item.text}
                                                                {color && <i className="bi bi-link-45deg ms-2 small"></i>}
                                                            </button>
                                                        );
                                                    })}
                                                </div>
                                            </div>
                                        </div>
                                        );
                                    })() : (
                                        <div
                                            style={{
                                                display: "grid",
                                                gridTemplateColumns: "repeat(2, 1fr)",
                                                gap: "12px",
                                            }}
                                        >
                                            {currentQuestion.options.map((option) => {
                                                const style = getOptionStyle(option.id);
                                                return (
                                                    <motion.button
                                                        key={option.id}
                                                        className={`btn text-start p-3 rounded-3 border-2 w-100 ${style}`}
                                                        style={{
                                                            cursor: confirmedOptionId ? "default" : "pointer",
                                                            minHeight: "72px",
                                                            fontSize: "0.95rem",
                                                            transition: "all 0.2s",
                                                        }}
                                                        onClick={() => handleOptionSelect(option.id)}
                                                        whileTap={confirmedOptionId ? {} : { scale: 0.97 }}
                                                        animate={
                                                            confirmedOptionId && revealResult
                                                                ? option.id === revealResult.correct_option_id
                                                                    ? { scale: [1, 1.03, 1] }
                                                                    : {}
                                                                : {}
                                                        }
                                                    >
                                                        <span>{option.text}</span>
                                                    </motion.button>
                                                );
                                            })}
                                        </div>
                                    )}

                                    {/* Confirm button */}
                                    <div className="mt-4">
                                        {confirmedOptionId === null ? (
                                            <button
                                                className="btn btn-primary btn-lg w-100"
                                                onClick={handleConfirm}
                                                disabled={
                                                    isSubmitting || (
                                                        currentQuestion.type === "matching"
                                                            ? connectionPairs.length < (currentQuestion.left_items?.length ?? 0)
                                                            : !selectedOptionId
                                                    )
                                                }
                                            >
                                                {isSubmitting ? (
                                                    <><span className="spinner-border spinner-border-sm me-2"></span>در حال ثبت...</>
                                                ) : (
                                                    <><i className="bi bi-check-circle me-2"></i>ثبت پاسخ</>
                                                )}
                                            </button>
                                        ) : !attempt.reveal_answers_during_quiz ? (
                                            <button
                                                className="btn btn-outline-primary btn-lg w-100"
                                                onClick={() => advanceToNext(attempt)}
                                            >
                                                {currentQIdx + 1 < totalQuestions
                                                    ? <><i className="bi bi-arrow-left me-2"></i>سوال بعدی</>
                                                    : <><i className="bi bi-flag-fill me-2"></i>پایان آزمون</>
                                                }
                                            </button>
                                        ) : null}
                                    </div>
                                </motion.div>
                            </AnimatePresence>
                        </div>
                    </div>
                </div>
            </main>
        );
    }

    return null;
}

export default QuizPlayPage;
