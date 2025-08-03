import { Button } from "@/components/ui/button";
import { Plus, Loader2, AlertCircle } from "lucide-react";
import { Link } from "react-router-dom";
import { TestsDataTable } from "@/components/TestsTable/data-table";
import { createColumns } from "@/components/TestsTable/columns";
import { useGetTestsQuery, useDeleteTestMutation } from "@/api/testApi";
import { useProfileQuery } from "@/api/authApi";
import { type Test as TableTest } from "@/components/TestTable/columns";
import { type Test as ApiTest } from "@/api/testApi";
import { Card, CardContent } from "@/components/ui/card";

// Transform API test data to table format (map status to allowed values)
const mapStatus = (status: string): TableTest["test_status"] => {
  switch (status) {
    case "draft":
      return "draft";
    case "scheduled":
      return "scheduled";
    case "ongoing":
    case "published":
      return "ongoing";
    case "completed":
      return "completed";
    default:
      return "draft";
  }
};
const transformTestData = (apiTests: ApiTest[]): TableTest[] => {
  return apiTests.map((test) => ({
    test_id: test.test_id.toString(),
    test_name: test.test_name,
    test_status: mapStatus(test.status),
    test_created_at: test.created_at,
    test_duration: test.time_limit_minutes || 60,
    total_candidate: 0,
  }));
};

export default function Tests() {
  const { data: testsData, isLoading, error, refetch } = useGetTestsQuery({});

  const [deleteTest] = useDeleteTestMutation();
  const handleDelete = async (testId: string) => {
    const testToDelete = testsData?.find(
      (test) => test.test_id.toString() === testId
    );
    console.log("Deleting test:", testToDelete);
    if (!testToDelete) {
      alert("Test not found!");
      return;
    }
    if (
      testToDelete.status === "published" ||
      testToDelete.status === "ongoing"
    ) {
      alert(
        "Cannot Delete Test\n\nThis test is currently ongoing and cannot be deleted. Please wait for the test to complete before attempting to delete it."
      );
      return;
    }

    // Confirmation dialog for valid deletion
    const confirmMessage = `Delete Test Confirmation\n\nAre you sure you want to delete "${testToDelete.test_name}"?\n\nThis action cannot be undone.`;
    if (confirm(confirmMessage)) {
      try {
        await deleteTest(Number(testId)).unwrap();
        alert("Test deleted successfully!");
        refetch();
      } catch (error) {
        console.error("Failed to delete test:", error);
        alert("Failed to delete test. Please try again.");
      }
    }
  };
  const columns = createColumns({
    onDelete: handleDelete,
  });
  const tableData = Array.isArray(testsData)
    ? testsData.map((test) => ({
        test_id: test.test_id?.toString() ?? "",
        test_name: test.test_name ?? "",
        test_status: test.status ?? "",
        test_created_at: test.created_at ?? "",
        test_duration: test.time_limit_minutes ?? 0,
        total_candidate: 0,
      }))
    : [];

  return (
    <div className="w-full flex flex-col gap-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="font-bold text-2xl">Tests</h1>
        <Link to="/recruiter/test/create">
          <Button className="gap-2">
            <Plus className="h-4 w-4" />
            Create New Test
          </Button>
        </Link>
      </div>

      {/* Loading State */}
      {isLoading && (
        <Card>
          <CardContent className="flex items-center justify-center py-8">
            <div className="flex items-center gap-2">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>Loading tests...</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error State */}
      {error && (
        <Card>
          <CardContent className="flex items-center justify-center py-8">
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle className="h-5 w-5" />
              <span>Failed to load tests. Please try again.</span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => refetch()}
                className="ml-2"
              >
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tests Table */}
      {!isLoading && !error && (
        <TestsDataTable data={tableData} columns={columns} />
      )}

      {/* Empty State */}
      {!isLoading && !error && tableData.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <div className="text-center">
              <h3 className="text-lg font-medium">No tests found</h3>
              <p className="text-muted-foreground mt-1">
                You haven't created any tests yet. Create your first test to get
                started.
              </p>
              <Link to="/recruiter/test/create">
                <Button className="mt-4 gap-2">
                  <Plus className="h-4 w-4" />
                  Create Your First Test
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
