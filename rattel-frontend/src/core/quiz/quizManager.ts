"use client";

import { api } from "../api";

// ─── Types ────────────────────────────────────────────────────────────────────

export type QuizDifficulty = "easy" | "medium" | "hard";
export type AttemptStatus = "in_progress" | "completed" | "expired";
export type QuestionType = "multiple_choice" | "fill_blank" | "true_false" | "matching";

export interface QuizCategory {
    id: number;
    name: string;
    slug: string;
}

export interface QuestionOption {
    id: string;
    text: string;
    order: number;
}

export interface MatchingItem {
    id: string;
    text: string;
}

export interface Question {
    id: string;
    type: QuestionType;
    text: string;
    order: number;
    score: number;
    time_to_answer: number;
    options: QuestionOption[];
    left_items?: MatchingItem[];
    right_items?: MatchingItem[];
}

export interface AccessRequirement {
    id: number;
    type: "free" | "completed_quiz" | "min_score" | "subscription";
    required_quiz: { id: string; title: string } | null;
    required_score: number | null;
}

export interface Quiz {
    id: string;
    title: string;
    description?: string;
    thumbnail: string | null;
    categories: QuizCategory[];
    difficulty: QuizDifficulty;
    difficulty_display: string;
    is_active: boolean;
    start_date: string | null;
    end_date: string | null;
    created_at: string;
    attempts_remaining: number | null;
    access_met: boolean;
    access_reason?: string;
    question_count?: number;
    randomize_question_order?: boolean;
    max_attempts_per_user?: number;
    reveal_answers_during_quiz?: boolean;
    allow_retry_on_expiry?: boolean;
    access_requirements?: AccessRequirement[];
}

export interface QuizAttempt {
    id: string;
    quiz: { id: string; title: string };
    started_at: string;
    finished_at: string | null;
    score: number;
    correct_count: number;
    incorrect_count: number;
    time_spent: number;
    status: AttemptStatus;
    status_display: string;
    created_at: string;
}

export interface ActiveAttempt {
    attempt_id: string;
    quiz_id: string;
    questions: Question[];
    total_time_seconds: number;
    reveal_answers_during_quiz: boolean;
}

export interface MatchingCorrectPair {
    left_id: string;
    right_id: string;
    left_text: string;
    right_text: string;
}

export interface SubmitAnswerResult {
    success: boolean;
    is_correct?: boolean;
    correct_option_id?: string;
    correct_pairs?: { left_id: string; right_id: string }[];
    message?: string;
}

export interface AttemptAnswerResult {
    question_id: string;
    selected_option_id: string | null;
    correct_option_id: string | null;
    is_correct: boolean;
    matching_answer?: Record<string, string> | null;
    correct_pairs?: MatchingCorrectPair[] | null;
}

export interface FinishResult {
    score: number;
    correct_count: number;
    incorrect_count: number;
    total_questions: number;
    time_spent: number;
    status: AttemptStatus;
    answers: AttemptAnswerResult[];
}

export interface LeaderboardEntry {
    user__id: number;
    user__username: string;
    total_score: number;
}

export interface QuizParticipant {
    user_id: number;
    username: string;
    score: number;
    correct_count: number;
    incorrect_count: number;
    time_spent: number;
    finished_at: string;
}

export interface QuizResult {
    success: boolean;
    message?: string;
    error?: number;
}

// ─── Admin types ──────────────────────────────────────────────────────────────

export interface QuestionOptionAdmin extends QuestionOption {
    is_correct: boolean;
}

export interface MatchingPairAdmin {
    id: string;
    left_text: string;
    right_text: string;
    left_id: string;
    right_id: string;
    order: number;
}

export interface QuestionAdmin extends Question {
    options: QuestionOptionAdmin[];
    pairs?: MatchingPairAdmin[];
    created_at: string;
    updated_at: string;
}

export interface QuizAdmin extends Quiz {
    questions: QuestionAdmin[];
}

export interface CreateQuizPayload {
    title: string;
    description?: string;
    difficulty?: QuizDifficulty;
    is_active?: boolean;
    randomize_question_order?: boolean;
    max_attempts_per_user?: number;
    reveal_answers_during_quiz?: boolean;
    allow_retry_on_expiry?: boolean;
    start_date?: string | null;
    end_date?: string | null;
    categories?: number[];
    thumbnail?: File | null;
}

