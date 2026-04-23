'use client'
import {useNavbar} from "@/src/core/hooks/useNavbar";
import {toast} from "react-toastify";
import LoadingSkeleton from "@/src/components/skeleton/loadingSkeleton";
import {indexOf} from "eslint-config-next";

export default function Navbar() {
    const {isLoadingNavbar, navbarData, navbarError} = useNavbar();

    return (
        <>
            <header className="navbar-light navbar-sticky header-static">
                <nav className="navbar navbar-expand-xl">
                    <div className="container-fluid px-3 px-xl-5">
                        <a className="navbar-brand" href="/">
                            <LoadingSkeleton isLoading={isLoadingNavbar} width={"126px"} height={"36px"} Content={() => (
                                <img className="light-mode-item navbar-brand-item" src={navbarData?.navbar_logo}
                                     alt="logo"/>
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
                            <ul className="navbar-nav navbar-nav-scroll me-auto">
                                <LoadingSkeleton isLoading={isLoadingNavbar} width={"75px"} height={"40px"} count={3}
                                                 Content={() => (
                                                     navbarData?.navbar_links?.map((item, index) => (
                                                         <li className="nav-item" key={index}>
                                                             <a className="nav-link" href={item.url} id="demoMenu"
                                                                aria-expanded="false">
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
                                                        navbarData?.col1.items.map((item, index) => (
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
                                                    navbarData?.col2.items.map((item, index) => (
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
                                                    navbarData?.col3.items.map((item, index) => (
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
                                    <form className="position-relative">
                                        <input className="form-control pe-5 bg-transparent" type="search"
                                               placeholder="جستجو..." aria-label="Search"/>
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
                        <div className="dropdown ms-1 ms-lg-0">
                            <a className="avatar avatar-sm p-0" href="#" id="profileDropdown" role="button"
                               data-bs-auto-close="outside" data-bs-display="static" data-bs-toggle="dropdown"
                               aria-expanded="false">
                                <img className="avatar-img rounded-circle" src="assets/images/avatar/01.jpg"
                                     alt="avatar"/>
                            </a>
                            <ul className="dropdown-menu dropdown-animation dropdown-menu-end shadow pt-3"
                                aria-labelledby="profileDropdown">
                                <li className="px-3 mb-3">
                                    <div className="d-flex align-items-center">
                                        <div className="avatar me-3">
                                            <img className="avatar-img rounded-circle shadow"
                                                 src="assets/images/avatar/01.jpg" alt="avatar"/>
                                        </div>
                                        <div>
                                            <a className="h6" href="#">
                                                الهام حسینی
                                            </a>
                                            <p className="small m-0">
                                                example@gmail.com
                                            </p>
                                        </div>
                                    </div>
                                </li>
                                <li>
                                    <hr className="dropdown-divider"/>
                                </li>
                                <li>
                                    <a className="dropdown-item" href="#">
                                        <i className="bi bi-person fa-fw me-2">
                                        </i>
                                        پروفایل
                                    </a>
                                </li>
                                <li>
                                    <a className="dropdown-item" href="#">
                                        <i className="bi bi-gear fa-fw me-2">
                                        </i>
                                        تنظیمات
                                    </a>
                                </li>
                                {/*<li>*/}
                                {/*    <hr className="dropdown-divider"/>*/}
                                {/*</li>*/}
                                {/*<li>*/}
                                {/*    <div*/}
                                {/*        className="bg-light dark-mode-switch theme-icon-active d-flex align-items-center p-1 rounded mt-2">*/}
                                {/*        <button type="button" className="btn btn-sm mb-0 active"*/}
                                {/*                data-bs-theme-value="light">*/}
                                {/*            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"*/}
                                {/*                 fill="currentColor" className="bi bi-sun fa-fw mode-switch"*/}
                                {/*                 viewBox="0 0 16 16">*/}
                                {/*                <path*/}
                                {/*                    d="M8 11a3 3 0 1 1 0-6 3 3 0 0 1 0 6zm0 1a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM8 0a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-1 0v-2A.5.5 0 0 1 8 0zm0 13a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-1 0v-2A.5.5 0 0 1 8 13zm8-5a.5.5 0 0 1-.5.5h-2a.5.5 0 0 1 0-1h2a.5.5 0 0 1 .5.5zM3 8a.5.5 0 0 1-.5.5h-2a.5.5 0 0 1 0-1h2A.5.5 0 0 1 3 8zm10.657-5.657a.5.5 0 0 1 0 .707l-1.414 1.415a.5.5 0 1 1-.707-.708l1.414-1.414a.5.5 0 0 1 .707 0zm-9.193 9.193a.5.5 0 0 1 0 .707L3.05 13.657a.5.5 0 0 1-.707-.707l1.414-1.414a.5.5 0 0 1 .707 0zm9.193 2.121a.5.5 0 0 1-.707 0l-1.414-1.414a.5.5 0 0 1 .707-.707l1.414 1.414a.5.5 0 0 1 0 .707zM4.464 4.465a.5.5 0 0 1-.707 0L2.343 3.05a.5.5 0 1 1 .707-.707l1.414 1.414a.5.5 0 0 1 0 .708z">*/}
                                {/*                </path>*/}
                                {/*                <use href="#">*/}
                                {/*                </use>*/}
                                {/*            </svg>*/}
                                {/*            روشن*/}
                                {/*        </button>*/}
                                {/*        <button type="button" className="btn btn-sm mb-0" data-bs-theme-value="dark">*/}
                                {/*            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"*/}
                                {/*                 fill="currentColor" className="bi bi-moon-stars fa-fw mode-switch"*/}
                                {/*                 viewBox="0 0 16 16">*/}
                                {/*                <path*/}
                                {/*                    d="M6 .278a.768.768 0 0 1 .08.858 7.208 7.208 0 0 0-.878 3.46c0 4.021 3.278 7.277 7.318 7.277.527 0 1.04-.055 1.533-.16a.787.787 0 0 1 .81.316.733.733 0 0 1-.031.893A8.349 8.349 0 0 1 8.344 16C3.734 16 0 12.286 0 7.71 0 4.266 2.114 1.312 5.124.06A.752.752 0 0 1 6 .278zM4.858 1.311A7.269 7.269 0 0 0 1.025 7.71c0 4.02 3.279 7.276 7.319 7.276a7.316 7.316 0 0 0 5.205-2.162c-.337.042-.68.063-1.029.063-4.61 0-8.343-3.714-8.343-8.29 0-1.167.242-2.278.681-3.286z">*/}
                                {/*                </path>*/}
                                {/*                <path*/}
                                {/*                    d="M10.794 3.148a.217.217 0 0 1 .412 0l.387 1.162c.173.518.579.924 1.097 1.097l1.162.387a.217.217 0 0 1 0 .412l-1.162.387a1.734 1.734 0 0 0-1.097 1.097l-.387 1.162a.217.217 0 0 1-.412 0l-.387-1.162A1.734 1.734 0 0 0 9.31 6.593l-1.162-.387a.217.217 0 0 1 0-.412l1.162-.387a1.734 1.734 0 0 0 1.097-1.097l.387-1.162zM13.863.099a.145.145 0 0 1 .274 0l.258.774c.115.346.386.617.732.732l.774.258a.145.145 0 0 1 0 .274l-.774.258a1.156 1.156 0 0 0-.732.732l-.258.774a.145.145 0 0 1-.274 0l-.258-.774a1.156 1.156 0 0 0-.732-.732l-.774-.258a.145.145 0 0 1 0-.274l.774-.258c.346-.115.617-.386.732-.732L13.863.1z">*/}
                                {/*                </path>*/}
                                {/*                <use href="#">*/}
                                {/*                </use>*/}
                                {/*            </svg>*/}
                                {/*            تیره*/}
                                {/*        </button>*/}
                                {/*        <button type="button" className="btn btn-sm mb-0" data-bs-theme-value="auto">*/}
                                {/*            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"*/}
                                {/*                 fill="currentColor" className="bi bi-circle-half fa-fw mode-switch"*/}
                                {/*                 viewBox="0 0 16 16">*/}
                                {/*                <path d="M8 15A7 7 0 1 0 8 1v14zm0 1A8 8 0 1 1 8 0a8 8 0 0 1 0 16z">*/}
                                {/*                </path>*/}
                                {/*                <use href="#">*/}
                                {/*                </use>*/}
                                {/*            </svg>*/}
                                {/*            خودکار*/}
                                {/*        </button>*/}
                                {/*    </div>*/}
                                {/*</li>*/}
                            </ul>
                        </div>
                    </div>
                </nav>
            </header>
            <div id="sticky-space" style={{height: 0}} className=""></div>
        </>
    );
}
