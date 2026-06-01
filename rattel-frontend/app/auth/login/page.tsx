"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/src/core/hooks/useAuth";
import AuthMessage from "@/src/components/auth/AuthMessage";
import { toast } from "react-toastify";

function LoginContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const next = searchParams.get("next") || "";
    const { login, isAuthenticated } = useAuth();
    const [username, setUsername] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    const getErrorMessage = (error?: number): string => {
        switch (error) {
            case -1:
                return "لطفا نام کاربری یا شماره تلفن را به درستی وارد کنید";
            case -2:
                return "از نام کاربری یا شماره تلفن برای ورود استفاده کنید";
            case -3:
                return "نام کاربری یا شماره تلفن یافت نشد";
            case -4:
                return "حساب کاربری شما غیرفعال است";
            case -5:
                return "خطا در سرور لطفا مجددا تلاش کنید."
            case -6:
                return "یک کد تایید اخیرا برای شما ارسال شده است لطفا دقایقی صبر کنید و مجددا تلاش کنید";
            case -7:
                return "خطا در ارسال پیامک. لطفا دوباره تلاش کنید";
            default:
                return "خطا در ورود. لطفا دوباره تلاش کنید";
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!username.trim()) {
            toast.error("لطفا نام کاربری یا شماره تلفن خود را وارد کنید");
            return;
        }

        setIsLoading(true);

        try {
            const result = await login(username);
            console.log({...result});

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
                                    <span className="mb-0 fs-1">👋</span>
                                    <h1 className="fs-4">ورود به حساب کاربری</h1>
                                    <form onSubmit={handleSubmit}>
                                        <div className="mb-4">
                                            <label htmlFor="username" className="form-label">
                                                نام کاربری یا شماره تلفن *
                                            </label>
                                            <div className="input-group input-group-lg">
                                                <span className="input-group-text bg-light rounded-start border-0 text-secondary px-3">
                                                    <i className="bi bi-person-fill"></i>
                                                </span>
                                                <input
                                                    type="text"
                                                    className="form-control border-0 bg-light rounded-end ps-1"
                                                    placeholder="نام کاربری یا 09123456789"
                                                    id="username"
                                                    value={username}
                                                    onChange={(e) => setUsername(e.target.value)}
                                                    required
                                                    disabled={isLoading}
                                                />
                                            </div>
                                            <div className="form-text">
                                                کد تایید به شماره تلفن شما ارسال خواهد شد
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
                                            حساب کاربری ندارید؟{" "}
                                            <a href={`/auth/register?${next ? `next=${encodeURIComponent(next)}` : ""}`}>ثبت نام</a>
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

export default function LoginPage() {
    return (
        <Suspense fallback={null}>
            <LoginContent />
        </Suspense>
    );
}
