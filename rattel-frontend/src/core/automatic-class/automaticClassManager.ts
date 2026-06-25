"use client";

import { api } from "../api";

// ─── Shared types ─────────────────────────────────────────────────────────────

export type StepStatus = "pending" | "delayed" | "completed" | "skipped";
export type StepType = "memorize" | "review" | "extra_review" | "final_review";
export type CallSessionStatus = "pending" | "completed" | "no_answer";
export type PlanStatus = "draft" | "active" | "completed" | "cancelled";
export type RequestStatus = "pending" | "contacted" | "plan_created" | "rejected";

export interface PlanStep {
    id: string;
    step_number: number;
    scheduled_date: string | null;
    step_type: StepType;
    step_type_display: string;
    page_start: number;
    page_end: number;
    sub_part: "full" | "first_half" | "second_half";
    sub_part_display: string;
    status: StepStatus;
    status_display: string;
    is_delayed: boolean;
    original_scheduled_date: string | null;
    completed_at: string | null;
    delay_reason: string;
    admin_note: string;
    is_overdue: boolean;
}

export interface UserCallSession {
    id: string;
    session_number: number;
    status: CallSessionStatus;
    status_display: string;
    completed_at: string | null;
    notes: string;
}

export interface AutomaticPlan {
    id: string;
    start_page: number;
    end_page: number;
    start_date: string;
    time_to_finish: string;
    time_freq: string;
    time_freq_display: string;
    reading_freq: string;
    reading_freq_display: string;
    review_freq: number;
    extra_review_start_page: number | null;
    extra_review_end_page: number | null;
    extra_review_pages_per_session: number;
    user_day_availability: string;
    user_day_availability_display: string;
    user_time_availability: string;
    user_time_availability_display: string;
    status: PlanStatus;
    status_display: string;
    teacher_display: { id: number; username: string } | null;
    total_steps: number;
    completed_steps: number;
    progress_percent: number;
    call_sessions: UserCallSession[];
    created_at: string;
}

export interface ClassRequest {
    id: string;
    notes: string;
    status: RequestStatus;
    status_display: string;
    plan_is_cancelled: boolean;
    plan_is_completed: boolean;
    created_at: string;
    updated_at: string;
}

export interface TodayData {
    has_delayed: boolean;
    delayed_steps: PlanStep[];
    today_steps: PlanStep[];
    upcoming_steps: PlanStep[];
}

export interface ProgressData {
    plan: AutomaticPlan;
    steps: PlanStep[];
    stats: {
        total: number;
        completed: number;
        delayed: number;
        pending: number;
        skipped: number;
        progress_percent: number;
        delayed_completions: number;
    };
    today: string;
}

// ─── Admin types ──────────────────────────────────────────────────────────────

export interface AdminClassRequest extends ClassRequest {
    user: number;
    user_display: { id: number; username: string; phone: string | null };
    admin_notes: string;
}

export interface AdminPlan extends AutomaticPlan {
    user_display: { id: number; username: string; phone: string | null };
    admin_notes: string;
    _steps_generated: boolean;
    steps: PlanStep[];
    call_sessions: OnlineCallSession[];
    subscription_info: SubscriptionInfo | null;
    extra_review_start_page: number | null;
    extra_review_end_page: number | null;
    extra_review_pages_per_session: number;
}

export interface AdminCallLog {
    id: string;
    plan: string;
    called_by: number;
    called_by_display: string;
    notes: string;
    call_date: string;
    created_at: string;
}

export interface OnlineCallSession {
    id: string;
    session_number: number;
    status: CallSessionStatus;
    status_display: string;
    completed_at: string | null;
    notes: string;
    marked_by_display: string | null;
    created_at: string;
}

export interface SubscriptionInfo {
    plan_name: string;
    online_class_limit: number;
    is_active: boolean;
}

export interface CreatePlanPayload {
    request?: string | null;
    user: number | string;
    teacher?: number | string | null;
    start_page: number;
    end_page: number;
    start_date: string;
    time_to_finish: string;
    time_freq: string;
    reading_freq: string;
    review_freq: number;
    extra_review_start_page?: number | null;
    extra_review_end_page?: number | null;
    extra_review_pages_per_session?: number;
    user_day_availability: string;
    user_time_availability: string;
    status: string;
    admin_notes?: string;
}

