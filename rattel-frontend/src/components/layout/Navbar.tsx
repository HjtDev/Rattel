'use client'
import {useNavbar} from "@/src/core/hooks/useNavbar";
import LoadingSkeleton from "@/src/components/skeleton/loadingSkeleton";
import {useAuth} from "@/src/core/hooks/useAuth";
import {useCart} from "@/src/core/hooks/useCart";
import {useRouter} from "next/navigation";
import {useState} from "react";

export default function Navbar() {
    const {isLoadingNavbar, navbarData, navbarError} = useNavbar();
    const {user, logout, isLoading, isAuthenticated} = useAuth();
    const {items: cartItems, itemCount, totalPrice, remove: removeFromCart} = useCart();
    const [searchQuery, setSearchQuery] = useState<string>("");
    const router = useRouter();

    return (
        <>
            <header className="navbar-light navbar-sticky header-static">
                <nav className="navbar navbar-expand-xl">
                    <div className="container-fluid px-3 px-xl-5">
                        <a className="navbar-brand" href="/">
                            <LoadingSkeleton isLoading={isLoadingNavbar} Content={() => (
                                <img className="light-mode-item navbar-brand-item" style={{width: 200, height: 50}} src={navbarData?.navbar_logo}
                                     alt="navbar logo"/>
                            )}
                            />
                            {/*<img className="dark-mode-item navbar-brand-item" src="assets/images/logo-light.svg"*/}
                            {/*     alt="logo"/>*/}
                        </a>
                        <button className="navbar-toggler ms-auto" type="button" data-bs-toggle="collapse"
                                data-bs-target="#navbarCollapse" aria-controls="navbarCollapse" aria-expanded="false"
                                aria-label="Toggle navigation">
                                    <span className="navbar-toggler-animation">
                                      <span>
                                      </span>
                                      <span>
                                      </span>
                                      <span>
                                      </span>
                                    </span>
                        </button>
                        <div className="navbar-collapse w-100 collapse" id="navbarCollapse">
                            <ul className="navbar-nav navbar-nav-scroll me-auto">
                                <li className="nav-item dropdown dropdown-menu-shadow-stacked">
                                </li>
                            </ul>
                            <ul className="navbar-nav navbar-nav-scroll me-auto flex-nowrap">
                                <LoadingSkeleton isLoading={isLoadingNavbar} width={"75px"} height={"40px"} count={3}
                                                 Content={() => (
                                                     navbarData?.navbar_links?.map((item, index) => (
                                                         <li className="nav-item" key={index}>
                                                             <a className="nav-link" href={item.url} id="demoMenu"
                                                                aria-expanded="false" style={{ whiteSpace: 'nowrap' }}>
                                                                 {item.name}
                                                             </a>
                                                         </li>
                                                     )))}/>
                                <li className="nav-item dropdown dropdown-fullwidth">
                                    <a className="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown"
                                       aria-haspopup="true" aria-expanded="false">
                                        <LoadingSkeleton isLoading={isLoadingNavbar} width={"75px"} height={"40px"} Content={() => "مگامنو"} />
                                    </a>
                                    <div className="dropdown-menu dropdown-menu-end" data-bs-popper="none">
                                        <div className="row p-4 g-4">
                                            <div className="col-xl-6 col-xxl-3">
                                                <h6 className="mb-0">
                                                    {navbarData?.col1.title}
                                                </h6>
                                                <hr/>
                                                <ul className="list-unstyled">
                                                    {
                                                        navbarData?.col1.items.map((item, index: number) => (
                                                            <li key={index}>
                                                                <a className="dropdown-item" href={item.link.url}>
                                                                    {item.label || item.link.name}
                                                                </a>
                                                            </li>
                                                        ))
                                                    }
                                                </ul>
                                            </div>
                                            <div className="col-xl-6 col-xxl-3">
                                                <h6 className="mb-0">
                                                    {navbarData?.col2.title}
                                                </h6>
                                                <hr/>
                                                {
                                                    navbarData?.col2.items.map((item, index: number) => (
                                                        <div className="mb-2 position-relative bg-primary-soft-hover rounded-2 transition-base p-3" key={index}>
                                                            <a className="stretched-link h6 mb-0" href={item.link.url}>
                                                                {item.label || item.link.name}
                                                            </a>
                                                            <p className="mb-0 small text-truncate-2">
                                                                {item.description}
                                                            </p>
                                                        </div>
                                                    ))
                                                }
                                            </div>
                                            <div className="col-xl-6 col-xxl-3">
                                                <h6 className="mb-0">
                                                    {navbarData?.col3.title}
                                                </h6>
                                                <hr/>
                                                {
                                                    navbarData?.col3.items.map((item, index: number) => (
                                                        <div className="d-flex mb-4 position-relative" key={index}>
                                                            <h2 className="mb-0">
                                                                <img src={item.icon} alt={item.label || item.link.name}/>
                                                            </h2>
                                                            <div className="ms-2">
                                                                <a className="stretched-link h6 mb-0" href={item.link.url}>
                                                                    {item.label || item.link.name}
                                                                </a>
                                                                <p className="mb-0 small">
                                                                    {item.description}
                                                                </p>
                                                            </div>
                                                        </div>
                                                    ))
                                                }
                                            </div>
                                            <div className="col-xl-6 col-xxl-3">
                                                <h6 className="mb-0">
                                                    {navbarData?.banner.title}
                                                </h6>
                                                <hr/>
                                                <a href={navbarData?.banner.link}>
                                                    <img src={navbarData?.banner.image} alt={navbarData?.banner.title}/>
                                                </a>
                                            </div>
                                            {
                                                navbarData?.notification ? (
                                                    <div className="col-12">
                                                        <div
                                                            className="alert alert-success alert-dismissible fade show mt-2 mb-0 rounded-3"
                                                            role="alert">
                                                            {navbarData?.notification}
                                                        </div>
                                                    </div>
                                                ) : null
                                            }
                                        </div>
                                    </div>
                                </li>
                            </ul>
                            <div className="nav my-3 my-xl-0 px-4 flex-nowrap align-items-center">
                                <div className="nav-item w-100">
                                    <form className="position-relative" action={"/courses/"}>
                                        <input className="form-control pe-5 bg-transparent"
                                               type="search" name={"search"} placeholder="جستجو..." aria-label="Search"/>
                                        <button
                                            className="bg-transparent p-2 position-absolute top-50 end-0 translate-middle-y border-0 text-primary-hover text-reset"
                                            type="submit">
                                            <i className="fas fa-search fs-6 ">
                                            </i>
                                        </button>
                                    </form>
                                </div>
                            </div>
                        </div>
                        {/* Cart */}
                        <div className="dropdown ms-1">
                            <a
                                className="position-relative d-flex align-items-center justify-content-center p-2 text-body"
                                href="#"
                                id="cartDropdown"
                                role="button"
                                data-bs-auto-close="outside"
                                data-bs-display="static"
                                data-bs-toggle="dropdown"
                                aria-expanded="false"
                                style={{width: 40, height: 40}}
                            >
                                <i className="bi bi-cart3 fs-5"></i>
                                {itemCount > 0 && (
                                    <span
                                        className="position-absolute badge rounded-pill bg-danger"
                                        style={{top: 0, right: 0, transform: 'translate(30%, -30%)', fontSize: '0.62rem', minWidth: '1.15rem', textAlign: 'center', lineHeight: '1.15rem', padding: '0 0.25rem'}}
                                    >
                                        {itemCount > 99 ? '99+' : itemCount}
                                    </span>
                                )}
                            </a>
                            <ul
                                className="dropdown-menu dropdown-animation dropdown-menu-end shadow pt-3 px-3"
                                aria-labelledby="cartDropdown"
                                style={{minWidth: 300}}
                            >
                                {itemCount === 0 ? (
                                    <li className="text-center py-4 text-muted">
                                        <i className="bi bi-cart3 fs-2 d-block mb-2 opacity-50"></i>
                                        <small>سبد خرید خالی است</small>
                                    </li>
                                ) : (
                                    <>
                                        <li className="mb-1">
                                            <small className="text-muted fw-semibold">سبد خرید ({itemCount} مورد)</small>
                                        </li>
                                        <li><hr className="dropdown-divider my-2"/></li>
                                        <div style={{maxHeight: 260, overflowY: 'auto'}}>
                                            {cartItems.map((item, idx) => (
                                                <li key={idx} className="d-flex align-items-center py-2 gap-2">
                                                    <div className="flex-shrink-0">
                                                        {item.picture ? (
                                                            <img
                                                                src={item.picture}
                                                                alt={item.name}
                                                                className="rounded"
                                                                style={{width: 42, height: 42, objectFit: 'cover'}}
                                                            />
                                                        ) : (
                                                            <div
                                                                className="bg-light rounded d-flex align-items-center justify-content-center"
                                                                style={{width: 42, height: 42}}
                                                            >
                                                                <i className="bi bi-mortarboard text-muted small"></i>
                                                            </div>
                                                        )}
                                                    </div>
                                                    <div className="flex-grow-1 overflow-hidden">
                                                        <p className="mb-0 small fw-medium text-truncate">
                                                            {item.name || 'آیتم'}
                                                        </p>
                                                        {item.price !== undefined && (
                                                            <small className="text-muted">
                                                                {(item.new_price && item.new_price > 0
                                                                    ? item.new_price
                                                                    : item.price
                                                                ).toLocaleString('fa-IR')} تومان
                                                            </small>
                                                        )}
                                                    </div>
                                                    <button
                                                        className="btn btn-sm p-0 text-danger flex-shrink-0"
                                                        style={{lineHeight: 1}}
                                                        title="حذف"
                                                        onClick={() => removeFromCart(item.app_label, item.model, item.object_id)}
                                                    >
                                                        <i className="bi bi-x-lg small"></i>
                                                    </button>
                                                </li>
                                            ))}
                                        </div>
                                        {totalPrice > 0 && (
                                            <>
                                                <li><hr className="dropdown-divider my-2"/></li>
                                                <li className="d-flex justify-content-between align-items-center pb-1">
                                                    <small className="fw-bold">مجموع:</small>
                                                    <small className="fw-bold text-primary">
                                                        {totalPrice.toLocaleString('fa-IR')} تومان
                                                    </small>
                                                </li>
                                            </>
                                        )}
                                        <li className="pb-3 pt-2">
                                            <a href="/cart/" className="btn btn-primary btn-sm w-100">
                                                مشاهده سبد خرید
                                            </a>
                                        </li>
                                    </>
                                )}
                            </ul>
                        </div>

                        {/* Profile */}
                        <div className="dropdown ms-1 ms-lg-0">
                            {isAuthenticated && !isLoading ? (
                                <>
                                    <a className="avatar avatar-sm p-0" href="#" id="profileDropdown" role="button"
                                       data-bs-auto-close="outside" data-bs-display="static" data-bs-toggle="dropdown"
                                       aria-expanded="false">
                                        <LoadingSkeleton isLoading={isLoading} width="40px" height="40px"
                                                         Content={() => (
                                                             <img className="avatar-img rounded-circle"
                                                                  src={user?.profile_picture || "/assets/images/auth/default_profile.png"}
                                                                  alt={user?.name || "User"}/>
                                                         )}/>
                                    </a>
                                    <ul className="dropdown-menu dropdown-animation dropdown-menu-end shadow pt-3"
                                        aria-labelledby="profileDropdown">
                                        <li className="px-3 mb-3">
                                            <div className="d-flex align-items-center">
                                                <div className="avatar me-3">
                                                    <LoadingSkeleton isLoading={isLoading} width="50px" height="50px"
                                                                     Content={() => (
                                                                         <img className="avatar-img rounded-circle
  shadow"
                                                                              src={user?.profile_picture || "/assets/images/element/01.svg"}
                                                                              alt={user?.name || "User"}/>
                                                                     )}/>
                                                </div>
                                                <div>
                                                    <LoadingSkeleton isLoading={isLoading} width="120px" height="20px"
                                                                     Content={() => (
                                                                         <a className="h6" href="#">
                                                                             {user?.name}
                                                                         </a>
                                                                     )}/>
                                                    <LoadingSkeleton isLoading={isLoading} width="150px" height="16px"
                                                                     Content={() => (
                                                                         <p className="small m-0">
                                                                             {user?.email || user?.phone}
                                                                         </p>
                                                                     )}/>
                                                </div>
                                            </div>
                                        </li>
                                        <li>
                                            <hr className="dropdown-divider"/>
                                        </li>
                                        <li>
                                            <a className="dropdown-item" href="/dashboard/">
                                                <i className="bi bi-person fa-fw me-2"></i>
                                                داشبورد
                                            </a>
                                        </li>
                                        <li>
                                            <a className="dropdown-item" href="/dashboard/personal-information/">
                                                <i className="bi bi-person-check fa-fw me-2"></i>
                                                اطلاعات شخصی
                                            </a>
                                        </li>
                                        <li>
                                            <a className="dropdown-item" href="/dashboard/profile/">
                                                <i className="bi bi-person-add fa-fw me-2"></i>
                                                پروفایل
                                            </a>
                                        </li>
                                        <li>
                                            <a className="dropdown-item" href="/dashboard/settings/">
                                                <i className="bi bi-gear fa-fw me-2"></i>
                                                تنظیمات
                                            </a>
                                        </li>
                                        <li>
                                            <a className="dropdown-item" href="/dashboard/tickets/">
                                                <i className="bi bi-ticket-detailed fa-fw me-2"></i>
                                                تیکت های شما
                                            </a>
                                        </li>
                                        <li>
                                            <a className="dropdown-item" href="/dashboard/transactions/">
                                                <i className="bi bi-wallet fa-fw me-2"></i>
                                                تراکنش های شما
                                            </a>
                                        </li>
                                        <li>
                                            <a className="dropdown-item" href="/dashboard/saved-courses/">
                                                <i className="bi bi-bookmark fa-fw me-2"></i>
                                                دوره های نشان شده
                                            </a>
                                        </li>
                                        <li>
                                            <a className="dropdown-item" href="/dashboard/saved-blogs/">
                                                <i className="bi bi-journal-bookmark-fill fa-fw me-2"></i>
                                                پست های نشان شده
                                            </a>
                                        </li>
                                        <li>
                                            <a className="dropdown-item" href="#" onClick={(e) => {
                                                e.preventDefault();
                                                logout();
                                                router.push('/');
                                            }}>
                                                <i className="bi bi-box-arrow-right fa-fw me-2"></i>
                                                خروج
                                            </a>
                                        </li>
                                    </ul>
                                </>
                            ) : (
                                <>
                                    <a className="avatar avatar-sm p-0" href="#" id="profileDropdown" role="button"
                                       data-bs-auto-close="outside" data-bs-display="static" data-bs-toggle="dropdown"
                                       aria-expanded="false">
                                        <img className="avatar-img rounded-circle"
                                             src={"/assets/images/auth/default_profile.png"}
                                             alt={"Default Profile"}/>
                                    </a>
                                    <ul className="dropdown-menu dropdown-animation dropdown-menu-end shadow pt-3"
                                        aria-labelledby="profileDropdown">
                                        <li>
                                            <a className="dropdown-item" href="/auth/login">
                                                <i className="bi bi-person fa-fw me-2"></i>
                                                ورود
                                            </a>
                                        </li>
                                        <li>
                                            <a className="dropdown-item" href="/auth/register">
                                                <i className="bi bi-person-fill-add fa-fw me-2"></i>
                                                ثبت نام
                                            </a>
                                        </li>
                                    </ul>
                                </>
                            )}
                        </div>
                    </div>
                </nav>
            </header>
            <div id="sticky-space" style={{height: 0}} className=""></div>
        </>
    );
}
