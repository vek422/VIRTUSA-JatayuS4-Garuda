import { BASE_URL } from '@/config';
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export interface Log {
  id: number;
  timestamp: string;
  action: string;
  status: string;
  details: string;
  user: string;
  entity: string | null;
  source: string;
}

export interface FetchLogsParams {
  skip?: number;
  limit?: number;
  user?: string;
  action?: string;
  status?: string;
  entity?: string;
  source?: string;
}

export const logsApi = createApi({
  reducerPath: 'logsApi',
  baseQuery: fetchBaseQuery({
    baseUrl: BASE_URL,
    prepareHeaders: (headers, { getState }) => {
      // Adjust this path if your token is stored elsewhere
      const token = (getState() as { auth?: { token?: string } }).auth?.token;
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  endpoints: (builder) => ({
    getLogs: builder.query<Log[], FetchLogsParams>({
      query: (params) => {
        const searchParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== '') {
            searchParams.append(key, String(value));
          }
        });
        // Always send skip and limit, defaulting to 0 and 50 if not provided
        if (!searchParams.has('skip')) searchParams.append('skip', '0');
        if (!searchParams.has('limit')) searchParams.append('limit', '50');
        return `/logs?${searchParams.toString()}`;
      },
    }),
  }),
});

export const { useGetLogsQuery } = logsApi;
