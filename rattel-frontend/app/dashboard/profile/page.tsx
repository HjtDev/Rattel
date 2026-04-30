"use client"

import { useState, useEffect } from "react";
import DashboardBase from "@/src/components/dashboard/DashboardBase";
import {useAuth} from "@/src/core/hooks/useAuth";
import { toast } from "react-toastify";
import {Properties} from "csstype";

// Validation regex patterns
const NATIONAL_CODE_REGEX = /^\d{10}$/;
const RTL: Properties<string> = {direction: "rtl"};

// Validation functions
const validateNationalCode = (code: string): string | null => {
    if (!code || code.trim().length === 0) {
        return null; // Optional field
    }
    if (!NATIONAL_CODE_REGEX.test(code)) {
        return "کد ملی باید 10 رقم باشد";
    }
    return null;
};

const validateTextField = (value: string, maxLength: number, fieldName: string): string | null => {
    if (!value || value.trim().length === 0) {
        return null; // Optional field
    }
    if (value.length > maxLength) {
        return `${fieldName} نباید بیشتر از ${maxLength} کاراکتر باشد`;
    }
    return null;
};

const validateDate = (date: string): string | null => {
    if (!date || date.trim().length === 0) {
        return null; // Optional field
    }
    const dateObj = new Date(date);
    if (isNaN(dateObj.getTime())) {
        return "تاریخ نامعتبر است";
    }
    return null;
};

