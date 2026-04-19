export default function PopularCourses() {
  return (
      <section>
        <div className="container">
          <div className="row mb-4">
            <div className="col-lg-8 mx-auto text-center">
              <h2 className="fs-3">
                محبوب ترین دوره ها
              </h2>
              <p className="mb-0">
                هر موضوعی را در هر زمان مطالعه کنید. هزاران دوره آموزشی را با کمترین قیمت جستجو کنید!
              </p>
            </div>
          </div>
          <ul className="nav nav-pills nav-pills-bg-soft justify-content-sm-center mb-4 px-3" id="course-pills-tab"
              role="tablist">
            <li className="nav-item me-2 me-sm-5" role="presentation">
              <button className="nav-link mb-2 mb-md-0 active" id="course-pills-tab-1" data-bs-toggle="pill"
                      data-bs-target="#course-pills-tabs-1" type="button" role="tab"
                      aria-controls="course-pills-tabs-1" aria-selected="true">
                طراحی وب
              </button>
            </li>
            <li className="nav-item me-2 me-sm-5" role="presentation">
              <button className="nav-link mb-2 mb-md-0" id="course-pills-tab-2" data-bs-toggle="pill"
                      data-bs-target="#course-pills-tabs-2" type="button" role="tab"
                      aria-controls="course-pills-tabs-2" aria-selected="false" tabIndex={-1}>
                برنامه نویسی
              </button>
            </li>
            <li className="nav-item me-2 me-sm-5" role="presentation">
              <button className="nav-link mb-2 mb-md-0" id="course-pills-tab-3" data-bs-toggle="pill"
                      data-bs-target="#course-pills-tabs-3" type="button" role="tab"
                      aria-controls="course-pills-tabs-3" aria-selected="false" tabIndex={-1}>
                طراحی گرافیکی
              </button>
            </li>
            <li className="nav-item me-2 me-sm-5" role="presentation">
              <button className="nav-link mb-2 mb-md-0" id="course-pills-tab-4" data-bs-toggle="pill"
                      data-bs-target="#course-pills-tabs-4" type="button" role="tab"
                      aria-controls="course-pills-tabs-4" aria-selected="false" tabIndex={-1}>
                دیجیتال مارکتنیگ
              </button>
            </li>
            <li className="nav-item me-2 me-sm-5" role="presentation">
              <button className="nav-link mb-2 mb-md-0" id="course-pills-tab-5" data-bs-toggle="pill"
                      data-bs-target="#course-pills-tabs-5" type="button" role="tab"
                      aria-controls="course-pills-tabs-5" aria-selected="false" tabIndex={-1}>
                بازار مالی
              </button>
            </li>
          </ul>
          <div className="tab-content" id="course-pills-tabContent">
            <div className="tab-pane fade show active" id="course-pills-tabs-1" role="tabpanel"
                 aria-labelledby="course-pills-tab-1">
              <div className="row g-4">
                <div className="col-sm-6 col-lg-4 col-xl-3">
                  <div className="card shadow h-100">
                    <img src="assets/images/courses/4by3/08.jpg" className="card-img-top" alt="course image"/>
                    <div className="card-body pb-0">
                      <div className="d-flex justify-content-between mb-2">
                        <a href="#" className="badge bg-purple bg-opacity-10 text-purple">
                          همه سطح
                        </a>
                        <a href="#" className="h6 mb-0">
                          <i className="far fa-heart">
                          </i>
                        </a>
                      </div>
                      <h5 className="card-title fw-normal">
                        <a href="#">
                          آموزش Sketch
                        </a>
                      </h5>
                      <p className="mb-2 text-truncate-2">
                        با تولید سادگی نامفهوم از صنعت چاپ و با استفاده از طراحان گرافیک
                      </p>
                      <ul className="list-inline mb-0">
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="far fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item ms-2 h6 fw-light mb-0">
                          4.0/5.0
                        </li>
                      </ul>
                    </div>
                    <div className="card-footer pt-0 pb-3">
                      <hr/>
                      <div className="d-flex justify-content-between">
                  <span className="h6 fw-light mb-0">
                    <i className="far fa-clock text-danger me-2">
                    </i>
                    12دقیقه
                  </span>
                        <span className="h6 fw-light mb-0">
                    <i className="fas fa-table text-orange me-2">
                    </i>
                    15 ویدیو
                  </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="col-sm-6 col-lg-4 col-xl-3">
                  <div className="card shadow h-100">
                    <img src="assets/images/courses/4by3/02.jpg" className="card-img-top" alt="course image"/>
                    <div className="card-body pb-0">
                      <div className="d-flex justify-content-between mb-2">
                        <a href="#" className="badge bg-success bg-opacity-10 text-success">
                          مقدماتی
                        </a>
                        <a href="#" className="text-danger">
                          <i className="fas fa-heart">
                          </i>
                        </a>
                      </div>
                      <h5 className="card-title fw-normal">
                        <a href="#">
                          آموزش Photoshop
                        </a>
                      </h5>
                      <p className="mb-2 text-truncate-2">
                        با تولید سادگی نامفهوم از صنعت چاپ و با استفاده از طراحان گرافیک
                      </p>
                      <ul className="list-inline mb-0">
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star-half-alt text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item ms-2 h6 fw-light mb-0">
                          4.5/5.0
                        </li>
                      </ul>
                    </div>
                    <div className="card-footer pt-0 pb-3">
                      <hr/>
                      <div className="d-flex justify-content-between ">
                  <span className="h6 fw-light mb-0">
                    <i className="far fa-clock text-danger me-2">
                    </i>
                    9ساعت
                  </span>
                        <span className="h6 fw-light mb-0">
                    <i className="fas fa-table text-orange me-2">
                    </i>
                    65 ویدیو
                  </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="col-sm-6 col-lg-4 col-xl-3">
                  <div className="card shadow h-100">
                    <img src="assets/images/courses/4by3/03.jpg" className="card-img-top" alt="course image"/>
                    <div className="card-body pb-0">
                      <div className="d-flex justify-content-between mb-2">
                        <a href="#" className="badge bg-success bg-opacity-10 text-success">
                          مقدماتی
                        </a>
                        <a href="#" className="h6 fw-light mb-0">
                          <i className="far fa-heart">
                          </i>
                        </a>
                      </div>
                      <h5 className="card-title fw-normal">
                        <a href="#">
                          آموزش Figma
                        </a>
                      </h5>
                      <p className="mb-2 text-truncate-2">
                        با تولید سادگی نامفهوم از صنعت چاپ و با استفاده از طراحان گرافیک
                      </p>
                      <ul className="list-inline mb-0">
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star-half-alt text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item ms-2 h6 fw-light mb-0">
                          4.5/5.0
                        </li>
                      </ul>
                    </div>
                    <div className="card-footer pt-0 pb-3">
                      <hr/>
                      <div className="d-flex justify-content-between">
                  <span className="h6 fw-light mb-0">
                    <i className="far fa-clock text-danger me-2">
                    </i>
                    5دقیقه
                  </span>
                        <span className="h6 fw-light mb-0">
                    <i className="fas fa-table text-orange me-2">
                    </i>
                    32 ویدیو
                  </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="col-sm-6 col-lg-4 col-xl-3">
                  <div className="card shadow h-100">
                    <img src="assets/images/courses/4by3/07.jpg" className="card-img-top" alt="course image"/>
                    <div className="card-body pb-0">
                      <div className="d-flex justify-content-between mb-2">
                        <a href="#" className="badge bg-success bg-opacity-10 text-success">
                          مقدماتی
                        </a>
                        <a href="#" className="text-danger">
                          <i className="fas fa-heart">
                          </i>
                        </a>
                      </div>
                      <h5 className="card-title fw-normal">
                        <a href="#">
                          آموزش React-Native
                        </a>
                      </h5>
                      <p className="mb-2 text-truncate-2">
                        با تولید سادگی نامفهوم از صنعت چاپ و با استفاده از طراحان گرافیک
                      </p>
                      <ul className="list-inline mb-0">
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="far fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item ms-2 h6 fw-light mb-0">
                          4.0/5.0
                        </li>
                      </ul>
                    </div>
                    <div className="card-footer pt-0 pb-3">
                      <hr/>
                      <div className="d-flex justify-content-between">
                  <span className="h6 fw-light mb-0">
                    <i className="far fa-clock text-danger me-2">
                    </i>
                    18دقیقه
                  </span>
                        <span className="h6 fw-light mb-0">
                    <i className="fas fa-table text-orange me-2">
                    </i>
                    99 ویدیو
                  </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="col-sm-6 col-lg-4 col-xl-3">
                  <div className="card shadow h-100">
                    <img src="assets/images/courses/4by3/11.jpg" className="card-img-top" alt="course image"/>
                    <div className="card-body pb-0">
                      <div className="d-flex justify-content-between mb-2">
                        <a href="#" className="badge bg-purple bg-opacity-10 text-purple">
                          همه سطح
                        </a>
                        <a href="#" className="text-danger">
                          <i className="fas fa-heart">
                          </i>
                        </a>
                      </div>
                      <h5 className="card-title fw-normal">
                        <a href="#">
                          آموزش HTML
                        </a>
                      </h5>
                      <p className="mb-2 text-truncate-2">
                        با تولید سادگی نامفهوم از صنعت چاپ و با استفاده از طراحان گرافیک
                      </p>
                      <ul className="list-inline mb-0">
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="far fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item ms-2 h6 fw-light mb-0">
                          4.0/5.0
                        </li>
                      </ul>
                    </div>
                    <div className="card-footer pt-0 pb-3">
                      <hr/>
                      <div className="d-flex justify-content-between">
                  <span className="h6 fw-light mb-0">
                    <i className="far fa-clock text-danger me-2">
                    </i>
                    15دقیقه
                  </span>
                        <span className="h6 fw-light mb-0">
                    <i className="fas fa-table text-orange me-2">
                    </i>
                    68 ویدیو
                  </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="col-sm-6 col-lg-4 col-xl-3">
                  <div className="card shadow h-100">
                    <img src="assets/images/courses/4by3/12.jpg" className="card-img-top" alt="course image"/>
                    <div className="card-body pb-0">
                      <div className="d-flex justify-content-between mb-2">
                        <a href="#" className="badge bg-success bg-opacity-10 text-success">
                          مقدماتی
                        </a>
                        <a href="#" className="h6 fw-light mb-0">
                          <i className="far fa-heart">
                          </i>
                        </a>
                      </div>
                      <h5 className="card-title fw-normal">
                        <a href="#">
                          آموزش CSS
                        </a>
                      </h5>
                      <p className="text-truncate-2 mb-2">
                        با تولید سادگی نامفهوم از صنعت چاپ و با استفاده از طراحان گرافیک
                      </p>
                      <ul className="list-inline mb-0">
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star-half-alt text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item ms-2 h6 fw-light mb-0">
                          4.5/5.0
                        </li>
                      </ul>
                    </div>
                    <div className="card-footer pt-0 pb-3">
                      <hr/>
                      <div className="d-flex justify-content-between mt-2">
                  <span className="h6 fw-light mb-0">
                    <i className="far fa-clock text-danger me-2">
                    </i>
                    36دقیقه
                  </span>
                        <span className="h6 fw-light mb-0">
                    <i className="fas fa-table text-orange me-2">
                    </i>
                    72 ویدیو
                  </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="col-sm-6 col-lg-4 col-xl-3">
                  <div className="card shadow h-100">
                    <img src="assets/images/courses/4by3/04.jpg" className="card-img-top" alt="course image"/>
                    <div className="card-body pb-0">
                      <div className="d-flex justify-content-between mb-2">
                        <a href="#" className="badge bg-purple bg-opacity-10 text-purple">
                          همه سطح
                        </a>
                        <a href="#" className="text-danger">
                          <i className="fas fa-heart">
                          </i>
                        </a>
                      </div>
                      <h5 className="card-title fw-normal">
                        <a href="#">
                          آموزش Invision
                        </a>
                      </h5>
                      <p className="mb-2">
                        با تولید سادگی نامفهوم از صنعت چاپ و با استفاده از طراحان گرافیک
                      </p>
                      <ul className="list-inline mb-0">
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star-half-alt text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="far fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item ms-2 h6 fw-light mb-0">
                          3.5/5.0
                        </li>
                      </ul>
                    </div>
                    <div className="card-footer pt-0 pb-3">
                      <hr/>
                      <div className="d-flex justify-content-between mt-2">
                  <span className="h6 fw-light mb-0">
                    <i className="far fa-clock text-danger me-2">
                    </i>
                    6ساعت
                  </span>
                        <span className="h6 fw-light mb-0">
                    <i className="fas fa-table text-orange me-2">
                    </i>
                    82 ویدیو
                  </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="col-sm-6 col-lg-4 col-xl-3">
                  <div className="card shadow h-100">
                    <img src="assets/images/courses/4by3/09.jpg" className="card-img-top" alt="course image"/>
                    <div className="card-body pb-0">
                      <div className="d-flex justify-content-between mb-2">
                        <a href="#" className="badge bg-purple bg-opacity-10 text-purple">
                          همه سطح
                        </a>
                        <a href="#" className="h6 fw-light mb-0">
                          <i className="far fa-heart">
                          </i>
                        </a>
                      </div>
                      <h5 className="card-title fw-normal">
                        <a href="#">
                          آموزش JavaScript
                        </a>
                      </h5>
                      <p className="text-truncate-2 mb-2">
                        با تولید سادگی نامفهوم از صنعت چاپ و با استفاده از طراحان گرافیک
                      </p>
                      <ul className="list-inline mb-0">
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item ms-2 h6 fw-light mb-0">
                          5.0/5.0
                        </li>
                      </ul>
                    </div>
                    <div className="card-footer pt-0 pb-3">
                      <hr/>
                      <div className="d-flex justify-content-between">
                  <span className="h6 fw-light mb-0">
                    <i className="far fa-clock text-danger me-2">
                    </i>
                    35دقیقه
                  </span>
                        <span className="h6 fw-light mb-0">
                    <i className="fas fa-table text-orange me-2">
                    </i>
                    89 دوره
                  </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="tab-pane fade" id="course-pills-tabs-2" role="tabpanel"
                 aria-labelledby="course-pills-tab-2">
              <div className="row g-4">
                <div className="col-sm-6 col-lg-4 col-xl-3">
                  <div className="card shadow h-100">
                    <img src="assets/images/courses/4by3/05.jpg" className="card-img-top" alt="course image"/>
                    <div className="card-body pb-0">
                      <div className="d-flex justify-content-between mb-2">
                        <a href="#" className="badge bg-success bg-opacity-10 text-success">
                          مقدماتی
                        </a>
                        <a href="#" className="h6 fw-light mb-0">
                          <i className="far fa-heart">
                          </i>
                        </a>
                      </div>
                      <h5 className="card-title fw-normal">
                        <a href="#">
                          آموزش Python
                        </a>
                      </h5>
                      <p className="text-truncate-2 mb-2">
                        با تولید سادگی نامفهوم از صنعت چاپ و با استفاده از طراحان گرافیک
                      </p>
                      <ul className="list-inline mb-0">
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star-half-alt text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item ms-2 h6 fw-light mb-0">
                          4.5/5.0
                        </li>
                      </ul>
                    </div>
                    <div className="card-footer pt-0 pb-3">
                      <hr/>
                      <div className="d-flex justify-content-between mt-2">
                  <span className="h6 fw-light mb-0">
                    <i className="far fa-clock text-danger me-2">
                    </i>
                    10ساعت
                  </span>
                        <span className="h6 fw-light mb-0">
                    <i className="fas fa-table text-orange me-2">
                    </i>
                    26 دوره
                  </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="col-sm-6 col-lg-4 col-xl-3">
                  <div className="card shadow h-100">
                    <img src="assets/images/courses/4by3/06.jpg" className="card-img-top" alt="course image"/>
                    <div className="card-body pb-0">
                      <div className="d-flex justify-content-between mb-2">
                        <a href="#" className="badge bg-info bg-opacity-10 text-info">
                          پیشرفته
                        </a>
                        <a href="#" className="h6 fw-light mb-0">
                          <i className="far fa-heart">
                          </i>
                        </a>
                      </div>
                      <h5 className="card-title fw-normal">
                        <a href="#">
                          آموزش Angular
                        </a>
                      </h5>
                      <p className="text-truncate-2 mb-2">
                        با تولید سادگی نامفهوم از صنعت چاپ و با استفاده از طراحان گرافیک
                      </p>
                      <ul className="list-inline mb-0">
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star-half-alt text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item ms-2 h6 fw-light mb-0">
                          4.5/5.0
                        </li>
                      </ul>
                    </div>
                    <div className="card-footer pt-0 pb-3">
                      <hr/>
                      <div className="d-flex justify-content-between mt-2">
                  <span className="h6 fw-light mb-0">
                    <i className="far fa-clock text-danger me-2">
                    </i>
                    9ساعت
                  </span>
                        <span className="h6 fw-light mb-0">
                    <i className="fas fa-table text-orange me-2">
                    </i>
                    42 ویدیو
                  </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="col-sm-6 col-lg-4 col-xl-3">
                  <div className="card shadow">
                    <img src="assets/images/courses/4by3/07.jpg" className="card-img-top" alt="course image"/>
                    <div className="card-body pb-0">
                      <div className="d-flex justify-content-between mb-2">
                        <a href="#" className="badge bg-success bg-opacity-10 text-success">
                          مقدماتی
                        </a>
                        <a href="#" className="text-danger">
                          <i className="fas fa-heart">
                          </i>
                        </a>
                      </div>
                      <h5 className="card-title fw-normal">
                        <a href="#">
                          آموزش React-Native
                        </a>
                      </h5>
                      <p className="text-truncate-2 mb-2">
                        با تولید سادگی نامفهوم از صنعت چاپ و با استفاده از طراحان گرافیک
                      </p>
                      <ul className="list-inline mb-0">
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="far fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item ms-2 h6 fw-light mb-0">
                          4.0/5.0
                        </li>
                      </ul>
                    </div>
                    <div className="card-footer pt-0 pb-3">
                      <hr/>
                      <div className="d-flex justify-content-between">
                  <span className="h6 fw-light mb-0">
                    <i className="far fa-clock text-danger me-2">
                    </i>
                    18دقیقه
                  </span>
                        <span className="h6 fw-light mb-0">
                    <i className="fas fa-table text-orange me-2">
                    </i>
                    99 دوره
                  </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="col-sm-6 col-lg-4 col-xl-3">
                  <div className="card shadow h-100">
                    <img src="assets/images/courses/4by3/09.jpg" className="card-img-top" alt="course image"/>
                    <div className="card-body pb-0">
                      <div className="d-flex justify-content-between mb-2">
                        <a href="#" className="badge bg-purple bg-opacity-10 text-purple">
                          همه سطح
                        </a>
                        <a href="#" className="h6 fw-light mb-0">
                          <i className="far fa-heart">
                          </i>
                        </a>
                      </div>
                      <h5 className="card-title fw-normal">
                        <a href="#">
                          آموزش JavaScript
                        </a>
                      </h5>
                      <p className="text-truncate-2 mb-2">
                        با تولید سادگی نامفهوم از صنعت چاپ و با استفاده از طراحان گرافیک
                      </p>
                      <ul className="list-inline mb-0">
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item ms-2 h6 fw-light mb-0">
                          5.0/5.0
                        </li>
                      </ul>
                    </div>
                    <div className="card-footer pt-0 pb-3">
                      <hr/>
                      <div className="d-flex justify-content-between">
                  <span className="h6 fw-light mb-0">
                    <i className="far fa-clock text-danger me-2">
                    </i>
                    35دقیقه
                  </span>
                        <span className="h6 fw-light mb-0">
                    <i className="fas fa-table text-orange me-2">
                    </i>
                    89 ویدیو
                  </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="col-sm-6 col-lg-4 col-xl-3">
                  <div className="card shadow h-100">
                    <img src="assets/images/courses/4by3/10.jpg" className="card-img-top" alt="course image"/>
                    <div className="card-body pb-0">
                      <div className="d-flex justify-content-between mb-2">
                        <a href="#" className="badge bg-info bg-opacity-10 text-info">
                          پیشرفته
                        </a>
                        <a href="#" className="text-danger">
                          <i className="fas fa-heart">
                          </i>
                        </a>
                      </div>
                      <h5 className="card-title fw-normal">
                        <a href="#">
                          آموزش Bootstrap
                        </a>
                      </h5>
                      <p className="text-truncate-2 mb-2">
                        با تولید سادگی نامفهوم از صنعت چاپ و با استفاده از طراحان گرافیک
                      </p>
                      <ul className="list-inline mb-0">
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star-half-alt text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item ms-2 h6 fw-light mb-0">
                          4.5/5.0
                        </li>
                      </ul>
                    </div>
                    <div className="card-footer pt-0 pb-3">
                      <hr/>
                      <div className="d-flex justify-content-between mt-2">
                  <span className="h6 fw-light mb-0">
                    <i className="far fa-clock text-danger me-2">
                    </i>
                    25دقیقه
                  </span>
                        <span className="h6 fw-light mb-0">
                    <i className="fas fa-table text-orange me-2">
                    </i>
                    38 دوره
                  </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="col-sm-6 col-lg-4 col-xl-3">
                  <div className="card shadow h-100">
                    <img src="assets/images/courses/4by3/13.jpg" className="card-img-top" alt="course image"/>
                    <div className="card-body pb-0">
                      <div className="d-flex justify-content-between mb-2">
                        <a href="#" className="badge bg-success bg-opacity-10 text-success">
                          مقدماتی
                        </a>
                        <a href="#" className="h6 fw-light mb-0">
                          <i className="far fa-heart">
                          </i>
                        </a>
                      </div>
                      <h5 className="card-title fw-normal">
                        <a href="#">
                          آموزش PHP
                        </a>
                      </h5>
                      <p className="text-truncate-2 mb-2">
                        با تولید سادگی نامفهوم از صنعت چاپ و با استفاده از طراحان گرافیک
                      </p>
                      <ul className="list-inline mb-0">
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="far fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item ms-2 h6 fw-light mb-0">
                          4.0/5.0
                        </li>
                      </ul>
                    </div>
                    <div className="card-footer pt-0 pb-3">
                      <hr/>
                      <div className="d-flex justify-content-between">
                  <span className="h6 fw-light mb-0">
                    <i className="far fa-clock text-danger me-2">
                    </i>
                    21ساعت
                  </span>
                        <span className="h6 fw-light mb-0">
                    <i className="fas fa-table text-orange me-2">
                    </i>
                    30 ویدیو
                  </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="tab-pane fade" id="course-pills-tabs-3" role="tabpanel"
                 aria-labelledby="course-pills-tab-3">
              <div className="row g-4">
                <div className="col-sm-6 col-lg-4 col-xl-3">
                  <div className="card shadow h-100">
                    <img src="assets/images/courses/4by3/08.jpg" className="card-img-top" alt="course image"/>
                    <div className="card-body pb-0">
                      <div className="d-flex justify-content-between mb-2">
                        <a href="#" className="badge bg-purple bg-opacity-10 text-purple">
                          همه سطح
                        </a>
                        <a href="#" className="h6 fw-light mb-0">
                          <i className="far fa-heart">
                          </i>
                        </a>
                      </div>
                      <h5 className="card-title fw-normal">
                        <a href="#">
                          آموزش Sketch
                        </a>
                      </h5>
                      <p className="text-truncate-2 mb-2">
                        با تولید سادگی نامفهوم از صنعت چاپ و با استفاده از طراحان گرافیک
                      </p>
                      <ul className="list-inline mb-0">
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="far fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item ms-2 h6 fw-light mb-0">
                          4.0/5.0
                        </li>
                      </ul>
                    </div>
                    <div className="card-footer pt-0 pb-3">
                      <hr/>
                      <div className="d-flex justify-content-between">
                  <span className="h6 fw-light mb-0">
                    <i className="far fa-clock text-danger me-2">
                    </i>
                    12دقیقه
                  </span>
                        <span className="h6 fw-light mb-0">
                    <i className="fas fa-table text-orange me-2">
                    </i>
                    15 ویدیو
                  </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="col-sm-6 col-lg-4 col-xl-3">
                  <div className="card shadow h-100">
                    <img src="assets/images/courses/4by3/04.jpg" className="card-img-top" alt="course image"/>
                    <div className="card-body pb-0">
                      <div className="d-flex justify-content-between mb-2">
                        <a href="#" className="badge bg-purple bg-opacity-10 text-purple">
                          همه سطح
                        </a>
                        <a href="#" className="text-danger">
                          <i className="fas fa-heart">
                          </i>
                        </a>
                      </div>
                      <h5 className="card-title fw-normal">
                        <a href="#">
                          آموزش Invision
                        </a>
                      </h5>
                      <p className="mb-2">
                        با تولید سادگی نامفهوم از صنعت چاپ و با استفاده از طراحان گرافیک
                      </p>
                      <ul className="list-inline mb-0">
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star-half-alt text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="far fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item ms-2 h6 fw-light mb-0">
                          3.5/5.0
                        </li>
                      </ul>
                    </div>
                    <div className="card-footer pt-0 pb-3">
                      <hr/>
                      <div className="d-flex justify-content-between mt-2">
                  <span className="h6 fw-light mb-0">
                    <i className="far fa-clock text-danger me-2">
                    </i>
                    6ساعت
                  </span>
                        <span className="h6 fw-light mb-0">
                    <i className="fas fa-table text-orange me-2">
                    </i>
                    82 ویدیو
                  </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="col-sm-6 col-lg-4 col-xl-3">
                  <div className="card shadow h-100">
                    <img src="assets/images/courses/4by3/02.jpg" className="card-img-top" alt="course image"/>
                    <div className="card-body pb-0">
                      <div className="d-flex justify-content-between mb-2">
                        <a href="#" className="badge bg-success bg-opacity-10 text-success">
                          مقدماتی
                        </a>
                        <a href="#" className="text-danger">
                          <i className="fas fa-heart">
                          </i>
                        </a>
                      </div>
                      <h5 className="card-title fw-normal">
                        <a href="#">
                          آموزش Photoshop
                        </a>
                      </h5>
                      <p className="text-truncate-2 mb-2">
                        با تولید سادگی نامفهوم از صنعت چاپ و با استفاده از طراحان گرافیک
                      </p>
                      <ul className="list-inline mb-0">
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star-half-alt text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item ms-2 h6 fw-light mb-0">
                          4.5/5.0
                        </li>
                      </ul>
                    </div>
                    <div className="card-footer pt-0 pb-3">
                      <hr/>
                      <div className="d-flex justify-content-between">
                  <span className="h6 fw-light mb-0">
                    <i className="far fa-clock text-danger me-2">
                    </i>
                    9ساعت
                  </span>
                        <span className="h6 fw-light mb-0">
                    <i className="fas fa-table text-orange me-2">
                    </i>
                    65 ویدیو
                  </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="col-sm-6 col-lg-4 col-xl-3">
                  <div className="card shadow h-100">
                    <img src="assets/images/courses/4by3/03.jpg" className="card-img-top" alt="course image"/>
                    <div className="card-body pb-0">
                      <div className="d-flex justify-content-between mb-2">
                        <a href="#" className="badge bg-success bg-opacity-10 text-success">
                          مقدماتی
                        </a>
                        <a href="#" className="h6 fw-light mb-0">
                          <i className="far fa-heart">
                          </i>
                        </a>
                      </div>
                      <h5 className="card-title fw-normal">
                        <a href="#">
                          آموزش Figma
                        </a>
                      </h5>
                      <p className="text-truncate-2 mb-2">
                        با تولید سادگی نامفهوم از صنعت چاپ و با استفاده از طراحان گرافیک
                      </p>
                      <ul className="list-inline mb-0">
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star-half-alt text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item ms-2 h6 fw-light mb-0">
                          4.5/5.0
                        </li>
                      </ul>
                    </div>
                    <div className="card-footer pt-0 pb-3">
                      <hr/>
                      <div className="d-flex justify-content-between">
                  <span className="h6 fw-light mb-0">
                    <i className="far fa-clock text-danger me-2">
                    </i>
                    5دقیقه
                  </span>
                        <span className="h6 fw-light mb-0">
                    <i className="fas fa-table text-orange me-2">
                    </i>
                    32 ویدیو
                  </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="tab-pane fade" id="course-pills-tabs-4" role="tabpanel"
                 aria-labelledby="course-pills-tab-4">
              <div className="row g-4">
                <div className="col-sm-6 col-lg-4 col-xl-3">
                  <div className="card shadow h-100">
                    <img src="assets/images/courses/4by3/01.jpg" className="card-img-top" alt="course image"/>
                    <div className="card-body pb-0">
                      <div className="d-flex justify-content-between mb-2">
                        <a href="#" className="badge bg-success bg-opacity-10 text-success">
                          مقدماتی
                        </a>
                        <a href="#" className="text-danger">
                          <i className="fas fa-heart">
                          </i>
                        </a>
                      </div>
                      <h5 className="card-title fw-normal">
                        <a href="#">
                          آموزش Laravel
                        </a>
                      </h5>
                      <p className="text-truncate-2 mb-2">
                        با تولید سادگی نامفهوم از صنعت چاپ و با استفاده از طراحان گرافیک
                      </p>
                      <ul className="list-inline mb-0">
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star-half-alt text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item ms-2 h6 fw-light mb-0">
                          4.5/5.0
                        </li>
                      </ul>
                    </div>
                    <div className="card-footer pt-0 pb-3">
                      <hr/>
                      <div className="d-flex justify-content-between">
                  <span className="h6 fw-light mb-0">
                    <i className="far fa-clock text-danger me-2">
                    </i>
                    6ساعت
                  </span>
                        <span className="h6 fw-light mb-0">
                    <i className="fas fa-table text-orange me-2">
                    </i>
                    82 ویدیو
                  </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="col-sm-6 col-lg-4 col-xl-3">
                  <div className="card shadow h-100">
                    <img src="assets/images/courses/4by3/08.jpg" className="card-img-top" alt="course image"/>
                    <div className="card-body pb-0">
                      <div className="d-flex justify-content-between mb-2">
                        <a href="#" className="badge bg-purple bg-opacity-10 text-purple">
                          همه سطح
                        </a>
                        <a href="#" className="h6 fw-light mb-0">
                          <i className="far fa-heart">
                          </i>
                        </a>
                      </div>
                      <h5 className="card-title fw-normal">
                        <a href="#">
                          آموزش Sketch
                        </a>
                      </h5>
                      <p className="text-truncate-2 mb-2">
                        با تولید سادگی نامفهوم از صنعت چاپ و با استفاده از طراحان گرافیک
                      </p>
                      <ul className="list-inline mb-0">
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="far fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item ms-2 h6 fw-light mb-0">
                          4.0/5.0
                        </li>
                      </ul>
                    </div>
                    <div className="card-footer pt-0 pb-3">
                      <hr/>
                      <div className="d-flex justify-content-between">
                  <span className="h6 fw-light mb-0">
                    <i className="far fa-clock text-danger me-2">
                    </i>
                    12دقیقه
                  </span>
                        <span className="h6 fw-light mb-0">
                    <i className="fas fa-table text-orange me-2">
                    </i>
                    15 ویدیو
                  </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="tab-pane fade" id="course-pills-tabs-5" role="tabpanel"
                 aria-labelledby="course-pills-tab-5">
              <div className="row g-4">
                <div className="col-sm-6 col-lg-4 col-xl-3">
                  <div className="card shadow h-100">
                    <img src="assets/images/courses/4by3/04.jpg" className="card-img-top" alt="course image"/>
                    <div className="card-body pb-0">
                      <div className="d-flex justify-content-between mb-2">
                        <a href="#" className="badge bg-purple bg-opacity-10 text-purple">
                          همه سطح
                        </a>
                        <a href="#" className="text-danger">
                          <i className="fas fa-heart">
                          </i>
                        </a>
                      </div>
                      <h5 className="card-title fw-normal">
                        <a href="#">
                          آموزش Invision
                        </a>
                      </h5>
                      <p className="text-truncate-2 mb-2">
                        با تولید سادگی نامفهوم از صنعت چاپ و با استفاده از طراحان گرافیک
                      </p>
                      <ul className="list-inline mb-0">
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star-half-alt text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="far fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item ms-2 h6 fw-light mb-0">
                          3.5/5.0
                        </li>
                      </ul>
                    </div>
                    <div className="card-footer pt-0 pb-3">
                      <hr/>
                      <div className="d-flex justify-content-between">
                  <span className="h6 fw-light mb-0">
                    <i className="far fa-clock text-danger me-2">
                    </i>
                    6ساعت
                  </span>
                        <span className="h6 fw-light mb-0">
                    <i className="fas fa-table text-orange me-2">
                    </i>
                    82 ویدیو
                  </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="col-sm-6 col-lg-4 col-xl-3">
                  <div className="card shadow h-100">
                    <img src="assets/images/courses/4by3/09.jpg" className="card-img-top" alt="course image"/>
                    <div className="card-body pb-0">
                      <div className="d-flex justify-content-between mb-2">
                        <a href="#" className="badge bg-purple bg-opacity-10 text-purple">
                          همه سطح
                        </a>
                        <a href="#" className="h6 fw-light mb-0">
                          <i className="far fa-heart">
                          </i>
                        </a>
                      </div>
                      <h5 className="card-title fw-normal">
                        <a href="#">
                          آموزش JavaScript
                        </a>
                      </h5>
                      <p className="text-truncate-2 mb-2">
                        با تولید سادگی نامفهوم از صنعت چاپ و با استفاده از طراحان گرافیک
                      </p>
                      <ul className="list-inline mb-0">
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item me-0 small">
                          <i className="fas fa-star text-warning">
                          </i>
                        </li>
                        <li className="list-inline-item ms-2 h6 fw-light mb-0">
                          5.0/5.0
                        </li>
                      </ul>
                    </div>
                    <div className="card-footer pt-0 pb-3">
                      <hr/>
                      <div className="d-flex justify-content-between">
                  <span className="h6 fw-light mb-0">
                    <i className="far fa-clock text-danger me-2">
                    </i>
                    35دقیقه
                  </span>
                        <span className="h6 fw-light mb-0">
                    <i className="fas fa-table text-orange me-2">
                    </i>
                    89 ویدیو
                  </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
  );
}
