"use client";

import DashboardBase from "@/src/components/dashboard/DashboardBase";
import { useDashboard } from "@/src/core/hooks/useDashboard";
import { useMyInPersonClassRegistrations } from "@/src/core/hooks/useInPersonClasses";
import { getMediaUrl, toJalali } from "@/src/core/utils";

const formatPrice = (price: number) =>
    new Intl.NumberFormat("fa-IR").format(price);

function RegisteredClassesContent() {
    const { isLoadingDashboard } = useDashboard();
    const { registrations, isLoadingRegistrations } = useMyInPersonClassRegistrations();

    return !isLoadingDashboard && (
        <div className="col-xl-9">
            <div className="card bg-transparent border rounded-3">
                <div className="card-header bg-transparent border-bottom">
                    <h3 className="mb-0 fs-5 ff-vb">کلاس‌های حضوری ثبت‌نام‌شده</h3>
                </div>

                <div className="card-body">
                    {isLoadingRegistrations ? (
                        <div className="text-center py-5">
                            <div className="spinner-border text-primary" role="status">
                                <span className="visually-hidden">در حال بارگذاری...</span>
                            </div>
                        </div>
                    ) : !registrations || registrations.length === 0 ? (
                        <div className="text-center py-5">
                            <i className="bi bi-calendar-x fs-1 text-muted mb-3 d-block"></i>
                            <p className="text-muted">هنوز در هیچ کلاسی ثبت‌نام نکرده‌اید</p>
                            <a href="/in-person-classes/" className="btn btn-primary btn-sm mt-2">
                                مشاهده کلاس‌های حضوری
                            </a>
                        </div>
                    ) : (
                        <div className="table-responsive border-0">
                            <table className="table table-dark-gray align-middle p-4 mb-0 table-hover">
                                <thead>
                                    <tr>
                                        <th scope="col" className="border-0 rounded-start">کلاس</th>
                                        <th scope="col" className="border-0">زمان</th>
                                        <th scope="col" className="border-0">تاریخ شروع</th>
                                        <th scope="col" className="border-0">تاریخ پایان</th>
                                        <th scope="col" className="border-0">ثبت‌نام‌شدگان</th>
                                        <th scope="col" className="border-0">قیمت پرداختی</th>
                                        <th scope="col" className="border-0 rounded-end">لینک آنلاین</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {registrations.map((reg) => (
                                        <tr key={reg.id}>
                                            <td>
                                                <div className="d-flex align-items-center">
                                                    <div className="w-80px flex-shrink-0">
                                                        <img
                                                            src={
                                                                reg.in_person_class.thumbnail
                                                                    ? getMediaUrl(reg.in_person_class.thumbnail)
                                                                    : "/assets/images/courses/4by3/06.jpg"
                                                            }
                                                            className="rounded"
                                                            style={{ width: "80px", height: "55px", objectFit: "cover" }}
                                                            alt={reg.in_person_class.title}
                                                        />
                                                    </div>
                                                    <div className="mb-0 ms-2">
                                                        <h6 className="mb-0">{reg.in_person_class.title}</h6>
                                                        {reg.in_person_class.categories.length > 0 && (
                                                            <small className="text-muted">
                                                                {reg.in_person_class.categories.map((c) => c.name).join("، ")}
                                                            </small>
                                                        )}
                                                    </div>
                                                </div>
                                            </td>
                                            <td>
                                                <span className="badge bg-primary bg-opacity-10 text-primary">
                                                    <i className="bi bi-clock me-1"></i>
                                                    {reg.time_range.label}
                                                </span>
                                            </td>
                                            <td className="text-nowrap">{toJalali(reg.start_date)}</td>
                                            <td className="text-nowrap">{toJalali(reg.end_date)}</td>
                                            <td>
                                                <span className="badge bg-success bg-opacity-10 text-success">
                                                    <i className="bi bi-people me-1"></i>
                                                    {reg.registered_count} نفر
                                                </span>
                                            </td>
                                            <td className="text-nowrap">
                                                <span className="text-success fw-semibold">
                                                    {formatPrice(reg.new_price > 0 ? reg.new_price : reg.price)} تومان
                                                </span>
                                            </td>
                                            <td>
                                                {reg.in_person_class.meeting_url ? (
                                                    <a
                                                        href={reg.in_person_class.meeting_url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="btn btn-sm btn-outline-primary"
                                                    >
                                                        <i className="bi bi-camera-video me-1"></i>
                                                        ورود به جلسه
                                                    </a>
                                                ) : (
                                                    <span className="text-muted">—</span>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default function RegisteredClassesPage() {
    return <DashboardBase Content={<RegisteredClassesContent />} />;
}
