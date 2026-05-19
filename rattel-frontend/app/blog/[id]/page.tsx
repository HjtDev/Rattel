"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { toast } from "react-toastify";
import { useAuth } from "@/src/core/hooks/useAuth";
import { sendBlogViewCount, useBlogDetail } from "@/src/core/hooks/useBlogDetail";
import { toggleSaveBlog } from "@/src/core/hooks/useSavedBlogs";
import { getMediaUrl } from "@/src/core/utils";
import { api } from "@/src/core/api";

export default function BlogPostPage() {
  const params = useParams<{ id: string }>();
  const postId = params?.id || null;

  const { isAuthenticated } = useAuth();
  const { blogDetail, setBlogDetail, isLoadingBlogDetail, blogDetailError } = useBlogDetail(postId);
  const [viewSent, setViewSent] = useState(false);
  const [commentText, setCommentText] = useState("");
  const [replyToId, setReplyToId] = useState<number | null>(null);
  const [isSubmittingComment, setIsSubmittingComment] = useState(false);
  const [showCommentModal, setShowCommentModal] = useState(false);

  useEffect(() => {
    if (!postId || viewSent) return;

    const timer = setTimeout(async () => {
      const success = await sendBlogViewCount(postId);
      if (success) {
        setViewSent(true);
      }
    }, 30000);

    return () => clearTimeout(timer);
  }, [postId, viewSent]);

  const publishDate = useMemo(() => {
    if (!blogDetail) return "";
    const value = blogDetail.published_at || blogDetail.created_at;
    return new Date(value).toLocaleDateString("fa-IR");
  }, [blogDetail]);

  const handleToggleSave = async () => {
    if (!postId) return;
    if (!isAuthenticated) {
      toast.warning("ابتدا وارد حساب کاربری خود شوید.");
      return;
    }

    const result = await toggleSaveBlog(postId);
    if (!result.success) {
      toast.error(result.message);
      return;
    }

    setBlogDetail((prev) => {
      if (!prev) return prev;
      return { ...prev, is_saved: result.is_saved };
    });

    toast.success(result.is_saved ? "پست ذخیره شد" : "پست از ذخیره‌شده‌ها حذف شد");
  };

  const handleSubmitComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!postId) return;
    if (!isAuthenticated) {
      toast.warning("برای ارسال دیدگاه ابتدا وارد حساب کاربری شوید.");
      return;
    }
    if (!commentText.trim()) {
      toast.warning("متن دیدگاه را وارد کنید.");
      return;
    }

    setIsSubmittingComment(true);
    try {
      const response = await api.post(`/blog/${postId}/comments/`, {
        content: commentText.trim(),
        reply_to: replyToId,
      });

      if (response.data.success) {
        toast.success("دیدگاه شما ثبت شد.");
        setCommentText("");
        setReplyToId(null);
        setShowCommentModal(false);
        const detailResponse = await api.get(`/blog/${postId}/?t=${Date.now()}`);
        if (detailResponse.data.success) {
          setBlogDetail(detailResponse.data.post);
        }
      } else {
        toast.error(response.data.message || "ارسال دیدگاه ناموفق بود.");
      }
    } catch (err: any) {
      toast.error(err.response?.data?.message || "ارسال دیدگاه ناموفق بود.");
    } finally {
      setIsSubmittingComment(false);
    }
  };

  if (isLoadingBlogDetail) {
    return (
      <main className="py-5 text-center">
        <div className="spinner-border text-primary" role="status"><span className="visually-hidden">در حال بارگذاری...</span></div>
      </main>
    );
  }

  if (blogDetailError || !blogDetail) {
    return (
      <main className="py-5 text-center">
        <p className="text-muted">{blogDetailError || "پست پیدا نشد"}</p>
      </main>
    );
  }

  return (
    <main>
      <section className="pb-0 pt-4 pb-md-5">
        <div className="container">
          <div className="row">
            <div className="col-12">
              <div className="row">
                <div className="col-lg-3 align-items-center mt-4 mt-lg-5 order-2 order-lg-1">
                  <div className="text-lg-center">
                    <div className="avatar avatar-xxl">
                      <img className="avatar-img rounded-circle" src={blogDetail.author.profile_picture ? getMediaUrl(blogDetail.author.profile_picture) : "/assets/images/avatar/09.jpg"} alt={blogDetail.author.name} />
                    </div>
                    <h5 className="mt-2 mb-0 d-block">{blogDetail.author.name}</h5>
                    <p className="mb-2">نویسنده</p>
                    <ul className="list-inline list-unstyled">
                      <li className="list-inline-item d-lg-block my-lg-2">{publishDate}</li>
                      <li className="list-inline-item d-lg-block my-lg-2">{blogDetail.ttr} دقیقه زمان مطالعه</li>
                      <li className="list-inline-item badge text-bg-info"><i className="far fa-eye me-1"></i>{blogDetail.view_count} بازدید</li>
                    </ul>
                    <button className="btn btn-sm btn-outline-danger" onClick={handleToggleSave}>
                      <i className={`${blogDetail.is_saved ? "fas" : "far"} fa-heart ms-1`}></i>
                      {blogDetail.is_saved ? "ذخیره شده" : "ذخیره پست"}
                    </button>
                  </div>
                </div>

                <div className="col-lg-9 order-1">
                  <span>{blogDetail.time_since} پیش</span>
                  <span className="mx-2">|</span>
                  <div className="badge text-bg-success">{blogDetail.category?.name || "عمومی"}</div>
                  <h1 className="mt-2 mb-0 fs-4">{blogDetail.title}</h1>
                  <div className="mt-2" dangerouslySetInnerHTML={{ __html: blogDetail.short_description }}></div>
                </div>
              </div>

              <div className="row mt-4">
                <div className="col-xl-10 mx-auto">
                  <img
                    src={blogDetail.thumbnail ? getMediaUrl(blogDetail.thumbnail) : "/assets/images/event/10.jpg"}
                    className="rounded-3 w-100"
                    alt={blogDetail.title}
                  />
                </div>
              </div>

              <div className="row mt-4">
                <div className="col-12 mt-4 mt-lg-0">
                  <div dangerouslySetInnerHTML={{ __html: blogDetail.description }}></div>
                  {blogDetail.conclusion && (
                    <div className="bg-light rounded-3 p-3 p-md-4 mt-4">
                      <div className="row align-items-center g-3">
                        <div className="col-md-4">
                          <div className="d-flex align-items-center justify-content-md-start">
                            <div className="avatar avatar-md">
                              <img
                                className="avatar-img rounded-circle"
                                src={blogDetail.author.profile_picture ? getMediaUrl(blogDetail.author.profile_picture) : "/assets/images/avatar/07.jpg"}
                                alt={blogDetail.author.name}
                              />
                            </div>
                            <div className="ms-2">
                              <h6 className="mb-0">{blogDetail.author.name}</h6>
                              <p className="mb-0 small">نویسنده</p>
                            </div>
                          </div>
                        </div>
                        <div className="col-md-8">
                          <span dangerouslySetInnerHTML={{ __html: blogDetail.conclusion }}></span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="d-lg-flex justify-content-lg-between my-4">
                <div className="align-items-center">
                  <h6 className="mb-2 me-4 d-inline-block">برچسب‌ها:</h6>
                  <ul className="list-inline mb-0 social-media-btn">
                    {blogDetail.tags.map((item) => (
                      <li key={item.slug} className="list-inline-item">
                        <Link className="btn btn-outline-light btn-sm mb-lg-0" href={`/blog?tag=${item.slug}`}>{item.name}</Link>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <hr />

              <div className="row mt-4">
                <div className="col-md-8">
                  <div className="d-flex justify-content-between align-items-center mb-3">
                    <h3 className="fs-5 mb-0">دیدگاه کاربران ({blogDetail.comments.length})</h3>
                    <button
                      type="button"
                      className="btn btn-sm btn-primary"
                      onClick={() => {
                        if (!isAuthenticated) {
                          toast.warning("برای ارسال دیدگاه ابتدا وارد حساب کاربری شوید.");
                          return;
                        }
                        setShowCommentModal(true);
                      }}
                    >
                      <i className="bi bi-plus-circle me-1"></i>
                      ثبت دیدگاه
                    </button>
                  </div>
                  {blogDetail.comments.length === 0 ? (
                    <p className="text-muted">هنوز دیدگاهی ثبت نشده است.</p>
                  ) : (
                    blogDetail.comments.map((comment) => (
                      <div key={comment.id} className="my-4 d-flex">
                        <img className="avatar avatar-md rounded-circle me-3" src={comment.user.profile_picture ? getMediaUrl(comment.user.profile_picture) : "/assets/images/avatar/01.jpg"} alt={comment.user.name} />
                        <div>
                          <div className="mb-2">
                            <h6 className="m-0">{comment.user.name}</h6>
                            <span className="me-3 small">{new Date(comment.created_at).toLocaleDateString("fa-IR")}</span>
                          </div>
                          <div>{comment.content}</div>
                          {isAuthenticated && (
                            <button
                              type="button"
                              className="btn btn-sm btn-link p-0 mt-1"
                              onClick={() => {
                                if (!isAuthenticated) {
                                  toast.warning("برای پاسخ ابتدا وارد حساب کاربری شوید.");
                                  return;
                                }
                                setReplyToId(comment.id);
                                setShowCommentModal(true);
                              }}
                            >
                              پاسخ
                            </button>
                          )}
                          {comment.replies?.length > 0 && (
                            <div className="mt-3 ps-3 border-start">
                              {comment.replies.map((reply) => (
                                <div key={reply.id} className="mb-2">
                                  <strong className="small">{reply.user.name}:</strong> {reply.content}
                                  {isAuthenticated && (
                                    <button
                                      type="button"
                                      className="btn btn-sm btn-link p-0 ms-2"
                                      onClick={() => {
                                        if (!isAuthenticated) {
                                          toast.warning("برای پاسخ ابتدا وارد حساب کاربری شوید.");
                                          return;
                                        }
                                        setReplyToId(comment.id);
                                        setShowCommentModal(true);
                                      }}
                                    >
                                      پاسخ
                                    </button>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {showCommentModal && (
        <div className="modal show d-block" tabIndex={-1} style={{ backgroundColor: "rgba(0,0,0,0.5)" }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title ff-vb">{replyToId ? "پاسخ به دیدگاه" : "ثبت دیدگاه جدید"}</h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => {
                    setShowCommentModal(false);
                    setReplyToId(null);
                  }}
                ></button>
              </div>
              <form onSubmit={handleSubmitComment}>
                <div className="modal-body">
                  {replyToId && (
                    <div className="alert alert-info d-flex justify-content-between align-items-center py-2">
                      <span className="small">در حال پاسخ به یک دیدگاه</span>
                      <button
                        type="button"
                        className="btn btn-sm btn-outline-secondary"
                        onClick={() => setReplyToId(null)}
                      >
                        لغو پاسخ
                      </button>
                    </div>
                  )}
                  <textarea
                    className="form-control"
                    rows={5}
                    placeholder={isAuthenticated ? "دیدگاه خود را بنویسید..." : "برای ارسال دیدگاه وارد شوید"}
                    value={commentText}
                    onChange={(e) => setCommentText(e.target.value)}
                    disabled={!isAuthenticated || isSubmittingComment}
                  />
                </div>
                <div className="modal-footer">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => {
                      setShowCommentModal(false);
                      setReplyToId(null);
                    }}
                  >
                    لغو
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={!isAuthenticated || isSubmittingComment}
                  >
                    {isSubmittingComment ? "در حال ارسال..." : "ارسال دیدگاه"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
