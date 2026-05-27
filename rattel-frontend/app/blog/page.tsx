"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { type BlogSortOption, useBlogMeta, useBlogs } from "@/src/core/hooks/useBlogs";
import { getMediaUrl } from "@/src/core/utils";

function BlogListContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [page, setPage] = useState(Number(searchParams.get("page")) || 1);
  const [sort, setSort] = useState<BlogSortOption | undefined>((searchParams.get("sort") as BlogSortOption) || undefined);
  const [category, setCategory] = useState<string | undefined>(searchParams.get("category") || undefined);
  const [tag, setTag] = useState<string | undefined>(searchParams.get("tag") || undefined);
  const [search, setSearch] = useState<string>(searchParams.get("search") || "");

  const { categories, tags } = useBlogMeta();
  const { blogsData, isLoadingBlogs } = useBlogs({
    page,
    count: 12,
    sort,
    category,
    tag,
    search: search || undefined,
  });

  useEffect(() => {
    const params = new URLSearchParams();
    if (page > 1) params.set("page", String(page));
    if (sort) params.set("sort", sort);
    if (category) params.set("category", category);
    if (tag) params.set("tag", tag);
    if (search) params.set("search", search);

    const queryString = params.toString();
    router.push(`/blog${queryString ? `?${queryString}` : ""}`, { scroll: false });
  }, [page, sort, category, tag, search, router]);

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const renderPagination = () => {
    if (!blogsData || !blogsData.total_pages || blogsData.total_pages <= 1) return null;

    const pages = [];
    const totalPages = blogsData.total_pages;
    const currentPage = blogsData.page;

    pages.push(
      <li key="prev" className={`page-item mb-0 ${!blogsData.has_previous ? "disabled" : ""}`}>
        <a className="page-link" href="#" onClick={(e) => { e.preventDefault(); if (blogsData.has_previous) handlePageChange(currentPage - 1); }}>
          <i className="fas fa-angle-double-right"></i>
        </a>
      </li>
    );

    for (let i = 1; i <= totalPages; i += 1) {
      if (i === 1 || i === totalPages || (i >= currentPage - 1 && i <= currentPage + 1)) {
        pages.push(
          <li key={i} className={`page-item mb-0 ${i === currentPage ? "active" : ""}`}>
            <a className="page-link" href="#" onClick={(e) => { e.preventDefault(); handlePageChange(i); }}>{i}</a>
          </li>
        );
      } else if (i === currentPage - 2 || i === currentPage + 2) {
        pages.push(<li key={i} className="page-item mb-0 disabled"><span className="page-link">..</span></li>);
      }
    }

    pages.push(
      <li key="next" className={`page-item mb-0 ${!blogsData.has_next ? "disabled" : ""}`}>
        <a className="page-link" href="#" onClick={(e) => { e.preventDefault(); if (blogsData.has_next) handlePageChange(currentPage + 1); }}>
          <i className="fas fa-angle-double-left"></i>
        </a>
      </li>
    );

    return pages;
  };

  return (
    <main>
      <section className="py-5">
        <div className="container">
          <div className="row position-relative">
            <div className="col-lg-10 mx-auto text-center position-relative">
              <h1 className="fs-2">لیست وبلاگ</h1>
              <div className="d-flex justify-content-center position-relative">
                <nav aria-label="breadcrumb">
                  <ol className="breadcrumb mb-0">
                    <li className="breadcrumb-item"><Link href="/">صفحه اصلی</Link></li>
                    <li className="breadcrumb-item active" aria-current="page">لیست وبلاگ</li>
                  </ol>
                </nav>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="position-relative pt-0 pt-lg-2 pb-5">
        <div className="container">
          <div className="row g-3 align-items-center mb-4">
            <div className="col-md-4">
              <h4 className="mb-0 fs-6 fw-normal">
                {blogsData ? `نمایش ${((blogsData.page - 1) * blogsData.page_size) + 1}-${Math.min(blogsData.page * blogsData.page_size, blogsData.total)} از ${blogsData.total} نتیجه` : "در حال بارگذاری..."}
              </h4>
            </div>
            <div className="col-md-8">
              <div className="row g-2 justify-content-md-end">
                <div className="col-sm-4">
                  <select className="form-select text-rtl" value={sort || ""} onChange={(e) => { setSort((e.target.value as BlogSortOption) || undefined); setPage(1); }}>
                    <option value="">مرتب سازی</option>
                    <option value="newest">جدیدترین</option>
                    <option value="oldest">قدیمی‌ترین</option>
                    <option value="most_views">بیشترین بازدید</option>
                    <option value="least_views">کمترین بازدید</option>
                    <option value="most_read">بیشترین زمان مطالعه</option>
                  </select>
                </div>
                <div className="col-sm-4">
                  <select className="form-select text-rtl" value={category || ""} onChange={(e) => { setCategory(e.target.value || undefined); setPage(1); }}>
                    <option value="">دسته‌بندی</option>
                    {categories.map((item) => (
                      <option key={item.slug} value={item.slug}>{item.name}</option>
                    ))}
                  </select>
                </div>
                <div className="col-sm-4">
                  <select className="form-select text-rtl" value={tag || ""} onChange={(e) => { setTag(e.target.value || undefined); setPage(1); }}>
                    <option value="">برچسب</option>
                    {tags.map((item) => (
                      <option key={item.slug} value={item.slug}>{item.name}</option>
                    ))}
                  </select>
                </div>
                <div className="col-12">
                  <input
                    className="form-control"
                    placeholder="جستجو در عنوان و محتوا"
                    value={search}
                    onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="row g-4">
            {isLoadingBlogs ? (
              <div className="col-12 text-center py-5">
                <div className="spinner-border text-primary" role="status"><span className="visually-hidden">در حال بارگذاری...</span></div>
              </div>
            ) : blogsData?.posts.length === 0 ? (
              <div className="col-12 text-center py-5 text-muted">پستی یافت نشد</div>
            ) : (
              blogsData?.posts.map((post) => (
                <div key={post.id} className="col-sm-6 col-lg-4 col-xl-3">
                  <div className="card bg-transparent h-100">
                    <div className="overflow-hidden rounded-3 position-relative" onClick={(e) => {e.preventDefault(); router.push(`/blog/${post.slug}`);}}>
                      <img src={post.thumbnail ? getMediaUrl(post.thumbnail) : "/assets/images/event/02.jpg"} className="card-img" alt={post.title} />
                      <div className="bg-overlay bg-dark opacity-4"></div>
                      <div className="card-img-overlay d-flex align-items-start justify-content-between p-3">
                        <span className="badge text-bg-success">{post.category?.name || "عمومی"}</span>
                      </div>
                    </div>
                    <div className="card-body">
                      <h5 className="card-title fw-normal"><Link href={`/blog/${post.slug}`}>{post.title}</Link></h5>
                      <p className="text-truncate-2" dangerouslySetInnerHTML={{ __html: post.short_description }}></p>
                      <div className="d-flex justify-content-between align-items-center">
                        <h6 className="mb-0 fw-normal">{post.author.name}</h6>
                        <span className="small">{post.ttr} دقیقه</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {blogsData && blogsData.total_pages && blogsData.total_pages > 1 && (
            <nav className="d-flex justify-content-center mt-5" aria-label="navigation">
              <ul className="pagination pagination-primary-soft rounded mb-0">{renderPagination()}</ul>
            </nav>
          )}
        </div>
      </section>
    </main>
  );
}

export default function BlogList() {
  return (
    <Suspense fallback={null}>
      <BlogListContent />
    </Suspense>
  );
}
