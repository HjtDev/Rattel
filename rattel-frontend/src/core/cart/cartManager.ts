"use client";

import { api } from "../api";
import { authManager } from "../auth/authManager";

export interface CartItem {
    app_label: string;
    model: string;
    object_id: string;
    quantity: number;
    name?: string;
    picture?: string | null;
    price?: number;
    new_price?: number;
}

export interface CartItemMeta {
    name?: string;
    picture?: string | null;
    price?: number;
    new_price?: number;
}

const GUEST_CART_KEY = "guest_cart";

class CartManager {
    private static instance: CartManager;
    private items: CartItem[] = [];
    private totalPrice: number = 0;
    private isAuth: boolean = false;
    private listeners: Set<() => void> = new Set();

    private constructor() {
        if (typeof window === "undefined") return;

        this.isAuth = authManager.isAuthenticated();

        authManager.subscribe((user) => {
            const wasAuth = this.isAuth;
            this.isAuth = user !== null;

            if (!wasAuth && this.isAuth) {
                this.migrateGuestCartToBackend();
            } else if (wasAuth && !this.isAuth) {
                this.items = [];
                this.totalPrice = 0;
                this.notifyListeners();
            }
        });

        if (this.isAuth) {
            this.refresh();
        } else {
            this.loadFromStorage();
        }
    }

    public static getInstance(): CartManager {
        if (!CartManager.instance) {
            CartManager.instance = new CartManager();
        }
        return CartManager.instance;
    }

    public subscribe(callback: () => void): () => void {
        this.listeners.add(callback);
        return () => this.listeners.delete(callback);
    }

    private notifyListeners(): void {
        this.listeners.forEach((cb) => cb());
    }

    private loadFromStorage(): void {
        try {
            const raw = localStorage.getItem(GUEST_CART_KEY);
            this.items = raw ? JSON.parse(raw) : [];
            this.totalPrice = this.calculateTotal();
        } catch {
            this.items = [];
            this.totalPrice = 0;
        }
    }

    private saveToStorage(): void {
        try {
            localStorage.setItem(GUEST_CART_KEY, JSON.stringify(this.items));
        } catch {
            // quota exceeded or private browsing — silently ignore
        }
    }

    private clearStorage(): void {
        try {
            localStorage.removeItem(GUEST_CART_KEY);
        } catch {}
    }

    private calculateTotal(): number {
        return this.items.reduce((total, item) => {
            const unit =
                item.new_price && item.new_price > 0
                    ? item.new_price
                    : item.price ?? 0;
            return total + unit * item.quantity;
        }, 0);
    }

    public async refresh(): Promise<void> {
        try {
            const response = await api.get("/cart/", { cache: false });
            if (response.data.success) {
                this.items = (response.data.items ?? []).map((item: any) => ({
                    app_label: item.app_label ?? "",
                    model: item.model ?? "",
                    object_id: String(item.object_id ?? ""),
                    quantity: item.quantity ?? 1,
                    name: item.name,
                    picture: item.picture ?? null,
                    price: item.price,
                    new_price: item.new_price,
                }));
                this.totalPrice = response.data.total_price ?? this.calculateTotal();
                this.notifyListeners();
            }
        } catch {
            // keep existing state on network failure
        }
    }

    private async migrateGuestCartToBackend(): Promise<void> {
        const guestItems = [...this.items];
        this.items = [];
        this.totalPrice = 0;
        this.clearStorage();
        this.notifyListeners();

        for (const item of guestItems) {
            try {
                await api.post("/cart/", {
                    app_label: item.app_label,
                    model: item.model,
                    object_id: item.object_id,
                    quantity: item.quantity,
                });
            } catch {
                // item may be invalid or already purchased — skip silently
            }
        }

        await this.refresh();
    }

    public async add(
        app_label: string,
        model: string,
        object_id: string,
        quantity: number = 1,
        meta?: CartItemMeta
    ): Promise<{ success: boolean; message: string }> {
        if (this.isAuth) {
            try {
                const response = await api.post("/cart/", {
                    app_label,
                    model,
                    object_id,
                    quantity,
                });
                if (response.data.success) {
                    await this.refresh();
                    return { success: true, message: response.data.message };
                }
                return { success: false, message: response.data.message ?? "Failed to add item" };
            } catch (error: any) {
                return {
                    success: false,
                    message: error.response?.data?.message ?? "Failed to add item",
                };
            }
        }

        const existing = this.items.find(
            (i) =>
                i.app_label === app_label &&
                i.model === model &&
                i.object_id === object_id
        );

        if (existing) {
            const newQty = existing.quantity + quantity;
            if (newQty <= 0) {
                this.items = this.items.filter(
                    (i) =>
                        !(
                            i.app_label === app_label &&
                            i.model === model &&
                            i.object_id === object_id
                        )
                );
                this.totalPrice = this.calculateTotal();
                this.saveToStorage();
                this.notifyListeners();
                return { success: true, message: "removed" };
            }
            existing.quantity = newQty;
        } else {
            if (quantity <= 0) {
                return { success: false, message: "Item not in cart" };
            }
            this.items.push({ app_label, model, object_id, quantity, ...meta });
        }

        this.totalPrice = this.calculateTotal();
        this.saveToStorage();
        this.notifyListeners();
        return { success: true, message: existing ? "updated" : "added" };
    }

    public async remove(
        app_label: string,
        model: string,
        object_id: string
    ): Promise<{ success: boolean; message: string }> {
        if (this.isAuth) {
            try {
                const response = await api.delete("/cart/", {
                    data: { app_label, model, object_id },
                });
                if (response.data.success) {
                    this.items = this.items.filter(
                        (i) =>
                            !(
                                i.app_label === app_label &&
                                i.model === model &&
                                i.object_id === object_id
                            )
                    );
                    this.notifyListeners();
                    return { success: true, message: "removed" };
                }
                return { success: false, message: response.data.message ?? "Failed to remove" };
            } catch (error: any) {
                return {
                    success: false,
                    message: error.response?.data?.message ?? "Failed to remove item",
                };
            }
        }

        const before = this.items.length;
        this.items = this.items.filter(
            (i) =>
                !(
                    i.app_label === app_label &&
                    i.model === model &&
                    i.object_id === object_id
                )
        );
        if (this.items.length === before) {
            return { success: false, message: "Item not in cart" };
        }
        this.totalPrice = this.calculateTotal();
        this.saveToStorage();
        this.notifyListeners();
        return { success: true, message: "removed" };
    }

    public async clear(): Promise<{ success: boolean }> {
        if (this.isAuth) {
            try {
                await api.delete("/cart/");
                this.items = [];
                this.totalPrice = 0;
                this.notifyListeners();
                return { success: true };
            } catch {
                return { success: false };
            }
        }

        this.items = [];
        this.totalPrice = 0;
        this.clearStorage();
        this.notifyListeners();
        return { success: true };
    }

    public getItems(): CartItem[] {
        return this.items;
    }

    public length(): number {
        return this.items.length;
    }

    public getTotalPrice(): number {
        return this.totalPrice;
    }
}

export const cartManager = CartManager.getInstance();
