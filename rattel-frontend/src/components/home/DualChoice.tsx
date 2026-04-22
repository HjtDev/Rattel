export default function DualChoice() {
    return (
        <section className="py-0">
            <div className="container">
                <div className="row g-4">
                    <div className="col-lg-6 position-relative overflow-hidden">
                        <div className="bg-primary bg-opacity-10 rounded-3 p-5 h-100">
                            <div className="position-absolute bottom-0 end-0 me-3">
                                <img src="assets/images/element/08.svg" className="h-100px h-sm-200px"/>
                            </div>
                            <div className="row">
                                <div className="col-sm-8 position-relative">
                                    <h2 className="mb-1 h4">
                                        اعطای مدرک معتبر
                                    </h2>
                                    <p className="mb-3 h5 fw-light">
                                        برنامه گواهینامه حرفه ای مناسب را برای خود دریافت کنید.
                                    </p>
                                    <a href="#" className="btn btn-primary mb-0">
                                        مشاهده
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="col-lg-6 position-relative overflow-hidden">
                        <div className="bg-secondary rounded-3 bg-opacity-10 p-5 h-100">
                            <div className="position-absolute bottom-0 end-0 me-3">
                                <img src="assets/images/element/15.svg" className="h-100px h-sm-200px"/>
                            </div>
                            <div className="row">
                                <div className="col-sm-8 position-relative">
                                    <h2 className="mb-1 h4">
                                        بهترین دوره های آنلاین
                                    </h2>
                                    <p className="mb-3 h5 fw-light">
                                        اکنون در محبوب ترین و بهترین دوره ها ثبت نام کنید.
                                    </p>
                                    <a href="#" className="btn btn-warning mb-0">
                                        مشاهده
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    )
}