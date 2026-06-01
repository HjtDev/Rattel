"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

function PaymentFailContent() {
    const searchParams = useSearchParams();
    const transactionId = searchParams.get("transaction_id");

    return (
        <div className="text-center py-5">
            <i
                className="bi bi-x-circle-fill text-danger d-block mb-4"
                style={{ fontSize: "4rem" }}
            ></i>
            <h2 className="mb-2">پرداخت ناموفق</h2>
            <p className="mb-1">
                متأسفانه تراکنش شما تکمیل نشد یا لغو گردید.
            </p>
            <p className="mb-4 small">
                در صورت کسر مبلغ از حساب شما مبلغ تا ۷۲ ساعت کاری بعد به حساب شما بر میگردد.
            </p>
            {transactionId && (
                <p className="small mb-4">
                    شناسه تراکنش جهت پیگیری: <code>{transactionId}</code>
                </p>
            )}
            <div className="d-flex gap-3 justify-content-center flex-wrap">
                <a href="/cart/" className="btn btn-primary btn-lg">
                    <i className="bi bi-cart3 me-2"></i>
                    بازگشت به سبد خرید
                </a>
                <a href="/" className="btn btn-outline-secondary btn-lg">
                    صفحه اصلی
                </a>
            </div>
        </div>
    );
}

export default function PaymentFailPage() {
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
                                        <div className="text-center py-4">
                                            <div className="spinner-border text-primary" role="status">
                                                <span className="visually-hidden">Loading...</span>
                                            </div>
                                        </div>
                                    }
                                >
                                    <PaymentFailContent />
                                </Suspense>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </main>
    );
}
