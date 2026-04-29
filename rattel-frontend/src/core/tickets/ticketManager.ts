"use client";

import { api } from "../api";

// ─── Types ────────────────────────────────────────────────────────────────────

export type TicketStatus = "open" | "in_progress" | "waiting_user" | "closed";
export type TicketPriority = "low" | "medium" | "high" | "urgent";
export type TicketCategory =
    | "technical"
    | "billing"
    | "content"
    | "account"
    | "other";

export interface MessageSender {
    name: string;
    profile_picture: string | null;
}

export interface TicketMessage {
    id: number;
    sender: MessageSender | null;
    body: string;
    attachment: string | null;
    is_staff_reply: boolean;
    created_at: string;
}

export interface Ticket {
    id: string;
    subject: string;
    status: TicketStatus;
    priority: TicketPriority;
    category: TicketCategory;
    message_count: number;
    created_at: string;
    updated_at: string;
}

export interface TicketDetail extends Ticket {
    messages: TicketMessage[];
}

// ─── Result shapes ────────────────────────────────────────────────────────────

export interface TicketResult {
    success: boolean;
    message?: string;
    error?: number;
}

export interface TicketListResult extends TicketResult {
    tickets?: Ticket[];
    total?: number;
}

export interface TicketDetailResult extends TicketResult {
    ticket?: TicketDetail;
}

export interface TicketCreateResult extends TicketResult {
    ticket?: TicketDetail;
}

export interface MessageSendResult extends TicketResult {
    reply?: TicketMessage;
}

// ─── Create-ticket payload ─────────────────────────────────────────────────

export interface CreateTicketPayload {
    subject: string;
    body: string;
    category?: TicketCategory;
    priority?: TicketPriority;
    /** Optional image file (JPG/PNG ≤ 3 MB). */
    attachment?: File | null;
}

// ─── Reply payload ────────────────────────────────────────────────────────────

export interface SendMessagePayload {
    body: string;
    /** Optional image file (JPG/PNG ≤ 3 MB). */
    attachment?: File | null;
}

// ─── Manager ──────────────────────────────────────────────────────────────────

/**
 * Singleton that owns all ticket-related state and API calls.
 * Components subscribe via the `useTickets` hook instead of
 * calling this class directly.
 */
class TicketManager {
    private static instance: TicketManager;

    private tickets: Ticket[] = [];
    private total: number = 0;
    private activeTicket: TicketDetail | null = null;
    private isLoading: boolean = false;
    private error: string | null = null;

    private listeners: Set<() => void> = new Set();

    private constructor() {}

    public static getInstance(): TicketManager {
        if (!TicketManager.instance) {
            TicketManager.instance = new TicketManager();
        }
        return TicketManager.instance;
    }

    // ── Subscription ──────────────────────────────────────────────────────────

    /**
     * Subscribe to any state change. Returns an unsubscribe function.
     *
     * @param callback - Called whenever state changes.
     */
    public subscribe(callback: () => void): () => void {
        this.listeners.add(callback);
        return () => this.listeners.delete(callback);
    }

    private notify(): void {
        this.listeners.forEach((cb) => cb());
    }

    // ── State accessors ───────────────────────────────────────────────────────

    public getTickets(): Ticket[] {
        return this.tickets;
    }

    public getTotal(): number {
        return this.total;
    }

    public getActiveTicket(): TicketDetail | null {
        return this.activeTicket;
    }

    public getIsLoading(): boolean {
        return this.isLoading;
    }

    public getError(): string | null {
        return this.error;
    }

    // ── Private helpers ───────────────────────────────────────────────────────

    private setLoading(value: boolean): void {
        this.isLoading = value;
        this.notify();
    }

    private setError(value: string | null): void {
        this.error = value;
        this.notify();
    }

    /**
     * Build a FormData body so both text fields and an optional file can be
     * sent in a single multipart request.
     */
    private buildFormData(
        fields: Record<string, string | undefined | null>,
        attachment?: File | null
    ): FormData {
        const form = new FormData();
        for (const [key, value] of Object.entries(fields)) {
            if (value !== undefined && value !== null) {
                form.append(key, value);
            }
        }
        if (attachment) {
            form.append("attachment", attachment);
        }
        return form;
    }

