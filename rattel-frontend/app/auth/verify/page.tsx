"use client";

import { Suspense, useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/src/core/hooks/useAuth";
import AuthMessage from "@/src/components/auth/AuthMessage";
import { toast } from "react-toastify";

function VerifyPageContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { verifyOTP } = useAuth();

    const [identifier, setIdentifier] = useState("");
    const [code, setCode] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    const getErrorMessage = (error?: number): string => {
        switch (error) {
            case -1:
                return "لطفا کد تایید را به درستی وارد کنید";
            case -2:
                return "کد تایید اشتباه است";
            case -3:
                return "کد تایید منقضی شده است. لطفا مجددا درخواست کنید";
            case -4:
            case -5:
            case -6:
            case -8:
                return "خطا در تایید کد. لطفا دوباره تلاش کنید";
            case -7:
                return "تعداد تلاش‌های شما به حداکثر رسیده است";
            case -9:
                return "مشکلی در ثبت نام شما به وجود آمد لطفا بعدا تلاش کنید";
            case -10:
                return "مشکلی در ورود به حساب پیش آمد لطفا بعدا تلاش کنید.";
            case -11:
                return "درخواست شما نامعتبر است.";
            default:
                return "خطا در تایید کد. لطفا دوباره تلاش کنید";
        }
    };

    useEffect(() => {
        const id = searchParams.get("indicator");
        if (id) {
            setIdentifier(id);
        } else {
            toast.error("شناسه تایید یافت نشد");
            router.push("/auth/login");
        }
    }, [searchParams, router]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!code.trim() || code.length < 1) {
            toast.error("لطفا کد تایید را وارد کنید");
            return;
        }

        setIsLoading(true);

        try {
            const result = await verifyOTP(identifier, code);

            if (result.success) {
                toast.success("ورود موفقیت آمیز بود");
                router.push("/");
            } else {
                toast.error(getErrorMessage(result.error));
            }
        } catch (err) {
            toast.error("خطا در برقراری ارتباط با سرور");
        } finally {
            setIsLoading(false);
        }
    };

    const handleResend = () => {
        toast.info("در حال انتقال به صفحه قبل...");
        router.back();
    };

    if (!identifier) {
        return null;
    }

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
                                    <h1 className="fs-4">تایید شماره تلفن</h1>
                                    <p className="mb-4">
                                        لطفا کد تاییدی که به شماره تلفن شما پیامک شده است را در فیلد زیر وارد کنید
                                    </p>

                                    <form onSubmit={handleSubmit}>
                                        <div className="mb-4">
                                            <label htmlFor="code" className="form-label">
                                                کد تایید *
                                            </label>
                                            <div className="input-group input-group-lg">
                                                <span className="input-group-text bg-light rounded-start border-0 text-secondary px-3">
                                                    <i className="fas fa-lock"></i>
                                                </span>
                                                <input
                                                    type="text"
                                                    className="form-control border-0 bg-light rounded-end ps-1"
                                                    placeholder="1234"
                                                    id="code"
                                                    value={code}
                                                    onChange={(e) => setCode(e.target.value.trim())}
                                                    required
                                                    disabled={isLoading}
                                                    maxLength={10}
                                                />
                                            </div>
                                            <div className="form-text">
                                                کد تایید ارسال شده را وارد کنید
                                            </div>
                                        </div>

                                        <div className="align-items-center mt-0">
                                            <div className="d-grid">
                                                <button
                                                    className="btn btn-primary mb-0"
                                                    type="submit"
                                                    disabled={isLoading || code.length < 1}
                                                >
                                                    {isLoading ? "در حال تایید..." : "تایید و ورود"}
                                                </button>
                                            </div>
                                        </div>
                                    </form>

                                    <div className="mt-4 text-center">
                                        <span>
                                            کد را دریافت نکردید؟{" "}
                                            <a
                                                href="#"
                                                onClick={(e) => {
                                                    e.preventDefault();
                                                    handleResend();
                                                }}
                                            >
                                                ارسال مجدد
                                            </a>
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

export default function VerifyPage() {
    return (
        <Suspense fallback={null}>
            <VerifyPageContent />
        </Suspense>
    );
}
