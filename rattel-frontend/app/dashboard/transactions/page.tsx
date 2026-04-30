"use client"

import { useState, useMemo } from "react";
import DashboardBase from "@/src/components/dashboard/DashboardBase";
import { useTransactions } from "@/src/core/hooks/useTransactions";

// Helper function to format date
const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('fa-IR').format(date);
};

// Helper function to format amount
const formatAmount = (amount: number, currency: string): string => {
    const formatted = new Intl.NumberFormat('fa-IR').format(amount);
    const currencyLabel = currency === 'IRT' ? 'تومان' : 'ریال';
    return `${formatted} ${currencyLabel}`;
};

// Helper function to get status badge
const getStatusBadge = (status: string): { className: string; label: string } => {
    switch (status) {
        case 'success':
            return { className: 'badge bg-success bg-opacity-10 text-success', label: 'موفق' };
        case 'pending':
            return { className: 'badge bg-warning bg-opacity-10 text-warning', label: 'در انتظار' };
        case 'failed':
            return { className: 'badge bg-danger bg-opacity-10 text-danger', label: 'ناموفق' };
        case 'refunded':
            return { className: 'badge bg-info bg-opacity-10 text-info', label: 'بازگشت داده شده' };
        default:
            return { className: 'badge bg-secondary bg-opacity-10 text-secondary', label: status };
    }
};

// Helper function to get reason label
const getReasonLabel = (reason: string): string => {
    switch (reason) {
        case 'payment':
            return 'پرداخت';
        case 'refund':
            return 'بازگشت وجه';
        case 'withdrawal':
            return 'برداشت';
        case 'deposit':
            return 'واریز';
        case 'fee':
            return 'کارمزد';
        case 'adjustment':
            return 'تعدیل';
        default:
            return reason;
    }
};

function TransactionContent() {
    const { transactions, isLoading } = useTransactions();
    const [searchQuery, setSearchQuery] = useState("");

    // Filter transactions based on search query
    const filteredTransactions = useMemo(() => {
        if (!searchQuery.trim()) {
            return transactions;
        }

        const query = searchQuery.toLowerCase();
        return transactions.filter((transaction) => {
            const id = transaction.tracking_id.toLowerCase();
            const description = transaction.description?.toLowerCase() || '';
            const amount = transaction.amount.toString();
            const status = getStatusBadge(transaction.transaction_status).label.toLowerCase();
            const reason = getReasonLabel(transaction.transaction_reason).toLowerCase();
            
            return (
                id.includes(query) ||
                description.includes(query) ||
                amount.includes(query) ||
                status.includes(query) ||
                reason.includes(query)
            );
        });
    }, [transactions, searchQuery]);

    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSearchQuery(e.target.value);
    };

    const handleSearchSubmit = (e: React.FormEvent) => {
        e.preventDefault();
    };

    return (
        <div className="col-xl-9">
            <div className="card bg-transparent border rounded-3">
                <div className="card-header bg-transparent border-bottom">
                    <h3 className="mb-0 fs-5 ff-vb">
                        پرداخت ها
                    </h3>
                </div>
                <div className="card-body">
                    <div className="row g-3 align-items-center justify-content-between mb-4">
                        <div className="col-md-12">
                            <form className="rounded position-relative" onSubmit={handleSearchSubmit}>
                                <input 
                                    className="form-control pe-5 bg-transparent" 
                                    type="search" 
                                    placeholder="جستجو در تراکنش‌ها..."
                                    aria-label="Search"
                                    value={searchQuery}
                                    onChange={handleSearchChange}
                                />
                                <button
                                    className="bg-transparent p-2 position-absolute top-50 end-0 translate-middle-y border-0 text-primary-hover text-reset"
                                    type="submit">
                                    <i className="fas fa-search fs-6">
                                    </i>
                                </button>
                            </form>
                        </div>
                    </div>
                    
                    {isLoading ? (
                        <div className="text-center py-5">
                            <div className="spinner-border text-primary" role="status">
                                <span className="visually-hidden">در حال بارگذاری...</span>
                            </div>
                        </div>
                    ) : filteredTransactions.length === 0 ? (
                        <div className="text-center py-5">
                            <p className="text-muted">
                                {searchQuery ? 'تراکنشی یافت نشد' : 'هنوز تراکنشی ثبت نشده است'}
                            </p>
                        </div>
                    ) : (
                        <div className="table-responsive border-0">
                            <table className="table table-dark-gray align-middle p-4 mb-0 table-hover">
                                <thead>
                                <tr>
                                    <th scope="col" className="border-0 rounded-start">
                                        پرداختی
                                    </th>
                                    <th scope="col" className="border-0">
                                        مبلغ
                                    </th>
                                    <th scope="col" className="border-0">
                                        وضعیت
                                    </th>
                                    <th scope="col" className="border-0 rounded-end">
                                        تاریخ
                                    </th>
                                </tr>
                                </thead>
                                <tbody>
                                {filteredTransactions.map((transaction) => {
                                    const statusBadge = getStatusBadge(transaction.transaction_status);
                                    return (
                                        <tr key={transaction.tracking_id}>
                                            <td>
                                                <h6 className="mt-2 mt-lg-0 mb-0 fw-normal">
                                                    {getReasonLabel(transaction.transaction_reason)} {transaction.tracking_id}
                                                </h6>
                                                {transaction.description && (
                                                    <small className="text-muted">{transaction.description}</small>
                                                )}
                                            </td>
                                            <td>
                                                {formatAmount(transaction.amount, transaction.currency)}
                                            </td>
                                            <td className="text-center text-sm-start">
                                                <span className={statusBadge.className}>
                                                    {statusBadge.label}
                                                </span>
                                            </td>
                                            <td>
                                                {formatDate(transaction.created_at)}
                                            </td>
                                        </tr>
                                    );
                                })}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

export default function Transactions() {
    return (
        <DashboardBase Content={<TransactionContent />} />
    )
}
