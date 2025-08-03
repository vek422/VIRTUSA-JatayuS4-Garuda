import { apiSlice } from "@/store/apiSlice";

// TypeScript interfaces for Candidate Application API
export interface CandidateApplication {
  application_id: number;
  user_id: number;
  test_id: number;
  resume_link: string;
  resume_text?: string;
  parsed_resume?: string;
  resume_score: number;
  skill_match_percentage: number;
  experience_score: number;
  education_score: number;
  ai_reasoning?: string;
  is_shortlisted: boolean;
  applied_at: string;
  updated_at: string;
  screening_completed_at?: string;
}

// Enhanced candidate with user info for UI display
export interface CandidateWithUserInfo {
  id: number;
  application_id: number;
  user_id: number;
  test_id: number;
  name: string;
  email: string;
  resume_link: string;
  resume_text?: string;
  parsed_resume?: string;
  score: number | null; // Use resume_score or null if not taken
  skill_match_percentage?: number;
  experience_score?: number;
  education_score?: number;
  ai_reasoning?: string;
  is_shortlisted: boolean;
  created_at: string; // Use applied_at
  updated_at: string;
  screening_completed_at?: string;
}

// Bulk upload request interface
export interface BulkUploadRequest {
  applications: BulkApplicationItem[];
}

export interface BulkApplicationItem {
  email: string;
  name?: string;
  test_id: number;
  resume_link: string;
}

// Bulk upload response interface
export interface BulkUploadResponse {
  results: BulkUploadResult[];
  total: number;
  success: number;
  failed: number;
  created: number; // Add created count for UI feedback
}

export interface BulkUploadResult {
  status: "success" | "error";
  application_id?: number;
  email: string;
  message: string;
  user_id?: number;
  resume_score?: number;
  is_shortlisted?: boolean;
}

// Update candidate request interface
export interface UpdateCandidateRequest {
  resume_link?: string;
  resume_text?: string;
  parsed_resume?: string;
  resume_score?: number;
  skill_match_percentage?: number;
  experience_score?: number;
  education_score?: number;
  ai_reasoning?: string;
  is_shortlisted?: boolean;
  shortlist_reason?: string;
  screening_completed_at?: string;
  notified_at?: string;
}

// Recruiter Dashboard Summary API response type
export interface DashboardSummary {
  scheduled_tests: number;
  total_candidates: number;
  completed_tests: number;
  recent_tests: Array<{
    name: string;
    status: string;
    test_id: string;
    candidate_count: number;
    duration_minutes: number;
    date: string;
  }>;
  test_distribution: Array<{
    label: string;
    count: number;
  }>;
  quick_stats: {
    active_tests: number;
    draft_tests: number;
    avg_duration_minutes: number;
    total_tests: number;
  };
}

// Shortlist bulk candidates for a test (manual shortlisting)
export interface ShortlistBulkRequest {
  test_id: number;
  min_score: number;
}

export interface ShortlistBulkResponse {
  shortlisted: Array<{
    candidate_email: string;
    resume_score: number;
  }>;
  notified: number;
  message: string;
}

const candidateApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    // Get all assessments/tests assigned to a candidate
    getCandidateAssessments: builder.query<any, number>({
      query: (candidateId) => ({
        url: `/tests/candidates/${candidateId}/assessments`,
        method: 'GET'
      }),
      providesTags: ["CandidateAssessments"]
    }),
    // Bulk upload candidates
    bulkUploadCandidates: builder.mutation<BulkUploadResponse, { applications: BulkApplicationItem[] }>({
      query: ({ applications }) => ({
        url: '/candidate-applications/bulk',
        method: 'POST',
        data: { applications },
        headers: {
          'Content-Type': 'application/json'
        }
      }),
      invalidatesTags: ["Candidates"]
    }),

    // Get all candidates for a specific test
    getCandidatesByTest: builder.query<CandidateWithUserInfo[], number>({
      query: (testId) => ({
        url: `/candidate-applications/test/${testId}`,
        method: 'GET'
      }),
      providesTags: ["Candidates"]
    }),

    // Update candidate application
    updateCandidate: builder.mutation<CandidateApplication, { applicationId: number; updateData: UpdateCandidateRequest }>({
      query: ({ applicationId, updateData }) => ({
        url: `/candidate-applications/${applicationId}`,
        method: 'PUT',
        data: updateData,
        headers: {
          'Content-Type': 'application/json'
        }
      }),
      invalidatesTags: ["Candidates"]
    }),

    // Delete candidate application
    deleteCandidate: builder.mutation<{ message: string }, number>({
      query: (applicationId) => ({
        url: `/candidate-applications/${applicationId}`,
        method: 'DELETE'
      }),
      invalidatesTags: ["Candidates"]
    }),

    // Get single candidate application (for viewing screening result)
    getCandidateApplication: builder.query<CandidateApplication, number>({
      query: (applicationId) => ({
        url: `/candidate-applications/${applicationId}`,
        method: 'GET'
      }),
      providesTags: ["Candidates"]
    }),
    // Create single candidate application (for individual uploads)
    createSingleCandidate: builder.mutation<CandidateApplication, BulkApplicationItem>({
      query: (candidateData) => ({
        url: '/candidate-application/single',
        method: 'POST',
        data: candidateData,
        headers: {
          'Content-Type': 'application/json'
        }
      }),
      invalidatesTags: ["Candidates"]
    }),

    // Recruiter Dashboard Summary
    getRecruiterDashboardSummary: builder.query<DashboardSummary, void>({
      query: () => ({
        url: '/dashboard/summary',
        method: 'GET',
      }),
    }),

    // Shortlist bulk candidates for a test (manual shortlisting)
    shortlistBulkCandidates: builder.mutation<ShortlistBulkResponse, ShortlistBulkRequest>({
      query: (body) => ({
        url: '/candidate-applications/shortlist-bulk',
        method: 'POST',
        data: body,
        headers: {
          'Content-Type': 'application/json'
        }
      }),
      invalidatesTags: ["Candidates"]
    }),
  })
});

// Export hooks for use in components (following your existing pattern)
export const {
  useBulkUploadCandidatesMutation,
  useGetCandidatesByTestQuery,
  useUpdateCandidateMutation,
  useDeleteCandidateMutation,
  useCreateSingleCandidateMutation,
  useGetRecruiterDashboardSummaryQuery,
  useShortlistBulkCandidatesMutation,
  useGetCandidateAssessmentsQuery,
  useGetCandidateApplicationQuery
} = candidateApi;
