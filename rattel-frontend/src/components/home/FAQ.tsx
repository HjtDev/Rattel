"use client";

import LoadingSkeleton from "@/src/components/skeleton/loadingSkeleton";
import { useFAQ } from "@/src/core/hooks/useFAQ";

export default function FAQ() {
    const { faqData, isLoading, error } = useFAQ();

    if (error) {
        return null; // Silently hide FAQ section on error
    }

    return (
        <section className="position-relative overflow-hidden pt-0 pt-sm-5">
            <div className="container">
                <div className="row position-relative z-index-9">
                    <div className="col-12 text-center mx-auto mt-2">
                        <h2 className="mb-0">
                            پرسش و پاسخ
                        </h2>
                    </div>
                </div>
                <div className="row">
                    <div className="col-lg-10 col-xl-8 mx-auto text-center position-relative">
                        <figure className="position-absolute top-0 start-0 translate-middle ms-8">
                            <svg style={{transform: 'scale(-1,1)'}}>
                                <path className="fill-success"
                                      d="M137.7,53.1c9.6,29.3,1.8,64.7-20.2,80.7s-58.1,12.6-83.5-5.8C8.6,109.5-6.1,76.1,2.4,48.7 C10.8,21.1,42.2-0.7,71.5,0S128.1,23.8,137.7,53.1z">
                                </path>
                            </svg>
                        </figure>
                        <figure className="position-absolute bottom-0 end-0 me-n9 rotate-193">
                            <svg style={{transform: 'scale(-1,1)'}} width="297.5px" height="295.9px">
                                <path stroke="#F99D2B" fill="none" strokeWidth="13"
                                      d="M286.2,165.5c-9.8,74.9-78.8,128.9-153.9,120.4c-76-8.6-131.4-78.2-122.8-154.2C18.2,55.8,87.8,0.3,163.7,9">
                                </path>
                            </svg>
                        </figure>
                        <LoadingSkeleton 
                            isLoading={isLoading}
                            Content={() => (
                                <div className="accordion accordion-icon accordion-shadow mt-4 text-start position-relative"
                                     id="accordionExample2">
                                    {faqData?.map((faq, index) => (
                                        <div key={index} className="accordion-item mb-3">
                                            <h6 className="accordion-header font-base" id={`heading-${index}`}>
                                                <button 
                                                    className={`accordion-button fw-bold rounded ${index !== 0 ? 'collapsed' : ''} pe-5`}
                                                    type="button"
                                                    data-bs-toggle="collapse" 
                                                    data-bs-target={`#collapse-${index}`}
                                                    aria-expanded={index === 0 ? "true" : "false"}
                                                    aria-controls={`collapse-${index}`}>
                                                    {faq.question}
                                                </button>
                                            </h6>
                                            <div 
                                                id={`collapse-${index}`}
                                                className={`accordion-collapse collapse ${index === 0 ? 'show' : ''}`}
                                                aria-labelledby={`heading-${index}`}
                                                data-bs-parent="#accordionExample2">
                                                <div className="accordion-body mt-3">
                                                    {faq.answer}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                            width={600}
                            height={200}
                            count={3}
                        />
                    </div>
                </div>
            </div>
        </section>
    );
}
