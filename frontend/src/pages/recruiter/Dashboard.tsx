import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import TestDistributionChart from "@/components/TestDistributionChart";
import { useGetRecruiterDashboardSummaryQuery } from "@/api/candidateApi";
import {
  Clock,
  CalendarCheck,
  CheckCircle,
  AlertTriangle,
  Ban,
  CircleDashed,
} from "lucide-react";
import {
  CalendarDays,
  Users,
  CheckSquare,
  Plus,
  TrendingUp,
  Activity,
  Users2,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function Dashboard() {
  // Fetch real dashboard data from API
  const { data, isLoading, error } = useGetRecruiterDashboardSummaryQuery();

  console.log(data);
  // Show loading and error states
  if (isLoading) {
    return <div className="p-6">Loading dashboard...</div>;
  }
  if (error || !data) {
    return (
      <div className="p-6 text-red-600">Failed to load dashboard data.</div>
    );
  }

  // Destructure API data
  const scheduledTests = data.scheduled_tests;
  const totalCandidates = data.total_candidates;
  const completedTests = data.completed_tests;
  const chartData = data.test_distribution.map((item) => ({
    type: item.label.toLowerCase(),
    value: item.count,
  }));
  const recentTests = data.recent_tests;
  const liveTestsCount = data?.live_tests;

  return (
    <div className="flex flex-col gap-6 p-2 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        </div>
        <Link to="/recruiter/test/create">
          <Button className="gap-2">
            <Plus className="h-4 w-4" />
            Create New Test
          </Button>
        </Link>
      </div>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 max-h-min">
        {/* Main Section - 8 columns */}
        <div className="lg:col-span-8 space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Scheduled Tests Card */}
            <Card className="">
              <CardHeader className="flex flex-col  justify-between ">
                <CardTitle className="text-sm font-normal text-muted-foreground flex justify-between w-full">
                  Scheduled Tests
                  <CalendarDays className="h-5 w-5" />
                </CardTitle>
                {scheduledTests ? (
                  <>
                    <div className="text-3xl font-extrabold">
                      {scheduledTests}
                    </div>
                    <p className="text-xs s font-semibold">
                      Tests ready to start
                    </p>
                  </>
                ) : (
                  <p className="text-muted-foreground italic text-xs text-center ">
                    No Tests are scheduled
                  </p>
                )}
              </CardHeader>
            </Card>

            {/* Total Candidates Card */}
            <Card className="">
              <CardHeader className="flex flex-col justify-between space-y-0">
                <CardTitle className="text-sm font-normal text-muted-foreground flex justify-between w-full">
                  Total Candidates
                  <Users2 className="w-5 h-5" />
                </CardTitle>
                <div className="text-3xl font-extrabold ">
                  {totalCandidates}
                </div>
                <p className="text-xs font-semibold">Across all tests</p>
              </CardHeader>
            </Card>

            {/* Completed Tests Card */}
            <Card className="">
              <CardHeader className="flex flex-col justify-between space-y-0">
                <CardTitle className="text-sm font-normal text-muted-foreground">
                  Live Tests
                </CardTitle>
                <div className="text-3xl font-extrabold ">{liveTestsCount}</div>
                <p className="text-xs font-semibold">Currently Live</p>
              </CardHeader>
            </Card>
          </div>

          {/* Recent Tests Table */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Recent Tests
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[350px]">
                <div className="space-y-4">
                  {recentTests.map((test) => (
                    <RecentTestCard test={test} />
                  ))}
                </div>

                {/* View All Tests Link */}
                <div className="mt-4 pt-4 border-t">
                  <Link to="/recruiter/tests">
                    <Button variant="outline" className="w-full">
                      View All Tests
                    </Button>
                  </Link>
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar Section - 4 columns */}
        <div className="lg:col-span-4 space-y-6">
          {/* Test Distribution Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Test Distribution
              </CardTitle>
            </CardHeader>{" "}
            <CardContent className="p-0">
              {chartData.length > 0 ? (
                <div>
                  <TestDistributionChart data={chartData} />{" "}
                  <div className="p-4 border-t">
                    <div className="flex flex-wrap gap-2">
                      {chartData.map((item, index) => {
                        const colorMap: Record<string, string> = {
                          ended: "#5ec269",
                          live: "#952aa9",
                          preparing: "#845eed",
                          draft: "#f59e0b",
                        };
                        const color = colorMap[item.type] || "#6b7280";

                        return (
                          <Button
                            key={index}
                            variant="outline"
                            size="sm"
                            className="flex items-center gap-2 text-xs"
                          >
                            <div
                              className="w-3 h-3 rounded-full"
                              style={{
                                backgroundColor: color,
                              }}
                            />
                            <span className="capitalize">{item.type}</span>
                            <Badge variant="secondary" className="text-xs">
                              {item.value}
                            </Badge>
                          </Button>
                        );
                      })}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                  <div className="text-center">
                    <Activity className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p>No test data available</p>
                    <p className="text-sm">
                      Create your first test to see distribution
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
const statusMap: Record<
  string,
  { label: string; icon: React.ReactNode; className: string }
> = {
  draft: {
    label: "Draft",
    icon: <CircleDashed className="h-3 w-3 mr-1" />,
    className: "bg-gray-100 text-gray-800",
  },
  scheduled: {
    label: "Scheduled",
    icon: <CalendarCheck className="h-3 w-3 mr-1" />,
    className: "bg-blue-100 text-blue-800",
  },
  live: {
    label: "Live",
    icon: <Clock className="h-3 w-3 mr-1" />,
    className: "bg-yellow-100 text-yellow-800",
  },
  completed: {
    label: "Completed",
    icon: <CheckCircle className="h-3 w-3 mr-1" />,
    className: "bg-green-100 text-green-800",
  },
  ended: {
    label: "Ended",
    icon: <Ban className="h-3 w-3 mr-1" />,
    className: "bg-red-100 text-red-800",
  },
};

export const RecentTestCard = ({ test }: { test: any }) => {
  const statusInfo = statusMap[test.status] || {
    label: test.status,
    icon: null,
    className: "bg-muted text-muted-foreground",
  };

  return (
    <div
      className="flex items-center justify-between px-3 py-2 rounded-md  hover:bg-muted transition-colors border"
      key={test.test_id}
    >
      {/* Left Side: Name & Status */}
      <div className="flex items-center gap-3 flex-1">
        <span className="font-medium text-sm text-foreground">{test.name}</span>
        <Badge
          className={cn(
            "text-xs font-medium px-2 py-0.5 rounded-sm inline-flex items-center",
            statusInfo.className
          )}
        >
          {statusInfo.icon}
          {statusInfo.label}
        </Badge>
      </div>

      {/* Middle Info: ID, candidates, duration */}
      <div className="text-sm text-muted-foreground flex gap-3 whitespace-nowrap">
        <span className="font-medium">{test.test_id}</span>
        <span className="font-medium">{test.candidate_count} candidates</span>
        <span className="font-medium">{test.duration_minutes} min</span>
      </div>

      {/* Right Side: Date */}
      <div className="text-sm font-medium text-purple-700 whitespace-nowrap ml-4">
        {test.date}
      </div>
    </div>
  );
};
