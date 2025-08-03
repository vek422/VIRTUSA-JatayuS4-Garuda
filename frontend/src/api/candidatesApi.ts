import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export interface Candidate {
  user_id: number;
  name: string;
  email: string;
  role: string;
  created_at: string;
  updated_at: string;
}

export interface CandidateTest {
  test_id: number;
  test_name: string;
  status: string;
  scheduled_at: string;
  application_deadline: string;
  assessment_deadline: string;
  [key: string]: any;
}

export const candidatesApi = createApi({
  reducerPath: 'candidatesApi',
  baseQuery: fetchBaseQuery({
    baseUrl: 'http://localhost:8000',
    prepareHeaders: (headers, { getState }) => {
      const token = (getState() as { auth?: { token?: string } }).auth?.token;
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  endpoints: (builder) => ({
    getCandidates: builder.query<Candidate[], void>({
      query: () => '/candidate-applications/recruiter/candidates',
    }),
    getCandidateTests: builder.query<CandidateTest[], number>({
      query: (candidateId) => `/candidate-applications/recruiter/candidate/${candidateId}/tests`,
    }),
  }),
});

export const { useGetCandidatesQuery, useGetCandidateTestsQuery } = candidatesApi;
