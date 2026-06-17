"use client";

import { motion } from "framer-motion";
import { fadeInUp, staggerContainer } from "@/src/core/motionVariants";
import Link from "next/link";
import { useRouter } from "next/navigation";
import LoadingSkeleton from "@/src/components/skeleton/loadingSkeleton";
import { useBlogs, type BlogPostCard } from "@/src/core/hooks/useBlogs";
import { getMediaUrl } from "@/src/core/utils";

function RecentBlogPostCard({ post }: { post: BlogPostCard }) {
  const router = useRouter();

  return (
    <motion.div className="col-sm-6 col-lg-4 col-xl-3" variants={fadeInUp} whileHover={{ y: -6, transition: { duration: 0.2 } }}>
      <div className="card action-trigger-hover border bg-transparent h-100">
        <div className="position-relative overflow-hidden rounded-top">
          <img
            src={post.thumbnail ? getMediaUrl(post.thumbnail) : "/assets/images/event/02.jpg"}
            className="card-img-top"
            alt={post.title}
            onClick={(e) => {
              e.preventDefault();
              router.push(`/blog/${post.slug}`);
            }}
            style={{ cursor: "pointer" }}
          />
        </div>

        <div className="card-body pb-0">
          <div className="d-flex justify-content-between mb-2">
            <span className="badge bg-purple bg-opacity-10 text-purple">{post.category?.name || "عمومی"}</span>
            <span className="small text-muted">{post.ttr} دقیقه</span>
          </div>

          <h5 className="card-title fw-normal">
            <Link href={`/blog/${post.slug}`}>{post.title}</Link>
          </h5>

          <p className="text-truncate-2" dangerouslySetInnerHTML={{ __html: post.short_description }}></p>
        </div>

        <div className="card-footer pt-0 bg-transparent">
          <hr />
          <div className="d-flex justify-content-between align-items-center">
            <span className="h6 fw-light mb-0">{post.author.name}</span>
            <span className="small text-muted">
              <i className="far fa-eye me-1"></i>
              {post.view_count}
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default function RecentBlogPosts() {
  const { blogsData, isLoadingBlogs } = useBlogs({ count: 8, sort: "newest" });

  return (
    <section>
      <div className="container">
        <motion.div
          className="row mb-4"
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, amount: 0.3 }}
          variants={fadeInUp}
        >
          <div className="col-lg-8 mx-auto text-center">
            <h2 className="fs-3">جدیدترین مطالب وبلاگ</h2>
            <p className="mb-0">آخرین پست های منتشرشده برای یادگیری سریع تر و عمیق تر</p>
          </div>
        </motion.div>

        <LoadingSkeleton
          isLoading={isLoadingBlogs}
          width="100%"
          height={360}
          count={4}
          Content={() => (
            <motion.div
              className="row g-4"
              variants={staggerContainer}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, amount: 0.05 }}
            >
              {blogsData?.posts.map((post) => (
                <RecentBlogPostCard key={post.id} post={post} />
              ))}
            </motion.div>
          )}
        />
      </div>
    </section>
  );
}
