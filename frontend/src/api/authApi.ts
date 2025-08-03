import { apiSlice } from "@/store/apiSlice";


interface ProfileResponse {
    user_id: number;
    name: string;
    email: string;
    role: "candidate" | "recruiter";
    created_at: string;
    updated_at: string;
}

const authApi = apiSlice.injectEndpoints({
    endpoints: (builder) => ({
        login: builder.mutation<{ token: string, role: "candidate" | "recruiter", user_id: number }, { email: string, password: string }>({
            query: (credentials) => ({
                url: '/auth/login',
                method: 'POST',
                data: credentials
            }),
            invalidatesTags: ["Auth"]
        }),
        register: builder.mutation<{ user_id: string }, { name: string, email: string, password: string, role: "candidate" | "recruiter" }>({
            query: (credentials) => ({
                url: "/auth/register",
                method: 'POST',
                data: credentials
            }),
            invalidatesTags: ["Auth"]
        }),

        profile: builder.query<ProfileResponse, void>({
            query: () => ({ url: "/auth/profile", method: 'GET' }),
            providesTags: ["Auth"]
        }),

        logout: builder.mutation<void, void>({
            query: () => ({ url: "/auth/logout", method: 'POST' }),
            invalidatesTags: ["Auth"]
        })
    })
})

export const { useLoginMutation, useLogoutMutation, useRegisterMutation, useProfileQuery } = authApi