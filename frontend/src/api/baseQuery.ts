import { type BaseQueryFn } from '@reduxjs/toolkit/query/react';
import { type AxiosRequestConfig, AxiosError } from 'axios';
import axiosInstance from "."

interface AxiosBaseQueryArgs {
    url: string;
    method: AxiosRequestConfig['method'];
    data?: AxiosRequestConfig['data'];
    params?: AxiosRequestConfig['params'];
}

export const axiosBaseQuery = (): BaseQueryFn<AxiosBaseQueryArgs, unknown, { status: number; data: any }> => async ({ url, method, data, params }) => {
    try {
        const result = await axiosInstance({ url, method, data, params })
        return { data: result.data }
    } catch (err) {
        const error = err as AxiosError;
        return {
            error: {
                status: error.response?.status ?? 500,
                data: error.response?.data ?? error.message
            }
        }
    }
}