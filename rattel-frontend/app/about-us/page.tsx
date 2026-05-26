"use client";

import { useAboutUs } from "@/src/core/hooks/useAboutUs";
import { getMediaUrl } from "@/src/core/utils";
import InformationBoxes from "@/src/components/home/InformationBoxes";

export default function AboutUs() {
  const { aboutUsData, isLoadingAboutUs, aboutUsError } = useAboutUs();

  if (isLoadingAboutUs) {
    return (
      <main>
        <div className="text-center py-5">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">در حال بارگذاری...</span>
          </div>
        </div>
      </main>
    );
  }

  if (aboutUsError) {
    return (
      <main>
        <div style={{ padding: "2rem", textAlign: "center" }}>
          <p>خطا در بارگذاری اطلاعات: {aboutUsError}</p>
        </div>
      </main>
    );
  }

  return (
    <main>
      <section>
        <div className="container">
          <div className="row g-4">
            <div className="col-10 text-center mx-auto position-relative">
              <h1 className="position-relative fs-3">{aboutUsData?.image_section_title}</h1>
            </div>
          </div>
          <div className="row g-4 mt-0 mt-lg-5 align-items-center">
            <div className="col-6 col-md-4">
              <div className="row g-4">
                {aboutUsData?.image_section_top_right_image && (
                  <div className="col-10 col-lg-6">
                    <img className="rounded-4" src={getMediaUrl(aboutUsData.image_section_top_right_image)} alt="about-us" />
                  </div>
                )}
                {aboutUsData?.image_section_bottom_right_image && (
                  <div className="col-12">
                    <img className="rounded-4" src={getMediaUrl(aboutUsData.image_section_bottom_right_image)} alt="about-us" />
                  </div>
                )}
              </div>
            </div>
            <div className="col-6 col-md-4 position-relative">
              {aboutUsData?.image_section_middle_image && <img className="rounded-4" src={getMediaUrl(aboutUsData.image_section_middle_image)} alt="about-us" />}
            </div>
            <div className="col-md-4">
              <div className="bg-grad rounded-4 p-5 text-start">
                <span className="text-white">{aboutUsData?.image_section_box_title}</span>
                <h3 className="text-white ff-vb">{aboutUsData?.image_section_box_description}</h3>
              </div>
              {aboutUsData?.image_section_bottom_left_image && (
                <div className="mt-3">
                  <img className="rounded-4" src={getMediaUrl(aboutUsData.image_section_bottom_left_image)} alt="about-us" />
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      <section className="pt-0 pt-md-5">
        <div className="container">
          <div className="row mb-4">
            <div className="col-lg-8">
              <h2>{aboutUsData?.info_section_title}</h2>
              <div dangerouslySetInnerHTML={{ __html: aboutUsData?.info_section_description || "" }} />
            </div>
          </div>
        </div>
      </section>

      <InformationBoxes data={{ boxes: aboutUsData?.info_section_information_boxes || [] }} isLoading={isLoadingAboutUs} />

      <section className="bg-light py-4" id="trust-section" key="trust-section">
        <div className="container">
          <div className="row mb-4">
            <div className="col-lg-8 mx-auto text-center">
              <h2 className="fs-3">{aboutUsData?.trust_logo_section_title}</h2>
            </div>
          </div>
          <div className="row d-flex justify-content-center">
            {aboutUsData?.trust_logo_section_links.map((link) => (
              <div key={link.name} className="col-6 col-sm-4 col-lg-2">
                <div className="p-4 grayscale text-center">
                  <img src={link.logo ? getMediaUrl(link.logo) : "/assets/images/client/importio.svg"} alt={link.name} />
                </div>
              </div>
            ))}
            <div key={"ENAMAD_TRUST_LOGO"} className="col-6 col-sm-4 col-lg-2">
              <div className="p-4 grayscale text-center" dangerouslySetInnerHTML={{ __html: `<a referrerpolicy='origin' target='_blank' href='https://trustseal.enamad.ir/?id=730490&Code=GKtCGmkr9hUtZIy914X8HJe7tMOWIQuF'><img referrerpolicy='origin' src='https://trustseal.enamad.ir/logo.aspx?id=730490&Code=GKtCGmkr9hUtZIy914X8HJe7tMOWIQuF' alt='' style='cursor:pointer' code='GKtCGmkr9hUtZIy914X8HJe7tMOWIQuF'></a>` }} />
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
