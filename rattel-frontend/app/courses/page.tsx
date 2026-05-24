"use client";

import { Suspense, useState, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Navbar from "@/src/components/layout/Navbar";
import Footer from "@/src/components/layout/Footer";
import { useCourses, type SortOption, type DifficultyOption, type CategoryOption, type AgeGroupOption } from "@/src/core/hooks/useCourses";
import { getMediaUrl } from "@/src/core/utils";
import { toggleSaveCourse } from "@/src/core/hooks/useSavedCourses";
import { toast } from "react-toastify";
import {useAuth} from "@/src/core/hooks/useAuth";

function CoursesContent() {
    const router = useRouter();
    const searchParams = useSearchParams();

    const {isAuthenticated} = useAuth();
    
    // Get initial values from URL
    const [page, setPage] = useState(Number(searchParams.get('page')) || 1);
    const [sort, setSort] = useState<SortOption | undefined>(searchParams.get('sort') as SortOption || undefined);
    const [category, setCategory] = useState<CategoryOption | undefined>(searchParams.get('category') as CategoryOption || undefined);
    const [difficulty, setDifficulty] = useState<DifficultyOption | undefined>(searchParams.get('difficulty') as DifficultyOption || undefined);
    const [ageGroup, setAgeGroup] = useState<AgeGroupOption | undefined>(searchParams.get('age_group') as AgeGroupOption || undefined);
    const [search, setSearch] = useState<string | undefined>(searchParams.get('search') || undefined);
    const [savedStates, setSavedStates] = useState<Record<string, boolean>>({});

    const { coursesData, isLoadingCourses } = useCourses({
        page,
        count: 4,
        sort,
        category,
        difficulty,
        age_group: ageGroup,
        search,
    });

    // Initialize saved states when courses load
    useEffect(() => {
        if (coursesData?.courses) {
            const initialStates: Record<string, boolean> = {};
            coursesData.courses.forEach(course => {
                initialStates[course.id] = course.is_saved || false;
            });
            setSavedStates(initialStates);
        }
    }, [coursesData]);

    const handleToggleSave = async (courseId: string, e: React.MouseEvent) => {
        e.preventDefault();
        if(!isAuthenticated) {
            toast.warning("ابتدا وارد حساب کاربری خود شوید.");
            return;
        }
        const result = await toggleSaveCourse(courseId);
        if (result.success) {
            setSavedStates(prev => ({ ...prev, [courseId]: result.is_saved }));
            toast.success(result.is_saved ? "دوره ذخیره شد" : "دوره از ذخیره‌شده‌ها حذف شد");
        } else {
            toast.error(result.message);
        }
    };
    // Update URL when filters change
    useEffect(() => {
        const params = new URLSearchParams();
        if (page > 1) params.set('page', String(page));
        if (sort) params.set('sort', sort);
        if (category) params.set('category', category);
        if (difficulty) params.set('difficulty', difficulty);
        if (ageGroup) params.set('age_group', ageGroup);
        if (search) params.set('search', search);
        
        const queryString = params.toString();
        router.push(`/courses${queryString ? `?${queryString}` : ''}`, { scroll: false });
    }, [page, sort, category, difficulty, ageGroup, search, router]);

    const handlePageChange = (newPage: number) => {
        setPage(newPage);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const getCategoryLabel = (cat: string) => {
        switch (cat) {
            case 'telavat': return 'تلاوت';
            case 'tahfiz': return 'تحفیظ';
            case 'tadabbor': return 'تدبر';
            default: return cat;
        }
    };

    const getDifficultyLabel = (diff: string) => {
        switch (diff) {
            case 'beginner': return 'مقدماتی';
            case 'intermediate': return 'متوسطه';
            case 'advanced': return 'پیشرفته';
            default: return diff;
        }
    };

    const formatTime = (minutes: number) => {
        const hours = Math.floor(minutes / 60);
        return `${hours} ساعت`;
    };

    const formatPrice = (price: number) => {
        return new Intl.NumberFormat('fa-IR').format(price);
    };

    // Generate pagination
    const renderPagination = () => {
        if (!coursesData || !coursesData.total_pages) return null;
        
        const pages = [];
        const totalPages = coursesData.total_pages;
        const currentPage = coursesData.page;

        pages.push(
            <li key="prev" className={`page-item mb-0 ${!coursesData.has_previous ? 'disabled' : ''}`}>
                <a className="page-link" href="#" onClick={(e) => { e.preventDefault(); if (coursesData.has_previous) handlePageChange(currentPage - 1); }}>
                    <i className="fas fa-angle-double-right"></i>
                </a>
            </li>
        );

        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= currentPage - 1 && i <= currentPage + 1)) {
                pages.push(
                    <li key={i} className={`page-item mb-0 ${i === currentPage ? 'active' : ''}`}>
                        <a className="page-link" href="#" onClick={(e) => { e.preventDefault(); handlePageChange(i); }}>{i}</a>
                    </li>
                );
            } else if (i === currentPage - 2 || i === currentPage + 2) {
                pages.push(<li key={i} className="page-item mb-0 disabled"><span className="page-link">..</span></li>);
            }
        }

        pages.push(
            <li key="next" className={`page-item mb-0 ${!coursesData.has_next ? 'disabled' : ''}`}>
                <a className="page-link" href="#" onClick={(e) => { e.preventDefault(); if (coursesData.has_next) handlePageChange(currentPage + 1); }}>
                    <i className="fas fa-angle-double-left"></i>
                </a>
            </li>
        );

        return pages;
    };

    return (
        <>
            <main>
                <section className="bg-dark align-items-center d-flex"
                         style={{
                             background: 'url(assets/images/pattern/04.png) no-repeat center center',
                             backgroundSize: 'cover'
                         }}>
                    <div className="container">
                        <div className="row">
                            <div className="col-12">
                                <h1 className="text-white fs-2">
                                    لیست دوره ها
                                </h1>
                                <div className="d-flex">
                                    <nav aria-label="breadcrumb">
                                        <ol className="breadcrumb breadcrumb-dark breadcrumb-dots mb-0">
                                            <li className="breadcrumb-item">
                                                <a href="/">
                                                    صفحه اصلی
                                                </a>
                                            </li>
                                            <li className="breadcrumb-item active" aria-current="page">
                                                لیست دوره ها
                                            </li>
                                        </ol>
                                    </nav>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
                <section className="pb-0 py-sm-5">
                    <div className="container">
                        <div className="row g-3 align-items-center mb-4">
                            <div className="col-md-4">
                                <h4 className="mb-0 fs-5 fw-normal">
                                    {coursesData ? `نمایش ${((coursesData.page - 1) * coursesData.page_size) + 1}-${Math.min(coursesData.page * coursesData.page_size, coursesData.total)} از ${coursesData.total} نتیجه` : 'در حال بارگذاری...'}
                                </h4>
                            </div>
                            <div className="col-md-8">
                                <div className="row g-3 align-items-center justify-content-md-end me-auto">
                                    <div className="col-sm-4 col-xl-6 text-md-end d-none d-md-block">
                                    </div>
                                    <form className="col-md-4 border rounded p-1 input-borderless">
                                        <select 
                                            className="form-select js-choice z-index-9"
                                            value={sort || ''}
                                            onChange={(e) => { setSort(e.target.value as SortOption || undefined); setPage(1); }}
                                        >
                                            <option value="">مرتب سازی</option>
                                            <option value="rating">بیشترین امتیاز</option>
                                            <option value="total_sell">پرفروش‌ترین</option>
                                            <option value="has_discount">تخفیف‌دار</option>
                                            <option value="most_videos">بیشترین ویدیو</option>
                                            <option value="longest">طولانی‌ترین</option>
                                            <option value="shortest">کوتاه‌ترین</option>
                                        </select>
                                    </form>
                                    <div className="col-4 text-md-end">
                                        <button className="btn btn-primary mb-0 d-xl-none" type="button"
                                                data-bs-toggle="offcanvas"
                                                data-bs-target="#offcanvasSidebar" aria-controls="offcanvasSidebar">
                                            <i className="fas fa-sliders-h me-1">
                                            </i>
                                            نمایش فیلتر
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="row">
                            <div className="col-xl-9 col-xxl-8">
                                {isLoadingCourses ? (
                                    <div className="text-center py-5">
                                        <div className="spinner-border text-primary" role="status">
                                            <span className="visually-hidden">در حال بارگذاری...</span>
                                        </div>
                                    </div>
                                ) : coursesData?.courses.length === 0 ? (
                                    <div className="text-center py-5">
                                        <p className="text-muted">دوره‌ای یافت نشد</p>
                                    </div>
                                ) : (
                                <div className="row g-4">
                                    {coursesData?.courses.map((course) => (
                                    <div key={course.id} className="col-12">
                                        <div className="card shadow overflow-hidden p-2">
                                            <div className="row g-0">
                                                <div className="col-md-5 overflow-hidden">
                                                    <img src={course.image ? getMediaUrl(course.image) : '/assets/images/courses/4by3/06.jpg'} className="rounded-2"
                                                         alt={course.name}
                                                         onClick={(e) => {e.preventDefault(); router.push(`/courses/${course.id}`)}}
                                                    />
                                                    {course.new_price !== 0 && (
                                                        <div
                                                            className="card-img-overlay"
                                                            onClick={(e) => {e.preventDefault(); router.push(`/courses/${course.id}`)}}
                                                        >
                                                            <div className="ribbon">
                                                                <span>تخفیف</span>
                                                            </div>
                                                        </div>
                                                    )}
                                                </div>
                                                <div className="col-md-7">
                                                    <div className="card-body">
                                                        <div className="d-flex justify-content-between align-items-center mb-2">
                                                            <a href="#" className="badge text-bg-primary mb-2 mb-sm-0">
                                                                {getCategoryLabel(course.category)}
                                                            </a>
                                                            <div>
                                                                <span className="h6 fw-light me-3">
                                                                    <i className="fas fa-star text-warning me-1"></i>
                                                                    {course.rating.toFixed(1)}
                                                                </span>
                                                                <button 
                                                                    onClick={(e) => handleToggleSave(course.id, e)} 
                                                                    className="btn btn-link p-0 text-danger"
                                                                    style={{ border: "none", background: "none" }}
                                                                >
                                                                    <i className={`${savedStates[course.id] ? 'fas' : 'far'} fa-heart`}></i>
                                                                </button>
                                                            </div>
                                                        </div>
                                                        <h5 className="card-title fw-normal">
                                                            <a href={`/courses/${course.id}/`}>
                                                                {course.name}
                                                            </a>
                                                        </h5>
                                                        <p className="text-truncate-2 d-none d-lg-block" dangerouslySetInnerHTML={{__html: course.short_description}}></p>
                                                        <ul className="list-inline">
                                                            <li className="list-inline-item h6 fw-light mb-1 mb-sm-0">
                                                                <i className="far fa-clock text-danger me-2"></i>
                                                                {course.total_time} ساعت
                                                            </li>
                                                            <li className="list-inline-item h6 fw-light mb-1 mb-sm-0">
                                                                <i className="fas fa-table text-orange me-2"></i>
                                                                {course.number_of_episodes} فایل
                                                            </li>
                                                            <li className="list-inline-item h6 fw-light">
                                                                <i className="fas fa-signal text-success me-2"></i>
                                                                {getDifficultyLabel(course.difficulty)}
                                                            </li>
                                                        </ul>
                                                        {/* Progress Bar - Only show if user has progress */}
                                                        {course.progress && course.progress.total > 0 && (
                                                            <div className="mb-2">
                                                                <div className="d-flex justify-content-between align-items-center mb-1">
                                                                    <small className="text-muted">پیشرفت: {course.progress.percentage}%</small>
                                                                </div>
                                                                <div className="progress" style={{ height: '5px' }}>
                                                                    <div 
                                                                        className="progress-bar bg-success" 
                                                                        style={{ width: `${course.progress.percentage}%` }}
                                                                    ></div>
                                                                </div>
                                                            </div>
                                                        )}
                                                        <div className="d-sm-flex justify-content-sm-between align-items-center">
                                                            <div className="d-flex align-items-center">
                                                                <div className="avatar">
                                                                    <img className="avatar-img rounded-circle"
                                                                         src={course.teacher.profile_picture ? getMediaUrl(course.teacher.profile_picture) : '/assets/images/avatar/06.jpg'} 
                                                                         alt={course.teacher.name}/>
                                                                </div>
                                                                <p className="mb-0 ms-2">
                                                                    <a href="#" className="h6 fw-light">
                                                                        {course.teacher.name}
                                                                    </a>
                                                                </p>
                                                            </div>
                                                            <div className="mt-3 mt-sm-0">
                                                                {course.new_price > 0 ? (
                                                                    <div className="d-flex flex-column align-items-end">
                                                                        {course.price !== course.new_price && (
                                                                            <span className="text-decoration-line-through text-muted small">
                                                                                {formatPrice(course.price)} تومان
                                                                            </span>
                                                                        )}
                                                                        <span className="h5 mb-0 text-success">
                                                                            {formatPrice(course.new_price)} تومان
                                                                        </span>
                                                                    </div>
                                                                ) : (
                                                                    <span className="h5 mb-0 text-success">{formatPrice(course.price)} تومان</span>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    ))}
                                </div>
                                )}
                                {coursesData && coursesData.total_pages && coursesData.total_pages > 1 && (
                                <div className="col-12">
                                    <nav className="mt-4 d-flex justify-content-center" aria-label="navigation">
                                        <ul className="pagination pagination-primary-soft d-inline-block d-md-flex rounded mb-0">
                                            {renderPagination()}
                                        </ul>
                                    </nav>
                                </div>
                                )}
                            </div>
                            <div className="col-xl-3 col-xxl-4">
                                <div className="offcanvas-xl offcanvas-end" tabIndex={-1} id="offcanvasSidebar">
                                    <div className="offcanvas-header bg-light">
                                        <h5 className="offcanvas-title" id="offcanvasNavbarLabel">
                                            جستجوی پیشرفته
                                        </h5>
                                        <button type="button" className="btn-close" data-bs-dismiss="offcanvas"
                                                data-bs-target="#offcanvasSidebar" aria-label="Close">
                                        </button>
                                    </div>
                                    <div className="offcanvas-body p-3 p-xl-0">
                                        <form>
                                            <div className="card card-body shadow p-4 mb-4">
                                                <h4 className="mb-4 fs-6">
                                                    فیلتر دسته بندی
                                                </h4>
                                                <div className="row">
                                                    <div className="col-12">
                                                        <div className="form-check">
                                                            <input className="form-check-input" type="radio" name="category"
                                                                   id="category-all" checked={!category} onChange={() => { setCategory(undefined); setPage(1); }}/>
                                                            <label className="form-check-label" htmlFor="category-all">
                                                                همه
                                                            </label>
                                                        </div>
                                                            <div className="form-check">
                                                                <input className="form-check-input" type="radio" name="category"
                                                                   id="category-telavat" checked={category === 'telavat'} onChange={() => { setCategory('telavat'); setPage(1); }}/>
                                                            <label className="form-check-label" htmlFor="category-telavat">
                                                                تلاوت
                                                            </label>
                                                        </div>
                                                        <div className="form-check">
                                                            <input className="form-check-input" type="radio" name="category"
                                                                   id="category-tahfiz" checked={category === 'tahfiz'} onChange={() => { setCategory('tahfiz'); setPage(1); }}/>
                                                            <label className="form-check-label" htmlFor="category-tahfiz">
                                                                تحفیظ
                                                            </label>
                                                        </div>
                                                        <div className="form-check">
                                                            <input className="form-check-input" type="radio" name="category"
                                                                   id="category-tadabbor" checked={category === 'tadabbor'} onChange={() => { setCategory('tadabbor'); setPage(1); }}/>
                                                            <label className="form-check-label" htmlFor="category-tadabbor">
                                                                تدبر
                                                            </label>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="card card-body shadow p-4 mb-4">
                                                <h4 className="mb-3 fs-6">
                                                    فیلتر سطح مهارت
                                                </h4>
                                                <ul className="list-inline mb-0">
                                                    <li className="list-inline-item mb-2">
                                                        <input type="radio" className="btn-check" name="difficulty" id="difficulty-all" checked={!difficulty} onChange={() => { setDifficulty(undefined); setPage(1); }}/>
                                                        <label className="btn btn-light btn-primary-soft-check" htmlFor="difficulty-all">
                                                            همه سطح
                                                        </label>
                                                    </li>
                                                    <li className="list-inline-item mb-2">
                                                        <input type="radio" className="btn-check" name="difficulty" id="difficulty-beginner" checked={difficulty === 'beginner'} onChange={() => { setDifficulty('beginner'); setPage(1); }}/>
                                                        <label className="btn btn-light btn-primary-soft-check" htmlFor="difficulty-beginner">
                                                            مقدماتی
                                                        </label>
                                                    </li>
                                                    <li className="list-inline-item mb-2">
                                                        <input type="radio" className="btn-check" name="difficulty" id="difficulty-intermediate" checked={difficulty === 'intermediate'} onChange={() => { setDifficulty('intermediate'); setPage(1); }}/>
                                                        <label className="btn btn-light btn-primary-soft-check" htmlFor="difficulty-intermediate">
                                                            متوسطه
                                                        </label>
                                                    </li>
                                                    <li className="list-inline-item mb-2">
                                                        <input type="radio" className="btn-check" name="difficulty" id="difficulty-advanced" checked={difficulty === 'advanced'} onChange={() => { setDifficulty('advanced'); setPage(1); }}/>
                                                        <label className="btn btn-light btn-primary-soft-check" htmlFor="difficulty-advanced">
                                                            پیشرفته
                                                        </label>
                                                    </li>
                                                </ul>
                                            </div>
                                            <div className="card card-body shadow p-4 mb-4">
                                                <h4 className="mb-3 fs-6">
                                                    گروه سنی
                                                </h4>
                                                <ul className="list-inline mb-0">
                                                    <li className="list-inline-item mb-2">
                                                        <input type="radio" className="btn-check" name="age_group" id="age-all-ages" checked={ageGroup === 'all'} onChange={() => { setAgeGroup('all'); setPage(1); }}/>
                                                        <label className="btn btn-light btn-primary-soft-check" htmlFor="age-all-ages">
                                                            همه سنین
                                                        </label>
                                                    </li>
                                                    <li className="list-inline-item mb-2">
                                                        <input type="radio" className="btn-check" name="age_group" id="age-kid" checked={ageGroup === 'kid'} onChange={() => { setAgeGroup('kid'); setPage(1); }}/>
                                                        <label className="btn btn-light btn-primary-soft-check" htmlFor="age-kid">
                                                            کودک
                                                        </label>
                                                    </li>
                                                    <li className="list-inline-item mb-2">
                                                        <input type="radio" className="btn-check" name="age_group" id="age-teen" checked={ageGroup === 'teen'} onChange={() => { setAgeGroup('teen'); setPage(1); }}/>
                                                        <label className="btn btn-light btn-primary-soft-check" htmlFor="age-teen">
                                                            نوجوان
                                                        </label>
                                                    </li>
                                                    <li className="list-inline-item mb-2">
                                                        <input type="radio" className="btn-check" name="age_group" id="age-adult" checked={ageGroup === 'adult'} onChange={() => { setAgeGroup('adult'); setPage(1); }}/>
                                                        <label className="btn btn-light btn-primary-soft-check" htmlFor="age-adult">
                                                            بزرگسال
                                                        </label>
                                                    </li>
                                                </ul>
                                            </div>
                                        </form>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
            </main>
        </>
    );
}

export default function Courses() {
    return (
        <Suspense fallback={null}>
            <CoursesContent />
        </Suspense>
    );
}
