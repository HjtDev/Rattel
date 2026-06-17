"use client"

import { useState, useEffect } from "react";
import DashboardBase from "@/src/components/dashboard/DashboardBase";
import {useAuth} from "@/src/core/hooks/useAuth";
import { toast } from "react-toastify";
import { getMediaUrl } from "@/src/core/utils";

// Validation regex patterns (matching backend)
const USERNAME_REGEX = /^[a-zA-Z][a-zA-Z0-9_.]{2,29}$/;
const EMAIL_REGEX = /^[\w\.-]+@[\w\.-]+\.\w+$/;
const PERSIAN_NAME_REGEX = /^[\u0600-\u06FF ]{1,60}$/;
const ENGLISH_NAME_REGEX = /^[A-Za-z ]{1,60}$/;

// Validation functions
const validateUsername = (username: string): string | null => {
    if (!username || username.trim().length === 0) {
        return "نام کاربری نمی‌تواند خالی باشد";
    }
    if (!USERNAME_REGEX.test(username)) {
        return "نام کاربری باید با حرف شروع شود، 3-30 کاراکتر باشد و فقط شامل حروف، اعداد، _ و . باشد";
    }
    return null;
};

const validateEmail = (email: string): string | null => {
    if (!email || email.trim().length === 0) {
        return null; // Email is optional
    }
    if (!EMAIL_REGEX.test(email)) {
        return "ایمیل معتبر نیست";
    }
    return null;
};

const validateName = (name: string): string | null => {
    if (!name || name.trim().length === 0) {
        return "نام نمی‌تواند خالی باشد";
    }
    const isPersian = PERSIAN_NAME_REGEX.test(name);
    const isEnglish = ENGLISH_NAME_REGEX.test(name);
    
    if (!isPersian && !isEnglish) {
        return "نام باید فقط فارسی یا فقط انگلیسی باشد و نباید شامل کاراکترهای خاص باشد";
    }
    if (name.length > 60) {
        return "نام نباید بیشتر از 60 کاراکتر باشد";
    }
    return null;
};

