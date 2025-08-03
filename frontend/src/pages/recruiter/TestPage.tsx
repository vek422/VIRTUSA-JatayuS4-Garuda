import React, { useState, useEffect } from "react";

import { useParams, useNavigate, Link } from "react-router-dom";
import {
  useGetTestByIdQuery,
  useUpdateTestMutation,
  useScheduleTestMutation,
  useDeleteTestMutation,
  useAddCandidateToAssessmentMutation,
} from "@/api/testApi";
import {
  useGetCandidatesByTestQuery,
  useDeleteCandidateMutation,
  useGetCandidateApplicationQuery,
} from "@/api/candidateApi";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Label } from "@/components/ui/label";
import {
  Calendar,
  Clock,
  Users,
  Network,
  Settings,
  CheckCircle,
  Loader2,
  Eye,
  Calendar as CalendarIcon,
  ChevronDown,
  ChevronUp,
  Activity,
  FileText,
  RefreshCcw,
} from "lucide-react";

import SkillGraphTab from "./Component/TestPage/SkillGraphTab";
import CandidateUpload from "./Component/TestPage/CandidateUpload";
import ShortlistingCard from "./Component/TestPage/ShortlistingCard";
import TestCandidateTable from "./Component/TestPage/CandidateTable/data-table";
import SettingsTab from "./Component/TestPage/SettingsTab";

