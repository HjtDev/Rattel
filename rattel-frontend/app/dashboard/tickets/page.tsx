"use client"

import { useState, useEffect, useRef } from "react";
import DashboardBase from "@/src/components/dashboard/DashboardBase";
import { useTickets } from "@/src/core/hooks/useTickets";
import { toast } from "react-toastify";
import { getMediaUrl } from "@/src/core/utils";
import type { TicketCategory, TicketPriority } from "@/src/core/tickets/ticketManager";

// Helper functions
const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('fa-IR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
};

const getStatusBadge = (status: string): { className: string; label: string } => {
    switch (status) {
        case 'open':
            return { className: 'badge bg-success bg-opacity-10 text-success', label: 'باز' };
        case 'in_progress':
            return { className: 'badge bg-primary bg-opacity-10 text-primary', label: 'در حال بررسی' };
        case 'waiting_user':
            return { className: 'badge bg-warning bg-opacity-10 text-warning', label: 'در انتظار پاسخ شما' };
        case 'closed':
            return { className: 'badge bg-secondary bg-opacity-10 text-secondary', label: 'بسته شده' };
        default:
            return { className: 'badge bg-secondary', label: status };
    }
};

const getPriorityBadge = (priority: string): { className: string; label: string } => {
    switch (priority) {
        case 'urgent':
            return { className: 'badge bg-danger', label: 'فوری' };
        case 'high':
            return { className: 'badge bg-warning', label: 'بالا' };
        case 'medium':
            return { className: 'badge bg-info', label: 'متوسط' };
        case 'low':
            return { className: 'badge bg-secondary', label: 'پایین' };
        default:
            return { className: 'badge bg-secondary', label: priority };
    }
};

const getCategoryLabel = (category: string): string => {
    switch (category) {
        case 'technical': return 'فنی';
        case 'billing': return 'مالی';
        case 'content': return 'محتوا';
        case 'account': return 'حساب کاربری';
        case 'other': return 'سایر';
        default: return category;
    }
};

