import LoadingSkeleton from "@/src/components/skeleton/loadingSkeleton";

interface Link {
    name: string;
    logo: string | null;
    url: string;
}

interface StatsSection {
    stat1_title: string;
    stat1_description: string;
    stat1_link: Link | null;
    stat2_title: string;
    stat2_description: string;
    stat2_link: Link | null;
    stat3_title: string;
    stat3_description: string;
    stat3_link: Link | null;
    stat4_title: string;
    stat4_description: string;
    stat4_link: Link | null;
}

interface StatisticsProps {
    data: StatsSection | null;
    isLoading: boolean;
}

export default function Statistics({ data, isLoading }: StatisticsProps) {
  return (
      <section className="py-0 py-xl-5">
        <div className="container">
          <div className="row g-4">
            <div className="col-sm-6 col-xl-3">
              <div
                  className="d-flex justify-content-center align-items-center p-4 bg-warning bg-opacity-15 rounded-3">
          <span className="display-6 lh-1 text-warning mb-0">
            <i className="fas fa-tv">
            </i>
          </span>
                <div className="ms-4 h6 fw-normal mb-0">
                  <div className="d-flex">
                    <LoadingSkeleton isLoading={isLoading} Content={() => (
                        <a href={data?.stat1_link?.url}>
                            <h5 className="mb-0 fw-bold">
                                {data?.stat1_title}
                            </h5>
                        </a>
                    )} width={80} height={28} />
                  </div>
                  <LoadingSkeleton isLoading={isLoading} Content={() => (
                    <p className="mb-0">
                      {data?.stat1_description}
                    </p>
                  )} width={100} height={20} />
                </div>
              </div>
            </div>
            <div className="col-sm-6 col-xl-3">
              <div className="d-flex justify-content-center align-items-center p-4 bg-blue bg-opacity-10 rounded-3">
          <span className="display-6 lh-1 text-blue mb-0">
            <i className="fas fa-user-tie">
            </i>
          </span>
                <div className="ms-4 h6 fw-normal mb-0">
                  <div className="d-flex">
                    <LoadingSkeleton isLoading={isLoading} Content={() => (
                        <a href={data?.stat2_link?.url}>
                            <h5 className="mb-0 fw-bold">
                                {data?.stat2_title}
                            </h5>
                        </a>
                    )} width={80} height={28} />
                  </div>
                  <LoadingSkeleton isLoading={isLoading} Content={() => (
                    <p className="mb-0">
                      {data?.stat2_description}
                    </p>
                  )} width={100} height={20} />
                </div>
              </div>
            </div>
            <div className="col-sm-6 col-xl-3">
              <div className="d-flex justify-content-center align-items-center p-4 bg-purple bg-opacity-10 rounded-3">
          <span className="display-6 lh-1 text-purple mb-0">
            <i className="fas fa-user-graduate">
            </i>
          </span>
                <div className="ms-4 h6 fw-normal mb-0">
                  <div className="d-flex">
                    <LoadingSkeleton isLoading={isLoading} Content={() => (
                        <a href={data?.stat3_link?.url}>
                            <h5 className="mb-0 fw-bold">
                                {data?.stat3_title}
                            </h5>
                        </a>
                    )} width={80} height={28} />
                  </div>
                  <LoadingSkeleton isLoading={isLoading} Content={() => (
                    <p className="mb-0">
                      {data?.stat3_description}
                    </p>
                  )} width={100} height={20} />
                </div>
              </div>
            </div>
            <div className="col-sm-6 col-xl-3">
              <div className="d-flex justify-content-center align-items-center p-4 bg-info bg-opacity-10 rounded-3">
          <span className="display-6 lh-1 text-info mb-0">
            <i className="bi bi-patch-check-fill">
            </i>
          </span>
                <div className="ms-4 h6 fw-normal mb-0">
                  <div className="d-flex">
                    <LoadingSkeleton isLoading={isLoading} Content={() => (
                        <a href={data?.stat4_link?.url}>
                            <h5 className="mb-0 fw-bold">
                                {data?.stat4_title}
                            </h5>
                        </a>
                    )} width={80} height={28} />
                  </div>
                  <LoadingSkeleton isLoading={isLoading} Content={() => (
                    <p className="mb-0">
                      {data?.stat4_description}
                    </p>
                  )} width={100} height={20} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
  );
}
