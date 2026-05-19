"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import DashboardBase from "@/src/components/dashboard/DashboardBase";
import { useDashboard } from "@/src/core/hooks/useDashboard";
import { getMediaUrl } from "@/src/core/utils";
import { useSavedBlogs } from "@/src/core/hooks/useSavedBlogs";

function SavedBlogsContent() {
  const { isLoadingDashboard } = useDashboard();
  const { savedBlogs, isLoadingSavedBlogs } = useSavedBlogs();
  const [searchQuery, setSearchQuery] = useState("");
  const router = useRouter();

  const filteredBlogs = useMemo(() => {
    if (!searchQuery.trim()) return savedBlogs;

    const query = searchQuery.toLowerCase();
    return savedBlogs?.filter((post) => {
      const title = post.title.toLowerCase();
      const author = post.author.name.toLowerCase();
      const category = (post.category?.name || "").toLowerCase();
      const description = (post.short_description || "").toLowerCase();

      return (
        title.includes(query)
        || author.includes(query)
        || category.includes(query)
        || description.includes(query)
      );
    });
  }, [savedBlogs, searchQuery]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
  };

  return !isLoadingDashboard && (
    <div className="col-xl-9">
      <div className="card bg-transparent border rounded-3">
        <div className="card-header bg-transparent border-bottom">
          <h3 className="mb-0 fs-5 ff-vb">پست های ذخیره‌شده من</h3>
        </div>

        <div className="card-body">
          <div className="row g-3 align-items-center justify-content-between mb-4">
            <div className="col-md-12">
              <form className="rounded position-relative" onSubmit={handleSearchSubmit}>
                <input
                  className="form-control pe-5 bg-transparent"
                  type="search"
                  placeholder="جستجوی پست"
                  aria-label="Search"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                <button
                  className="bg-transparent p-2 position-absolute top-50 end-0 translate-middle-y border-0 text-primary-hover text-reset"
                  type="submit"
                >
                  <i className="fas fa-search fs-6"></i>
                </button>
              </form>
            </div>
          </div>

          {isLoadingSavedBlogs ? (
            <div className="text-center py-5">
              <div className="spinner-border text-primary" role="status">
                <span className="visually-hidden">در حال بارگذاری...</span>
              </div>
            </div>
          ) : filteredBlogs?.length === 0 ? (
            <div className="text-center py-5">
              <p className="text-muted">
                {searchQuery ? "پستی یافت نشد" : "هنوز پستی ذخیره نکرده‌اید"}
              </p>
            </div>
          ) : (
            <div className="table-responsive border-0">
              <table className="table table-dark-gray align-middle p-4 mb-0 table-hover">
                <thead>
                  <tr>
                    <th scope="col" className="border-0 rounded-start">پست</th>
                    <th scope="col" className="border-0">دسته‌بندی</th>
                    <th scope="col" className="border-0">بازدید</th>
                    <th scope="col" className="border-0">زمان مطالعه</th>
                    <th scope="col" className="border-0 rounded-end">عملیات</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredBlogs?.map((post) => (
                    <tr key={post.id}>
                      <td>
                        <div className="d-flex align-items-center">
                          <div className="w-100px">
                            <img
                              src={post.thumbnail ? getMediaUrl(post.thumbnail) : "/assets/images/event/08.jpg"}
                              className="rounded"
                              alt={post.title}
                              onClick={(e) => {
                                e.preventDefault();
                                router.push(`/blog/${post.id}`);
                              }}
                            />
                          </div>
                          <div className="mb-0 ms-2">
                            <h6>
                              <a href={`/blog/${post.id}`}>{post.title}</a>
                            </h6>
                            <div className="d-sm-flex">
                              <p className="h6 fw-light mb-0 small me-3">
                                <i className="fas fa-user text-orange me-2"></i>
                                {post.author.name}
                              </p>
                            </div>
                          </div>
                        </div>
                      </td>
                      <td>{post.category?.name || "عمومی"}</td>
                      <td>{post.view_count}</td>
                      <td>{post.ttr} دقیقه</td>
                      <td>
                        <a href={`/blog/${post.id}`} className="btn btn-sm btn-primary-soft me-1 mb-1 mb-md-0">
                          <i className="bi bi-eye me-1"></i>
                          مشاهده
                        </a>
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

export default function SavedBlogsPage() {
  return <DashboardBase Content={<SavedBlogsContent />} />;
}
