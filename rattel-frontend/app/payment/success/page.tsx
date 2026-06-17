"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/src/core/api";
import { cartManager } from "@/src/core/cart/cartManager";

type FinalizeState = "loading" | "success" | "error";

function PaymentSuccessContent() {
    const searchParams = useSearchParams();
    const transactionId = searchParams.get("transaction_id");

    const [state, setState] = useState<FinalizeState>("loading");
    const [errorMessage, setErrorMessage] = useState("");
    const called = useRef(false);  // guard against React strict-mode double-invoke

    useEffect(() => {
        if (called.current) return;
        called.current = true;

        if (!transactionId) {
            setState("error");
            setErrorMessage("اطلاعات تراکنش در URL یافت نشد.");
            return;
        }

        const finalize = async () => {
            try {
                const response = await api.post("/cart/finalize/", {
                    transaction_id: transactionId,
                });

                if (response.data.success) {
                    await cartManager.refresh();
                    setState("success");
                } else {
                    setState("error");
                    setErrorMessage(response.data.message || "خطا در نهایی‌سازی خرید");
                }
            } catch (err: any) {
                const status = err.response?.status;
                if (status === 409) {
                    // Transaction already finalized — idempotent success
                    await cartManager.refresh();
                    setState("success");
                } else {
                    setState("error");
                    setErrorMessage(
                        err.response?.data?.message || "خطا در اتصال به سرور"
                    );
                }
            }
        };

        finalize();
    }, [transactionId]);

    if (state === "loading") {
        return (
            <div className="text-center py-5">
                <div className="spinner-border text-primary mb-3" role="status">
                    <span className="visually-hidden">Loading...</span>
                </div>
                <h5 className="text-muted">در حال تأیید و ثبت خرید...</h5>
                <p className="text-muted small mt-1">لطفاً صفحه را نبندید</p>
            </div>
        );
    }

    if (state === "success") {
        return (
            <div className="text-center py-5">
                <i
                    className="bi bi-check-circle-fill text-success d-block mb-4"
                    style={{ fontSize: "4rem" }}
                ></i>
                <h2 className="mb-2">پرداخت موفق!</h2>
                <p className="mb-1">
                    خرید شما با موفقیت انجام شد.
                </p>
                <p className="mb-4">
                    اشتراک/دوره ها به داشبورد حساب کاربری اضافه شد.
                </p>
                {transactionId && (
                    <p className="small mb-4">
                        شناسه تراکنش: <code>{transactionId}</code>
                    </p>
                )}
                <div className="d-flex gap-3 justify-content-center flex-wrap">
                    <a href="/dashboard/" className="btn btn-primary btn-lg">
                        <i className="bi bi-grid me-2"></i>
                        داشبورد من
                    </a>
                    <a href="/courses/" className="btn btn-outline-secondary btn-lg">
                        مشاهده دوره‌ها
                    </a>
                </div>
            </div>
        );
    }

    // error state
    return (
        <div className="text-center py-5">
            <i
                className="bi bi-exclamation-triangle-fill text-warning d-block mb-4"
                style={{ fontSize: "4rem" }}
            ></i>
            <h2 className="mb-2">پرداخت انجام شد اما خطایی رخ داد</h2>
            <p className="text-muted mb-2">{errorMessage}</p>
            <p className="text-muted small mb-1">
                پرداخت شما ثبت شده است. لطفاً با پشتیبانی تماس بگیرید.
            </p>
            {transactionId && (
                <p className="text-muted small mb-4">
                    شناسه تراکنش جهت پیگیری: <code>{transactionId}</code>
                </p>
            )}
            <div className="d-flex gap-3 justify-content-center flex-wrap">
                <a href="/cart/" className="btn btn-primary btn-lg">
                    بازگشت به سبد خرید
                </a>
                <a href="/dashboard/" className="btn btn-outline-secondary btn-lg">
                    داشبورد من
                </a>
            </div>
        </div>
    );
}

export default function PaymentSuccessPage() {
    return (
        <main>
            <section className="py-0">
                <div className="container">
                    <div className="row">
                        <div className="col-12">
                            <div className="bg-light p-4 text-center rounded-3">
                                <h1 className="m-0 fs-2">نتیجه پرداخت</h1>
                                <div className="d-flex justify-content-center">
                                    <nav aria-label="breadcrumb">
                                        <ol className="breadcrumb breadcrumb-dots mb-0">
                                            <li className="breadcrumb-item">
                                                <a href="/">صفحه اصلی</a>
                                            </li>
                                            <li className="breadcrumb-item">
                                                <a href="/cart/">سبد خرید</a>
                                            </li>
                                            <li className="breadcrumb-item active" aria-current="page">
                                                نتیجه پرداخت
                                            </li>
                                        </ol>
                                    </nav>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
            <section className="pt-5 pb-5">
                <div className="container">
                    <div className="row justify-content-center">
                        <div className="col-lg-6">
                            <div className="card card-body shadow p-4 p-md-5">
                                <Suspense
                                    fallback={
                                        <div className="text-center py-5">
                                            <div className="spinner-border text-primary" role="status">
                                                <span className="visually-hidden">Loading...</span>
                                            </div>
                                        </div>
                                    }
                                >
                                    <PaymentSuccessContent />
                                </Suspense>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </main>
    );
}