export interface CreateQuestionPayload {
    type: QuestionType;
    text: string;
    order?: number;
    score?: number;
    time_to_answer?: number;
    options: { text: string; is_correct: boolean; order: number }[];
    pairs?: { left_text: string; right_text: string }[];
    image?: File | null;
}

export interface AccessRequirementPayload {
    type: "free" | "completed_quiz" | "min_score" | "subscription";
    required_quiz_id?: string | null;
    required_score?: number | null;
}

// ─── Manager ──────────────────────────────────────────────────────────────────

class QuizManager {
    private static instance: QuizManager;

    private quizzes: Quiz[] = [];
    private quizzesTotal = 0;
    private quizzesTotalPages = 0;
    private currentQuiz: Quiz | null = null;
    private activeAttempt: ActiveAttempt | null = null;
    private myAttempts: QuizAttempt[] = [];
    private myAttemptsTotal = 0;
    private leaderboard: LeaderboardEntry[] = [];
    private userRank: number | null = null;
    private userLeaderboardEntry: (LeaderboardEntry & { rank: number }) | null = null;

    private adminQuizzes: QuizAdmin[] = [];
    private adminQuizzesTotal = 0;
    private adminCategories: QuizCategory[] = [];

    private isLoading = false;
    private error: string | null = null;

    private listeners: Set<() => void> = new Set();

    private constructor() {}

    public static getInstance(): QuizManager {
        if (!QuizManager.instance) {
            QuizManager.instance = new QuizManager();
        }
        return QuizManager.instance;
    }

    public subscribe(cb: () => void): () => void {
        this.listeners.add(cb);
        return () => this.listeners.delete(cb);
    }

    private notify(): void {
        this.listeners.forEach((cb) => cb());
    }

    private setLoading(v: boolean): void {
        this.isLoading = v;
        this.notify();
    }

    // ── Accessors ─────────────────────────────────────────────────────────────

    public getQuizzes() { return this.quizzes; }
    public getQuizzesTotal() { return this.quizzesTotal; }
    public getQuizzesTotalPages() { return this.quizzesTotalPages; }
    public getCurrentQuiz() { return this.currentQuiz; }
    public getActiveAttempt() { return this.activeAttempt; }
    public getMyAttempts() { return this.myAttempts; }
    public getMyAttemptsTotal() { return this.myAttemptsTotal; }
    public getLeaderboard() { return this.leaderboard; }
    public getUserRank() { return this.userRank; }
    public getUserLeaderboardEntry() { return this.userLeaderboardEntry; }
    public getAdminQuizzes() { return this.adminQuizzes; }
    public getAdminQuizzesTotal() { return this.adminQuizzesTotal; }
    public getAdminCategories() { return this.adminCategories; }
    public getIsLoading() { return this.isLoading; }
    public getError() { return this.error; }

    // ── User API ──────────────────────────────────────────────────────────────

    public async fetchQuizzes(page = 1, count = 9, category?: string): Promise<QuizResult> {
        this.setLoading(true);
        try {
            const params = new URLSearchParams({ page: String(page), count: String(count) });
            if (category) params.set("category", category);
            const res = await api.get(`/quiz/?${params}`, { cache: false });
            if (res.data.success) {
                this.quizzes = res.data.quizzes;
                this.quizzesTotal = res.data.total;
                this.quizzesTotalPages = res.data.total_pages;
                this.notify();
                return { success: true };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: "خطا در دریافت آزمون‌ها" };
        } finally {
            this.setLoading(false);
        }
    }

    public async fetchQuizDetail(quizId: string): Promise<QuizResult> {
        this.setLoading(true);
        try {
            const res = await api.get(`/quiz/${quizId}/`, { cache: false });
            if (res.data.success) {
                this.currentQuiz = res.data.quiz;
                this.notify();
                return { success: true };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: "خطا در دریافت آزمون" };
        } finally {
            this.setLoading(false);
        }
    }

    public async startQuiz(quizId: string): Promise<QuizResult & { attempt?: ActiveAttempt }> {
        this.setLoading(true);
        try {
            const res = await api.post(`/quiz/${quizId}/start/`, {}, { cache: false } as any);
            if (res.data.success) {
                const attempt: ActiveAttempt = {
                    attempt_id: res.data.attempt_id,
                    quiz_id: quizId,
                    questions: res.data.questions,
                    total_time_seconds: res.data.total_time_seconds,
                    reveal_answers_during_quiz: res.data.reveal_answers_during_quiz,
                };
                this.activeAttempt = attempt;
                this.notify();
                return { success: true, attempt };
            }
            return { success: false, message: res.data.message, error: res.data.error };
        } catch (e: any) {
            const msg = e.response?.data?.message;
            return { success: false, message: msg || "خطا در شروع آزمون" };
        } finally {
            this.setLoading(false);
        }
    }

