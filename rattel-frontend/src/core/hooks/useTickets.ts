"use client";

import { useEffect, useState } from "react";
import { ticketManager, Ticket, TicketDetail } from "../tickets/ticketManager";

/**
 * useTickets hook - Provides reactive access to ticket state
 * Follows the same pattern as useAuth
 */
export function useTickets() {
    const [tickets, setTickets] = useState<Ticket[]>(ticketManager.getTickets());
    const [total, setTotal] = useState<number>(ticketManager.getTotal());
    const [activeTicket, setActiveTicket] = useState<TicketDetail | null>(
        ticketManager.getActiveTicket()
    );
    const [isLoading, setIsLoading] = useState<boolean>(ticketManager.getIsLoading());
    const [error, setError] = useState<string | null>(ticketManager.getError());

    useEffect(() => {
        // Subscribe to ticket state changes
        const unsubscribe = ticketManager.subscribe(() => {
            setTickets(ticketManager.getTickets());
            setTotal(ticketManager.getTotal());
            setActiveTicket(ticketManager.getActiveTicket());
            setIsLoading(ticketManager.getIsLoading());
            setError(ticketManager.getError());
        });

        // Cleanup subscription on unmount
        return () => {
            unsubscribe();
        };
    }, []);

    return {
        tickets,
        total,
        activeTicket,
        isLoading,
        error,
        fetchTickets: ticketManager.fetchTickets.bind(ticketManager),
        fetchTicketDetail: ticketManager.fetchTicketDetail.bind(ticketManager),
        createTicket: ticketManager.createTicket.bind(ticketManager),
        sendMessage: ticketManager.sendMessage.bind(ticketManager),
        closeTicket: ticketManager.closeTicket.bind(ticketManager),
        reopenTicket: ticketManager.reopenTicket.bind(ticketManager),
        clearActiveTicket: ticketManager.clearActiveTicket.bind(ticketManager),
        reset: ticketManager.reset.bind(ticketManager),
    };
}
