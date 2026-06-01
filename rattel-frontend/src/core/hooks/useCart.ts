"use client";

import { useEffect, useState } from "react";
import { cartManager, CartItem } from "../cart/cartManager";

export function useCart() {
    const [items, setItems] = useState<CartItem[]>(cartManager.getItems());
    const [totalPrice, setTotalPrice] = useState<number>(cartManager.getTotalPrice());

    useEffect(() => {
        const unsubscribe = cartManager.subscribe(() => {
            setItems([...cartManager.getItems()]);
            setTotalPrice(cartManager.getTotalPrice());
        });
        // Sync state with any changes that happened before this component mounted
        setItems([...cartManager.getItems()]);
        setTotalPrice(cartManager.getTotalPrice());
        return unsubscribe;
    }, []);

    return {
        items,
        totalPrice,
        itemCount: items.length,
        add: cartManager.add.bind(cartManager),
        remove: cartManager.remove.bind(cartManager),
        clear: cartManager.clear.bind(cartManager),
        refresh: cartManager.refresh.bind(cartManager),
    };
}