    public async submitAnswer(
        quizId: string,
        attemptId: string,
        questionId: string,
        selectedOptionId: string | null,
        timeTaken = 0,
        matchingAnswer?: Record<string, string>,
    ): Promise<QuizResult & SubmitAnswerResult> {
        try {
            const body: Record<string, unknown> = {
                question_id: questionId,
                time_taken: timeTaken,
            };
            if (matchingAnswer !== undefined) {
                body.matching_answer = matchingAnswer;
            } else {
                body.selected_option_id = selectedOptionId;
            }
            const res = await api.post(
                `/quiz/${quizId}/submit/${attemptId}/`,
                body,
                { cache: false } as any,
            );
            if (res.data.success) {
                return {
                    success: true,
                    is_correct: res.data.is_correct,
                    correct_option_id: res.data.correct_option_id,
                    correct_pairs: res.data.correct_pairs,
                };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: e.response?.data?.message || "خطا در ثبت پاسخ" };
        }
    }

    public async finishQuiz(
        quizId: string,
        attemptId: string,
    ): Promise<QuizResult & { result?: FinishResult }> {
        this.setLoading(true);
        try {
            const res = await api.post(`/quiz/${quizId}/finish/${attemptId}/`, {}, { cache: false } as any);
            if (res.data.success) {
                const result: FinishResult = {
                    score: res.data.score,
                    correct_count: res.data.correct_count,
                    incorrect_count: res.data.incorrect_count,
                    total_questions: res.data.total_questions,
                    time_spent: res.data.time_spent,
                    status: res.data.status,
                    answers: res.data.answers,
                };
                this.activeAttempt = null;
                this.notify();
                return { success: true, result };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: e.response?.data?.message || "خطا در پایان دادن به آزمون" };
        } finally {
            this.setLoading(false);
        }
    }

    public async fetchLeaderboard(): Promise<QuizResult> {
        this.setLoading(true);
        try {
            const res = await api.get("/quiz/leaderboard/", { cache: false });
            if (res.data.success) {
                this.leaderboard = res.data.leaderboard;
                this.userRank = res.data.user_rank;
                this.userLeaderboardEntry = res.data.user_entry ?? null;
                this.notify();
                return { success: true };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: "خطا در دریافت جدول امتیازات" };
        } finally {
            this.setLoading(false);
        }
    }

    public async fetchMyAttempts(): Promise<QuizResult> {
        this.setLoading(true);
        try {
            const res = await api.get("/quiz/my-attempts/", { cache: false });
            if (res.data.success) {
                this.myAttempts = res.data.attempts;
                this.myAttemptsTotal = res.data.total;
                this.notify();
                return { success: true };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: "خطا در دریافت تاریخچه آزمون‌ها" };
        } finally {
            this.setLoading(false);
        }
    }

    public clearActiveAttempt(): void {
        this.activeAttempt = null;
        this.notify();
    }

    // ── Admin API ─────────────────────────────────────────────────────────────

    public async fetchAdminQuizzes(page = 1, count = 9): Promise<QuizResult> {
        this.setLoading(true);
        try {
            const res = await api.get(`/quiz/admin/?page=${page}&count=${count}`, { cache: false });
            if (res.data.success) {
                this.adminQuizzes = res.data.quizzes;
                this.adminQuizzesTotal = res.data.total;
                this.notify();
                return { success: true };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: "خطا در دریافت لیست آزمون‌ها" };
        } finally {
            this.setLoading(false);
        }
    }