function PersonalInformationContent() {
    const {user, isAuthenticated, isLoading, logout, updateUserInfo} = useAuth();
    
    // Form state
    const [formData, setFormData] = useState({
        name: "",
        username: "",
        email: "",
    });
    const [profilePicture, setProfilePicture] = useState<File | null>(null);
    const [previewUrl, setPreviewUrl] = useState<string>("");
    const [hasChanges, setHasChanges] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [errors, setErrors] = useState({
        name: "",
        username: "",
        email: "",
    });

    // Initialize form data when user loads
    useEffect(() => {
        if (user) {
            setFormData({
                name: user.name || "",
                username: user.username || "",
                email: user.email || "",
            });
            setPreviewUrl(user.profile_picture ? getMediaUrl(user.profile_picture) : "/assets/images/auth/default_profile.png");
        }
    }, [user]);

    // Check if form has changes
    useEffect(() => {
        if (!user) return;
        
        const nameChanged = formData.name !== (user.name || "");
        const usernameChanged = formData.username !== (user.username || "");
        const emailChanged = formData.email !== (user.email || "");
        const pictureChanged = profilePicture !== null;
        
        setHasChanges(nameChanged || usernameChanged || emailChanged || pictureChanged);
    }, [formData, profilePicture, user]);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value,
        }));
        
        // Clear error for this field when user types
        setErrors(prev => ({
            ...prev,
            [name]: "",
        }));
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            // Validate file size (2MB max)
            if (file.size > 2 * 1024 * 1024) {
                toast.error("حجم تصویر نباید بیشتر از 2 مگابایت باشد");
                return;
            }
            
            // Validate file type
            if (!['image/jpeg', 'image/jpg', 'image/png'].includes(file.type)) {
                toast.error("فقط فایل‌های JPG و PNG مجاز هستند");
                return;
            }
            
            setProfilePicture(file);
            setPreviewUrl(URL.createObjectURL(file));
        }
    };

    const validateForm = (): boolean => {
        const newErrors = {
            name: validateName(formData.name) || "",
            username: validateUsername(formData.username) || "",
            email: validateEmail(formData.email) || "",
        };
        
        setErrors(newErrors);
        
        return !newErrors.name && !newErrors.username && !newErrors.email;
    };

    const parseErrorMessage = (message: any): string => {
        if (typeof message === 'string') return message;
        
        if (typeof message === 'object' && message !== null) {
            // Handle field-specific errors: { "email": ["error1", "error2"] }
            const errorMessages = Object.entries(message)
                .map(([field, errors]) => Array.isArray(errors) ? errors.join(' ') : errors)
                .join(' ');
            return errorMessages || "خطا در به‌روزرسانی اطلاعات";
        }
        
        return "خطا در به‌روزرسانی اطلاعات";
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
            // Prepare update payload
            const updatePayload: any = {};
            
            if (formData.name !== user?.name) updatePayload.name = formData.name;
            if (formData.username !== user?.username) updatePayload.username = formData.username;
            if (formData.email !== user?.email) updatePayload.email = formData.email;
            if (profilePicture) updatePayload.profile_picture = profilePicture;

            const result = await updateUserInfo(updatePayload);

            if (result.success) {
                toast.success(parseErrorMessage("اطلاعات با موفقیت به‌روزرسانی شد"));
                
                // Reset file input
                setProfilePicture(null);
                
                // If username changed, warn and logout
                if (result.usernameChanged) {
                    toast.warning("نام کاربری شما تغییر کرد. لطفاً دوباره وارد شوید", {
                        autoClose: 3000,
                    });
                    
                    // Logout after 3 seconds
                    setTimeout(() => {
                        logout();
                    }, 3000);
                }
            } else {
                toast.error(parseErrorMessage(result.message));
            }
        } catch (error) {
            toast.error("خطا در به‌روزرسانی اطلاعات");
        } finally {
            setIsSaving(false);
        }
    };

    return !isLoading && (
        <div className="col-xl-9">
            <div className="card bg-transparent border rounded-3">
                <div className="card-header bg-transparent border-bottom">
                    <h3 className="card-header-title mb-0 ff-vb fs-5">
                        ویرایش اطلاعات
                    </h3>
                </div>
                <div className="card-body">
                    <form className="row g-4">
                        <div className="col-12 justify-content-center align-items-center">
                            <label className="form-label">
                                تصویر پروفایل
                            </label>
                            <div className="d-flex align-items-center">
                                <label className="position-relative me-4" htmlFor="uploadfile-1"
                                       title="Replace this pic">
              <span className="avatar avatar-xl">
                <img id="uploadfile-1-preview" className="avatar-img rounded-circle border border-white border-3 shadow"
                     src={previewUrl}
                     alt={formData.name || "Default Profile"}
                />
              </span>
                                </label>
                                <label className="btn btn-primary-soft mb-0" htmlFor="uploadfile-1">
                                    تغییر
                                </label>
                                <input id="uploadfile-1" className="form-control d-none" type="file" accept="image/png,image/jpeg,image/jpg" onChange={handleFileChange}/>
                            </div>
                        </div>
                        <div className="col-12">
                            <label className="form-label">
                                نام
                            </label>
                            <div className="input-group">
                                <input type="text" name="name" className={`form-control ${errors.name ? 'is-invalid' : ''}`} value={formData.name} onChange={handleInputChange} placeholder="نام"/>
                                <input type="text" className="form-control" value={user?.phone} placeholder="شماره تماس" disabled={true} />
                            </div>
                            {errors.name && (
                                <div className="text-danger small mt-1">{errors.name}</div>
                            )}
                        </div>
                        <div className="col-md-6">
                            <label className="form-label">
                                نام کاربری
                            </label>
                            <div className="input-group">
            <span className="input-group-text">
              exirequran.ir
            </span>
                                <input type="text" name="username" className={`form-control ${errors.username ? 'is-invalid' : ''}`} value={formData.username} onChange={handleInputChange}/>
                            </div>
                            {errors.username && (
                                <div className="text-danger small mt-1">{errors.username}</div>
                            )}
                        </div>
                        <div className="col-md-6">
                            <label className="form-label">
                                ایمیل
                            </label>
                            <input className={`form-control ${errors.email ? 'is-invalid' : ''}`} name="email" type="email" value={formData.email} onChange={handleInputChange} placeholder="ایمیل"/>
                            {errors.email && (
                                <div className="text-danger small mt-1">{errors.email}</div>
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

export default function PersonalInformation() {
    return (
        <DashboardBase Content={<PersonalInformationContent />} />
    )
}
