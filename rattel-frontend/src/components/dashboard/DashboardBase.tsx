"use client"

import {ReactNode, useEffect} from "react";
import Navbar from "@/src/components/layout/Navbar";
import Footer from "@/src/components/layout/Footer";
import {useAuth} from "@/src/core/hooks/useAuth";
import {useRouter, usePathname} from "next/navigation";
import {getRoleLabel, isLinkActive} from "@/src/core/utils";
import {useMySubscription} from "@/src/core/hooks/useMySubscription";

interface DashboardContent {
    Content: ReactNode;
}

export default function DashboardBase({Content}: DashboardContent) {
    const {user, isAuthenticated, isLoading, logout} = useAuth();
    const {subscription} = useMySubscription();
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        if (!isLoading && !isAuthenticated) {
            router.push("/auth/login/");
        }
    }, [isLoading, isAuthenticated, router]);

    return !isLoading  && (
        <>
            <main>
                <section className="pt-0">
                    <div className="container-fluid px-0">
                        <div className="card bg-blue h-100px h-md-200px rounded-0" style={{
                            background: 'url(/assets/images/pattern/04.png) no-repeat center center',
                            backgroundSize: 'cover'
                        }}>
                        </div>
                    </div>
                    <div className="container mt-n4">
                        <div className="row">
                            <div className="col-12">
                                <div className="card bg-transparent card-body pb-0 px-0 mt-2 mt-sm-0">
                                    <div className="row d-sm-flex justify-sm-content-between mt-2 mt-md-0">
                                        <div className="col-auto">
                                            <div className="avatar avatar-xxl position-relative mt-n3">
                                                <img
                                                    className="avatar-img rounded-circle border border-white border-3 shadow"
                                                    src={user?.profile_picture || "/assets/images/auth/default_profile.png"}
                                                    alt={user?.name || "Default Profile"}
                                                />
                                                <span className="badge text-bg-success rounded-pill position-absolute top-50 start-100 translate-middle mt-4 mt-md-5 ms-n3 px-md-3">
                                                    {user?.profile?.role && getRoleLabel(user.profile.role)}
                                                </span>
                                            </div>
                                        </div>
                                        <div className="col d-sm-flex justify-content-between align-items-center">
                                            <div>
                                                <h1 className="my-1 fs-4">
                                                    {user?.name}
                                                </h1>
                                                <ul className="list-inline mb-0">
                                                    <li className="list-inline-item me-3 mb-1 mb-sm-0">
                                                        <span className="text-body fw-light">
                                                            {user?.username}@
                                                        </span>
                                                    </li>
                                                    <li className="list-inline-item me-3 mb-1 mb-sm-0">
                                                        <span className="text-body fw-light">
                                                            {user?.phone}
                                                        </span>
                                                    </li>
                                                    <li className="list-inline-item mb-1 mb-sm-0">
                                                        {subscription?.is_active ? (
                                                            <span className="badge bg-success bg-opacity-10 text-success border border-success rounded-pill px-2 py-1">
                                                                <i className="bi bi-star-fill me-1"></i>
                                                                {subscription.plan.name}
                                                            </span>
                                                        ) : (
                                                            <a href="/subscriptions/" className="badge bg-primary bg-opacity-10 text-primary border border-primary rounded-pill px-2 py-1 text-decoration-none">
                                                                <i className="bi bi-star me-1"></i>
                                                                خرید اشتراک
                                                            </a>
                                                        )}
                                                    </li>
                                                </ul>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <hr className="d-xl-none"/>
                                <div className="col-12 col-xl-3 d-flex justify-content-between align-items-center">
                                    <a className="h6 mb-0 fw-bold d-xl-none" href="#">
                                        داشبورد
                                    </a>
                                    <button className="btn btn-primary d-xl-none" type="button"
                                            data-bs-toggle="offcanvas"
                                            data-bs-target="#offcanvasSidebar" aria-controls="offcanvasSidebar">
                                        <i className="fas fa-sliders-h">
                                        </i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
                <section className="pt-0">
                    <div className="container">
                        <div className="row">
                            <div className="col-xl-3">
                                <div className="offcanvas-xl offcanvas-end" tabIndex={-1} id="offcanvasSidebar">
                                    <div className="offcanvas-header bg-light">
                                        <h5 className="offcanvas-title" id="offcanvasNavbarLabel">
                                            داشبورد
                                        </h5>
                                        <button type="button" className="btn-close" data-bs-dismiss="offcanvas"
                                                data-bs-target="#offcanvasSidebar" aria-label="Close">
                                        </button>
                                    </div>
                                    <div className="offcanvas-body p-3 p-xl-0">
                                        <div className="bg-dark border rounded-3 p-3 w-100">
                                            <div
                                                className="list-group list-group-dark list-group-borderless collapse-list">
                                                <a className={`list-group-item ${isLinkActive("/dashboard", pathname) ? "active" : ""}`} href="/dashboard">
                                                    <i className="bi bi-ui-checks-grid fa-fw me-2">
                                                    </i>
                                                    داشبورد
                                                </a>
                                                <a className={`list-group-item ${isLinkActive("/dashboard/personal-information", pathname) ? "active" : ""}`} href="/dashboard/personal-information">
                                                    <i className="bi bi-card-checklist fa-fw me-2">
                                                    </i>
                                                    اطلاعات شخصی
                                                </a>
                                                <a className={`list-group-item ${isLinkActive("/dashboard/profile", pathname) ? "active" : ""}`} href="/dashboard/profile">
                                                    <i className="bi bi-basket fa-fw me-2">
                                                    </i>
                                                    پروفایل
                                                </a>
                                                <a className={`list-group-item ${isLinkActive("/dashboard/settings", pathname) ? "active" : ""}`} href="/dashboard/settings">
                                                    <i className="far fa-fw fa-file-alt me-2">
                                                    </i>
                                                    تنظیمات
                                                </a>
                                                <a className={`list-group-item ${isLinkActive("/dashboard/tickets", pathname) ? "active" : ""}`} href="/dashboard/tickets">
                                                    <i className="bi bi-question-diamond fa-fw me-2">
                                                    </i>
                                                    تیکت ها
                                                </a>
                                                <a className={`list-group-item ${isLinkActive("/dashboard/transactions", pathname) ? "active" : ""}`} href="/dashboard/transactions">
                                                    <i className="bi bi-credit-card-2-front fa-fw me-2">
                                                    </i>
                                                    تراکنش ها
                                                </a>
                                                <a className={`list-group-item ${isLinkActive("/dashboard/saved-courses", pathname) ? "active" : ""}`} href="/dashboard/saved-courses">
                                                    <i className="bi bi-credit-card-2-front fa-fw me-2">
                                                    </i>
                                                    دوره های نشان شده
                                                </a>
                                                <a className={`list-group-item ${isLinkActive("/dashboard/saved-blogs", pathname) ? "active" : ""}`} href="/dashboard/saved-blogs">
                                                    <i className="bi bi-bookmark-heart fa-fw me-2">
                                                    </i>
                                                    پست های نشان شده
                                                </a>
                                                <a className={`list-group-item ${isLinkActive("/dashboard/automatic-class", pathname, true) ? "active" : ""}`} href="/dashboard/automatic-class">
                                                    <i className="bi bi-journal-bookmark-fill fa-fw me-2">
                                                    </i>
                                                    کلاس خودکار حفظ
                                                </a>
                                                {user?.profile?.role === 'teacher' && (
                                                    <a className={`list-group-item ${isLinkActive("/dashboard/automatic-class/admin", pathname) ? "active" : ""}`} href="/dashboard/automatic-class/admin">
                                                        <i className="bi bi-shield-check fa-fw me-2">
                                                        </i>
                                                        پنل مدیریت کلاس
                                                    </a>
                                                )}
                                                <a className="list-group-item text-danger bg-danger-soft-hover"
                                                   href="#" onClick={(e) => {
                                                    e.preventDefault();
                                                    logout();
                                                    router.push("/auth/login/");
                                                }}>
                                                    <i className="fas fa-sign-out-alt fa-fw me-2">
                                                    </i>
                                                    خروج
                                                </a>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            {
                                Content
                            }
                        </div>
                    </div>
                </section>
            </main>
        </>
    )
}