    public async createQuiz(payload: CreateQuizPayload): Promise<QuizResult & { quiz?: QuizAdmin }> {
        try {
            const formData = new FormData();
            formData.append("title", payload.title);
            if (payload.description) formData.append("description", payload.description);
            if (payload.difficulty) formData.append("difficulty", payload.difficulty);
            formData.append("is_active", String(payload.is_active ?? true));
            formData.append("randomize_question_order", String(payload.randomize_question_order ?? false));
            formData.append("max_attempts_per_user", String(payload.max_attempts_per_user ?? 0));
            formData.append("reveal_answers_during_quiz", String(payload.reveal_answers_during_quiz ?? false));
            formData.append("allow_retry_on_expiry", String(payload.allow_retry_on_expiry ?? true));
            if (payload.start_date) formData.append("start_date", payload.start_date);
            if (payload.end_date) formData.append("end_date", payload.end_date);
            if (payload.thumbnail) formData.append("thumbnail", payload.thumbnail);
            if (payload.categories) {
                payload.categories.forEach((id) => formData.append("categories", String(id)));
            }
            const res = await api.post("/quiz/admin/", formData, { cache: false, headers: { 'Content-Type': undefined } } as any);
            if (res.data.success) {
                this.adminQuizzes = [res.data.quiz, ...this.adminQuizzes];
                this.adminQuizzesTotal += 1;
                this.notify();
                return { success: true, quiz: res.data.quiz };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: e.response?.data?.message || "خطا در ایجاد آزمون" };
        }
    }

    public async updateQuiz(
        quizId: string,
        payload: Partial<CreateQuizPayload>,
    ): Promise<QuizResult & { quiz?: QuizAdmin }> {
        try {
            const formData = new FormData();
            if (payload.title !== undefined) formData.append("title", payload.title);
            if (payload.description !== undefined) formData.append("description", payload.description);
            if (payload.difficulty !== undefined) formData.append("difficulty", payload.difficulty);
            if (payload.is_active !== undefined) formData.append("is_active", String(payload.is_active));
            if (payload.randomize_question_order !== undefined)
                formData.append("randomize_question_order", String(payload.randomize_question_order));
            if (payload.max_attempts_per_user !== undefined)
                formData.append("max_attempts_per_user", String(payload.max_attempts_per_user));
            if (payload.reveal_answers_during_quiz !== undefined)
                formData.append("reveal_answers_during_quiz", String(payload.reveal_answers_during_quiz));
            if (payload.allow_retry_on_expiry !== undefined)
                formData.append("allow_retry_on_expiry", String(payload.allow_retry_on_expiry));
            if (payload.start_date !== undefined)
                formData.append("start_date", payload.start_date || "");
            if (payload.end_date !== undefined)
                formData.append("end_date", payload.end_date || "");
            if (payload.thumbnail) formData.append("thumbnail", payload.thumbnail);
            if (payload.categories) {
                payload.categories.forEach((id) => formData.append("categories", String(id)));
            }
            const res = await api.put(`/quiz/admin/${quizId}/`, formData, { cache: false, headers: { 'Content-Type': undefined } } as any);
            if (res.data.success) {
                this.adminQuizzes = this.adminQuizzes.map((q) =>
                    q.id === quizId ? { ...q, ...res.data.quiz } : q,
                );
                this.notify();
                return { success: true, quiz: res.data.quiz };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: e.response?.data?.message || "خطا در ویرایش آزمون" };
        }
    }

    public async deleteQuiz(quizId: string): Promise<QuizResult> {
        try {
            await api.delete(`/quiz/admin/${quizId}/`, { cache: false } as any);
            this.adminQuizzes = this.adminQuizzes.filter((q) => q.id !== quizId);
            this.adminQuizzesTotal = Math.max(0, this.adminQuizzesTotal - 1);
            this.notify();
            return { success: true };
        } catch (e: any) {
            return { success: false, message: e.response?.data?.message || "خطا در حذف آزمون" };
        }
    }

    public async fetchAdminQuizDetail(quizId: string): Promise<QuizResult & { quiz?: QuizAdmin }> {
        this.setLoading(true);
        try {
            const res = await api.get(`/quiz/admin/${quizId}/`, { cache: false });
            if (res.data.success) {
                this.notify();
                return { success: true, quiz: res.data.quiz };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: "خطا در دریافت آزمون" };
        } finally {
            this.setLoading(false);
        }
    }

    public async createQuestion(
        quizId: string,
        payload: CreateQuestionPayload,
    ): Promise<QuizResult & { question?: QuestionAdmin }> {
        try {
            const formData = new FormData();
            formData.append("type", payload.type);
            formData.append("text", payload.text);
            if (payload.type === "matching") {
                if (payload.pairs !== undefined)
                    formData.append("pairs", JSON.stringify(payload.pairs));
            } else {
                formData.append("options", JSON.stringify(payload.options));
            }
            if (payload.score !== undefined) formData.append("score", String(payload.score));
            if (payload.time_to_answer !== undefined) formData.append("time_to_answer", String(payload.time_to_answer));
            if (payload.order !== undefined) formData.append("order", String(payload.order));
            if (payload.image) formData.append("image", payload.image);
            const res = await api.post(`/quiz/admin/${quizId}/questions/`, formData, { cache: false, headers: { 'Content-Type': undefined } } as any);
            if (res.data.success) {
                return { success: true, question: res.data.question };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: e.response?.data?.message || "خطا در ایجاد سوال" };
        }
    }

