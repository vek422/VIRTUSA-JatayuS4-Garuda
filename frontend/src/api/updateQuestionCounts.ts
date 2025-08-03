import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { apiSlice } from '@/store/apiSlice';

export interface UpdateQuestionCountsRequest {
  high_priority_questions: number;
  medium_priority_questions: number;
  low_priority_questions: number;
  total_questions: number;
  time_limit_minutes: number;
}

export interface UpdateQuestionCountsResponse {
  test_id: number;
  high_priority_questions: number;
  medium_priority_questions: number;
  low_priority_questions: number;
  total_questions: number;
  time_limit_minutes: number;
  message: string;
}
export const updateQuestionCountsEndpoint = (builder: any) => ({
  updateQuestionCounts: builder.mutation({
    query: ({ test_id, data }: { test_id: number; data: UpdateQuestionCountsRequest }) => ({
      url: `/tests/${test_id}/update-question-counts`,
      method: 'PUT',
      data,
    }),
    invalidatesTags: ['Tests'],
  }),
});