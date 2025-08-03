import { useNavigate } from "react-router-dom";
import { useProfileQuery } from "@/api/authApi";
import { useGetCandidateAssessmentsQuery } from "@/api/candidateApi";
import { AssignedTestCard } from "./components/AssignedTestCard";
import { EmptyState } from "./components/EmptyState";
import { motion } from "motion/react";
import { User } from "lucide-react";

export default function CandidateHomePage() {
  const navigate = useNavigate();

  // Get candidate info from Redux auth state

  // Fetch profile data from API
  const { data: profile } = useProfileQuery();
  const candidateName = profile?.name || "Candidate";
  const candidateId = profile?.user_id;

  // Fetch assessments/tests for candidate
  const {
    data: assessments = [],
    isLoading,
    isError,
    refetch,
  } = useGetCandidateAssessmentsQuery(candidateId || 0, { skip: !candidateId });

  const getCountdownText = (scheduledDate: Date): string | undefined => {
    const now = new Date();
    const timeDiff = scheduledDate.getTime() - now.getTime();

    if (timeDiff <= 0) return undefined;

    const days = Math.floor(timeDiff / (1000 * 60 * 60 * 24));
    const hours = Math.floor(
      (timeDiff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)
    );
    const minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60));

    if (days > 0) {
      return `${days}d ${hours}h`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  };
  const handleTestAction = (testId: string, status: string) => {
    // Handle test actions based on status
    console.log(`Action for test ${testId} with status ${status}`);

    if (status === "completed" || status === "finished") {
      // Navigate to results/report page (if available)
      navigate(`/candidate/test/${testId}/results`);
    } else if (
      status === "ongoing" ||
      status === "in-progress" ||
      status === "started" ||
      status === "live" ||
      status === "active" ||
      status === "available" ||
      status === "scheduled"
    ) {
      // Navigate to test interface
      navigate(`/candidate/test/${testId}`);
    }
  };

  const handleRefresh = () => {
    // Refresh tests data
    console.log("Refreshing tests...");
    // Add your refresh logic here
    refetch();
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Header Section */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-8"
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="flex items-center justify-center w-12 h-12 rounded-full bg-primary/10">
              <User className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">
                Welcome back, {candidateName}!
              </h1>
              <p className="text-muted-foreground mt-1">
                Here are the upcoming assessments you're assigned to.
              </p>
            </div>
          </div>
        </motion.div>

        {/* Main Content */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <h2 className="text-2xl font-semibold mb-6">Upcoming Assessments</h2>

          {isLoading ? (
            <div>Loading assessments...</div>
          ) : isError ? (
            <EmptyState onRefresh={handleRefresh} />
          ) : assessments.length === 0 ? (
            <EmptyState onRefresh={handleRefresh} />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {assessments
                .filter((test: any) => test.status !== "completed")
                .map((test: any, index: number) => {
                  const scheduledDate = new Date(test.scheduled_at);
                  const now = new Date();
                  const isScheduled =
                    test.status === "scheduled" && scheduledDate > now;
                  const isLive = test.status === "ongoing";
                  const countdown = isScheduled
                    ? getCountdownText(scheduledDate)
                    : undefined;
                  return (
                    <motion.div
                      key={test.id || test.test_id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: index * 0.1 }}
                    >
                      <AssignedTestCard
                        testName={test.test_name || test.testName || test.name}
                        jobDescription={test.job_description}
                        scheduledTime={scheduledDate.toLocaleString()}
                        scheduledAt={test.scheduled_at}
                        duration={
                          test.duration
                            ? `${test.duration} mins`
                            : `${Math.round(
                                (new Date(test.assessment_deadline).getTime() -
                                  scheduledDate.getTime()) /
                                  60000
                              )} mins`
                        }
                        deadline={new Date(
                          test.assessment_deadline
                        ).toLocaleString()}
                        status={test.status || "scheduled"}
                        showStartButton={isLive}
                        onAction={() =>
                          handleTestAction(
                            test.id || test.test_id,
                            test.status || "scheduled"
                          )
                        }
                      />
                    </motion.div>
                  );
                })}
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
