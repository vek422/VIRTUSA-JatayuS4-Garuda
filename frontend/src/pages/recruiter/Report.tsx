import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";

import { DataTable } from "@/components/AssessmentsTable/data-table";
import { columns } from "@/components/AssessmentsTable/columns";
import { useGetTestAssessmentsQuery } from "@/api/assessmentApi";
import { useParams } from "react-router-dom";

export default function Report() {
  const { id } = useParams();
  const [currentPage, setCurrentPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState<string>("");

  const {
    data: assessmentsData,
    isLoading,
    error,
  } = useGetTestAssessmentsQuery({
    test_id: id || "",
    page: currentPage,
    per_page: 10,
  });

  console.log(assessmentsData, isLoading, error);

  // Filter the assessments data based on status and search term
  const filteredAssessments = (assessmentsData?.assessments || []).filter(
    (assessment) => {
      // Status filter
      const matchesStatus =
        statusFilter === "all" || assessment.status === statusFilter;

      // Search filter (candidate name)
      const matchesSearch =
        searchTerm === "" ||
        assessment.candidate_name
          .toLowerCase()
          .includes(searchTerm.toLowerCase());

      return matchesStatus && matchesSearch;
    }
  );

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const handleSearchChange = (searchTerm: string) => {
    setSearchTerm(searchTerm);
    // Reset to first page when searching
    setCurrentPage(1);
  };

  const handleFilterChange = (key: string, value: string) => {
    if (key === "status") {
      setStatusFilter(value);
      // Reset to first page when filtering
      setCurrentPage(1);
    }
  };

  const filterOptions = [
    { label: "All Status", value: "all", filterKey: "status" },
    { label: "Completed", value: "completed", filterKey: "status" },
    { label: "In Progress", value: "unknown", filterKey: "status" },
  ];

  return (
    <div className="space-y-6 p-6">
      {/* Header Section */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Test Assessment Report
          </h1>
          <p className="text-muted-foreground">
            Test ID: {id} • {assessmentsData?.total_assessments || 0} total
            assessments
          </p>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center text-red-600">
              Error loading assessments. Please try again.
            </div>
          </CardContent>
        </Card>
      )}

      {/* Assessments Table */}
      <Card>
        <CardContent>
          <DataTable
            columns={columns}
            data={filteredAssessments}
            pagination={assessmentsData?.pagination}
            onPageChange={handlePageChange}
            searchPlaceholder="Search candidates..."
            onSearchChange={handleSearchChange}
            filterOptions={filterOptions}
            onFilterChange={handleFilterChange}
            isLoading={isLoading}
          />
        </CardContent>
      </Card>
    </div>
  );
}
