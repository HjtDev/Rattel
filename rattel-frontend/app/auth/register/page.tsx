"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/src/core/hooks/useAuth";
import AuthMessage from "@/src/components/auth/AuthMessage";
import { toast } from "react-toastify";

function RegisterContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const next = searchParams.get("next") || "";
    const { register, isAuthenticated } = useAuth();
    const [formData, setFormData] = useState({
        username: "",
        name: "",
        phone: "",
        email: "",
    });
    const [isLoading, setIsLoading] = useState(false);

    const getErrorMessage = (error?: number): string => {
        switch (error) {
            case -1:
                return "لطفا تمام فیلدهای الزامی را به درستی پر کنید";
            case -2:
                return "آدرس ایمیل نامعتبر است";
            case -3:
                return "این اطلاعات قبلا ثبت شده است";
            case -4:
                return "خطا در سرور لطفا مجددا تلاش کنید."
            case -5:
                return "یک کد تایید اخیرا برای شما ارسال شده است لطفا دقایقی صبر کنید و مجددا تلاش کنید";
            case -6:
                return "خطا در ارسال پیامک. لطفا دوباره تلاش کنید";
            default:
                return "خطا در ثبت نام. لطفا دوباره تلاش کنید";
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value,
        });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        // Validation
        if (!formData.username.trim()) {
            toast.error("لطفا نام کاربری خود را وارد کنید");
            return;
        }
        if (!formData.name.trim()) {
            toast.error("لطفا نام و نام خانوادگی خود را وارد کنید");
            return;
        }
        if (!formData.phone.trim()) {
            toast.error("لطفا شماره تلفن خود را وارد کنید");
            return;
        }

        setIsLoading(true);

        try {
            const { email, ...requiredData } = formData;
            const payload = email.trim() ? { ...requiredData, email } : requiredData;

            const result = await register(payload);

            if (result.success && result.indicator) {
                toast.success("کد تایید به شماره تلفن شما ارسال شد");
                router.push(`/auth/verify?indicator=${result.indicator}${next ? `&next=${encodeURIComponent(next)}` : ""}`);
            } else {
                toast.error(getErrorMessage(result.error));
            }
        } catch (err) {
            toast.error("خطا در برقراری ارتباط با سرور");
        } finally {
            setIsLoading(false);
        }
    };

    if(isAuthenticated) router.push(next || "/")

    return (
        <main>
            <section className="p-0 d-flex align-items-center position-relative overflow-hidden">
                <div className="container-fluid">
                    <div className="row">
                        <AuthMessage />
                        <div className="col-12 col-lg-6 m-auto">
                            <div className="row my-5">
                                <div className="col-sm-10 col-xl-8 m-auto">
                                    <img src="/assets/images/auth/register_icon.png" className="h-40px mb-2" alt="Register Icon" />
                                    <h2>ثبت نام</h2>
                                    <form onSubmit={handleSubmit}>
                                        <div className="mb-4">
                                            <label htmlFor="username" className="form-label">
                                                نام کاربری *
                                            </label>
                                            <div className="input-group input-group-lg">
                                                <span className="input-group-text bg-light rounded-start border-0 text-secondary px-3">
                                                    <i className="bi bi-person-fill"></i>
                                                </span>
                                                <input
                                                    type="text"
                                                    className="form-control border-0 bg-light rounded-end ps-1"
                                                    placeholder="john_doe"
                                                    id="username"
                                                    name="username"
                                                    value={formData.username}
                                                    onChange={handleChange}
                                                    required
                                                    disabled={isLoading}
                                                />
                                            </div>
                                        </div>

                                        <div className="mb-4">
                                            <label htmlFor="name" className="form-label">
                                                نام و نام خانوادگی *
                                            </label>
                                            <div className="input-group input-group-lg">
                                                <span className="input-group-text bg-light rounded-start border-0 text-secondary px-3">
                                                    <i className="bi bi-person-badge-fill"></i>
                                                </span>
                                                <input
                                                    type="text"
                                                    className="form-control border-0 bg-light rounded-end ps-1"
                                                    placeholder="علی احمدی"
                                                    id="name"
                                                    name="name"
                                                    value={formData.name}
                                                    onChange={handleChange}
                                                    required
                                                    disabled={isLoading}
                                                />
                                            </div>
                                        </div>

                                        <div className="mb-4">
                                            <label htmlFor="phone" className="form-label">
                                                شماره تلفن *
                                            </label>
                                            <div className="input-group input-group-lg">
                                                <span className="input-group-text bg-light rounded-start border-0 text-secondary px-3">
                                                    <i className="bi bi-phone-fill"></i>
                                                </span>
                                                <input
                                                    type="tel"
                                                    className="form-control border-0 bg-light rounded-end ps-1"
                                                    placeholder="09123456789"
                                                    id="phone"
                                                    name="phone"
                                                    value={formData.phone}
                                                    onChange={handleChange}
                                                    required
                                                    disabled={isLoading}
                                                />
                                            </div>
                                            <div className="form-text">
                                                کد تایید به این شماره ارسال خواهد شد
                                            </div>
                                        </div>

                                        <div className="mb-4">
                                            <label htmlFor="email" className="form-label">
                                                ایمیل (اختیاری)
                                            </label>
                                            <div className="input-group input-group-lg">
                                                <span className="input-group-text bg-light rounded-start border-0 text-secondary px-3">
                                                    <i className="bi bi-envelope-fill"></i>
                                                </span>
                                                <input
                                                    type="email"
                                                    className="form-control border-0 bg-light rounded-end ps-1"
                                                    placeholder="example@email.com"
                                                    id="email"
                                                    name="email"
                                                    value={formData.email}
                                                    onChange={handleChange}
                                                    disabled={isLoading}
                                                />
                                            </div>
                                        </div>

                                        <div className="align-items-center mt-0">
                                            <div className="d-grid">
                                                <button
                                                    className="btn btn-primary mb-0"
                                                    type="submit"
                                                    disabled={isLoading}
                                                >
                                                    {isLoading ? "در حال ارسال..." : "ارسال کد تایید"}
                                                </button>
                                            </div>
                                        </div>
                                    </form>

                                    <div className="mt-4 text-center">
                                        <span>
                                            آیا قبلا ثبت نام کرده اید؟{" "}
                                            <a href={`/auth/login?${next ? `next=${encodeURIComponent(next)}` : ""}`}>ورود</a>
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </main>
    );
}

export default function RegisterPage() {
    return (
        <Suspense fallback={null}>
            <RegisterContent />
        </Suspense>
    );
}
