"use client";

import { useCart } from "@/src/core/hooks/useCart";
import { useAuth } from "@/src/core/hooks/useAuth";
import { useRouter } from "next/navigation";
import { toast } from "react-toastify";
import {getMediaUrl} from "@/src/core/utils";

export default function Cart() {
    const { items, totalPrice, remove } = useCart();
    const { isAuthenticated } = useAuth();
    const router = useRouter();

    const originalTotal = items.reduce(
        (sum, item) => sum + (item.price ?? 0) * item.quantity,
        0
    );
    const hasDiscount = originalTotal > 0 && originalTotal > totalPrice;

    const handleCheckout = () => {
        if (!isAuthenticated) {
            router.push("/auth/login");
            return;
        }
        toast.info("payment start");
    };

    return (
        <main>
            <section className="py-0">
                <div className="container">
                    <div className="row">
                        <div className="col-12">
                            <div className="bg-light p-4 text-center rounded-3">
                                <h1 className="m-0 fs-2">
                                    سبد خرید
                                </h1>
                                <div className="d-flex justify-content-center">
                                    <nav aria-label="breadcrumb">
                                        <ol className="breadcrumb breadcrumb-dots mb-0">
                                            <li className="breadcrumb-item">
                                                <a href="/">صفحه اصلی</a>
                                            </li>
                                            <li className="breadcrumb-item active" aria-current="page">
                                                سبد خرید
                                            </li>
                                        </ol>
                                    </nav>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <section className="pt-5">
                <div className="container">
                    {items.length === 0 ? (
                        <div className="text-center py-5">
                            <i className="bi bi-cart3 d-block mb-3 text-muted" style={{fontSize: '3rem'}}></i>
                            <h5 className="text-muted mb-3">سبد خرید شما خالی است</h5>
                            <a href="/courses/" className="btn btn-primary">مشاهده دوره‌ها</a>
                        </div>
                    ) : (
                        <div className="row g-4 g-sm-5">
                            <div className="col-lg-8 mb-4 mb-sm-0">
                                <div className="card card-body p-4 shadow">
                                    <div className="table-responsive border-0 rounded-3">
                                        <table className="table align-middle p-4 mb-0">
                                            <tbody className="border-top-0">
                                                {items.map((item, idx) => (
                                                    <tr key={idx}>
                                                        <td>
                                                            <div className="d-lg-flex align-items-center">
                                                                <div className="w-100px w-md-80px mb-2 mb-md-0 flex-shrink-0">
                                                                    {item.picture ? (
                                                                        <img
                                                                            src={getMediaUrl(item.picture)}
                                                                            className="rounded"
                                                                            alt={item.name}
                                                                            style={{width: '80px', height: '60px', objectFit: 'cover'}}
                                                                        />
                                                                    ) : (
                                                                        <div
                                                                            className="bg-light rounded d-flex align-items-center justify-content-center"
                                                                            style={{width: '80px', height: '60px'}}
                                                                        >
                                                                            <i className="bi bi-mortarboard text-muted fs-4"></i>
                                                                        </div>
                                                                    )}
                                                                </div>
                                                                <h6 className="mb-0 ms-lg-3 mt-2 mt-lg-0">
                                                                    {item.name || 'آیتم'}
                                                                </h6>
                                                            </div>
                                                        </td>
                                                        <td className="text-center">
                                                            {item.price !== undefined ? (
                                                                item.price === 0 ? (
                                                                    <h5 className="text-success mb-0">رایگان</h5>
                                                                ) : item.new_price && item.new_price > 0 ? (
                                                                    <>
                                                                        <small className="text-decoration-line-through text-muted d-block">
                                                                            {item.price.toLocaleString('fa-IR')} تومان
                                                                        </small>
                                                                        <h5 className="text-success mb-0">
                                                                            {item.new_price.toLocaleString('fa-IR')} تومان
                                                                        </h5>
                                                                    </>
                                                                ) : (
                                                                    <h5 className="text-success mb-0">
                                                                        {item.price.toLocaleString('fa-IR')} تومان
                                                                    </h5>
                                                                )
                                                            ) : (
                                                                <span className="text-muted small">—</span>
                                                            )}
                                                        </td>
                                                        <td>
                                                            <button
                                                                className="btn btn-sm btn-danger-soft px-2 mb-0"
                                                                onClick={() => remove(item.app_label, item.model, item.object_id)}
                                                            >
                                                                <i className="fas fa-fw fa-times"></i>
                                                            </button>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>

                            <div className="col-lg-4">
                                <div className="card card-body p-4 shadow">
                                    <h4 className="mb-3 fs-5">
                                        صورت حساب
                                    </h4>
                                    <ul className="list-group list-group-borderless mb-2">
                                        {hasDiscount && (
                                            <li className="list-group-item px-0 d-flex justify-content-between">
                                                <span className="h6 fw-light mb-0">قیمت</span>
                                                <span className="h6 fw-light mb-0 text-decoration-line-through text-muted">
                                                    {originalTotal.toLocaleString('fa-IR')} تومان
                                                </span>
                                            </li>
                                        )}
                                        <li className="list-group-item px-0 d-flex justify-content-between">
                                            <span className="h5 mb-0">قیمت نهایی</span>
                                            <span className="h5 mb-0">
                                                {totalPrice > 0
                                                    ? `${totalPrice.toLocaleString('fa-IR')} تومان`
                                                    : 'رایگان'
                                                }
                                            </span>
                                        </li>
                                    </ul>
                                    <div className="d-grid">
                                        <button className="btn btn-lg btn-success" onClick={handleCheckout}>
                                            تسویه حساب
                                        </button>
                                    </div>
                                    <p className="small mb-0 mt-2 text-center">
                                        با تکمیل خرید خود&nbsp;
                                        <a href="/about-us">
                                            <strong>شرایط و قوانین سایت</strong>
                                        </a>
                                        &nbsp;را خواهید پذیرفت
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </section>
        </main>
    );
}
