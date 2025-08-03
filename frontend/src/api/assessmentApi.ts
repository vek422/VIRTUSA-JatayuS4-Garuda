import { apiSlice } from "@/store/apiSlice"

export interface TestAssessments {
    test_id: number
    total_assessments: number
    assessments: Assessment[]
    pagination: {
        current_page: number
        total_pages: number
        page_size: number
        total_count: number
        has_next: boolean
        has_previous: boolean
        next_page: number | null
        previous_page: number | null
    }
    summary: {
        page_completed: number
        page_in_progress: number
        page_not_started: number
        page_average_score: number
        page_size: number
    }
    filters: {
        status?: string
    }
}

export type Assessment = {
    assessment_id: number
    candidate_id: number
    candidate_name: string
    status: "completed" | "unknown"
    percentage_score: number
    start_time: Date | string | number | null
    end_time: Date | string | number | null
    time_taken_seconds: number
    created_at: Date | string | number | null
    updated_at: Date | string | number | null
}


export interface AssessmentReportData {
    candidate_name: string
    technical_score: number
    passed_H: number
    passed_M: number
    strengths: string[]
    weaknesses: string[]
    recommendation: string
    domain_mastery: string
    alignment_with_jd: string
    curiosity_and_learning: string
    summary_text: string
    skill_gap_analysis: string
    learning_path_recommendations: string[]
    interview_focus_areas: string[]
    confidence_intervals: string
}

export interface AssessmentReport {
    assessment_id: number
    report_generated: boolean
    generated_at: string
    report: AssessmentReportData
}


const assessmentApi = apiSlice.injectEndpoints({
    endpoints: (builder) => ({
        getTestAssessments: builder.query<TestAssessments, { test_id: string; page?: number; per_page?: number }>({
            query: ({ test_id, page = 1, per_page = 100 }) => ({
                url: `/tests/${test_id}/assessments?skip=${(page - 1) * per_page}&limit=${per_page}`,
                method: 'GET'
            }),
            providesTags: (_, __, { test_id }) => [
                { type: "Reports", id: `test-${test_id}` },
                "Reports"
            ]
        }),
        generateAssessmentReport: builder.mutation<AssessmentReport, string>({
            query: (assessmentId) => ({
                url: `/tests/assessments/${assessmentId}/generate-report`,
                method: "POST"
            }),
            invalidatesTags: ["Reports"]
        }),
        getAssessmentReport: builder.query<{ data: AssessmentReport, success: boolean }, string>({
            query: (assessmentId) => ({
                url: `/tests/assessments/${assessmentId}/report`,
                method: 'GET'
            }),
            providesTags: (_, __, assessmentId) => [
                { type: "Reports", id: assessmentId },
                "Reports"
            ]
        })
    })

})

export const {
    useGenerateAssessmentReportMutation,
    useGetTestAssessmentsQuery,
    useGetAssessmentReportQuery
} = assessmentApi