function TicketsContent() {
    const { tickets, activeTicket, isLoading, fetchTickets, fetchTicketDetail, createTicket, sendMessage, closeTicket, reopenTicket, clearActiveTicket } = useTickets();
    
    // Modal states
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showDetailModal, setShowDetailModal] = useState(false);
    
    // Create ticket form
    const [createForm, setCreateForm] = useState({
        subject: '',
        body: '',
        category: 'technical' as TicketCategory,
        priority: 'medium' as TicketPriority,
        attachment: null as File | null,
    });
    const [createErrors, setCreateErrors] = useState({ subject: '', body: '' });
    const [isCreating, setIsCreating] = useState(false);
    
    // Reply form
    const [replyBody, setReplyBody] = useState('');
    const [replyAttachment, setReplyAttachment] = useState<File | null>(null);
    const [replyError, setReplyError] = useState('');
    const [isSending, setIsSending] = useState(false);
    
    // Auto-refresh interval
    const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);

    // Scroller
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };
    
    // Fetch tickets on mount
    useEffect(() => {
        fetchTickets();
    }, []);
    
    // Auto-refresh specific ticket every 15 seconds when its detail modal is open
    useEffect(() => {
        if (showDetailModal && activeTicket) {
            // Set up interval to refetch this specific ticket every 15 seconds
            refreshIntervalRef.current = setInterval(() => {
                fetchTicketDetail(activeTicket.id);
            }, 15000); // 15 seconds
            
            return () => {
                if (refreshIntervalRef.current) {
                    clearInterval(refreshIntervalRef.current);
                    refreshIntervalRef.current = null;
                }
            };
        } else {
            // Clear interval when modal is closed
            if (refreshIntervalRef.current) {
                clearInterval(refreshIntervalRef.current);
                refreshIntervalRef.current = null;
            }
        }
    }, [showDetailModal, activeTicket]);
    
    // Handle create modal
    const handleOpenCreateModal = () => {
        setShowCreateModal(true);
        setCreateForm({
            subject: '',
            body: '',
            category: 'technical',
            priority: 'medium',
            attachment: null,
        });
        setCreateErrors({ subject: '', body: '' });
    };
    
    const handleCloseCreateModal = () => {
        setShowCreateModal(false);
    };
    
    const handleCreateInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setCreateForm(prev => ({ ...prev, [name]: value }));
        setCreateErrors(prev => ({ ...prev, [name]: '' }));
    };
    
    const handleCreateFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            if (file.size > 3 * 1024 * 1024) {
                toast.error('حجم فایل نباید بیشتر از 3 مگابایت باشد');
                return;
            }
            if (!['image/jpeg', 'image/jpg', 'image/png'].includes(file.type)) {
                toast.error('فقط فایل‌های JPG و PNG مجاز هستند');
                return;
            }
            setCreateForm(prev => ({ ...prev, attachment: file }));
        }
    };
    
    const validateCreateForm = (): boolean => {
        const errors = { subject: '', body: '' };
        
        if (!createForm.subject.trim()) {
            errors.subject = 'موضوع نمی‌تواند خالی باشد';
        } else if (createForm.subject.length > 255) {
            errors.subject = 'موضوع نباید بیشتر از 255 کاراکتر باشد';
        }
        
        if (!createForm.body.trim()) {
            errors.body = 'متن پیام نمی‌تواند خالی باشد';
        }
        
        setCreateErrors(errors);
        return !errors.subject && !errors.body;
    };
    
    const handleCreateSubmit = async () => {
        if (!validateCreateForm() || isCreating) return;
        
        setIsCreating(true);
        
        try {
            const result = await createTicket({
                subject: createForm.subject,
                body: createForm.body,
                category: createForm.category,
                priority: createForm.priority,
                attachment: createForm.attachment,
            });
            
            if (result.success) {
                toast.success('تیکت با موفقیت ایجاد شد');
                handleCloseCreateModal();
                fetchTickets(); // Refresh list
            } else {
                toast.error(result.message || 'خطا در ایجاد تیکت');
            }
        } catch {
            toast.error('خطا در ایجاد تیکت');
        } finally {
            setIsCreating(false);
        }
    };
    
    // Handle detail modal
    const handleOpenDetailModal = async (ticketId: string) => {
        setShowDetailModal(true);
        // Fetch the ticket detail - this will trigger the useEffect to start auto-refresh
        await fetchTicketDetail(ticketId);
        setTimeout(scrollToBottom, 250);
    };
    
    const handleCloseDetailModal = () => {
        setShowDetailModal(false);
        clearActiveTicket();
        if (refreshIntervalRef.current) {
            clearInterval(refreshIntervalRef.current);
        }
    };
    
    const handleReplyFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            if (file.size > 3 * 1024 * 1024) {
                toast.error('حجم فایل نباید بیشتر از 3 مگابایت باشد');
                return;
            }
            if (!['image/jpeg', 'image/jpg', 'image/png'].includes(file.type)) {
                toast.error('فقط فایل‌های JPG و PNG مجاز هستند');
                return;
            }
            setReplyAttachment(file);
        }
    };
    
    const handleSendReply = async () => {
        if (!activeTicket || isSending) return;
        
        if (!replyBody.trim()) {
            setReplyError('متن پیام نمی‌تواند خالی باشد');
            return;
        }
        
        setIsSending(true);
        setReplyError('');
        
        try {
            const result = await sendMessage(activeTicket.id, {
                body: replyBody,
                attachment: replyAttachment,
            });
            
            if (result.success) {
                setReplyBody('');
                setReplyAttachment(null);
                // Refresh ticket to show new message
                await fetchTicketDetail(activeTicket.id);
                scrollToBottom();
            } else {
                toast.error(result.message || 'خطا در ارسال پیام');
            }
        } catch {
            toast.error('خطا در ارسال پیام');
        } finally {
            setIsSending(false);
        }
    };
    
    const handleCloseTicket = async () => {
        if (!activeTicket) return;
        
        const result = await closeTicket(activeTicket.id);
        if (result.success) {
            toast.success('تیکت بسته شد');
            await fetchTicketDetail(activeTicket.id);
            fetchTickets(); // Refresh list
        } else {
            toast.error(result.message || 'خطا در بستن تیکت');
        }
    };
    
    const handleReopenTicket = async () => {
        if (!activeTicket) return;
        
        const result = await reopenTicket(activeTicket.id);
        if (result.success) {
            toast.success('تیکت بازگشایی شد');
            await fetchTicketDetail(activeTicket.id);
            fetchTickets(); // Refresh list
        } else {
            toast.error(result.message || 'خطا در بازگشایی تیکت');
        }
    };

    return (
        <div className="col-xl-9">
            <div className="card bg-transparent border rounded-3">
                <div className="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center">
                    <h3 className="mb-0 fs-5 ff-vb">تیکت‌های من</h3>
                    <button className="btn btn-primary btn-sm" onClick={handleOpenCreateModal}>
                        <i className="bi bi-plus-circle me-2"></i>
                        تیکت جدید
                    </button>
                </div>
                <div className="card-body">
                    {isLoading && tickets.length === 0 ? (
                        <div className="text-center py-5">
                            <div className="spinner-border text-primary" role="status">
                                <span className="visually-hidden">در حال بارگذاری...</span>
                            </div>
                        </div>
                    ) : tickets.length === 0 ? (
                        <div className="text-center py-5">
                            <p className="text-muted">هنوز تیکتی ثبت نشده است</p>
                        </div>
                    ) : (
                        <div className="table-responsive border-0">
                            <table className="table table-dark-gray align-middle p-4 mb-0 table-hover">
                                <thead>
                                <tr>
                                    <th scope="col" className="border-0 rounded-start">موضوع</th>
                                    <th scope="col" className="border-0">دسته‌بندی</th>
                                    <th scope="col" className="border-0">اولویت</th>
                                    <th scope="col" className="border-0">وضعیت</th>
                                    <th scope="col" className="border-0">پیام‌ها</th>
                                    <th scope="col" className="border-0 rounded-end">تاریخ</th>
                                </tr>
                                </thead>
                                <tbody>
                                {tickets.map((ticket) => {
                                    const statusBadge = getStatusBadge(ticket.status);
                                    const priorityBadge = getPriorityBadge(ticket.priority);
                                    return (
                                        <tr key={ticket.id} onClick={() => handleOpenDetailModal(ticket.id)} style={{ cursor: 'pointer' }}>
                                            <td>
                                                <h6 className="mb-0 fw-normal">{ticket.subject}</h6>
                                                <small className="text-muted">#{ticket.id.slice(0, 8)}</small>
                                            </td>
                                            <td>{getCategoryLabel(ticket.category)}</td>
                                            <td><span className={priorityBadge.className}>{priorityBadge.label}</span></td>
                                            <td><span className={statusBadge.className}>{statusBadge.label}</span></td>
                                            <td>{ticket.message_count}</td>
                                            <td>{formatDate(ticket.created_at)}</td>
                                        </tr>
                                    );
                                })}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>
            
            {/* Create Ticket Modal */}
            {showCreateModal && (
                <div className="modal show d-block" tabIndex={-1} style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
                    <div className="modal-dialog modal-dialog-centered">
                        <div className="modal-content">
                            <div className="modal-header">
                                <h5 className="modal-title ff-vb">ایجاد تیکت جدید</h5>
                                <button type="button" className="btn-close" onClick={handleCloseCreateModal}></button>
                            </div>
                            <div className="modal-body">
                                <div className="mb-3">
                                    <label className="form-label">موضوع *</label>
                                    <input
                                        type="text"
                                        name="subject"
                                        className={`form-control ${createErrors.subject ? 'is-invalid' : ''}`}
                                        value={createForm.subject}
                                        onChange={handleCreateInputChange}
                                        placeholder="موضوع تیکت را وارد کنید"
                                    />
                                    {createErrors.subject && <div className="text-danger small mt-1">{createErrors.subject}</div>}
                                </div>
                                <div className="mb-3">
                                    <label className="form-label">دسته‌بندی</label>
                                    <select name="category" className="form-select" value={createForm.category} onChange={handleCreateInputChange}>
                                        <option value="technical" className={"text-rtl"}>فنی</option>
                                        <option value="billing" className={"text-rtl"}>مالی</option>
                                        <option value="content" className={"text-rtl"}>محتوا</option>
                                        <option value="account" className={"text-rtl"}>حساب کاربری</option>
                                        <option value="other" className={"text-rtl"}>سایر</option>
                                    </select>
                                </div>
                                <div className="mb-3">
                                    <label className="form-label">اولویت</label>
                                    <select name="priority" className="form-select" value={createForm.priority} onChange={handleCreateInputChange}>
                                        <option value="low" className={"text-rtl"}>پایین</option>
                                        <option value="medium" className={"text-rtl"}>متوسط</option>
                                        <option value="high" className={"text-rtl"}>بالا</option>
                                        <option value="urgent" className={"text-rtl"}>فوری</option>
                                    </select>
                                </div>
                                <div className="mb-3">
                                    <label className="form-label">پیام *</label>
                                    <textarea
                                        name="body"
                                        className={`form-control ${createErrors.body ? 'is-invalid' : ''}`}
                                        value={createForm.body}
                                        onChange={handleCreateInputChange}
                                        rows={4}
                                        placeholder="توضیحات خود را وارد کنید"
                                    />
                                    {createErrors.body && <div className="text-danger small mt-1">{createErrors.body}</div>}
                                </div>
                                <div className="mb-3">
                                    <label className="form-label">پیوست (اختیاری)</label>
                                    <input
                                        type="file"
                                        className="form-control"
                                        accept="image/png,image/jpeg,image/jpg"
                                        onChange={handleCreateFileChange}
                                    />
                                    <small className="text-muted">فقط JPG/PNG، حداکثر 3MB</small>
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={handleCloseCreateModal}>لغو</button>
                                <button type="button" className="btn btn-primary" onClick={handleCreateSubmit} disabled={isCreating}>
                                    {isCreating ? 'در حال ارسال...' : 'ایجاد تیکت'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
            
            {/* Ticket Detail Modal */}
            {showDetailModal && activeTicket && (
                <div className="modal show d-block" tabIndex={-1} style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
                    <div className="modal-dialog modal-dialog-centered modal-lg modal-dialog-scrollable">
                        <div className="modal-content">
                            <div className="modal-header">
                                <div>
                                    <h5 className="modal-title ff-vb">{activeTicket.subject}</h5>
                                    <small className="text-muted">#{activeTicket.id.slice(0, 8)}</small>
                                </div>
                                <button type="button" className="btn-close" onClick={handleCloseDetailModal}></button>
                            </div>
                            <div className="modal-body">
                                <div className="d-flex justify-content-between align-items-center mb-3 pb-3 border-bottom">
                                    <div>
                                        <span className={getStatusBadge(activeTicket.status).className + ' me-2'}>
                                            {getStatusBadge(activeTicket.status).label}
                                        </span>
                                        <span className={getPriorityBadge(activeTicket.priority).className + ' me-2'}>
                                            {getPriorityBadge(activeTicket.priority).label}
                                        </span>
                                        <span className="badge bg-light text-dark">
                                            {getCategoryLabel(activeTicket.category)}
                                        </span>
                                    </div>
                                    <div>
                                        {activeTicket.status === 'closed' ? (
                                            <button className="btn btn-sm btn-success" onClick={handleReopenTicket}>
                                                <i className="bi bi-arrow-clockwise me-1"></i>
                                                بازگشایی
                                            </button>
                                        ) : (
                                            <button className="btn btn-sm btn-danger" onClick={handleCloseTicket}>
                                                <i className="bi bi-x-circle me-1"></i>
                                                بستن تیکت
                                            </button>
                                        )}
                                    </div>
                                </div>
                                
                                {/* Messages */}
                                <div className="mb-4" style={{ maxHeight: '400px', overflowY: 'auto' }}>
                                    {activeTicket.messages.map((message) => (
                                        <div key={message.id} className={`mb-3 ${message.is_staff_reply ? 'text-end' : ''}`}>
                                            <div className={`d-inline-block p-3 rounded ${message.is_staff_reply ? 'bg-primary text-white' : 'bg-light'}`} style={{ maxWidth: '80%' }}>
                                                <div className="d-flex align-items-center mb-2">
                                                    {message.sender?.profile_picture && (
                                                        <img
                                                            src={getMediaUrl(message.sender.profile_picture)}
                                                            alt={message.sender.name}
                                                            className="rounded-circle me-2"
                                                            style={{ width: '30px', height: '30px' }}
                                                        />
                                                    )}
                                                    <strong>{message.sender?.name || 'کاربر'}</strong>
                                                    <small className="ms-2 opacity-75">{formatDate(message.created_at)}</small>
                                                </div>
                                                <p className="mb-0">{message.body}</p>
                                                {message.attachment && (
                                                    <div className="mt-2">
                                                        <a href={getMediaUrl(message.attachment)} target="_blank" rel="noopener noreferrer">
                                                            <img src={getMediaUrl(message.attachment)} alt="attachment" className="img-fluid rounded" style={{ maxHeight: '200px' }} />
                                                        </a>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                    <div ref={messagesEndRef} />  {/* Scroll Reference */}
                                </div>
                                
                                {/* Reply Form */}
                                {activeTicket.status !== 'closed' && (
                                    <div className="border-top pt-3">
                                        <div className="mb-3">
                                            <textarea
                                                className={`form-control ${replyError ? 'is-invalid' : ''}`}
                                                value={replyBody}
                                                onChange={(e) => {
                                                    setReplyBody(e.target.value);
                                                    setReplyError('');
                                                }}
                                                rows={3}
                                                placeholder="پاسخ خود را بنویسید..."
                                            />
                                            {replyError && <div className="text-danger small mt-1">{replyError}</div>}
                                        </div>
                                        <div className="d-flex justify-content-between align-items-center">
                                            <div>
                                                <input
                                                    type="file"
                                                    id="replyAttachment"
                                                    className="d-none"
                                                    accept="image/png,image/jpeg,image/jpg"
                                                    onChange={handleReplyFileChange}
                                                />
                                                <label htmlFor="replyAttachment" className="btn btn-sm btn-outline-secondary">
                                                    <i className="bi bi-paperclip me-1"></i>
                                                    {replyAttachment ? replyAttachment.name : 'پیوست'}
                                                </label>
                                            </div>
                                            <button className="btn btn-primary" onClick={handleSendReply} disabled={isSending}>
                                                {isSending ? 'در حال ارسال...' : 'ارسال پاسخ'}
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default function Tickets() {
    return (
        <DashboardBase Content={<TicketsContent />} />
    );
}
