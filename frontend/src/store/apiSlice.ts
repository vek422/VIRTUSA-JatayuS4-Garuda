import { createApi } from "@reduxjs/toolkit/query/react";
import { axiosBaseQuery } from "@/api/baseQuery";

export const apiSlice = createApi({
    reducerPath: "api",
    baseQuery: axiosBaseQuery(),
    tagTypes: ['Auth', 'Tests', 'Candidates', "CandidateAssessments", "Reports"],
    endpoints: () => ({
    })
})