    public async updateQuestion(
        questionId: string,
        payload: Partial<CreateQuestionPayload>,
    ): Promise<QuizResult & { question?: QuestionAdmin }> {
        try {
            const formData = new FormData();
            if (payload.type !== undefined) formData.append("type", payload.type);
            if (payload.text !== undefined) formData.append("text", payload.text);
            if (payload.pairs !== undefined) formData.append("pairs", JSON.stringify(payload.pairs));
            if (payload.options !== undefined) formData.append("options", JSON.stringify(payload.options));
            if (payload.score !== undefined) formData.append("score", String(payload.score));
            if (payload.time_to_answer !== undefined) formData.append("time_to_answer", String(payload.time_to_answer));
            if (payload.order !== undefined) formData.append("order", String(payload.order));
            if (payload.image) formData.append("image", payload.image);
            const res = await api.put(`/quiz/admin/questions/${questionId}/`, formData, { cache: false, headers: { 'Content-Type': undefined } } as any);
            if (res.data.success) {
                return { success: true, question: res.data.question };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: e.response?.data?.message || "خطا در ویرایش سوال" };
        }
    }

    public async createAccessRequirement(
        quizId: string,
        payload: AccessRequirementPayload,
    ): Promise<QuizResult & { requirement?: AccessRequirement }> {
        try {
            const res = await api.post(`/quiz/admin/${quizId}/requirements/`, payload, { cache: false } as any);
            if (res.data.success) {
                return { success: true, requirement: res.data.requirement };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: e.response?.data?.message || "خطا در افزودن شرط دسترسی" };
        }
    }

    public async deleteAccessRequirement(reqId: number): Promise<QuizResult> {
        try {
            await api.delete(`/quiz/admin/requirements/${reqId}/`, { cache: false } as any);
            return { success: true };
        } catch (e: any) {
            return { success: false, message: e.response?.data?.message || "خطا در حذف شرط دسترسی" };
        }
    }

    public async deleteQuestion(questionId: string): Promise<QuizResult> {
        try {
            await api.delete(`/quiz/admin/questions/${questionId}/`, { cache: false } as any);
            return { success: true };
        } catch (e: any) {
            return { success: false, message: e.response?.data?.message || "خطا در حذف سوال" };
        }
    }

    public async reorderQuestions(
        items: { id: string; order: number }[],
    ): Promise<QuizResult> {
        try {
            const res = await api.post(
                "/quiz/admin/questions/reorder/",
                { items },
                { cache: false } as any,
            );
            if (res.data.success) {
                return { success: true };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: e.response?.data?.message || "خطا در ترتیب‌بندی سوالات" };
        }
    }

    public async fetchAdminCategories(): Promise<QuizResult & { categories?: QuizCategory[] }> {
        try {
            const res = await api.get("/quiz/admin/categories/", { cache: false });
            if (res.data.success) {
                this.adminCategories = res.data.categories;
                this.notify();
                return { success: true, categories: res.data.categories };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: "خطا در دریافت دسته‌بندی‌ها" };
        }
    }

    public async createAdminCategory(name: string, slug: string): Promise<QuizResult & { category?: QuizCategory }> {
        try {
            const res = await api.post("/quiz/admin/categories/", { name, slug }, { cache: false } as any);
            if (res.data.success) {
                this.adminCategories = [...this.adminCategories, res.data.category];
                this.notify();
                return { success: true, category: res.data.category };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: e.response?.data?.message || "خطا در ایجاد دسته‌بندی" };
        }
    }

    public async fetchQuizParticipants(quizId: string): Promise<QuizResult & { participants?: QuizParticipant[] }> {
        try {
            const res = await api.get(`/quiz/admin/${quizId}/participants/`, { cache: false });
            if (res.data.success) return { success: true, participants: res.data.participants };
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: "خطا در دریافت شرکت‌کنندگان" };
        }
    }
}

export const quizManager = QuizManager.getInstance();
