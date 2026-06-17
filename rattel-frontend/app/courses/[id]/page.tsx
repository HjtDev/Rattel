"use client";

import { useParams, useRouter } from "next/navigation";
import {useEffect, useState} from "react";
import { useCourseDetail } from "@/src/core/hooks/useCourseDetail";
import { getMediaUrl, shareCurrentPage, getDifficultyLabel, getCategoryLabel } from "@/src/core/utils";
import Navbar from "@/src/components/layout/Navbar";
import Footer from "@/src/components/layout/Footer";
import { toast } from "react-toastify";
import LoadingSkeleton from "@/src/components/skeleton/loadingSkeleton";
import { toggleSaveCourse } from "@/src/core/hooks/useSavedCourses";
import {useAuth} from "@/src/core/hooks/useAuth";
import { useCart } from "@/src/core/hooks/useCart";
import { markEpisodeWatched, useCourseProgress } from "@/src/core/hooks/useCourseProgress";

export default function CourseDetail() {
    const params = useParams();
    const router = useRouter();
    const courseId = params.id as string;

    const {isAuthenticated} = useAuth();
    const { items: cartItems, add: addToCart, remove: removeFromCart } = useCart();

    const { courseDetail, isLoadingCourseDetail, courseDetailError } = useCourseDetail(courseId);

    const isInCart = cartItems.some(
        (item) => item.app_label === 'courses' && item.model === 'course' && item.object_id === courseId
    );

    const handleCartToggle = async () => {
        if (isInCart) {
            const result = await removeFromCart('courses', 'course', courseId);
            if (result.success) {
                toast.info("دوره از سبد خرید حذف شد");
            } else {
                toast.error(result.message);
            }
        } else {
            const result = await addToCart('courses', 'course', courseId, 1, {
                name: courseDetail?.name,
                picture: courseDetail?.image ? getMediaUrl(courseDetail.image) : null,
                price: courseDetail?.price,
                new_price: courseDetail?.new_price,
            });
            if (result.success) {
                toast.success("دوره به سبد خرید اضافه شد");
            } else {
                toast.error(result.message);
            }
        }
    };
    const [videoModalOpen, setVideoModalOpen] = useState(false);
    const [currentVideoUrl, setCurrentVideoUrl] = useState<string>("");
    const [isSaved, setIsSaved] = useState(false);
    const [currentEpisodeId, setCurrentEpisodeId] = useState<string | null>(null);
    const { progress, refetchProgress } = useCourseProgress(null);

    const formatPrice = (price: number) => {
        return new Intl.NumberFormat('fa-IR').format(price);
    };

    const formatTime = (minutes: number) => {
        const hours = Math.floor(minutes / 60);
        return `${hours} ساعت`;
    };

    const getAgeGroupLabel = (ageGroup: string) => {
        const labels: Record<string, string> = {
            child: "کودک",
            teen: "نوجوان",
            adult: "بزرگسال",
            all: "همه سنین"
        };
        return labels[ageGroup] || ageGroup;
    };

    const handleCategoryClick = (category: string) => {
        router.push(`/courses?category=${category}`);
    };

    const handleDifficultyClick = (difficulty: string) => {
        router.push(`/courses?difficulty=${difficulty}`);
    };

    const handleShare = async () => {
        const result = await shareCurrentPage({
            title: courseDetail?.name,
            text: courseDetail?.short_description?.replace(/<[^>]*>/g, ''),
        });

        if (result === "copied") {
            toast.success("لینک دوره کپی شد");
        }
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('fa-IR').format(date);
    };

    const openVideoModal = (videoUrl: string) => {
        setCurrentVideoUrl(videoUrl);
        setVideoModalOpen(true);
    };

    const closeVideoModal = () => {
        setVideoModalOpen(false);
        setCurrentVideoUrl("");
    };

    const handleEpisodeClick = async (episodeId: string, episodeType: string, fileUrl: string) => {
        if (episodeType === 'video') {
            setCurrentEpisodeId(episodeId);
            openVideoModal(fileUrl);
            
            // Mark episode as watched after opening
            if (isAuthenticated) {
                const result = await markEpisodeWatched(courseId, episodeId, true);
                if (result.success) {
                    refetchProgress();
                }
            }
        } else {
            // Download file for note or attachment
            if (isAuthenticated) {
                await markEpisodeWatched(courseId, episodeId, true);
                refetchProgress();
            }
            const link = document.createElement('a');
            link.href = fileUrl;
            link.download = '';
            link.target = '_blank';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    };

    const handleToggleSave = async () => {
        if(!isAuthenticated) {
            toast.warning("ابتدا وارد حساب کاربری خود شوید.");
            return;
        }
        const result = await toggleSaveCourse(courseId);
        if (result.success) {
            setIsSaved(result.is_saved);
            if (result.is_saved) {
                toast.success("دوره به لیست ذخیره‌شده‌ها اضافه شد");
            } else {
                toast.info("دوره از لیست ذخیره‌شده‌ها حذف شد");
            }
        } else {
            toast.error(result.message);
        }
    };

    // Update isSaved when courseDetail loads
    useEffect(() => {
        if (courseDetail) {
            setIsSaved(courseDetail.is_saved);
            if(courseDetail.is_owned) {
                refetchProgress(courseDetail.id)
            }
        }
    }, [courseDetail]);

    useEffect(() => {
        if(courseDetailError) {
            toast.error(courseDetailError);
            setTimeout(() => router.back(), 3000);
        }
    }, [courseDetailError]);

    if (isLoadingCourseDetail) {
        return (
            <>
                <main>
                    <section className="pt-3 pt-xl-5">
                        <div className="container">
                            <div className="row g-4">
                                <div className="col-xl-8">
                                    <div className="row g-4">
                                        {/* Image Skeleton */}
                                        <div className="col-12">
                                            <LoadingSkeleton width="100%" height="400px" isLoading={true} Content={() => <></>} />
                                        </div>
                                        {/* Title Skeleton */}
                                        <div className="col-12">
                                            <LoadingSkeleton width="60%" height="32px" isLoading={true} Content={() => <></>} />
                                            <div className="mt-2">
                                                <LoadingSkeleton width="80%" height="20px" isLoading={true} Content={() => <></>} />
                                            </div>
                                        </div>
                                        {/* Description Card Skeleton */}
                                        <div className="col-12">
                                            <div className="card border">
                                                <div className="card-header border-bottom">
                                                    <LoadingSkeleton width="150px" height="24px" isLoading={true} Content={() => <></>} />
                                                </div>
                                                <div className="card-body">
                                                    <LoadingSkeleton width="100%" height="20px" isLoading={true} Content={() => <></>} count={5} />
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                {/* Sidebar Skeleton */}
                                <div className="col-xl-4">
                                    <div className="card card-body border p-4">
                                        <LoadingSkeleton width="100%" height="40px" isLoading={true} Content={() => <></>} />
                                        <div className="mt-3">
                                            <LoadingSkeleton width="100%" height="45px" isLoading={true} Content={() => <></>} />
                                        </div>
                                        <div className="mt-3">
                                            <LoadingSkeleton width="100%" height="30px" isLoading={true} Content={() => <></>} count={5} />
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

    return courseDetail && (
        <>
            <main>
                <section className="pt-3 pt-xl-5">
                    <div className="container" data-sticky-container>
                        <div className="row g-4">
                            <div className="col-xl-8">
                                <div className="row g-4">
                                    {/* Course Image */}
                                    {courseDetail.image && (
                                        <div className="col-12">
                                            <img 
                                                src={getMediaUrl(courseDetail.image)} 
                                                alt={courseDetail.name}
                                                className="rounded-3 w-100"
                                                style={{ maxHeight: '400px', objectFit: 'cover' }}
                                            />
                                        </div>
                                    )}

                                    {/* Course Title and Info */}
                                    <div className="col-12">
                                        <h2 className="fs-3">
                                            {courseDetail.name}
                                        </h2>
                                        <div 
                                            dangerouslySetInnerHTML={{ __html: courseDetail.short_description }}
                                            style={{ color: "#383E43" }}
                                        />
                                        <ul className="list-inline mb-0 mt-3">
                                            <li className="list-inline-item fw-light h6 me-3 mb-1 mb-sm-0">
                                                <i className="fas fa-star text-warning me-2"></i>
                                                {courseDetail.rating}/5.0
                                            </li>
                                            <li className="list-inline-item fw-light h6 me-3 mb-1 mb-sm-0">
                                                <i className="fas fa-user-graduate me-2"></i>
                                                {new Intl.NumberFormat('fa-IR').format(courseDetail.total_sell)} شرکت کننده
                                            </li>
                                            <li className="list-inline-item fw-light h6 me-3 mb-1 mb-sm-0">
                                                <i className="fas fa-signal me-2"></i>
                                                <span 
                                                    onClick={() => handleDifficultyClick(courseDetail.difficulty)}
                                                    style={{ cursor: 'pointer' }}
                                                    className="text-primary"
                                                >
                                                    {getDifficultyLabel(courseDetail.difficulty)}
                                                </span>
                                            </li>
                                            <li className="list-inline-item fw-light h6 me-3 mb-1 mb-sm-0">
                                                <i className="bi bi-patch-exclamation-fill me-2"></i>
                                                آخرین بروزرسانی {formatDate(courseDetail.updated_at)}
                                            </li>
                                            <li className="list-inline-item fw-light h6">
                                                <i className="fas fa-tag me-2"></i>
                                                <span 
                                                    onClick={() => handleCategoryClick(courseDetail.category)}
                                                    style={{ cursor: 'pointer' }}
                                                    className="text-primary"
                                                >
                                                    {getCategoryLabel(courseDetail.category)}
                                                </span>
                                            </li>
                                        </ul>
                                    </div>

                                    {/* Intro Video */}
                                    {courseDetail.intro_video && (
                                        <div className="col-12 position-relative">
                                            <div className="d-flex align-items-center justify-content-center py-2 ms-0 ms-sm-4">
                                                <button 
                                                    onClick={() => openVideoModal(courseDetail.intro_video!)}
                                                    className="btn btn-round btn-primary-shadow mb-0 overflow-visible me-7"
                                                >
                                                    <i className="fas fa-play"></i>
                                                    <h6 className="mb-0 ms-3 fw-normal position-absolute start-100 top-50 translate-middle-y">
                                                        معرفی دوره
                                                    </h6>
                                                </button>
                                            </div>
                                        </div>
                                    )}

                                    {/* Course Description */}
                                    <div className="col-12">
                                        <div className="card border">
                                            <div className="card-header border-bottom">
                                                <h3 className="mb-0 fs-5">
                                                    توضیحات دوره
                                                </h3>
                                            </div>
                                            <div
                                                className="card-body"
                                                 style={{ color: "#383E43" }}
                                            >
                                                <div dangerouslySetInnerHTML={{ __html: courseDetail.long_description }} />
                                            </div>
                                        </div>
                                    </div>

                                    {/* Course Curriculum */}
                                    <div className="col-12">
                                        <div className="card border">
                                            <div className="card-header border-bottom">
                                                <h3 className="mb-0 fs-5">سرفصل دوره</h3>
                                            </div>
                                            <div className="card-body">
                                                <div className="accordion accordion-icon accordion-bg-light" id="accordionCurriculum">
                                                    {courseDetail.chapters.map((chapter, chapterIndex) => (
                                                        <div className="accordion-item mb-3" key={chapter.id}>
                                                            <h6 className="accordion-header" id={`heading-${chapter.id}`}>
                                                                <button
                                                                    className={`accordion-button fw-bold rounded d-sm-flex d-inline-block ${chapterIndex === 0 ? '' : 'collapsed'}`}
                                                                    type="button"
                                                                    data-bs-toggle="collapse"
                                                                    data-bs-target={`#collapse-${chapter.id}`}
                                                                    aria-expanded={chapterIndex === 0 ? 'true' : 'false'}
                                                                    aria-controls={`collapse-${chapter.id}`}
                                                                >
                                                                    {chapter.title}
                                                                    <span className="small ms-0 ms-sm-2">
                                                                        ({chapter.number_of_videos} ویدیو)
                                                                    </span>
                                                                </button>
                                                            </h6>
                                                            <div
                                                                id={`collapse-${chapter.id}`}
                                                                className={`accordion-collapse collapse ${chapterIndex === 0 ? 'show' : ''}`}
                                                                aria-labelledby={`heading-${chapter.id}`}
                                                                data-bs-parent="#accordionCurriculum"
                                                            >
                                                                <div className="accordion-body mt-3">
                                                                    {chapter.description && (
                                                                        <div 
                                                                            dangerouslySetInnerHTML={{ __html: chapter.description }}
                                                                            className="mb-3"
                                                                            style={{ color: "#383E43" }}
                                                                        />
                                                                    )}
                                                                    {chapter.episodes.map((episode) => {
                                                                        const isLocked = episode.file === 'hidden';
                                                                        return (
                                                                            <div
                                                                                key={episode.id}
                                                                                className="d-flex justify-content-between align-items-center mb-2"
                                                                            >
                                                                                <div className="position-relative d-flex align-items-center">
                                                                                    {isLocked ? (
                                                                                        <>
                                                                                            <i className="fas fa-lock text-muted me-2"></i>
                                                                                            <span className="text-muted">{episode.title}</span>
                                                                                        </>
                                                                                   ) : (
                                                                                       <>
                                                                                           <button
                                                                                                onClick={() => handleEpisodeClick(episode.id, episode.type, episode.file)}
                                                                                               className="btn btn-danger-soft btn-round btn-sm mb-0"
                                                                                           >
                                                                                               {episode.type === 'video' ? (
                                                                                                    <i className="fas fa-play me-0"></i>
                                                                                                ) : (
                                                                                                    <i className="fas fa-download me-0"></i>
                                                                                                )}
                                                                                            </button>
                                                                                            <span className="d-inline-block text-truncate ms-2 mb-0 h6 fw-light w-100px w-sm-200px w-md-400px">
                                                                                                {episode.title}
                                                                                            </span>
                                                                                        </>
                                                                                    )}
                                                                                </div>
                                                                                <p className="mb-0 text-truncate">
                                                                                    {episode.type === 'video' ? (
                                                                                        <i className="fas fa-video text-muted me-2"></i>
                                                                                    ) : episode.type === 'note' ? (
                                                                                        <i className="fas fa-file-alt text-muted me-2"></i>
                                                                                    ) : (
                                                                                        <i className="fas fa-paperclip text-muted me-2"></i>
                                                                                    )}
                                                                                </p>
                                                                            </div>
                                                                        );
                                                                    })}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Comments Section (replacing FAQ) */}
                                    <div className="col-12">
                                        <div className="card border">
                                            <div className="card-header border-bottom">
                                                <h3 className="mb-0 fs-5">نظرات</h3>
                                            </div>
                                            <div className="card-body">
                                                <div className="text-center text-muted py-5">
                                                    <i className="fas fa-comments fa-3x mb-3"></i>
                                                    <p>بخش نظرات به زودی فعال خواهد شد</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Sidebar */}
                            <div className="col-xl-4">
                                <div data-sticky data-margin-top="80" data-sticky-for="768">
                                    <div className="card card-body border p-4">
                                        {/* Course Info */}


                                        {/* Add to Cart Button */}
                                        {
                                            !courseDetail.is_owned && (
                                                <>
                                                    <div className="d-flex justify-content-between align-items-center mb-3">
                                                        {courseDetail.price === 0 ? (
                                                            <h3 className="fw-bold mb-0 text-success">رایگان</h3>
                                                        ) : (
                                                            <div>
                                                                {courseDetail.new_price > 0 && (
                                                                    <>
                                                            <span className="badge bg-danger mb-2">
                                                                {courseDetail.discount}% تخفیف
                                                            </span>
                                                                        <div
                                                                            className="text-decoration-line-through text-muted">
                                                                            {formatPrice(courseDetail.price)} تومان
                                                                        </div>
                                                                    </>
                                                                )}
                                                                <h3 className="fw-bold mb-0">
                                                                    {formatPrice(courseDetail.new_price > 0 ? courseDetail.new_price : courseDetail.price)} تومان
                                                                </h3>
                                                            </div>
                                                        )}
                                                    </div>
                                                    <div className="d-grid mb-3">
                                                        <button
                                                            className={`btn mb-0 ${isInCart ? 'btn-outline-danger' : 'btn-primary'}`}
                                                            onClick={handleCartToggle}
                                                        >
                                                            {isInCart ? 'حذف از سبد خرید' : 'افزودن به سبد خرید'}
                                                        </button>
                                                    </div>
                                                </>
                                            )
                                        }

                                        {/* Course Features */}
                                        <ul className="list-group list-group-borderless">
                                            {/* Progress Bar - Only show if user has access and progress exists */}
                                            {progress && progress.total > 0 && (
                                                <li className="list-group-item px-0 mb-3">
                                                    <div className="d-flex justify-content-between align-items-center mb-2">
                                                        <span className="h6 fw-light mb-0">پیشرفت دوره</span>
                                                        <span className="h6 fw-light mb-0">{progress.percentage}%</span>
                                                    </div>
                                                    <div className="progress" style={{ height: '8px' }}>
                                                        <div 
                                                            className="progress-bar bg-success" 
                                                            role="progressbar" 
                                                            style={{ width: `${progress.percentage}%` }}
                                                            aria-valuenow={progress.percentage} 
                                                            aria-valuemin={0} 
                                                            aria-valuemax={100}
                                                        ></div>
                                                    </div>
                                                    <small className="text-muted mt-1 d-block">{progress.completed} از {progress.total} قسمت تکمیل شده</small>
                                                </li>
                                            )}
                                            <li className="list-group-item d-flex justify-content-between align-items-center px-0">
                                                <span className="h6 fw-light mb-0">
                                                    <i className="fas fa-clock text-primary me-2"></i>
                                                    زمان مورد نیاز
                                                </span>
                                                <span>{courseDetail.total_time} ساعت</span>
                                            </li>
                                            <li className="list-group-item d-flex justify-content-between align-items-center px-0">
                                                <span className="h6 fw-light mb-0">
                                                    <i className="fas fa-play-circle text-primary me-2"></i>
                                                    فایل هاّ
                                                </span>
                                                <span>{new Intl.NumberFormat('fa-IR').format(courseDetail.number_of_episodes)}</span>
                                            </li>
                                            <li className="list-group-item d-flex justify-content-between align-items-center px-0">
                                                <span className="h6 fw-light mb-0">
                                                    <i className="fas fa-signal text-primary me-2"></i>
                                                    سطح
                                                </span>
                                                <span>{getDifficultyLabel(courseDetail.difficulty)}</span>
                                            </li>
                                            <li className="list-group-item d-flex justify-content-between align-items-center px-0">
                                                <span className="h6 fw-light mb-0">
                                                    <i className="fas fa-users text-primary me-2"></i>
                                                    گروه سنی
                                                </span>
                                                <span>{getAgeGroupLabel(courseDetail.age_group)}</span>
                                            </li>
                                            <li className="list-group-item d-flex justify-content-between align-items-center px-0">
                                                <span className="h6 fw-light mb-0">
                                                    <i className="fas fa-user-graduate text-primary me-2"></i>
                                                    دانشجویان
                                                </span>
                                                <span>{new Intl.NumberFormat('fa-IR').format(courseDetail.total_sell)} نفر</span>
                                            </li>
                                        </ul>

                                        {/* Share Button */}
                                        <div className="d-grid mt-3">
                                            <button onClick={handleShare} className="btn btn-outline-primary mb-0">
                                                <i className="fas fa-share-alt me-2"></i>
                                                اشتراک‌گذاری
                                            </button>
                                        </div>

                                        {/* Save Button */}
                                        <div className="d-grid mt-2">
                                            <button onClick={handleToggleSave} className={`btn ${isSaved ? 'btn-danger' : 'btn-outline-danger'} mb-0`}>
                                                <i className={`${isSaved ? 'fas' : 'far'} fa-heart me-2`}></i>
                                                {isSaved ? 'حذف از علاقه مندی ها' : 'ذخیره در علاقه مندی ها'}
                                            </button>
                                        </div>

                                        {/* Teacher Info */}
                                        <div className="card card-body border mt-4">
                                            <div className="d-sm-flex align-items-center">
                                                <div className="avatar avatar-xl">
                                                    <img
                                                        className="avatar-img rounded-circle"
                                                        src={getMediaUrl(courseDetail.teacher.profile_picture) || '/assets/images/avatar/default.jpg'}
                                                        alt={courseDetail.teacher.name}
                                                    />
                                                </div>
                                                <div className="ms-sm-3 mt-2 mt-sm-0">
                                                    <h5 className="mb-0">
                                                        <a href="#">{courseDetail.teacher.name}</a>
                                                    </h5>
                                                    <p className="mb-0 small">مدرس دوره</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
            </main>

            {/* Video Modal */}
            {videoModalOpen && (
                <div 
                    className="modal fade show" 
                    style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.8)' }}
                    onClick={closeVideoModal}
                >
                    <div 
                        className="modal-dialog modal-dialog-centered modal-xl"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="modal-content bg-transparent border-0">
                            <div className="modal-body p-0 position-relative">
                                <button 
                                    type="button" 
                                    className="btn-close btn-close-white position-absolute top-0 end-0 m-3" 
                                    onClick={closeVideoModal}
                                    style={{ zIndex: 1050 }}
                                ></button>
                                <div className="ratio ratio-16x9">
                                    <video
                                        src={currentVideoUrl}
                                        controls
                                        autoPlay
                                        className="rounded"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
