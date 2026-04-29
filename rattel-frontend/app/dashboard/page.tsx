"use client";

import DashboardBase from "@/src/components/dashboard/DashboardBase";
import {useDashboard} from "@/src/core/hooks/useDashboard";

function DashboardContent() {
    const {dashboardData, isLoadingDashboard} = useDashboard();

    return !isLoadingDashboard && (
        <div className="col-xl-9">
            <div className="row mb-4">
                <div className="col-sm-6 col-lg-4 mb-3 mb-lg-0">
                    <div
                        className="d-flex justify-content-center align-items-center p-4 bg-orange bg-opacity-15 rounded-3">
                <span className="display-6 lh-1 text-orange mb-0">
                  <i className="fas fa-clipboard-check fa-fw">
                  </i>
                </span>
                        <div className="ms-4">
                            <div className="d-flex">
                                <h5 className="purecounter mb-0 fw-bold" data-purecounter-start="0"
                                    data-purecounter-end="9" data-purecounter-delay="200"
                                    data-purecounter-duration="0">
                                    {dashboardData?.courses_count}
                                </h5>
                            </div>
                            <p className="mb-0 h6 fw-light">
                                دوره ها
                            </p>
                        </div>
                    </div>
                </div>
                <div className="col-sm-6 col-lg-4 mb-3 mb-lg-0">
                    <div
                        className="d-flex justify-content-center align-items-center p-4 bg-purple bg-opacity-15 rounded-3">
                <span className="display-6 lh-1 text-purple mb-0">
                  <i className="fas fa-tv fa-fw">
                  </i>
                </span>
                        <div className="ms-4">
                            <div className="d-flex">
                                <h5 className="purecounter mb-0 fw-bold" data-purecounter-start="0"
                                    data-purecounter-end="52" data-purecounter-delay="200"
                                    data-purecounter-duration="0">
                                    {dashboardData?.tickets_count}
                                </h5>
                            </div>
                            <p className="mb-0 h6 fw-light">
                                تیکت ها
                            </p>
                        </div>
                    </div>
                </div>
                <div className="col-sm-6 col-lg-4 mb-3 mb-lg-0">
                    <div
                        className="d-flex justify-content-center align-items-center p-4 bg-success bg-opacity-10 rounded-3">
                <span className="display-6 lh-1 text-success mb-0">
                  <i className="fas fa-medal fa-fw">
                  </i>
                </span>
                        <div className="ms-4">
                            <div className="d-flex">
                                <h5 className="purecounter mb-0 fw-bold" data-purecounter-start="0"
                                    data-purecounter-end="8" data-purecounter-delay="300"
                                    data-purecounter-duration="0">
                                    {dashboardData?.days_since_registration}
                                </h5>
                            </div>
                            <p className="mb-0 h6 fw-light">
                                روز از عضویت شما
                            </p>
                        </div>
                    </div>
                </div>
            </div>
            <div className="card bg-transparent border rounded-3">
                <div className="card-header bg-transparent border-bottom">
                    <h3 className="mb-0 fs-5 ff-vb">
                        لیست دوره های من
                    </h3>
                </div>
                <div className="card-body">
                    <div className="row g-3 align-items-center justify-content-between mb-4">
                        <div className="col-md-12">
                            <form className="rounded position-relative">
                                <input className="form-control pe-5 bg-transparent" type="search"
                                       placeholder="جستجوی دوره" aria-label="Search"/>
                                <button
                                    className="bg-transparent p-2 position-absolute top-50 end-0 translate-middle-y border-0 text-primary-hover text-reset"
                                    type="submit">
                                    <i className="fas fa-search fs-6 ">
                                    </i>
                                </button>
                            </form>
                        </div>
                    </div>
                    <div className="table-responsive border-0">
                        <table className="table table-dark-gray align-middle p-4 mb-0 table-hover">
                            <thead>
                            <tr>
                                <th scope="col" className="border-0 rounded-start">
                                    دوره
                                </th>
                                <th scope="col" className="border-0">
                                    کل دوره ها
                                </th>
                                <th scope="col" className="border-0">
                                    دوره های تکمیل
                                </th>
                                <th scope="col" className="border-0 rounded-end">
                                    عملیات
                                </th>
                            </tr>
                            </thead>
                            <tbody>
                            <tr>
                                <td>
                                    <div className="d-flex align-items-center">
                                        <div className="w-100px">
                                            <img src="/assets/images/courses/4by3/08.jpg"
                                                 className="rounded"
                                            />
                                        </div>
                                        <div className="mb-0 ms-2">
                                            <h6 className="fw-normal">
                                                <a href="#">
                                                    دوره جامع آموزش Sketch
                                                </a>
                                            </h6>
                                            <div className="overflow-hidden">
                                                <h6 className="mb-0 text-end">
                                                    85%
                                                </h6>
                                                <div
                                                    className="progress progress-sm bg-primary bg-opacity-10">
                                                    <div
                                                        className={"progress-bar bg-primary aos aos-init aos-animate"}
                                                        role={"progressbar"} data-aos={"slide-left"}
                                                        data-aos-delay={200} data-aos-duration={1000}
                                                        data-aos-easing={"ease-in-out"}
                                                        style={{width: '85%'}}
                                                        aria-valuenow={85} aria-valuemin={0}
                                                        aria-valuemax={100}
                                                    >
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </td>
                                <td>
                                    56
                                </td>
                                <td>
                                    40
                                </td>
                                <td>
                                    <a href="#"
                                       className="btn btn-sm btn-primary-soft me-1 mb-1 mb-md-0">
                                        <i className="bi bi-play-circle me-1">
                                        </i>
                                        ادامه
                                    </a>
                                </td>
                            </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default function Dashboard() {
    return (
        <DashboardBase Content={<DashboardContent />} />
    )
}