    // ── API methods ───────────────────────────────────────────────────────────

    /**
     * Fetch the authenticated user's ticket list.
     *
     * @param statusFilter - Optional status to filter by.
     */
    public async fetchTickets(
        statusFilter?: TicketStatus
    ): Promise<TicketListResult> {
        this.setLoading(true);
        this.setError(null);

        try {
            const params = statusFilter ? `?status=${statusFilter}` : "";
            const response = await api.get(`/tickets/${params}`, {
                cache: false,
            });

            if (response.data.success) {
                this.tickets = response.data.tickets ?? [];
                this.total = response.data.total ?? 0;
                this.notify();
                return {
                    success: true,
                    tickets: this.tickets,
                    total: this.total,
                };
            }

            const msg = response.data.message || "Failed to load tickets.";
            this.setError(msg);
            return { success: false, message: msg, error: response.data.error };
        } catch (err: any) {
            const msg =
                err.response?.data?.message || "Failed to load tickets.";
            this.setError(msg);
            return { success: false, message: msg };
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * Fetch a single ticket with its full message thread.
     *
     * @param ticketId - UUID of the ticket.
     */
    public async fetchTicketDetail(
        ticketId: string
    ): Promise<TicketDetailResult> {
        this.setLoading(true);
        this.setError(null);

        try {
            const response = await api.get(`/tickets/${ticketId}/`, {
                cache: false,
            });

            if (response.data.success) {
                this.activeTicket = response.data.ticket;
                this.notify();
                return { success: true, ticket: this.activeTicket ?? undefined };
            }

            const msg =
                response.data.message || "Failed to load ticket details.";
            this.setError(msg);
            return { success: false, message: msg, error: response.data.error };
        } catch (err: any) {
            const msg =
                err.response?.data?.message || "Failed to load ticket details.";
            this.setError(msg);
            return { success: false, message: msg };
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * Create a new ticket with an initial message.
     * Sends a multipart/form-data request so an optional attachment is supported.
     *
     * @param payload - Ticket creation data.
     */
    public async createTicket(
        payload: CreateTicketPayload
    ): Promise<TicketCreateResult> {
        this.setLoading(true);
        this.setError(null);

        try {
            const form = this.buildFormData(
                {
                    subject: payload.subject,
                    body: payload.body,
                    category: payload.category ?? "other",
                    priority: payload.priority ?? "medium",
                },
                payload.attachment
            );

            const response = await api.post("/tickets/", form, {
                headers: { "Content-Type": "multipart/form-data" },
                cache: false,
            } as any);

            if (response.data.success) {
                const newTicket: TicketDetail = response.data.ticket;

                // Prepend to local list so the UI updates immediately
                this.tickets = [
                    {
                        id: newTicket.id,
                        subject: newTicket.subject,
                        status: newTicket.status,
                        priority: newTicket.priority,
                        category: newTicket.category,
                        message_count: newTicket.message_count,
                        created_at: newTicket.created_at,
                        updated_at: newTicket.updated_at,
                    },
                    ...this.tickets,
                ];
                this.total += 1;
                this.activeTicket = newTicket;
                this.notify();

                return { success: true, ticket: newTicket };
            }

            const msg =
                response.data.message || "Failed to create ticket.";
            this.setError(msg);
            return { success: false, message: msg, error: response.data.error };
        } catch (err: any) {
            const msg =
                err.response?.data?.message || "Failed to create ticket.";
            this.setError(msg);
            return { success: false, message: msg };
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * Send a reply message to an existing ticket.
     * Sends a multipart/form-data request so an optional attachment is supported.
     *
     * @param ticketId - UUID of the ticket to reply to.
     * @param payload  - Message body and optional attachment.
     */
    public async sendMessage(
        ticketId: string,
        payload: SendMessagePayload
    ): Promise<MessageSendResult> {
        this.setLoading(true);
        this.setError(null);

        try {
            const form = this.buildFormData(
                { body: payload.body },
                payload.attachment
            );

            const response = await api.post(
                `/tickets/${ticketId}/messages/`,
                form,
                {
                    headers: { "Content-Type": "multipart/form-data" },
                    cache: false,
                } as any
            );

            if (response.data.success) {
                const newMessage: TicketMessage = response.data.reply;

                // Append message to activeTicket if it matches
                if (this.activeTicket?.id === ticketId) {
                    this.activeTicket = {
                        ...this.activeTicket,
                        messages: [...this.activeTicket.messages, newMessage],
                        message_count: this.activeTicket.message_count + 1,
                    };
                }

                // Update message_count in the flat ticket list
                this.tickets = this.tickets.map((t) =>
                    t.id === ticketId
                        ? { ...t, message_count: t.message_count + 1 }
                        : t
                );

                this.notify();
                return { success: true, reply: newMessage };
            }

            const msg = response.data.message || "Failed to send message.";
            this.setError(msg);
            return { success: false, message: msg, error: response.data.error };
        } catch (err: any) {
            const msg =
                err.response?.data?.message || "Failed to send message.";
            this.setError(msg);
            return { success: false, message: msg };
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * Close an open ticket.
     *
     * @param ticketId - UUID of the ticket.
     */
    public async closeTicket(ticketId: string): Promise<TicketResult> {
        this.setLoading(true);
        this.setError(null);

        try {
            const response = await api.post(
                `/tickets/${ticketId}/close/`,
                {},
                { cache: false } as any
            );

            if (response.data.success) {
                this._applyStatusUpdate(ticketId, "closed");
                return { success: true, message: response.data.message };
            }

            const msg = response.data.message || "Failed to close ticket.";
            this.setError(msg);
            return { success: false, message: msg, error: response.data.error };
        } catch (err: any) {
            const msg =
                err.response?.data?.message || "Failed to close ticket.";
            this.setError(msg);
            return { success: false, message: msg };
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * Reopen a previously closed ticket.
     *
     * @param ticketId - UUID of the ticket.
     */
    public async reopenTicket(ticketId: string): Promise<TicketResult> {
        this.setLoading(true);
        this.setError(null);

        try {
            const response = await api.post(
                `/tickets/${ticketId}/reopen/`,
                {},
                { cache: false } as any
            );

            if (response.data.success) {
                this._applyStatusUpdate(ticketId, "open");
                return { success: true, message: response.data.message };
            }

            const msg = response.data.message || "Failed to reopen ticket.";
            this.setError(msg);
            return { success: false, message: msg, error: response.data.error };
        } catch (err: any) {
            const msg =
                err.response?.data?.message || "Failed to reopen ticket.";
            this.setError(msg);
            return { success: false, message: msg };
        } finally {
            this.setLoading(false);
        }
    }

    // ── Local state helpers ───────────────────────────────────────────────────

    /**
     * Optimistically apply a status change to both the flat list and the
     * active ticket so the UI reflects the change without a re-fetch.
     */
    private _applyStatusUpdate(
        ticketId: string,
        newStatus: TicketStatus
    ): void {
        const now = new Date().toISOString();

        this.tickets = this.tickets.map((t) =>
            t.id === ticketId
                ? { ...t, status: newStatus, updated_at: now }
                : t
        );

        if (this.activeTicket?.id === ticketId) {
            this.activeTicket = {
                ...this.activeTicket,
                status: newStatus,
                updated_at: now,
            };
        }

        this.notify();
    }

    /**
     * Clear the cached active ticket. Call this when navigating away from
     * a ticket detail page.
     */
    public clearActiveTicket(): void {
        this.activeTicket = null;
        this.notify();
    }

    /**
     * Clear all cached tickets. Useful on logout.
     */
    public reset(): void {
        this.tickets = [];
        this.total = 0;
        this.activeTicket = null;
        this.isLoading = false;
        this.error = null;
        this.notify();
    }
}

export const ticketManager = TicketManager.getInstance();
