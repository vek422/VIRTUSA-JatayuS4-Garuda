import { useRef } from "react";
import { format } from "date-fns";
import { useReactToPrint } from "react-to-print";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import SpiderChart from "@/components/SpiderChart";
import {
  CheckCircle,
  XCircle,
  TrendingUp,
  Brain,
  Target,
  Download,
  ArrowLeft,
  AlertCircle,
  BookOpen,
  Users,
  Lightbulb,
  GraduationCap,
} from "lucide-react";
import {
  useGenerateAssessmentReportMutation,
  useGetAssessmentReportQuery,
  type AssessmentReportData,
} from "@/api/assessmentApi";
import { useParams } from "react-router-dom";

// Component for displaying strengths and weaknesses
function StrengthsWeaknessesSection({
  strengths,
  weaknesses,
}: {
  strengths: string[];
  weaknesses: string[];
}) {
  return (
    <div className="grid md:grid-cols-2 gap-6">
      <Card className="border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-950/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg text-green-800 dark:text-green-200 flex items-center gap-2">
            <CheckCircle className="h-5 w-5" />
            Strengths
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-3">
            {!strengths?.length && (
              <p className="text-destructive text-center">Cannot Determine</p>
            )}
            {strengths?.map((strength, index) => (
              <li key={index} className="flex items-start gap-2 text-sm">
                <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
                <span className="text-green-800 dark:text-green-200">
                  {strength}
                </span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <Card className="border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg text-red-800 dark:text-red-200 flex items-center gap-2">
            <XCircle className="h-5 w-5" />
            Areas for Improvement
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-3">
            {!weaknesses?.length && (
              <p className="text-destructive text-center">Cannot Determine</p>
            )}
            {weaknesses?.map((weakness, index) => (
              <li key={index} className="flex items-start gap-2 text-sm">
                <XCircle className="h-4 w-4 text-red-600 dark:text-red-400 mt-0.5 flex-shrink-0" />
                <span className="text-red-800 dark:text-red-200">
                  {weakness}
                </span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}

// Component for learning path recommendations
function LearningPathSection({
  recommendations,
}: {
  recommendations: string[];
}) {
  return (
    <Card className="border-muted">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <BookOpen className="h-5 w-5" />
          Learning Path Recommendations
        </CardTitle>
        <CardDescription>
          Suggested steps to address skill gaps and enhance expertise
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ol className="space-y-3">
          {!recommendations?.length && (
            <p className="text-destructive text-center">Cannot Determine</p>
          )}
          {recommendations?.map((recommendation, index) => (
            <li key={index} className="flex items-start gap-3 text-sm">
              <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs font-bold flex-shrink-0">
                {index + 1}
              </span>
              <span>{recommendation}</span>
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  );
}

// Component for interview focus areas
function InterviewFocusSection({ focusAreas }: { focusAreas: string[] }) {
  return (
    <Card className="border-muted">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <Users className="h-5 w-5" />
          Interview Focus Areas
        </CardTitle>
        <CardDescription>
          Key topics and questions for follow-up interviews
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="space-y-3">
          {!focusAreas?.length && (
            <p className="text-destructive text-center">Cannot Determine</p>
          )}
          {focusAreas?.map((area, index) => (
            <li key={index} className="flex items-start gap-2 text-sm">
              <Target className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <span>{area}</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

const Header = ({
  candidate_name,
  candidateGraph,
  percentage_score,
}: {
  candidate_name: string;
  candidateGraph: any[];
  percentage_score: number;
}) => {
  console.log("idk", candidateGraph);
  return (
    <>
      <Card>
        <CardContent className="flex justify-between items-center">
          <h1 className="text-xl">
            <span className="font-bold">Candidate</span>: {candidate_name}
          </h1>
          <h1 className="text-xl">
            <span className="font-bold">Score</span> : {percentage_score}%
          </h1>
        </CardContent>{" "}
      </Card>

      <SpiderChart
        data={candidateGraph.map((item) => ({
          ...item,
          score: item.score * 100,
        }))}
        title="Skill Assessment Overview"
        maxItems={8}
        height={400}
        scoreRange={[0, 100]}
      />
    </>
  );
};

export default function CandidateReport() {
  const { assessmentId = "" } = useParams();
  const printRef = useRef<HTMLDivElement>(null);

  const { data, isLoading } = useGetAssessmentReportQuery(assessmentId);
  const [
    generateReport,
    { data: generatedReport, isLoading: loadingGenerateReport },
  ] = useGenerateAssessmentReportMutation();

  const report = data?.data?.report || generatedReport?.report;
  const candidateGraph = data?.data?.result?.candidate_graph
    ? Array.from(data?.data?.result?.candidate_graph)
    : [];
  // Sample data for spider chart - replace with actual data from the report
  const sampleSpiderData = [
    { node_id: "JavaScript", score: 85 },
    { node_id: "React", score: 78 },
    { node_id: "Node.js", score: 72 },
    { node_id: "TypeScript", score: 68 },
    { node_id: "Database Design", score: 75 },
    { node_id: "API Development", score: 82 },
    { node_id: "Problem Solving", score: 88 },
    { node_id: "Code Quality", score: 79 },
    { node_id: "Testing", score: 65 },
    { node_id: "System Design", score: 70 },
    { node_id: "Git/Version Control", score: 90 },
    { node_id: "Communication", score: 73 },
  ];

  // Print handler
  const handlePrint = useReactToPrint({
    contentRef: printRef,
    documentTitle: `Assessment_Report_${
      report?.candidate_name?.replace(/\s+/g, "_") || "Candidate"
    }_${format(new Date(), "yyyy-MM-dd")}`,
    pageStyle: `
      @page {
        size: A4;
        margin: 20mm;
      }
      @media print {
        body { 
          font-family: Arial, sans-serif;
          font-size: 12px;
          line-height: 1.4;
          color: #000;
        }
        .print-container {
          max-width: none;
          padding: 0;
        }
        h1, h2, h3 {
          page-break-after: avoid;
        }
        .page-break {
          page-break-before: always;
        }
      }
    `,
  });

  console.log(data);
  const handleGenerateReport = async () => {
    try {
      await generateReport(assessmentId).unwrap();
    } catch (error) {
      console.error("Failed to generate report:", error);
    }
  };

  if (data && !data.data.report_generated) {
    return (
      <div className="flex flex-col gap-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" className="gap-2">
              <ArrowLeft className="h-4 w-4" />
              Back to Dashboard
            </Button>
          </div>
        </div>
        <Header
          candidateGraph={candidateGraph}
          candidate_name={data?.data?.candidate_name}
          percentage_score={data?.data?.percentage_score}
        />
        <Card className="my-10">
          <CardContent className="flex justify-center flex-col items-center py-8">
            <h1 className="text-lg mb-4">
              Report for this assessment is not generated yet
            </h1>
            <Button
              variant="default"
              className="max-w-min cursor-pointer"
              onClick={handleGenerateReport}
              disabled={loadingGenerateReport}
            >
              {loadingGenerateReport
                ? "Generating..."
                : "Click to generate the report"}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!report || isLoading) {
    return <div>Loading....</div>;
  }

  return (
    <div className="container mx-auto p-6 max-w-6xl space-y-8">
      {/* Hidden printable component */}
      <div style={{ display: "none" }}>
        <div ref={printRef}>
          <PrintableReport report={report} />
        </div>
      </div>

      {/* Header Section */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Dashboard
          </Button>
        </div>
        <Button className="gap-2" onClick={handlePrint} disabled={!report}>
          <Download className="h-4 w-4" />
          Download PDF
        </Button>
      </div>

      <Header
        candidateGraph={candidateGraph}
        candidate_name={data?.data?.candidate_name}
        percentage_score={data?.data?.percentage_score}
      />

      {/* Technical Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Technical Overview
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Key Metrics */}
          <div className="grid md:grid-cols-3 gap-4">
            <div className="text-center p-4 border rounded-lg">
              <Target className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
              <div className="text-2xl font-bold">
                {report.alignment_with_jd || "N/A"}
              </div>
              <div className="text-sm text-muted-foreground">
                Alignment with JD
              </div>
            </div>
            <div className="text-center p-4 border rounded-lg">
              <Lightbulb className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
              <div className="text-2xl font-bold">
                {report.curiosity_and_learning || "N/A"}
              </div>
              <div className="text-sm text-muted-foreground">
                Curiosity & Learning
              </div>
            </div>
            <div className="text-center p-4 border rounded-lg">
              <GraduationCap className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
              <div className="text-2xl font-bold">
                {report.technical_score ? `${report.technical_score}%` : "N/A"}
              </div>
              <div className="text-sm text-muted-foreground">
                Technical Score
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary & Insights */}
      <div className="grid md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Assessment Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed">
              {report.summary_text || "No summary available."}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5" />
              Skill Gap Analysis
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed">
              {report.skill_gap_analysis || "No skill gap analysis available."}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Strengths and Weaknesses */}
      <div>
        <h2 className="text-2xl font-semibold mb-4">
          Strengths and Areas for Improvement
        </h2>
        <StrengthsWeaknessesSection
          strengths={report.strengths || []}
          weaknesses={report.weaknesses || []}
        />
      </div>

      {/* Learning Path Recommendations */}
      <div>
        <LearningPathSection
          recommendations={report.learning_path_recommendations || []}
        />
      </div>

      {/* Interview Focus Areas */}
      <div>
        <InterviewFocusSection
          focusAreas={report.interview_focus_areas || []}
        />
      </div>

      {/* Confidence Intervals */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            Confidence Intervals
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm leading-relaxed">
            {report.confidence_intervals ||
              "No confidence interval data available."}
          </p>
        </CardContent>
      </Card>

      {/* Printable report component for PDF export */}
      <div style={{ display: "none" }}>
        <PrintableReport report={report} />
      </div>
    </div>
  );
}

// Printable report component for PDF export
const PrintableReport = ({ report }: { report: AssessmentReportData }) => {
  return (
    <div
      className="print-container"
      style={{ padding: "20px", fontFamily: "Arial, sans-serif" }}
    >
      {/* Header */}
      <div
        style={{
          marginBottom: "30px",
          borderBottom: "2px solid #e5e7eb",
          paddingBottom: "20px",
        }}
      >
        <h1
          style={{
            fontSize: "28px",
            fontWeight: "bold",
            color: "#1f2937",
            marginBottom: "10px",
          }}
        >
          Candidate Assessment Report
        </h1>
        <div style={{ fontSize: "18px", color: "#6b7280" }}>
          <strong>Candidate:</strong> {report.candidate_name || "N/A"}
        </div>
        <div
          style={{
            fontSize: "14px",
            color: "#6b7280",
            marginTop: "5px",
          }}
        >
          <strong>Generated on:</strong> {format(new Date(), "PPP")}
        </div>
      </div>

      {/* Technical Overview */}
      <div style={{ marginBottom: "30px" }}>
        <h2
          style={{
            fontSize: "20px",
            fontWeight: "bold",
            color: "#1f2937",
            marginBottom: "15px",
          }}
        >
          Technical Overview
        </h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: "20px",
            marginBottom: "20px",
          }}
        >
          <div
            style={{
              textAlign: "center",
              padding: "15px",
              border: "1px solid #e5e7eb",
              borderRadius: "8px",
            }}
          >
            <div
              style={{
                fontSize: "24px",
                fontWeight: "bold",
                color: "#1f2937",
              }}
            >
              {report.alignment_with_jd || "N/A"}
            </div>
            <div style={{ fontSize: "12px", color: "#6b7280" }}>
              Alignment with JD
            </div>
          </div>
          <div
            style={{
              textAlign: "center",
              padding: "15px",
              border: "1px solid #e5e7eb",
              borderRadius: "8px",
            }}
          >
            <div
              style={{
                fontSize: "24px",
                fontWeight: "bold",
                color: "#1f2937",
              }}
            >
              {report.curiosity_and_learning || "N/A"}
            </div>
            <div style={{ fontSize: "12px", color: "#6b7280" }}>
              Curiosity & Learning
            </div>
          </div>
          <div
            style={{
              textAlign: "center",
              padding: "15px",
              border: "1px solid #e5e7eb",
              borderRadius: "8px",
            }}
          >
            <div
              style={{
                fontSize: "24px",
                fontWeight: "bold",
                color: "#1f2937",
              }}
            >
              {report.technical_score ? `${report.technical_score}%` : "N/A"}
            </div>
            <div style={{ fontSize: "12px", color: "#6b7280" }}>
              Technical Score
            </div>
          </div>
        </div>
      </div>

      {/* Domain Mastery */}
      {report.domain_mastery && (
        <div style={{ marginBottom: "30px" }}>
          <h3
            style={{
              fontSize: "18px",
              fontWeight: "bold",
              color: "#1f2937",
              marginBottom: "15px",
            }}
          >
            Domain Mastery
          </h3>
          <p
            style={{
              fontSize: "14px",
              lineHeight: "1.6",
              color: "#374151",
            }}
          >
            {report.domain_mastery}
          </p>
        </div>
      )}

      {/* Summary & Insights */}
      <div style={{ marginBottom: "30px" }}>
        <h2
          style={{
            fontSize: "20px",
            fontWeight: "bold",
            color: "#1f2937",
            marginBottom: "15px",
          }}
        >
          Assessment Summary & Insights
        </h2>
        <div style={{ marginBottom: "20px" }}>
          <h3
            style={{
              fontSize: "16px",
              fontWeight: "bold",
              color: "#1f2937",
              marginBottom: "10px",
            }}
          >
            Assessment Summary
          </h3>
          <p
            style={{
              fontSize: "14px",
              lineHeight: "1.6",
              color: "#374151",
            }}
          >
            {report.summary_text || "No summary available."}
          </p>
        </div>
        <div>
          <h3
            style={{
              fontSize: "16px",
              fontWeight: "bold",
              color: "#1f2937",
              marginBottom: "10px",
            }}
          >
            Skill Gap Analysis
          </h3>
          <p
            style={{
              fontSize: "14px",
              lineHeight: "1.6",
              color: "#374151",
            }}
          >
            {report.skill_gap_analysis || "No skill gap analysis available."}
          </p>
        </div>
      </div>

      {/* Strengths and Weaknesses */}
      <div style={{ marginBottom: "30px" }}>
        <h2
          style={{
            fontSize: "20px",
            fontWeight: "bold",
            color: "#1f2937",
            marginBottom: "15px",
          }}
        >
          Strengths and Areas for Improvement
        </h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(2, 1fr)",
            gap: "20px",
          }}
        >
          <div>
            <h3
              style={{
                fontSize: "16px",
                fontWeight: "bold",
                color: "#059669",
                marginBottom: "10px",
              }}
            >
              Strengths
            </h3>
            <ul style={{ listStyle: "none", padding: 0 }}>
              {!report.strengths?.length && (
                <li
                  style={{
                    fontSize: "14px",
                    color: "#dc2626",
                    textAlign: "center",
                  }}
                >
                  Cannot Determine
                </li>
              )}
              {report.strengths?.map((strength, index) => (
                <li
                  key={index}
                  style={{
                    fontSize: "14px",
                    marginBottom: "8px",
                    color: "#374151",
                  }}
                >
                  • {strength}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3
              style={{
                fontSize: "16px",
                fontWeight: "bold",
                color: "#dc2626",
                marginBottom: "10px",
              }}
            >
              Areas for Improvement
            </h3>
            <ul style={{ listStyle: "none", padding: 0 }}>
              {!report.weaknesses?.length && (
                <li
                  style={{
                    fontSize: "14px",
                    color: "#dc2626",
                    textAlign: "center",
                  }}
                >
                  Cannot Determine
                </li>
              )}
              {report.weaknesses?.map((weakness, index) => (
                <li
                  key={index}
                  style={{
                    fontSize: "14px",
                    marginBottom: "8px",
                    color: "#374151",
                  }}
                >
                  • {weakness}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Learning Path Recommendations */}
      <div style={{ marginBottom: "30px" }}>
        <h2
          style={{
            fontSize: "20px",
            fontWeight: "bold",
            color: "#1f2937",
            marginBottom: "15px",
          }}
        >
          Learning Path Recommendations
        </h2>
        <ol style={{ paddingLeft: "20px" }}>
          {!report.learning_path_recommendations?.length && (
            <li
              style={{
                fontSize: "14px",
                color: "#dc2626",
                textAlign: "center",
              }}
            >
              Cannot Determine
            </li>
          )}
          {report.learning_path_recommendations?.map(
            (recommendation, index) => (
              <li
                key={index}
                style={{
                  fontSize: "14px",
                  marginBottom: "8px",
                  color: "#374151",
                  lineHeight: "1.5",
                }}
              >
                {recommendation}
              </li>
            )
          )}
        </ol>
      </div>

      {/* Interview Focus Areas */}
      <div style={{ marginBottom: "30px" }}>
        <h2
          style={{
            fontSize: "20px",
            fontWeight: "bold",
            color: "#1f2937",
            marginBottom: "15px",
          }}
        >
          Interview Focus Areas
        </h2>
        <ul style={{ listStyle: "none", padding: 0 }}>
          {!report.interview_focus_areas?.length && (
            <li
              style={{
                fontSize: "14px",
                color: "#dc2626",
                textAlign: "center",
              }}
            >
              Cannot Determine
            </li>
          )}
          {report.interview_focus_areas?.map((area, index) => (
            <li
              key={index}
              style={{
                fontSize: "14px",
                marginBottom: "8px",
                color: "#374151",
              }}
            >
              • {area}
            </li>
          ))}
        </ul>
      </div>

      {/* Confidence Intervals */}
      <div>
        <h2
          style={{
            fontSize: "20px",
            fontWeight: "bold",
            color: "#1f2937",
            marginBottom: "15px",
          }}
        >
          Confidence Intervals
        </h2>
        <p
          style={{
            fontSize: "14px",
            lineHeight: "1.6",
            color: "#374151",
          }}
        >
          {report.confidence_intervals ||
            "No confidence interval data available."}
        </p>
      </div>
    </div>
  );
};
