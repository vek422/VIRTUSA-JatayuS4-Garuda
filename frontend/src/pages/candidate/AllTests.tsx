import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { motion } from "motion/react";
import {
  ClipboardList,
  Trophy,
  Calendar,
  Timer,
  Eye,
  Star,
} from "lucide-react";
import { Link } from "react-router-dom";

interface CompletedTest {
  id: string;
  testName: string;
  completedOn: string;
  completedDate: Date;
  durationTaken: string;
  score: number;
  totalScore: number;
  status: "completed" | "pending";
}

interface CompletedTestCardProps {
  test: CompletedTest;
}

function CompletedTestCard({ test }: CompletedTestCardProps) {
  const getStatusBadge = () => {
    switch (test.status) {
      case "completed":
        return (
          <Badge className="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
            Completed
          </Badge>
        );

      case "pending":
        return (
          <Badge className="bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">
            🟡 Awaiting Evaluation
          </Badge>
        );
      default:
        return null;
    }
  };

  const getScoreDisplay = () => {
    if (test.status === "pending") {
      return "Pending";
    }
    return `${test.score} / ${test.totalScore}`;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      whileHover={{ scale: 1.02 }}
      className="relative"
    >
      <Card className="p-4 hover:shadow-lg transition-all duration-200">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <h3 className="font-semibold text-lg mb-2">{test.testName}</h3>

            <div className="space-y-1 text-sm text-muted-foreground mb-3">
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                <span>Completed on {test.completedOn}</span>
              </div>
              <div className="flex items-center gap-2">
                <Timer className="h-4 w-4" />
                <span>Duration: {test.durationTaken}</span>
              </div>
              <div className="flex items-center gap-2">
                <Trophy className="h-4 w-4" />
                <span className="font-medium">Score: {getScoreDisplay()}</span>
              </div>
            </div>
          </div>

          <div className="flex flex-col items-end gap-2 ml-4">
            {getStatusBadge()}
            <Link to={`/candidate/test/${test.id}`}>
              <Button variant="outline" size="sm" className="gap-2">
                <Eye className="h-4 w-4" />
                View Report
              </Button>
            </Link>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}

function CompletedTestsEmptyState() {
  return (
    <Card className="max-w-md mx-auto">
      <CardContent className="flex flex-col items-center justify-center py-12 text-center">
        <div className="mb-6 rounded-full bg-muted p-4">
          <ClipboardList className="h-12 w-12 text-muted-foreground" />
        </div>

        <h3 className="text-lg font-semibold mb-2">No Completed Tests</h3>

        <p className="text-muted-foreground mb-6 max-w-sm">
          You haven't completed any assessments yet. Once you finish a test,
          it'll show up here.
        </p>

        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Star className="h-4 w-4" />
          <span>Your test results will appear here once available</span>
        </div>
      </CardContent>
    </Card>
  );
}

export default function AllTests() {
  const [completedTests, setCompletedTests] = useState<CompletedTest[]>([]);
  const [loading, setLoading] = useState(true);

  // Mock data - replace with actual API call
  useEffect(() => {
    // Simulate API call
    const fetchCompletedTests = async () => {
      // Mock delay
      await new Promise((resolve) => setTimeout(resolve, 1000));

      const mockTests: CompletedTest[] = [
        {
          id: "1",
          testName: "Backend Challenge - API Design",
          completedOn: "Jul 2, 2025 at 3:00 PM",
          completedDate: new Date("2025-07-02T15:00:00"),
          durationTaken: "58 minutes",
          score: 74,
          totalScore: 100,
          status: "completed",
        },
        {
          id: "2",
          testName: "React.js Assessment",
          completedOn: "Jul 3, 2025 at 11:30 AM",
          completedDate: new Date("2025-07-03T11:30:00"),
          durationTaken: "45 minutes",
          score: 88,
          totalScore: 100,
          status: "completed",
        },
        {
          id: "3",
          testName: "Database Design Test",
          completedOn: "Jul 1, 2025 at 2:15 PM",
          completedDate: new Date("2025-07-01T14:15:00"),
          durationTaken: "72 minutes",
          score: 45,
          totalScore: 100,
          status: "completed",
        },
        {
          id: "4",
          testName: "System Design Interview",
          completedOn: "Jun 30, 2025 at 4:00 PM",
          completedDate: new Date("2025-06-30T16:00:00"),
          durationTaken: "90 minutes",
          score: 0,
          totalScore: 100,
          status: "pending",
        },
      ];

      setCompletedTests(mockTests);
      setLoading(false);
    };

    fetchCompletedTests();
  }, []);

  const completedCount = completedTests.length;

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <div className="container mx-auto px-4 py-8">
          <div className="space-y-6">
            {[...Array(3)].map((_, i) => (
              <Card key={i} className="p-4">
                <div className="animate-pulse">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/2 mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded w-2/3"></div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>
    );
  }

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
              <ClipboardList className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Past Tests</h1>
              <p className="text-muted-foreground mt-1">
                Here are the tests you've completed or attempted.
              </p>
            </div>
          </div>

          {/* Stats Cards */}
          {completedCount > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    Total Completed
                  </CardTitle>
                  <ClipboardList className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{completedCount}</div>
                  <p className="text-xs text-muted-foreground">assessments</p>
                </CardContent>
              </Card>
            </div>
          )}
        </motion.div>

        {/* Main Content */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          {completedTests.length === 0 ? (
            <CompletedTestsEmptyState />
          ) : (
            <div className="space-y-4">
              {completedTests
                .sort(
                  (a, b) =>
                    b.completedDate.getTime() - a.completedDate.getTime()
                )
                .map((test, index) => (
                  <motion.div
                    key={test.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.1 }}
                  >
                    <CompletedTestCard test={test} />
                  </motion.div>
                ))}
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