// ─── Result shapes ────────────────────────────────────────────────────────────

export interface ACResult {
    success: boolean;
    message?: string;
    error?: number;
}

// ─── Manager ──────────────────────────────────────────────────────────────────

class AutomaticClassManager {
    private static instance: AutomaticClassManager;

    // User state
    private classRequest: ClassRequest | null = null;
    private plan: AutomaticPlan | null = null;
    private todayData: TodayData | null = null;
    private progressData: ProgressData | null = null;

    // Admin state
    private adminRequests: AdminClassRequest[] = [];
    private adminRequestsTotal = 0;
    private adminPlans: AdminPlan[] = [];
    private adminPlansTotal = 0;
    private activePlan: AdminPlan | null = null;
    private callLogs: AdminCallLog[] = [];

    // Loading
    private isLoading = false;
    private error: string | null = null;
    private noSubscription = false;

    private listeners: Set<() => void> = new Set();

    private constructor() {}

    public static getInstance(): AutomaticClassManager {
        if (!AutomaticClassManager.instance) {
            AutomaticClassManager.instance = new AutomaticClassManager();
        }
        return AutomaticClassManager.instance;
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

    public getClassRequest() { return this.classRequest; }
    public getPlan() { return this.plan; }
    public getTodayData() { return this.todayData; }
    public getProgressData() { return this.progressData; }
    public getAdminRequests() { return this.adminRequests; }
    public getAdminRequestsTotal() { return this.adminRequestsTotal; }
    public getAdminPlans() { return this.adminPlans; }
    public getAdminPlansTotal() { return this.adminPlansTotal; }
    public getActivePlan() { return this.activePlan; }
    public getCallLogs() { return this.callLogs; }
    public getIsLoading() { return this.isLoading; }
    public getError() { return this.error; }
    public getNoSubscription() { return this.noSubscription; }

    // ── User API ──────────────────────────────────────────────────────────────

    public async fetchClassRequest(): Promise<ACResult> {
        this.setLoading(true);
        try {
            const res = await api.get("/class/automatic/request/", { cache: false });
            if (res.data.success) {
                this.classRequest = res.data.request;
                this.notify();
                return { success: true };
            }
            if (res.data.error === -1) {
                this.classRequest = null;
                this.notify();
                return { success: false, error: -1 };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            if (e.response?.status === 404) {
                this.classRequest = null;
                this.notify();
                return { success: false, error: -1 };
            }
            return { success: false, message: "خطا در دریافت اطلاعات" };
        } finally {
            this.setLoading(false);
        }
    }

    public async submitClassRequest(notes: string): Promise<ACResult> {
        this.setLoading(true);
        try {
            const res = await api.post("/class/automatic/request/", { notes }, { cache: false } as any);
            if (res.data.success) {
                this.classRequest = res.data.request;
                this.notify();
                return { success: true, message: res.data.message };
            }
            return { success: false, message: res.data.message, error: res.data.error };
        } catch (e: any) {
            return { success: false, message: e.response?.data?.message || "خطا در ارسال درخواست" };
        } finally {
            this.setLoading(false);
        }
    }

    public async fetchMyPlan(): Promise<ACResult> {
        this.setLoading(true);
        try {
            // validateStatus prevents axios from rejecting 403/404 so the response
            // interceptor never fires a toast — we handle those states ourselves.
            const res = await api.get("/class/automatic/my-plan/", {
                cache: false,
                validateStatus: (s: number) => s < 500,
            } as any);
            if (res.status === 403) {
                this.noSubscription = true;
                this.plan = null;
                this.notify();
                return { success: false, error: 403 };
            }
            if (res.status === 404 || !res.data.success) {
                this.noSubscription = false;
                this.plan = null;
                this.notify();
                return { success: false, error: res.data.error };
            }
            this.noSubscription = false;
            this.plan = res.data.plan;
            this.notify();
            return { success: true };
        } catch (e: any) {
            return { success: false, message: "خطا در دریافت برنامه" };
        } finally {
            this.setLoading(false);
        }
    }

    public async fetchTodaySteps(): Promise<ACResult> {
        this.setLoading(true);
        try {
            const res = await api.get("/class/automatic/today/", {
                cache: false,
                validateStatus: (s: number) => s < 500,
            } as any);
            if (res.status === 403) {
                this.noSubscription = true;
                this.notify();
                return { success: false, error: 403 };
            }
            if (res.data.success) {
                this.noSubscription = false;
                this.todayData = {
                    has_delayed: res.data.has_delayed,
                    delayed_steps: res.data.delayed_steps,
                    today_steps: res.data.today_steps,
                    upcoming_steps: res.data.upcoming_steps,
                };
                this.notify();
                return { success: true };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: "خطا در دریافت وظایف امروز" };
        } finally {
            this.setLoading(false);
        }
    }

    public async fetchProgress(): Promise<ACResult> {
        this.setLoading(true);
        try {
            const res = await api.get("/class/automatic/progress/", {
                cache: false,
                validateStatus: (s: number) => s < 500,
            } as any);
            if (res.status === 403) {
                this.noSubscription = true;
                this.notify();
                return { success: false, error: 403 };
            }
            if (res.data.success) {
                this.noSubscription = false;
                this.progressData = {
                    plan: res.data.plan,
                    steps: res.data.steps,
                    stats: res.data.stats,
                    today: res.data.today,
                };
                this.notify();
                return { success: true };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: "خطا در دریافت پیشرفت" };
        } finally {
            this.setLoading(false);
        }
    }

    public async completeStep(stepId: string, delayReason?: string): Promise<ACResult & { step?: PlanStep }> {
        try {
            const res = await api.post(
                `/class/automatic/steps/${stepId}/complete/`,
                { delay_reason: delayReason || "" },
                { cache: false } as any
            );
            if (res.data.success) {
                this._patchStep(res.data.step);
                return { success: true, step: res.data.step };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: e.response?.data?.message || "خطا در تکمیل مرحله" };
        }
    }

    public async reportDelay(stepId: string, delayReason: string): Promise<ACResult & { step?: PlanStep }> {
        try {
            const res = await api.post(
                `/class/automatic/steps/${stepId}/report/`,
                { delay_reason: delayReason },
                { cache: false } as any
            );
            if (res.data.success) {
                this._patchStep(res.data.step);
                return { success: true, step: res.data.step };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: e.response?.data?.message || "خطا در ثبت تأخیر" };
        }
    }

    private _patchStep(updated: PlanStep): void {
        if (this.todayData) {
            this.todayData = {
                ...this.todayData,
                delayed_steps: this.todayData.delayed_steps.map((s) => s.id === updated.id ? updated : s),
                today_steps: this.todayData.today_steps.map((s) => s.id === updated.id ? updated : s),
            };
        }
        if (this.progressData) {
            this.progressData = {
                ...this.progressData,
                steps: this.progressData.steps.map((s) => s.id === updated.id ? updated : s),
            };
        }
        this.notify();
    }

    // ── Admin API ─────────────────────────────────────────────────────────────

    public async fetchAdminRequests(filterStatus?: string): Promise<ACResult> {
        this.setLoading(true);
        try {
            const params = filterStatus ? `?status=${filterStatus}` : "";
            const res = await api.get(`/class/automatic/admin/requests/${params}`, { cache: false });
            if (res.data.success) {
                this.adminRequests = res.data.requests;
                this.adminRequestsTotal = res.data.total;
                this.notify();
                return { success: true };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: "خطا در دریافت درخواست‌ها" };
        } finally {
            this.setLoading(false);
        }
    }

    public async updateAdminRequest(id: string, data: { status?: string; admin_notes?: string }): Promise<ACResult> {
        try {
            const res = await api.patch(`/class/automatic/admin/requests/${id}/`, data, { cache: false } as any);
            if (res.data.success) {
                this.adminRequests = this.adminRequests.map((r) =>
                    r.id === id ? { ...r, ...res.data.request } : r
                );
                this.notify();
                return { success: true, message: res.data.message };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: "خطا در بروزرسانی درخواست" };
        }
    }

    public async fetchAdminPlans(filterStatus?: string): Promise<ACResult> {
        this.setLoading(true);
        try {
            const params = filterStatus ? `?status=${filterStatus}` : "";
            const res = await api.get(`/class/automatic/admin/plans/${params}`, { cache: false });
            if (res.data.success) {
                this.adminPlans = res.data.plans;
                this.adminPlansTotal = res.data.total;
                this.notify();
                return { success: true };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: "خطا در دریافت برنامه‌ها" };
        } finally {
            this.setLoading(false);
        }
    }

    public async fetchAdminPlanDetail(planId: string): Promise<ACResult> {
        this.setLoading(true);
        try {
            const res = await api.get(`/class/automatic/admin/plans/${planId}/`, { cache: false });
            if (res.data.success) {
                this.activePlan = res.data.plan;
                this.callLogs = res.data.call_logs || [];
                this.notify();
                return { success: true };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: "خطا در دریافت جزئیات برنامه" };
        } finally {
            this.setLoading(false);
        }
    }

    public async createPlan(payload: CreatePlanPayload): Promise<ACResult> {
        try {
            const res = await api.post("/class/automatic/admin/plans/", payload, { cache: false } as any);
            if (res.data.success) {
                this.adminPlans = [res.data.plan, ...this.adminPlans];
                this.adminPlansTotal += 1;
                this.notify();
                return { success: true, message: res.data.message };
            }
            return { success: false, message: res.data.message, error: res.data.error };
        } catch (e: any) {
            return { success: false, message: e.response?.data?.message || "خطا در ایجاد برنامه" };
        }
    }

    public async updatePlan(planId: string, data: Partial<CreatePlanPayload>): Promise<ACResult> {
        try {
            const res = await api.patch(`/class/automatic/admin/plans/${planId}/`, data, { cache: false } as any);
            if (res.data.success) {
                this.adminPlans = this.adminPlans.map((p) =>
                    p.id === planId ? { ...p, ...res.data.plan } : p
                );
                if (this.activePlan?.id === planId) {
                    this.activePlan = { ...this.activePlan, ...res.data.plan };
                }
                this.notify();
                return { success: true };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: "خطا در بروزرسانی برنامه" };
        }
    }

    public async updateAdminStep(stepId: string, data: { status?: string; admin_note?: string; scheduled_date?: string }): Promise<ACResult> {
        try {
            const res = await api.patch(`/class/automatic/admin/steps/${stepId}/`, data, { cache: false } as any);
            if (res.data.success && this.activePlan) {
                this.activePlan = {
                    ...this.activePlan,
                    steps: this.activePlan.steps.map((s) => s.id === stepId ? res.data.step : s),
                };
                this.notify();
                return { success: true };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: "خطا در بروزرسانی مرحله" };
        }
    }

    public async updateCallSession(
        sessionId: string,
        status: CallSessionStatus,
        notes?: string,
    ): Promise<ACResult & { session?: OnlineCallSession }> {
        try {
            const res = await api.patch(
                `/class/automatic/admin/call-sessions/${sessionId}/`,
                { status, notes: notes ?? "" },
                { cache: false } as any,
            );
            if (res.data.success && this.activePlan) {
                this.activePlan = {
                    ...this.activePlan,
                    call_sessions: this.activePlan.call_sessions.map((s) =>
                        s.id === sessionId ? res.data.session : s,
                    ),
                };
                this.notify();
                return { success: true, session: res.data.session };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: "خطا در بروزرسانی جلسه تماس" };
        }
    }

    public async logCall(planId: string, notes: string): Promise<ACResult> {
        try {
            const res = await api.post(
                "/class/automatic/admin/calls/",
                { plan: planId, notes },
                { cache: false } as any
            );
            if (res.data.success) {
                this.callLogs = [res.data.log, ...this.callLogs];
                this.notify();
                return { success: true, message: res.data.message };
            }
            return { success: false, message: res.data.message };
        } catch (e: any) {
            return { success: false, message: "خطا در ثبت تماس" };
        }
    }

    public clearActivePlan(): void {
        this.activePlan = null;
        this.callLogs = [];
        this.notify();
    }
}

export const automaticClassManager = AutomaticClassManager.getInstance();