function ProfileContent() {
    const {user, isLoading, updateProfile} = useAuth();
    
    // Form state
    const [formData, setFormData] = useState({
        gender: "",
        national_code: "",
        education: "",
        had_other_classes: "",
        memorized: "",
        invited_by: "",
        birthday: "",
        city: "",
        telegram_id: "",
        eitaa_id: "",
        instagram_id: "",
    });
    const [hasChanges, setHasChanges] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [errors, setErrors] = useState({
        national_code: "",
        education: "",
        had_other_classes: "",
        memorized: "",
        invited_by: "",
        birthday: "",
        city: "",
        telegram_id: "",
        eitaa_id: "",
        instagram_id: "",
    });

    // Initialize form data when user loads
    useEffect(() => {
        if (user?.profile) {
            setFormData({
                gender: user.profile.gender || "",
                national_code: user.profile.national_code || "",
                education: user.profile.education || "",
                had_other_classes: user.profile.had_other_classes || "",
                memorized: user.profile.memorized || "",
                invited_by: user.profile.invited_by || "",
                birthday: user.profile.birthday || "",
                city: user.profile.city || "",
                telegram_id: user.profile.telegram_id || "",
                eitaa_id: user.profile.eitaa_id || "",
                instagram_id: user.profile.instagram_id || "",
            });
        }
    }, [user, isLoading]);

    // Check if form has changes
    useEffect(() => {
        if (!user?.profile) return;
        
        const genderChanged = formData.gender !== (user.profile.gender || "");
        const nationalCodeChanged = formData.national_code !== (user.profile.national_code || "");
        const educationChanged = formData.education !== (user.profile.education || "");
        const hadOtherClassesChanged = formData.had_other_classes !== (user.profile.had_other_classes || "");
        const memorizedChanged = formData.memorized !== (user.profile.memorized || "");
        const invitedByChanged = formData.invited_by !== (user.profile.invited_by || "");
        const birthdayChanged = formData.birthday !== (user.profile.birthday || "");
        const cityChanged = formData.city !== (user.profile.city || "");
        const telegramChanged = formData.telegram_id !== (user.profile.telegram_id || "");
        const eitaaChanged = formData.eitaa_id !== (user.profile.eitaa_id || "");
        const instagramChanged = formData.instagram_id !== (user.profile.instagram_id || "");
        
        setHasChanges(
            genderChanged || nationalCodeChanged || educationChanged || 
            hadOtherClassesChanged || memorizedChanged || invitedByChanged || 
            birthdayChanged || cityChanged || telegramChanged || 
            eitaaChanged || instagramChanged
        );
    }, [formData, user]);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value,
        }));
        
        // Clear error for this field when user types
        if (name !== 'gender') {
            setErrors(prev => ({
                ...prev,
                [name]: "",
            }));
        }
    };

    const validateForm = (): boolean => {
        const newErrors = {
            national_code: validateNationalCode(formData.national_code) || "",
            education: validateTextField(formData.education, 150, "تحصیلات") || "",
            had_other_classes: validateTextField(formData.had_other_classes, 500, "کلاس‌های قبلی") || "",
            memorized: validateTextField(formData.memorized, 300, "حفظ قرآن") || "",
            invited_by: validateTextField(formData.invited_by, 60, "معرف") || "",
            birthday: validateDate(formData.birthday) || "",
            city: validateTextField(formData.city, 120, "شهر") || "",
            telegram_id: validateTextField(formData.telegram_id, 50, "آیدی تلگرام") || "",
            eitaa_id: validateTextField(formData.eitaa_id, 50, "آیدی ایتا") || "",
            instagram_id: validateTextField(formData.instagram_id, 50, "آیدی اینستاگرام") || "",
        };
        
        setErrors(newErrors);
        
        return !Object.values(newErrors).some(error => error !== "");
    };

    const getErrorMessage = (error: number | undefined, message: any): string => {
        // Handle error codes from backend
        switch (error) {
            case -1:
                return "اطلاعات وارد شده نامعتبر است یا شامل محتوای خطرناک می‌باشد";
            case -2:
                return "لطفاً ابتدا وارد شوید";
            case -3:
                // For database errors, try to parse the message
                if (typeof message === 'object' && message !== null) {
                    const fieldNames: Record<string, string> = {
                        'gender': 'جنسیت',
                        'national_code': 'کد ملی',
                        'education': 'تحصیلات',
                        'had_other_classes': 'کلاس‌های قبلی',
                        'memorized': 'حفظ قرآن',
                        'invited_by': 'معرف',
                        'birthday': 'تاریخ تولد',
                        'city': 'شهر',
                        'telegram_id': 'آیدی تلگرام',
                        'eitaa_id': 'آیدی ایتا',
                        'instagram_id': 'آیدی اینستاگرام',
                    };
                    const errorMessages = Object.entries(message)
                        .map(([field, errors]) => {
                            const fieldName = fieldNames[field] || field;
                            const errorText = Array.isArray(errors) ? errors.join(' ') : errors;
                            return `${fieldName}: ${errorText}`;
                        })
                        .join(' | ');
                    return errorMessages || "خطا در به‌روزرسانی پروفایل در پایگاه داده";
                }
                return "خطا در به‌روزرسانی پروفایل در پایگاه داده";
            default:
                // No error code, try to parse message
                if (typeof message === 'string') return message;
                
                if (typeof message === 'object' && message !== null) {
                    const errorMessages = Object.entries(message)
                        .map(([field, errors]) => Array.isArray(errors) ? errors.join(' ') : errors)
                        .join(' ');
                    return errorMessages || "خطا در به‌روزرسانی پروفایل";
                }
                
                return "خطا در به‌روزرسانی پروفایل";
        }
    };

    const handleSave = async () => {
        if (!hasChanges || isSaving) return;

        // Validate form before submitting
        if (!validateForm()) {
            toast.error("لطفاً خطاهای فرم را برطرف کنید");
            return;
        }

        setIsSaving(true);

        try {
            // Prepare update payload - only send changed fields
            const updatePayload: any = {};
            
            if (formData.gender !== user?.profile?.gender) updatePayload.gender = formData.gender;
            if (formData.national_code !== user?.profile?.national_code) updatePayload.national_code = formData.national_code;
            if (formData.education !== user?.profile?.education) updatePayload.education = formData.education;
            if (formData.had_other_classes !== user?.profile?.had_other_classes) updatePayload.had_other_classes = formData.had_other_classes;
            if (formData.memorized !== user?.profile?.memorized) updatePayload.memorized = formData.memorized;
            if (formData.invited_by !== user?.profile?.invited_by) updatePayload.invited_by = formData.invited_by;
            if (formData.birthday !== user?.profile?.birthday) updatePayload.birthday = formData.birthday;
            if (formData.city !== user?.profile?.city) updatePayload.city = formData.city;
            if (formData.telegram_id !== user?.profile?.telegram_id) updatePayload.telegram_id = formData.telegram_id;
            if (formData.eitaa_id !== user?.profile?.eitaa_id) updatePayload.eitaa_id = formData.eitaa_id;
            if (formData.instagram_id !== user?.profile?.instagram_id) updatePayload.instagram_id = formData.instagram_id;

            const result = await updateProfile(updatePayload);

            if (result.success) {
                toast.success("پروفایل با موفقیت به‌روزرسانی شد");
            } else {
                toast.error(getErrorMessage(result.error, result.message));
            }
        } catch (error) {
            toast.error("خطا در به‌روزرسانی پروفایل");
        } finally {
            setIsSaving(false);
        }
    };

    return !isLoading && (
        <div className="col-xl-9">
            <div className="card bg-transparent border rounded-3">
                <div className="card-header bg-transparent border-bottom">
                    <h3 className="card-header-title mb-0 ff-vb fs-5">
                        ویرایش پروفایل
                    </h3>
                </div>
                <div className="card-body">
                    <form className="row g-4">
                        <div className="col-md-6">
                            <label className="form-label">
                                جنسیت
                            </label>
                            <select 
                                name="gender" 
                                className="form-select"
                                value={formData.gender}
                                onChange={handleInputChange}
                            >
                                <option value="" className={"text-rtl"}>انتخاب کنید</option>
                                <option value="male" className={"text-rtl"}>مرد</option>
                                <option value="female" className={"text-rtl"}>زن</option>
                            </select>
                        </div>
                        <div className="col-md-6">
                            <label className="form-label">
                                کد ملی
                            </label>
                            <input 
                                type="text" 
                                name="national_code" 
                                className={`form-control ${errors.national_code ? 'is-invalid' : ''}`} 
                                value={formData.national_code} 
                                onChange={handleInputChange} 
                                placeholder="کد ملی 10 رقمی"
                                maxLength={10}
                            />
                            {errors.national_code && (
                                <div className="text-danger small mt-1">{errors.national_code}</div>
                            )}
                        </div>
                        <div className="col-md-6">
                            <label className="form-label">
                                تحصیلات
                            </label>
                            <input 
                                type="text" 
                                name="education" 
                                className={`form-control ${errors.education ? 'is-invalid' : ''}`} 
                                value={formData.education} 
                                onChange={handleInputChange} 
                                placeholder="مثال: کارشناسی کامپیوتر"
                            />
                            {errors.education && (
                                <div className="text-danger small mt-1">{errors.education}</div>
                            )}
                        </div>
                        <div className="col-md-6">
                            <label className="form-label">
                                تاریخ تولد
                            </label>
                            <input 
                                type="date" 
                                name="birthday" 
                                className={`form-control ${errors.birthday ? 'is-invalid' : ''}`} 
                                value={formData.birthday} 
                                onChange={handleInputChange}
                            />
                            {errors.birthday && (
                                <div className="text-danger small mt-1">{errors.birthday}</div>
                            )}
                        </div>
                        <div className="col-12">
                            <label className="form-label">
                                شهر
                            </label>
                            <input 
                                type="text" 
                                name="city" 
                                className={`form-control ${errors.city ? 'is-invalid' : ''}`} 
                                value={formData.city} 
                                onChange={handleInputChange} 
                                placeholder="استان/شهر"
                            />
                            {errors.city && (
                                <div className="text-danger small mt-1">{errors.city}</div>
                            )}
                        </div>
                        <div className="col-12">
                            <label className="form-label">
                                کلاس‌های قبلی قرآن
                            </label>
                            <textarea 
                                name="had_other_classes" 
                                className={`form-control ${errors.had_other_classes ? 'is-invalid' : ''}`} 
                                value={formData.had_other_classes} 
                                onChange={handleInputChange} 
                                placeholder="آیا قبلاً در کلاس قرآن شرکت کرده‌اید؟ کجا؟"
                                rows={3}
                            />
                            {errors.had_other_classes && (
                                <div className="text-danger small mt-1">{errors.had_other_classes}</div>
                            )}
                        </div>
                        <div className="col-12">
                            <label className="form-label">
                                میزان حفظ قرآن
                            </label>
                            <textarea 
                                name="memorized" 
                                className={`form-control ${errors.memorized ? 'is-invalid' : ''}`} 
                                value={formData.memorized} 
                                onChange={handleInputChange} 
                                placeholder="چه مقدار از قرآن را حفظ هستید؟"
                                rows={2}
                            />
                            {errors.memorized && (
                                <div className="text-danger small mt-1">{errors.memorized}</div>
                            )}
                        </div>
                        <div className="col-12">
                            <label className="form-label">
                                معرف
                            </label>
                            <input 
                                type="text" 
                                name="invited_by" 
                                className={`form-control ${errors.invited_by ? 'is-invalid' : ''}`} 
                                value={formData.invited_by} 
                                onChange={handleInputChange} 
                                placeholder="نام کاربری یا شماره تلفن معرف"
                            />
                            {errors.invited_by && (
                                <div className="text-danger small mt-1">{errors.invited_by}</div>
                            )}
                        </div>
                        <div className="col-md-4">
                            <label className="form-label">
                                آیدی تلگرام
                            </label>
                            <input 
                                type="text" 
                                name="telegram_id" 
                                className={`form-control text-ltr ${errors.telegram_id ? 'is-invalid' : ''}`}
                                value={formData.telegram_id} 
                                onChange={handleInputChange} 
                                placeholder="@username"
                            />
                            {errors.telegram_id && (
                                <div className="text-danger small mt-1">{errors.telegram_id}</div>
                            )}
                        </div>
                        <div className="col-md-4">
                            <label className="form-label">
                                آیدی ایتا
                            </label>
                            <input 
                                type="text" 
                                name="eitaa_id" 
                                className={`form-control text-ltr ${errors.eitaa_id ? 'is-invalid' : ''}`}
                                value={formData.eitaa_id} 
                                onChange={handleInputChange} 
                                placeholder="@username"
                            />
                            {errors.eitaa_id && (
                                <div className="text-danger small mt-1">{errors.eitaa_id}</div>
                            )}
                        </div>
                        <div className="col-md-4">
                            <label className="form-label">
                                آیدی اینستاگرام
                            </label>
                            <input 
                                type="text" 
                                name="instagram_id" 
                                className={`form-control text-ltr ${errors.instagram_id ? 'is-invalid' : ''}`}
                                value={formData.instagram_id} 
                                onChange={handleInputChange} 
                                placeholder="@username"
                            />
                            {errors.instagram_id && (
                                <div className="text-danger small mt-1">{errors.instagram_id}</div>
                            )}
                        </div>
                        <div className="d-sm-flex justify-content-end">
                            <button type="button" className="btn btn-primary mb-0" onClick={handleSave} disabled={!hasChanges || isSaving}>
                                {isSaving ? "در حال ذخیره..." : "ذخیره"}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    )
}

export default function Profile() {
    return (
        <DashboardBase Content={<ProfileContent />} />
    )
}
