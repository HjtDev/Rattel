"use client"

import { useState, useEffect } from "react";
import DashboardBase from "@/src/components/dashboard/DashboardBase";
import {useAuth} from "@/src/core/hooks/useAuth";
import { toast } from "react-toastify";

function SettingsContent() {
    const {user, isLoading, updateSettings} = useAuth();
    
    // Form state
    const [formData, setFormData] = useState({
        profile_visible: true,
        email_on_login: false,
        email_on_payment: false,
        sms_on_payment: true,
    });
    const [hasChanges, setHasChanges] = useState(false);
    const [isSaving, setIsSaving] = useState(false);

    // Initialize form data when user loads
    useEffect(() => {
        if (user?.settings) {
            setFormData({
                profile_visible: user.settings.profile_visible ?? true,
                email_on_login: user.settings.email_on_login ?? false,
                email_on_payment: user.settings.email_on_payment ?? false,
                sms_on_payment: user.settings.sms_on_payment ?? true,
            });
        }
    }, [user]);

    // Check if form has changes
    useEffect(() => {
        if (!user?.settings) return;
        
        const profileVisibleChanged = formData.profile_visible !== user.settings.profile_visible;
        const emailOnLoginChanged = formData.email_on_login !== user.settings.email_on_login;
        const emailOnPaymentChanged = formData.email_on_payment !== user.settings.email_on_payment;
        const smsOnPaymentChanged = formData.sms_on_payment !== user.settings.sms_on_payment;
        
        setHasChanges(
            profileVisibleChanged || emailOnLoginChanged || 
            emailOnPaymentChanged || smsOnPaymentChanged
        );
    }, [formData, user]);

    const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: checked,
        }));
    };

    const getErrorMessage = (error: number | undefined, message: any): string => {
        // Handle error codes from backend
        switch (error) {
            case -1:
                return "فیلد نامعتبر یا مقدار غیر بولین وارد شده است";
            case -2:
                // For database errors, try to parse the message
                if (typeof message === 'object' && message !== null) {
                    const fieldNames: Record<string, string> = {
                        'profile_visible': 'نمایش عمومی پروفایل',
                        'email_on_login': 'ایمیل هنگام ورود',
                        'email_on_payment': 'ایمیل هنگام پرداخت',
                        'sms_on_payment': 'پیامک هنگام پرداخت',
                    };
                    const errorMessages = Object.entries(message)
                        .map(([field, errors]) => {
                            const fieldName = fieldNames[field] || field;
                            const errorText = Array.isArray(errors) ? errors.join(' ') : errors;
                            return `${fieldName}: ${errorText}`;
                        })
                        .join(' | ');
                    return errorMessages || "خطا در به‌روزرسانی تنظیمات در پایگاه داده";
                }
                return "خطا در به‌روزرسانی تنظیمات در پایگاه داده";
            default:
                // No error code, try to parse message
                if (typeof message === 'string') return message;
                
                if (typeof message === 'object' && message !== null) {
                    const errorMessages = Object.entries(message)
                        .map(([field, errors]) => Array.isArray(errors) ? errors.join(' ') : errors)
                        .join(' ');
                    return errorMessages || "خطا در به‌روزرسانی تنظیمات";
                }
                
                return "خطا در به‌روزرسانی تنظیمات";
        }
    };

    const handleSave = async () => {
        if (!hasChanges || isSaving) return;

        setIsSaving(true);

        try {
            // Prepare update payload - only send changed fields
            const updatePayload: any = {};
            
            if (formData.profile_visible !== user?.settings?.profile_visible) {
                updatePayload.profile_visible = formData.profile_visible;
            }
            if (formData.email_on_login !== user?.settings?.email_on_login) {
                updatePayload.email_on_login = formData.email_on_login;
            }
            if (formData.email_on_payment !== user?.settings?.email_on_payment) {
                updatePayload.email_on_payment = formData.email_on_payment;
            }
            if (formData.sms_on_payment !== user?.settings?.sms_on_payment) {
                updatePayload.sms_on_payment = formData.sms_on_payment;
            }

            const result = await updateSettings(updatePayload);

            if (result.success) {
                toast.success("تنظیمات با موفقیت به‌روزرسانی شد");
            } else {
                toast.error(getErrorMessage(result.error, result.message));
            }
        } catch (error) {
            toast.error("خطا در به‌روزرسانی تنظیمات");
        } finally {
            setIsSaving(false);
        }
    };

    const handleCancel = () => {
        // Reset form to original values
        if (user?.settings) {
            setFormData({
                profile_visible: user.settings.profile_visible ?? true,
                email_on_login: user.settings.email_on_login ?? false,
                email_on_payment: user.settings.email_on_payment ?? false,
                sms_on_payment: user.settings.sms_on_payment ?? true,
            });
        }
    };

    return !isLoading && (
        <div className="col-xl-9">
            <div className="border rounded-3">
                <div className="row">
                    <div className="col-12">
                        <div className="card bg-transparent">
                            <div className="card-header bg-transparent border-bottom">
                                <h3 className="card-header-title fs-5 ff-vb">
                                    تنظیمات
                                </h3>
                            </div>
                            <div className="card-body">
                                <h5 className="mb-4">
                                    تنظیمات پروفایل
                                </h5>
                                <div className="form-check form-switch form-check-md">
                                    <input 
                                        className="form-check-input" 
                                        type="checkbox" 
                                        role="switch" 
                                        id="profilePublic" 
                                        name="profile_visible"
                                        checked={formData.profile_visible}
                                        onChange={handleCheckboxChange}
                                    />
                                    <label className="form-check-label" htmlFor="profilePublic">
                                        قابل مشاهده برای عموم
                                    </label>
                                </div>
                                <hr />
                                <h5 className="card-header-title">
                                    تنظیمات نوتیفیکیشن
                                </h5>
                                <p className="mb-2 mt-3">
                                    نوع اعلان‌هایی را که می‌خواهید دریافت کنید انتخاب کنید
                                </p>
                                <div className="form-check form-switch form-check-md mb-3">
                                    <input 
                                        className="form-check-input" 
                                        type="checkbox" 
                                        id="checkPrivacy1" 
                                        name="email_on_login"
                                        checked={formData.email_on_login}
                                        onChange={handleCheckboxChange}
                                        disabled={true}
                                    />
                                    <label className="form-check-label" htmlFor="checkPrivacy1">
                                        هنگام ورود به سیستم از طریق ایمیل به من اطلاع دهید
                                    </label>
                                </div>
                                <div className="form-check form-switch form-check-md mb-3">
                                    <input 
                                        className="form-check-input" 
                                        type="checkbox" 
                                        id="checkPrivacy2" 
                                        name="sms_on_payment"
                                        checked={formData.sms_on_payment}
                                        onChange={handleCheckboxChange}
                                    />
                                    <label className="form-check-label" htmlFor="checkPrivacy2">
                                        ارسال پیامک تایید برای تمام پرداخت های آنلاین
                                    </label>
                                </div>
                                <div className="form-check form-switch form-check-md mb-3">
                                    <input 
                                        className="form-check-input" 
                                        type="checkbox" 
                                        id="checkPrivacy3" 
                                        name="email_on_payment"
                                        checked={formData.email_on_payment}
                                        onChange={handleCheckboxChange}
                                        disabled={true}
                                    />
                                    <label className="form-check-label" htmlFor="checkPrivacy3">
                                        ارسال ایمیل تایید برای تمام پرداخت های آنلاین
                                    </label>
                                </div>
                                <div className="d-sm-flex justify-content-end">
                                    <button 
                                        type="button" 
                                        className="btn btn-sm btn-primary me-2 mb-0" 
                                        onClick={handleSave}
                                        disabled={!hasChanges || isSaving}
                                    >
                                        {isSaving ? "در حال ذخیره..." : "ذخیره"}
                                    </button>
                                    <button 
                                        type="button"
                                        className="btn btn-sm btn-outline-secondary mb-0"
                                        onClick={handleCancel}
                                        disabled={!hasChanges || isSaving}
                                    >
                                        لغو
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default function Settings() {
    return (
        <DashboardBase Content={<SettingsContent />} />
    )
}
