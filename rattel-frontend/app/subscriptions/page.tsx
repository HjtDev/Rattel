"use client";

import { motion, useReducedMotion } from "framer-motion";
import { useCart } from "@/src/core/hooks/useCart";
import { useSubscriptionPlans, Plan } from "@/src/core/hooks/useSubscriptionPlans";
import { useMySubscription } from "@/src/core/hooks/useMySubscription";
import { useAuth } from "@/src/core/hooks/useAuth";
import { getMediaUrl } from "@/src/core/utils";
import { toast } from "react-toastify";
import { fadeInUp, staggerContainer, scaleIn } from "@/src/core/motionVariants";

const formatPrice = (price: number) =>
    new Intl.NumberFormat("fa-IR").format(price);

const formatDuration = (days: number) => {
    if (days % 365 === 0) return `${days / 365} ساله`;
    if (days % 30 === 0) return `${days / 30} ماهه`;
    return `${days} روزه`;
};

const onlineClassLabel = (limit: Plan["online_class_limit"]) => {
    if (limit === 0) return null;
    return `حداکثر ${new Intl.NumberFormat("fa-IR").format(limit)} جلسه آنلاین در ماه`;
};

function FeatureRow({ label, plans, check }: { label: string; plans: Plan[]; check: (p: Plan) => boolean }) {
    return (
        <div className="row align-items-center p-3">
            <div className="col-md-6 text-center text-md-start">
                <h6 className="mb-3 mb-md-0 fw-normal">{label}</h6>
            </div>
            <div className="col-md-6 pt-2 pt-md-0">
                <div className="row">
                    {plans.map((plan) => (
                        <div key={plan.id} className={`col-${Math.floor(12 / plans.length)} d-flex justify-content-center`}>
                            {check(plan) ? (
                                <div className="icon-md bg-success bg-opacity-10 rounded-circle text-success">
                                    <i className="fas fa-check" />
                                </div>
                            ) : (
                                <div className="icon-md bg-danger bg-opacity-10 rounded-circle text-danger">
                                    <i className="fas fa-times" />
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

interface PlanCardProps {
    plan: Plan;
    activePlanId: string | null;
    hasActiveSub: boolean;
}

function PlanCard({ plan, activePlanId, hasActiveSub }: PlanCardProps) {
    const { items: cartItems, add: addToCart, remove: removeFromCart } = useCart();

    const isCurrentPlan = activePlanId === plan.id;
    const isInCart = cartItems.some(
        (item) =>
            item.app_label === "subscriptions" &&
            item.model === "plan" &&
            item.object_id === plan.id
    );

    const handleCartToggle = async () => {
        if (hasActiveSub) {
            toast.warning("شما در حال حاضر یک اشتراک فعال دارید");
            return;
        }

        if (isInCart) {
            const result = await removeFromCart("subscriptions", "plan", plan.id);
            if (result.success) {
                toast.info("پلن از سبد خرید حذف شد");
            } else {
                toast.error(result.message);
            }
            return;
        }

        const existingPlanInCart = cartItems.find(
            (item) => item.app_label === "subscriptions" && item.model === "plan"
        );
        if (existingPlanInCart) {
            await removeFromCart("subscriptions", "plan", existingPlanInCart.object_id);
        }

        const result = await addToCart("subscriptions", "plan", plan.id, 1, {
            name: plan.name,
            picture: plan.picture ? getMediaUrl(plan.picture) : null,
            price: plan.price,
            new_price: plan.new_price,
        });

        if (result.success) {
            if (existingPlanInCart) {
                toast.info("پلن قبلی با پلن جدید جایگزین شد");
            } else {
                toast.success("پلن به سبد خرید اضافه شد");
            }
        } else {
            toast.error(result.message);
        }
    };

    const classLabel = onlineClassLabel(plan.online_class_limit);

    return (
        <div className={`card border rounded-3 p-2 p-sm-4 h-100 ${isCurrentPlan ? "border-success border-2" : ""}`}>
            <div className="card-header p-0">
                <div className="d-flex justify-content-between align-items-center p-3 bg-light rounded-2">
                    <div>
                        <h5 className="mb-1">{plan.name}</h5>
                        <span className="badge text-bg-dark rounded-pill">
                            {formatDuration(plan.duration_days)}
                        </span>
                    </div>
                    <div className="text-end">
                        {plan.discount > 0 && (
                            <>
                                <span className="badge bg-danger mb-1 d-block">
                                    {new Intl.NumberFormat("fa-IR").format(plan.discount)}% تخفیف
                                </span>
                                <div className="text-muted text-decoration-line-through small">
                                    {formatPrice(plan.price)} تومان
                                </div>
                            </>
                        )}
                        <h4 className="text-success mb-0">
                            {formatPrice(plan.new_price > 0 ? plan.new_price : plan.price)} تومان
                        </h4>
                    </div>
                </div>
            </div>

            {plan.picture && (
                <div className="text-center my-3">
                    <img
                        src={getMediaUrl(plan.picture)}
                        alt={plan.name}
                        className="rounded-3"
                        style={{ maxHeight: "120px", objectFit: "contain" }}
                    />
                </div>
            )}

            <div className="position-relative my-3 text-center">
                <hr />
                <p className="small position-absolute top-50 start-50 translate-middle bg-body px-3">
                    امکانات
                </p>
            </div>

            <div className="card-body pt-0">
                <ul className="list-unstyled mt-2 mb-0">
                    <li className="mb-3 h6 fw-light">
                        {plan.has_early_news_access ? (
                            <i className="bi bi-patch-check-fill text-success me-2" />
                        ) : (
                            <i className="bi bi-x-octagon-fill text-danger me-2" />
                        )}
                        دریافت اخبار زودتر
                    </li>
                    <li className="mb-3 h6 fw-light">
                        {plan.has_quiz_access ? (
                            <i className="bi bi-patch-check-fill text-success me-2" />
                        ) : (
                            <i className="bi bi-x-octagon-fill text-danger me-2" />
                        )}
                        دسترسی به بخش آزمون
                    </li>
                    <li className="h6 fw-light">
                        {plan.online_class_limit > 0 ? (
                            <>
                                <i className="bi bi-patch-check-fill text-success me-2" />
                                {classLabel}
                            </>
                        ) : (
                            <>
                                <i className="bi bi-x-octagon-fill text-danger me-2" />
                                کلاس آنلاین
                            </>
                        )}
                    </li>
                </ul>
            </div>

            <div className="card-footer pb-0">
                {isCurrentPlan ? (
                    <div className="text-center py-2">
                        <span className="badge bg-success bg-opacity-10 text-success border border-success rounded-pill px-3 py-2">
                            <i className="bi bi-check-circle-fill me-2" />
                            پلن فعال شما
                        </span>
                    </div>
                ) : (
                    <div className="d-grid">
                        <button
                            type="button"
                            className={`btn mb-0 ${hasActiveSub ? "btn-secondary disabled" : isInCart ? "btn-outline-danger" : "btn-primary"}`}
                            onClick={handleCartToggle}
                            disabled={hasActiveSub}
                        >
                            {hasActiveSub
                                ? "اشتراک فعال دارید"
                                : isInCart
                                ? "حذف از سبد خرید"
                                : "افزودن به سبد خرید"}
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

function PlanCardSkeleton() {
    return (
        <div className="card border rounded-3 p-2 p-sm-4 h-100">
            <div className="card-header p-0">
                <div className="d-flex justify-content-between align-items-center p-3 bg-light rounded-2">
                    <div style={{ width: "40%" }}>
                        <div className="skeleton-loader rounded mb-2" style={{ height: "24px" }} />
                        <div className="skeleton-loader rounded" style={{ height: "20px", width: "60%" }} />
                    </div>
                    <div style={{ width: "35%" }}>
                        <div className="skeleton-loader rounded" style={{ height: "32px" }} />
                    </div>
                </div>
            </div>
            <div className="card-body pt-3">
                {[1, 2, 3].map((i) => (
                    <div key={i} className="skeleton-loader rounded mb-3" style={{ height: "20px" }} />
                ))}
            </div>
            <div className="card-footer d-grid pb-0">
                <div className="skeleton-loader rounded" style={{ height: "40px" }} />
            </div>
        </div>
    );
}

export default function Subscriptions() {
    const { plans, isLoading, error } = useSubscriptionPlans();
    const { isAuthenticated } = useAuth();
    const { subscription, isLoading: isLoadingSub } = useMySubscription();
    const shouldReduceMotion = useReducedMotion();

    const hasActiveSub = isAuthenticated && !isLoadingSub && subscription?.is_active === true;
    const activePlanId = hasActiveSub ? subscription!.plan.id : null;

    const colClass =
        plans.length === 1
            ? "col-md-6 col-xl-4 mx-auto"
            : plans.length === 2
            ? "col-md-6 col-xl-5"
            : "col-md-6 col-xl-4";

    // Shared viewport props — reused across all whileInView blocks
    const vp = { once: true };
    const initial = shouldReduceMotion ? false : "hidden";

    return (
        <main>
            <section className="py-5 price-wrap">
                <div className="container">

                    {/* Hero header */}
                    <motion.div
                        className="row g-4 position-relative mb-4"
                        variants={staggerContainer}
                        initial={initial}
                        whileInView="show"
                        viewport={vp}
                    >
                        <figure className="position-absolute top-0 start-0 d-none d-sm-block">
                            <svg width="22px" height="22px" viewBox="0 0 22 22">
                                <polygon
                                    className="fill-purple"
                                    points="22,8.3 13.7,8.3 13.7,0 8.3,0 8.3,8.3 0,8.3 0,13.7 8.3,13.7 8.3,22 13.7,22 13.7,13.7 22,13.7"
                                />
                            </svg>
                        </figure>
                        <div className="col-lg-10 mx-auto text-center position-relative">
                            <figure className="position-absolute top-50 end-0 translate-middle-y d-none d-md-block">
                                <svg width="27px" height="27px">
                                    <path
                                        className="fill-orange"
                                        d="M13.122,5.946 L17.679,-0.001 L17.404,7.528 L24.661,5.946 L19.683,11.533 L26.244,15.056 L18.891,16.089 L21.686,23.068 L15.400,19.062 L13.122,26.232 L10.843,19.062 L4.557,23.068 L7.352,16.089 L-0.000,15.056 L6.561,11.533 L1.582,5.946 L8.839,7.528 L8.565,-0.001 L13.122,5.946 Z"
                                    />
                                </svg>
                            </figure>
                            <motion.h1 className="fs-2" variants={fadeInUp}>
                                پکیج های اشتراکی
                            </motion.h1>
                            <motion.p className="mb-0" variants={fadeInUp}>
                                با خرید اشتراک به امکانات ویژه دسترسی پیدا کنید
                            </motion.p>
                        </div>
                    </motion.div>

                    {/* Active subscription banner */}
                    {hasActiveSub && subscription && (
                        <motion.div
                            className="alert alert-success text-center mb-4"
                            role="alert"
                            variants={fadeInUp}
                            initial={initial}
                            whileInView="show"
                            viewport={vp}
                        >
                            <i className="bi bi-check-circle-fill me-2" />
                            اشتراک فعال شما: <strong>{subscription.plan.name}</strong> — تا تاریخ{" "}
                            <strong>
                                {new Intl.DateTimeFormat("fa-IR").format(new Date(subscription.ends_in))}
                            </strong>
                        </motion.div>
                    )}

                    {error && (
                        <div className="alert alert-danger text-center" role="alert">
                            {error}
                        </div>
                    )}

                    {/* Plan cards grid */}
                    <div className={`row g-4 ${plans.length < 3 ? "justify-content-center" : ""}`}>
                        {isLoading
                            ? [1, 2, 3].map((i) => (
                                  <div key={i} className="col-md-6 col-xl-4">
                                      <PlanCardSkeleton />
                                  </div>
                              ))
                            : plans.map((plan, index) => (
                                  <motion.div
                                      key={plan.id}
                                      className={colClass}
                                      initial={initial}
                                      animate="show"
                                      variants={fadeInUp}
                                      transition={{
                                          duration: 0.55,
                                          ease: "easeOut",
                                          delay: shouldReduceMotion ? 0 : index * 0.12,
                                      }}
                                      whileHover={
                                          shouldReduceMotion
                                              ? undefined
                                              : { y: -6, transition: { duration: 0.2 } }
                                      }
                                  >
                                      <PlanCard
                                          plan={plan}
                                          activePlanId={activePlanId}
                                          hasActiveSub={hasActiveSub}
                                      />
                                  </motion.div>
                              ))}
                    </div>
                </div>
            </section>

            {/* Feature comparison table */}
            {!isLoading && plans.length > 0 && (
                <section className="pb-5">
                    <div className="container">

                        {/* Section heading */}
                        <motion.div
                            className="row"
                            variants={fadeInUp}
                            initial={initial}
                            whileInView="show"
                            viewport={vp}
                        >
                            <div className="col-md-8 text-center mx-auto mb-4">
                                <h2 className="fs-4">مقایسه امکانات</h2>
                            </div>
                        </motion.div>

                        <div className="row">
                            <div className="col-lg-10 mx-auto">

                                {/* Table header */}
                                <motion.div
                                    className="row"
                                    variants={scaleIn}
                                    initial={initial}
                                    whileInView="show"
                                    viewport={vp}
                                >
                                    <div className="col-12 bg-light p-3 rounded-3">
                                        <div className="row align-items-center">
                                            <div className="col-md-6 text-center text-md-start">
                                                <h5 className="mb-2 mb-md-0">ویژگی</h5>
                                            </div>
                                            <div className="col-md-6">
                                                <div className="row">
                                                    {plans.map((plan) => (
                                                        <div
                                                            key={plan.id}
                                                            className={`col-${Math.floor(12 / plans.length)} text-center py-2`}
                                                        >
                                                            <h6 className="mb-0">{plan.name}</h6>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>

                                {/* Feature rows — staggered */}
                                <motion.div
                                    variants={staggerContainer}
                                    initial={initial}
                                    whileInView="show"
                                    viewport={vp}
                                >
                                    {[
                                        { label: "دریافت اخبار زودتر", check: (p: Plan) => p.has_early_news_access },
                                        { label: "دسترسی به بخش آزمون", check: (p: Plan) => p.has_quiz_access },
                                        { label: "کلاس آنلاین (حداقل ۴ جلسه)", check: (p: Plan) => p.online_class_limit >= 4 },
                                        { label: "کلاس آنلاین (حداقل ۸ جلسه)", check: (p: Plan) => p.online_class_limit >= 8 },
                                        { label: "کلاس آنلاین (حداقل ۱۲ جلسه)", check: (p: Plan) => p.online_class_limit >= 12 },
                                    ].map((row, i) => (
                                        <motion.div key={i} variants={fadeInUp}>
                                            <FeatureRow label={row.label} plans={plans} check={row.check} />
                                            {i < 4 && <hr className="m-0" />}
                                        </motion.div>
                                    ))}
                                </motion.div>

                            </div>
                        </div>
                    </div>
                </section>
            )}
        </main>
    );
}
