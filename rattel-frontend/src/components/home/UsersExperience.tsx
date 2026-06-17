"use client";

import { motion } from "framer-motion";
import { fadeInLeft, fadeInRight } from "@/src/core/motionVariants";
import LoadingSkeleton from "@/src/components/skeleton/loadingSkeleton";
import { getMediaUrl } from "@/src/core/utils";

interface User {
    name: string;
    profile_picture: string | null;
}

interface UserExperienceSection {
    title: string;
    description: string;
    top_users: boolean | {
      title: string;
      list: User[];
    };
    comment1_text: string;
    comment1_user: User;
    comment1_rate: number;
    comment2_text: string;
    comment2_user: User;
    comment2_rate: number;
}

interface UsersExperienceProps {
    data: UserExperienceSection | null;
    isLoading: boolean;
}

export default function UsersExperience({ data, isLoading }: UsersExperienceProps) {
  const topUsers = data?.top_users && typeof data.top_users === "object" ? data.top_users : null;
  
  // Helper function to render star rating
  const renderStars = (rate: number) => {
    const fullStars = Math.floor(rate);
    const hasHalfStar = rate % 1 !== 0;
    const stars = [];
    
    for (let i = 0; i < fullStars; i++) {
      stars.push(
        <li key={`full-${i}`} className="list-inline-item me-0 small">
          <i className="fas fa-star text-warning"></i>
        </li>
      );
    }
    
    if (hasHalfStar) {
      stars.push(
        <li key="half" className="list-inline-item me-0 small">
          <i className="fas fa-star-half-alt text-warning"></i>
        </li>
      );
    }
    
    return stars;
  };
  
  return (
      <section className="bg-light overflow-hidden">
        <div className="container">
          <div className="row g-4 g-lg-5 align-items-center">
            <motion.div
                className="col-xl-7 order-2 order-xl-1"
                initial="hidden"
                whileInView="show"
                viewport={{ once: true, amount: 0.1 }}
                variants={fadeInLeft}
            >
              <div className="row mt-0 mt-xl-5">
                <div className="col-md-7 position-relative mb-0 mt-0 mt-md-5">
                  <figure className="fill-danger opacity-2 position-absolute top-0 start-0 translate-middle mb-3">
                    <svg width="211px" height="211px">
                      <path
                          d="M210.030,105.011 C210.030,163.014 163.010,210.029 105.012,210.029 C47.013,210.029 -0.005,163.014 -0.005,105.011 C-0.005,47.015 47.013,-0.004 105.012,-0.004 C163.010,-0.004 210.030,47.015 210.030,105.011 Z">
                      </path>
                    </svg>
                  </figure>
                  <div className="bg-body shadow text-center p-4 rounded-3 position-relative mb-5 mb-md-0">
                      {
                        data?.comment1_user?.profile_picture && (
                              <div className="avatar avatar-xl mb-3">
                                <img className="avatar-img rounded-circle" src={getMediaUrl(data.comment1_user.profile_picture)} alt={data.comment1_user.name}/>
                              </div>
                          )
                      }
                    <blockquote>
                      <LoadingSkeleton isLoading={isLoading} Content={() => (
                          <p>
                        <span className="me-1 small">
                          <i className="fas fa-quote-left"></i>
                        </span>
                            {data?.comment1_text}
                            <span className="ms-1 small">
                          <i className="fas fa-quote-right"></i>
                        </span>
                          </p>
                      )} width={190} height={110} />
                    </blockquote>
                    <LoadingSkeleton isLoading={isLoading} Content={() => (
                        <ul className="list-inline mb-2">
                          {renderStars(data?.comment1_rate ?? 0)}
                        </ul>
                    )} width={192} height={20} />
                    <LoadingSkeleton isLoading={isLoading} Content={() => (
                        <h6 className="mb-0">
                          {data?.comment1_user.name}
                        </h6>
                    )} width={192} height={20} />
                  </div>
                </div>
                {
                    topUsers && (
                        <div className="col-md-5 mt-5 mt-md-0 d-none d-md-block">
                          <div className="bg-body shadow p-4 rounded-3 d-inline-block position-relative">
                            <div
                                className="icon-lg bg-warning rounded-circle position-absolute top-0 start-100 translate-middle">
                              <i className="bi bi-shield-fill-check text-dark">
                              </i>
                            </div>
                            <LoadingSkeleton isLoading={isLoading} Content={() => (
                                <h6 className="mb-3">
                                  {topUsers?.title ?? ""}
                                </h6>
                            )} width={130} height={20}/>
                            <LoadingSkeleton isLoading={isLoading} Content={() => (
                                (topUsers?.list ?? []).map((user: User, index: number) => (
                                        <div className="d-flex align-items-center mb-3" key={index}>
                                          <div className="ms-2">
                                            <h6 className="mb-0">
                                              {user.name}
                                            </h6>
                                          </div>
                                        </div>
                                    )
                                )
                            )} width={175} height={75}/>
                          </div>
                        </div>
                    )
                }

              </div>
              <div className="row mt-5 mt-xl-0">
                <div className="col-7 mt-0 mt-xl-5 text-end position-relative z-index-1 d-none d-md-block">
                  <figure
                      className="fill-danger position-absolute top-0 start-50 mt-n7 ms-6 ps-3 pt-2 z-index-n1 d-none d-lg-block">
                    <svg style={{transform: 'scale(-1,1)'}} enableBackground="new 0 0 160.7 159.8"
                         height="180px">
                      <path
                          d="m153.2 114.5c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2-0.1-1.2 0.9-2.2 2.1-2.2z">
                      </path>
                      <path
                          d="m116.4 114.5c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2s0.9-2.2 2.1-2.2z">
                      </path>
                      <path
                          d="m134.8 114.5c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2s0.9-2.2 2.1-2.2z">
                      </path>
                      <path
                          d="m135.1 96.9c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2s0.9-2.2 2.1-2.2z">
                      </path>
                      <path
                          d="m153.5 96.9c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2-0.1-1.2 0.9-2.2 2.1-2.2z">
                      </path>
                      <path
                          d="m98.3 96.9c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2s0.9-2.2 2.1-2.2z">
                      </path>
                      <ellipse cx="116.7" cy="99.1" rx="2.1" ry="2.2">
                      </ellipse>
                      <path
                          d="m153.2 149.8c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2-0.1-1.3 0.9-2.2 2.1-2.2z">
                      </path>
                      <path
                          d="m135.1 132.2c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2 0-1.3 0.9-2.2 2.1-2.2z">
                      </path>
                      <path
                          d="m153.5 132.2c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2-0.1-1.3 0.9-2.2 2.1-2.2z">
                      </path>
                      <path
                          d="m80.2 79.3c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2s1-2.2 2.1-2.2z">
                      </path>
                      <path
                          d="m117 79.3c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2s0.9-2.2 2.1-2.2z">
                      </path>
                      <path
                          d="m98.6 79.3c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2s0.9-2.2 2.1-2.2z">
                      </path>
                      <path
                          d="m135.4 79.3c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2s0.9-2.2 2.1-2.2z">
                      </path>
                      <path
                          d="m153.8 79.3c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2s0.9-2.2 2.1-2.2z">
                      </path>
                      <path
                          d="m80.6 61.7c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2-0.1-1.2 0.9-2.2 2.1-2.2z">
                      </path>
                      <ellipse cx="98.9" cy="63.9" rx="2.1" ry="2.2">
                      </ellipse>
                      <path
                          d="m117.3 61.7c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2s0.9-2.2 2.1-2.2z">
                      </path>
                      <ellipse cx="62.2" cy="63.9" rx="2.1" ry="2.2">
                      </ellipse>
                      <ellipse cx="154.1" cy="63.9" rx="2.1" ry="2.2">
                      </ellipse>
                      <path
                          d="m135.7 61.7c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2s0.9-2.2 2.1-2.2z">
                      </path>
                      <path
                          d="m154.4 44.1c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2s0.9-2.2 2.1-2.2z">
                      </path>
                      <path
                          d="m80.9 44.1c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2-0.1-1.2 0.9-2.2 2.1-2.2z">
                      </path>
                      <path
                          d="m44.1 44.1c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2-0.1-1.2 0.9-2.2 2.1-2.2z">
                      </path>
                      <path
                          d="m99.2 44.1c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2s1-2.2 2.1-2.2z">
                      </path>
                      <ellipse cx="117.6" cy="46.3" rx="2.1" ry="2.2">
                      </ellipse>
                      <path
                          d="m136 44.1c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2s0.9-2.2 2.1-2.2z">
                      </path>
                      <path
                          d="m62.5 44.1c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2-0.1-1.2 0.9-2.2 2.1-2.2z">
                      </path>
                      <path
                          d="m154.7 26.5c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2s0.9-2.2 2.1-2.2z">
                      </path>
                      <path
                          d="m62.8 26.5c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2-0.1-1.2 0.9-2.2 2.1-2.2z">
                      </path>
                      <ellipse cx="136.3" cy="28.6" rx="2.1" ry="2.2">
                      </ellipse>
                      <path
                          d="m99.6 26.5c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2-0.1-1.2 0.9-2.2 2.1-2.2z">
                      </path>
                      <path
                          d="m117.9 26.5c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2s1-2.2 2.1-2.2z">
                      </path>
                      <path
                          d="m81.2 26.5c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2-0.1-1.2 0.9-2.2 2.1-2.2z">
                      </path>
                      <path
                          d="m26 26.5c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2c-1.2 0-2.1-1-2.1-2.2s0.9-2.2 2.1-2.2z">
                      </path>
                      <ellipse cx="44.4" cy="28.6" rx="2.1" ry="2.2">
                      </ellipse>
                      <path
                          d="m136.6 13.2c-1.2 0-2.1-1-2.1-2.2s1-2.2 2.1-2.2c1.2 0 2.1 1 2.1 2.2 0.1 1.2-0.9 2.2-2.1 2.2z">
                      </path>
                      <path
                          d="m155 13.2c-1.2 0-2.1-1-2.1-2.2s1-2.2 2.1-2.2c1.2 0 2.1 1 2.1 2.2 0.1 1.2-0.9 2.2-2.1 2.2z">
                      </path>
                      <path
                          d="m26.3 13.2c-1.2 0-2.1-1-2.1-2.2s1-2.2 2.1-2.2c1.2 0 2.1 1 2.1 2.2s-0.9 2.2-2.1 2.2z">
                      </path>
                      <path
                          d="m81.5 13.2c-1.2 0-2.1-1-2.1-2.2s1-2.2 2.1-2.2c1.2 0 2.1 1 2.1 2.2s-0.9 2.2-2.1 2.2z">
                      </path>
                      <path
                          d="m63.1 13.2c-1.2 0-2.1-1-2.1-2.2s1-2.2 2.1-2.2c1.2 0 2.1 1 2.1 2.2s-0.9 2.2-2.1 2.2z">
                      </path>
                      <path
                          d="m44.7 13.2c-1.2 0-2.1-1-2.1-2.2s1-2.2 2.1-2.2c1.2 0 2.1 1 2.1 2.2s-0.9 2.2-2.1 2.2z">
                      </path>
                      <path
                          d="m118.2 13.2c-1.2 0-2.1-1-2.1-2.2s1-2.2 2.1-2.2c1.2 0 2.1 1 2.1 2.2 0.1 1.2-0.9 2.2-2.1 2.2z">
                      </path>
                      <path
                          d="m7.9 13.2c-1.2 0-2.1-1-2.1-2.2s1-2.2 2.1-2.2c1.2 0 2.1 1 2.1 2.2 0.1 1.2-0.9 2.2-2.1 2.2z">
                      </path>
                      <path
                          d="m99.9 13.2c-1.2 0-2.1-1-2.1-2.2s1-2.2 2.1-2.2c1.2 0 2.1 1 2.1 2.2s-1 2.2-2.1 2.2z">
                      </path>
                    </svg>
                  </figure>
                </div>
                <div className="col-md-5 mt-n6 mb-0 mb-md-5">
                  <div className="bg-body shadow text-center p-4 rounded-3 mt-7">
                    {
                      data?.comment2_user?.profile_picture && (
                            <div className="avatar avatar-xl mb-3">
                              <img className="avatar-img rounded-circle" src={getMediaUrl(data.comment2_user.profile_picture)}
                                   alt="avatar"/>
                            </div>
                        )
                    }
                    <blockquote>

                      <LoadingSkeleton isLoading={isLoading} Content={() => (
                          <p>
                        <span className="me-1 small">
                          <i className="fas fa-quote-left"></i>
                        </span>
                            {data?.comment2_text}
                            <span className="ms-1 small">
                          <i className="fas fa-quote-right"></i>
                        </span>
                          </p>
                      )} width={190} height={110} />
                    </blockquote>
                    <LoadingSkeleton isLoading={isLoading} Content={() => (
                        <ul className="list-inline mb-2">
                          {renderStars(data?.comment2_rate ?? 0)}
                        </ul>
                    )} width={192} height={20} />
                    <LoadingSkeleton isLoading={isLoading} Content={() => (
                        <h6 className="mb-0">
                          {data?.comment2_user.name}
                        </h6>
                    )} width={192} height={20} />
                  </div>
                </div>
              </div>
            </motion.div>
            <motion.div
                className="col-xl-5 order-1 text-center text-xl-start"
                initial="hidden"
                whileInView="show"
                viewport={{ once: true, amount: 0.2 }}
                variants={fadeInRight}
            >
              <LoadingSkeleton isLoading={isLoading} Content={() => (
                  <h2 className="fs-2">
                    {data?.title}
                  </h2>
              )} width={435} height={45} />
              <LoadingSkeleton isLoading={isLoading} Content={() => (
                  <p>
                    {data?.description}
                  </p>
              )} width={435} height={90} />
            </motion.div>
          </div>
        </div>
      </section>
  );
}
