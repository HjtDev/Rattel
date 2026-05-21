"use client";

import { FormEvent, useState } from "react";
import { toast } from "react-toastify";
import { getMediaUrl } from "@/src/core/utils";
import {
  isValidIranPhoneNumber,
  submitWorkWithUsResume,
  useWorkWithUs,
  WorkWithUsResumePayload,
} from "@/src/core/hooks/useWorkWithUs";

type TabKey = 1 | 2 | 3;

const INITIAL_FORM: WorkWithUsResumePayload = {
  full_name: "",
  email: "",
  phone_number: "",
  message: "",
};

export default function WorkWithUs() {
  const { workWithUsData, isLoadingWorkWithUs, workWithUsError } = useWorkWithUs();
  const [activeTab, setActiveTab] = useState<TabKey>(1);
  const [formData, setFormData] = useState<WorkWithUsResumePayload>(INITIAL_FORM);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (field: keyof WorkWithUsResumePayload, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!formData.full_name.trim()) {
      toast.warning("نام را وارد کنید.");
      return;
    }

    if (!formData.email.trim() || !/^\S+@\S+\.\S+$/.test(formData.email.trim())) {
      toast.warning("ایمیل معتبر وارد کنید.");
      return;
    }

    if (!isValidIranPhoneNumber(formData.phone_number)) {
      toast.warning("شماره تماس باید ۱۱ رقم و با 09 شروع شود. مثال: 09123456789");
      return;
    }

    if (!formData.message.trim()) {
      toast.warning("متن درخواست را وارد کنید.");
      return;
    }

    setIsSubmitting(true);
    const result = await submitWorkWithUsResume({
      ...formData,
      full_name: formData.full_name.trim(),
      email: formData.email.trim(),
      phone_number: formData.phone_number.trim(),
      message: formData.message.trim(),
    });
    setIsSubmitting(false);

    if (!result.success) {
      toast.error(result.message || "ارسال رزومه ناموفق بود.");
      return;
    }

    toast.success("رزومه شما با موفقیت ارسال شد.");
    setFormData(INITIAL_FORM);
  };

  if (isLoadingWorkWithUs) {
    return (
      <main className="py-5 text-center">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">در حال بارگذاری...</span>
        </div>
      </main>
    );
  }

  if (workWithUsError || !workWithUsData) {
    return (
      <main className="py-5 text-center">
        <p className="text-muted">{workWithUsError || "اطلاعات این صفحه یافت نشد."}</p>
      </main>
    );
  }

  const tab1Active = activeTab === 1;
  const tab2Active = activeTab === 2;
  const tab3Active = activeTab === 3;

  return (
    <main>
      <section className="bg-light py-5">
        <div className="container">
          <div className="row g-4 align-items-center">
            <div className="col-md-6">
              <h1>{workWithUsData.hero_title}</h1>
              <p>{workWithUsData.hero_description}</p>
              <a
                href={workWithUsData.hero_link?.url || "#fill-instructor-form"}
                className="btn btn-primary mb-0"
              >
                {workWithUsData.hero_link?.name || "ثبت نام"}
              </a>
            </div>
            <div className="col-md-6 text-center">
              <img
                src={workWithUsData.hero_image ? getMediaUrl(workWithUsData.hero_image) : "/assets/images/element/04.svg"}
                className="h-300px h-xl-400px"
                alt={workWithUsData.hero_title}
              />
            </div>
          </div>
        </div>
      </section>

      <section>
        <div className="container">
          <div className="row mb-4">
            <div className="col-sm-10 col-xl-6 text-center mx-auto">
              <h2 className="fs-3">{workWithUsData.collaboration_section_title}</h2>
              <p className="mb-0">{workWithUsData.collaboration_section_description}</p>
            </div>
          </div>
          <div className="row g-4 g-md-5">
            <div className="col-md-4 text-center">
              <img
                src={workWithUsData.collaboration_section_step1_image ? getMediaUrl(workWithUsData.collaboration_section_step1_image) : "/assets/images/element/create-account.svg"}
                className="h-200px"
                alt={workWithUsData.collaboration_section_step1_title}
              />
              <h4 className="mt-3 ff-vb fs-5">{workWithUsData.collaboration_section_step1_title}</h4>
              <p className="text-truncate-2 mb-0">{workWithUsData.collaboration_section_step1_description}</p>
            </div>
            <div className="col-md-4 text-center">
              <img
                src={workWithUsData.collaboration_section_step2_image ? getMediaUrl(workWithUsData.collaboration_section_step2_image) : "/assets/images/element/add-course.svg"}
                className="h-200px"
                alt={workWithUsData.collaboration_section_step2_title}
              />
              <h4 className="mt-3 ff-vb fs-5">{workWithUsData.collaboration_section_step2_title}</h4>
              <p className="text-truncate-2 mb-0">{workWithUsData.collaboration_section_step2_description}</p>
            </div>
            <div className="col-md-4 text-center">
              <img
                src={workWithUsData.collaboration_section_step3_image ? getMediaUrl(workWithUsData.collaboration_section_step3_image) : "/assets/images/element/earn-money.svg"}
                className="h-200px"
                alt={workWithUsData.collaboration_section_step3_title}
              />
              <h4 className="mt-3 ff-vb fs-5">{workWithUsData.collaboration_section_step3_title}</h4>
              <p className="text-truncate-2 mb-0">{workWithUsData.collaboration_section_step3_description}</p>
            </div>
          </div>
        </div>
      </section>

      <section className="py-0 py-lg-5">
        <div className="container">
          <div className="bg-orange bg-opacity-10 p-4 p-sm-5 rounded">
            <div className="row g-4 position-relative align-items-center justify-content-center">
              <div className="col-sm-6 col-lg-3 text-center">
                <div className="d-flex justify-content-center">
                  <h4 className="display-6 text-orange fw-bold mb-0">{workWithUsData.counter_section_item1_value}</h4>
                  <span className="display-6 text-orange mb-0">+</span>
                </div>
                <h6 className="mb-0 fw-bold">{workWithUsData.counter_section_item1_label}</h6>
              </div>
              <div className="col-sm-6 col-lg-3 text-center">
                <div className="d-flex justify-content-center">
                  <h4 className="display-6 text-orange fw-bold mb-0">{workWithUsData.counter_section_item2_value}</h4>
                  <span className="display-6 text-orange mb-0">+</span>
                </div>
                <h6 className="mb-0 fw-bold">{workWithUsData.counter_section_item2_label}</h6>
              </div>
              <div className="col-sm-6 col-lg-3 text-center">
                <div className="d-flex justify-content-center">
                  <h4 className="display-6 text-orange fw-bold mb-0">{workWithUsData.counter_section_item3_value}</h4>
                  <span className="display-6 text-orange mb-0">+</span>
                </div>
                <h6 className="mb-0 fw-bold">{workWithUsData.counter_section_item3_label}</h6>
              </div>
              <div className="col-sm-6 col-lg-3 text-center">
                <div className="d-flex justify-content-center">
                  <h4 className="display-6 text-orange fw-bold mb-0">{workWithUsData.counter_section_item4_value}</h4>
                  <span className="display-6 text-orange mb-0">+</span>
                </div>
                <h6 className="mb-0 fw-bold">{workWithUsData.counter_section_item4_label}</h6>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section>
        <div className="container">
          <div className="row">
            <div className="col-lg-5 position-relative mt-xl-0" id="fill-instructor-form">
              <div className="card card-body shadow p-4">
                <h3 className="fs-4">ارسال رزومه</h3>
                <form className="row g-3 mt-2 position-relative z-index-9" onSubmit={handleSubmit}>
                  <div className="col-lg-6">
                    <label className="form-label">نام *</label>
                    <input
                      type="text"
                      className="form-control"
                      value={formData.full_name}
                      onChange={(e) => handleChange("full_name", e.target.value)}
                    />
                  </div>
                  <div className="col-lg-6">
                    <label className="form-label">ایمیل *</label>
                    <input
                      type="email"
                      className="form-control"
                      value={formData.email}
                      onChange={(e) => handleChange("email", e.target.value)}
                    />
                  </div>
                  <div className="col-lg-12">
                    <label className="form-label">شماره تماس *</label>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="09123456789"
                      maxLength={11}
                      value={formData.phone_number}
                      onChange={(e) => handleChange("phone_number", e.target.value)}
                    />
                  </div>
                  <div className="col-12">
                    <label className="form-label">متن درخواست *</label>
                    <textarea
                      className="form-control"
                      rows={3}
                      spellCheck={false}
                      value={formData.message}
                      onChange={(e) => handleChange("message", e.target.value)}
                    />
                  </div>
                  <div className="col-12">
                    <button type="submit" className="btn btn-primary mb-0" disabled={isSubmitting}>
                      {isSubmitting ? "در حال ارسال..." : "ارسال"}
                    </button>
                  </div>
                </form>
              </div>
            </div>
            <div className="col-lg-7 z-index-9 mt-5 mt-xl-0">
              <h3 className="fs-4">{workWithUsData.main_content_section_title}</h3>
              <ul className="nav nav-pills nav-pill-soft my-4" role="tablist">
                <li className="nav-item me-2 me-lg-4" role="presentation">
                  <button
                    className={`nav-link mb-2 mb-xl-0 ${tab1Active ? "active" : ""}`}
                    type="button"
                    onClick={() => setActiveTab(1)}
                  >
                    {workWithUsData.main_content_section_tab1_title}
                  </button>
                </li>
                <li className="nav-item me-2 me-lg-4" role="presentation">
                  <button
                    className={`nav-link mb-2 mb-xl-0 ${tab2Active ? "active" : ""}`}
                    type="button"
                    onClick={() => setActiveTab(2)}
                  >
                    {workWithUsData.main_content_section_tab2_title}
                  </button>
                </li>
                <li className="nav-item me-2 me-lg-4" role="presentation">
                  <button
                    className={`nav-link mb-2 mb-xl-0 ${tab3Active ? "active" : ""}`}
                    type="button"
                    onClick={() => setActiveTab(3)}
                  >
                    {workWithUsData.main_content_section_tab3_title}
                  </button>
                </li>
              </ul>
              <div className="tab-content">
                {tab1Active && (
                  <div className="tab-pane fade show active">
                    <h6>{workWithUsData.main_content_section_tab1_title}</h6>
                    <div dangerouslySetInnerHTML={{ __html: workWithUsData.main_content_section_tab1_description }} />
                  </div>
                )}
                {tab2Active && (
                  <div className="tab-pane fade show active">
                    <h6>{workWithUsData.main_content_section_tab2_title}</h6>
                    <div dangerouslySetInnerHTML={{ __html: workWithUsData.main_content_section_tab2_description }} />
                  </div>
                )}
                {tab3Active && (
                  <div className="tab-pane fade show active">
                    <h6>{workWithUsData.main_content_section_tab3_title}</h6>
                    <div dangerouslySetInnerHTML={{ __html: workWithUsData.main_content_section_tab3_description }} />
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="pt-0">
        <div className="container position-relative">
          <div className="bg-dark p-4 p-sm-5 rounded-3">
            <div className="row justify-content-center position-relative">
              <div className="col-11 position-relative">
                <div className="row align-items-center">
                  <div className="col-lg-7">
                    <h3 className="text-white">{workWithUsData.advertisement_section_title}</h3>
                    <p className="text-white mb-3 mb-lg-0">{workWithUsData.advertisement_section_description}</p>
                  </div>
                  <div className="col-lg-5 text-lg-end">
                    <a
                      href={workWithUsData.advertisement_section_link?.url || "#fill-instructor-form"}
                      className="btn btn-lg btn-white mb-0"
                    >
                      {workWithUsData.advertisement_section_link?.name || "ثبت نام"}
                    </a>
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