const TestPage: React.FC = () => {
  const { testId } = useParams<{ testId: string }>();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState("overview");
  const [jobDescriptionExpanded, setJobDescriptionExpanded] = useState(false);

  const {
    data: candidates,
    refetch: refetchCandidates,
    isLoading: candidateLoading,
  } = useGetCandidatesByTestQuery(Number(testId!), { skip: !testId });
  console.log(candidateLoading);
  function hasUnsavedChanges(formState, test) {
    if (!formState || !test) return false;
    const fields = [
      "test_name",
      "job_description",
      "scheduled_at",
      "time_limit_minutes",
      "resume_score_threshold",
      "max_shortlisted_candidates",
      "auto_shortlist",
      "total_questions",
      "total_marks",
      "application_deadline",
      "assessment_deadline",
      "text",
    ];
    for (let i = 0; i < fields.length; i++) {
      const key = fields[i];
      if (formState[key] !== (test[key] !== undefined ? test[key] : "")) {
        return true;
      }
    }
    return false;
  }
  const {
    data: test,
    isLoading: testLoading,
    error: testError,
  } = useGetTestByIdQuery(Number(testId), { skip: !testId });
  const [updateTest, { isLoading: isUpdatingTest }] = useUpdateTestMutation();
  const [editMode, setEditMode] = useState(false);
  const [updateError, setUpdateError] = useState<string | null>(null);
  const [updateSuccess, setUpdateSuccess] = useState<string | null>(null);
  const [formState, setFormState] = useState<any>(null);
  const [sliderValues, setSliderValues] = useState<number[]>([33, 66]);

  useEffect(() => {
    if (test) {
      setFormState({
        test_name: test.test_name || "",
        job_description: test.job_description || "",
        scheduled_at: test.scheduled_at
          ? new Date(test.scheduled_at).toISOString().slice(0, 16)
          : "",
        time_limit_minutes: test.time_limit_minutes || "",
        resume_score_threshold: test.resume_score_threshold ?? "",
        max_shortlisted_candidates: test.max_shortlisted_candidates ?? "",
        auto_shortlist: !!test.auto_shortlist,
        total_questions: test.total_questions || 0,
        total_marks: test.total_marks || "",
        application_deadline: test.application_deadline
          ? new Date(test.application_deadline).toISOString().slice(0, 16)
          : "",
        assessment_deadline: test.assessment_deadline
          ? new Date(test.assessment_deadline).toISOString().slice(0, 16)
          : "",
        question_distribution: test.parsed_job_description
          ?.question_distribution || { low: 0, medium: 0, high: 0 },
      });

      const dist = test.parsed_job_description?.question_distribution || {
        low: 33,
        medium: 33,
        high: 34,
      };
      setSliderValues([dist.low, dist.low + dist.medium]);
    }
  }, [test]);
  useEffect(() => {
    if (!formState) return;
    const low = sliderValues[0];
    const medium = sliderValues[1] - sliderValues[0];
    const high = 100 - sliderValues[1];
    const l = Math.round((low / 100) * (formState.total_questions || 0));
    const m = Math.round((medium / 100) * (formState.total_questions || 0));
    const h = (formState.total_questions || 0) - l - m;
    setFormState((prev: any) => ({
      ...prev,
      question_distribution: { low: l, medium: m, high: h },
    }));
  }, [sliderValues, formState?.total_questions]);

  const handleFieldChange = (field: string, value: any) => {
    setFormState((prev: any) => ({ ...prev, [field]: value }));
    if (field === "total_questions") {
      const low = sliderValues[0];
      const medium = sliderValues[1] - sliderValues[0];
      const high = 100 - sliderValues[1];
      const l = Math.round((low / 100) * value);
      const m = Math.round((medium / 100) * value);
      const h = value - l - m;
      setFormState((prev: any) => ({
        ...prev,
        question_distribution: { low: l, medium: m, high: h },
      }));
    }
  };

  // const [viewResultId, setViewResultId] = useState<number | null>(null);
  // const {
  //   data: candidateResult,
  //   isLoading: resultLoading,
  //   error: resultError,
  // } = useGetCandidateApplicationQuery(viewResultId ?? 0, {
  //   skip: !viewResultId,
  // });

  // Normalize candidates from API to a consistent structure for the table
  const normalizedCandidates = React.useMemo(() => {
    if (!candidates) return [];
    return candidates.map((c: any, idx: number) => ({
      application_id: c["application_id"],
      name: c["candidate_name"] || "",
      email: c["candidate_email"] || "",
      resume_link: c["resume_link"],
      resume_score: c["resume_score"] ?? null,
      is_shortlisted: c["is_shortlisted"],
      screening_status: c["screening_status"] ?? null,
      key: (c["candidate_email"] || "") + (c["resume_score"] ?? idx),
    }));
  }, [candidates]);

  const handleDeleteTest = async () => {
    console.log("invoked");
    if (!testId || !test) return;
    if (test.status === "ongoing" || test.status === "scheduled") {
      alert(
        "Cannot Delete Test\n\nThis test is currently active and cannot be deleted. Please wait for the test to complete before attempting to delete it."
      );
      return;
    }

    const confirmMessage = `Delete Test Confirmation\n\nAre you sure you want to delete "${test.test_name}"?\n\nThis action cannot be undone and will permanently remove all associated data including:\n• Test questions and settings\n• Candidate submissions\n• Results and reports\n\nType "DELETE" to confirm.`;

    const userInput = prompt(confirmMessage + "\n\nType 'DELETE' to confirm:");

    if (userInput === "DELETE") {
      try {
        alert("Delete test API not implemented. Please contact the developer.");
        alert("Test deleted successfully!");
        navigate("/recruiter/tests"); // Navigate back to tests list
      } catch (error) {
        console.error("Failed to delete test:", error);
        alert("Failed to delete test. Please try again.");
      }
    } else if (userInput !== null) {
      alert("Deletion cancelled. You must type 'DELETE' exactly to confirm.");
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { color: string; label: string }> = {
      draft: { color: "bg-gray-200 text-gray-800", label: "Draft" },
      scheduled: { color: "bg-blue-100 text-blue-800", label: "Scheduled" },
      ongoing: { color: "bg-yellow-100 text-yellow-800", label: "Ongoing" },
      completed: { color: "bg-green-100 text-green-800", label: "Completed" },
      ended: { color: "bg-red-100 text-red-800", label: "Ended" },
      active: { color: "bg-green-100 text-green-800", label: "Active" },
      // fallback
      default: {
        color: "bg-gray-200 text-gray-800",
        label: status.charAt(0).toUpperCase() + status.slice(1),
      },
    };
    const config = statusConfig[status] || statusConfig["default"];
    return (
      <span
        className={`px-2 py-1 rounded text-xs font-semibold ${config.color}`}
      >
        {config.label}
      </span>
    );
  };

  const formatDate = (dateString?: string | null) => {
    if (!dateString) return "-";
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const [scheduleState, setScheduleState] = useState({
    scheduled_at: "",
    application_deadline: "",
    assessment_deadline: "",
  });

  const [scheduleTest, { isLoading: isScheduling }] = useScheduleTestMutation();

  const handleSchedule = async () => {
    setUpdateError(null);
    setUpdateSuccess(null);
    if (!testId) return;
    try {
      const { scheduled_at, application_deadline, assessment_deadline } =
        scheduleState;
      const payload: any = {};
      if (scheduled_at) payload.scheduled_at = scheduled_at;
      if (application_deadline)
        payload.application_deadline = application_deadline;
      if (assessment_deadline)
        payload.assessment_deadline = assessment_deadline;
      console.log("[ScheduleTest] Sending payload:", payload);
      await scheduleTest({ testId: Number(testId), data: payload }).unwrap();
      setUpdateSuccess("Test scheduled successfully!");
    } catch (e: any) {
      setUpdateError(e?.data?.message || "Failed to schedule test");
    }
  };

  if (testLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (testError || !test) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-2">Test not found</h2>
          <p className="text-muted-foreground">
            The test you're looking for doesn't exist.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header & Metadata Section */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <CardTitle className="text-2xl">{test.test_name}</CardTitle>
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <div className="flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  {formatDate(test.scheduled_at)}
                </div>
                <div className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  {test.time_limit_minutes} mins
                </div>
                <div className="flex items-center gap-1">
                  <CalendarIcon className="h-4 w-4" />
                  Created {formatDate(test.created_at)}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {getStatusBadge(test.status)}
              <div>
                {
                  <Link to={`/recruiter/test/${testId}/report`}>
                    <Button
                      variant={"outline"}
                      size={"sm"}
                      className="cursor-pointer"
                    >
                      <FileText />
                      View Report
                    </Button>
                  </Link>
                }
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label className="text-sm font-medium">Job Description</Label>
              <Button
                variant="ghost"
                size="sm"
                onClick={() =>
                  setJobDescriptionExpanded(!jobDescriptionExpanded)
                }
              >
                {jobDescriptionExpanded ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </Button>
            </div>
            <div
              className={`text-sm text-muted-foreground ${
                jobDescriptionExpanded ? "" : "line-clamp-3"
              }`}
            >
              {test.job_description}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs Navigation */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <Eye className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="candidates" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Candidates
          </TabsTrigger>
          <TabsTrigger value="skill-graph" className="flex items-center gap-2">
            <Network className="h-4 w-4" />
            Skill Graph
          </TabsTrigger>
          <TabsTrigger value="settings" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Settings
          </TabsTrigger>
        </TabsList>
        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card className="bg-gradient-to-br from-blue-50 to-blue-200 dark:from-blue-900 dark:to-blue-800 border-0 shadow-md">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg text-blue-900 dark:text-blue-200 flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-500" /> Test Status
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-blue-900 dark:text-blue-100">
                    Test Created
                  </span>
                  <CheckCircle className="h-4 w-4 text-green-500" />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-blue-900 dark:text-blue-100">
                    Resume Parsing
                  </span>
                  <div className="flex items-center gap-1">
                    {(() => {
                      const total = candidates?.length || 0;
                      const completed =
                        candidates?.filter(
                          (c) => c.screening_status === "completed"
                        ).length || 0;
                      const pending =
                        candidates?.filter(
                          (c) => c.screening_status === "pending"
                        ).length || 0;
                      return (
                        <>
                          <span className="text-xs text-blue-700 dark:text-blue-200">
                            {completed}/{total}
                          </span>
                          {pending > 0 && (
                            <Loader2 className="h-4 w-4 text-blue-500 animate-spin ml-1" />
                          )}
                        </>
                      );
                    })()}
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-blue-900 dark:text-blue-100">
                    Graph Generation
                  </span>
                  <CheckCircle className="h-4 w-4 text-green-500" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-purple-50 to-purple-200 dark:from-purple-900 dark:to-purple-800 border-0 shadow-md">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg text-purple-900 dark:text-purple-200 flex items-center gap-2">
                  <Users className="h-5 w-5 text-purple-500" /> Candidates
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-extrabold text-purple-900 dark:text-purple-100">
                  {candidates?.length || 0}
                </div>
                <p className="text-sm text-purple-700 dark:text-purple-200">
                  Total candidates
                </p>
                <div className="mt-2 text-sm">
                  <div className="flex justify-between">
                    <span className="font-semibold text-purple-800 dark:text-purple-200">
                      Completed:
                    </span>
                    <span className="font-semibold text-purple-800 dark:text-purple-200">
                      {candidates?.filter((c) => c.score !== null).length || 0}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-semibold text-purple-800 dark:text-purple-200">
                      Shortlisted:
                    </span>
                    <span className="font-semibold text-purple-800 dark:text-purple-200">
                      {candidates?.filter((c) => c.is_shortlisted).length || 0}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>{" "}
        {/* Candidates Tab */}
        <TabsContent value="candidates" className="space-y-6">
          <CandidateUpload refetchCandidates={refetchCandidates} />
          <ShortlistingCard
            refetchCandidates={refetchCandidates}
            normalizedCandidates={normalizedCandidates}
          />

          {/* Candidates Table */}
          <Card>
            <CardHeader className="flex justify-between">
              <div>
                <CardTitle>Candidates</CardTitle>
                <CardDescription>
                  View and manage all candidates for this test
                </CardDescription>
              </div>
              <Button
                onClick={() => refetchCandidates()}
                disabled={candidateLoading}
                variant={"outline"}
              >
                <RefreshCcw
                  className={candidateLoading ? "animate-spin" : ""}
                />
                refresh
              </Button>
            </CardHeader>
            <CardContent>
              <TestCandidateTable
                data={normalizedCandidates.map((candidate) => ({
                  name: candidate.name,
                  email: candidate.email,
                  resume_link: candidate.resume_link,
                  score: candidate.resume_score || 0,
                  is_shortlisted: candidate.is_shortlisted,
                  screening_status: candidate.screening_status || "N/A",
                  application_id: String(candidate.application_id),
                }))}
              />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="skill-graph" className="space-y-6">
          <SkillGraphTab test={test} />
        </TabsContent>{" "}
        <TabsContent value="settings" className="space-y-6">
          <SettingsTab
            test={test}
            testId={testId!}
            scheduleState={scheduleState}
            setScheduleState={setScheduleState}
            formState={formState}
            handleFieldChange={handleFieldChange}
            handleSchedule={handleSchedule}
            isScheduling={isScheduling}
            updateError={updateError}
            updateSuccess={updateSuccess}
            formatDate={formatDate}
            getStatusBadge={getStatusBadge}
            updateTest={updateTest}
            isUpdatingTest={isUpdatingTest}
            hasUnsavedChanges={hasUnsavedChanges}
            setUpdateError={setUpdateError}
            setUpdateSuccess={setUpdateSuccess}
            setEditMode={setEditMode}
            setFormState={setFormState}
            handleDeleteTest={handleDeleteTest}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default TestPage;
