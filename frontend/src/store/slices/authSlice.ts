import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

export type User = {
    name: string;
    email: string;
    role: "candidate" | "recruiter";
    user_id: string
}
type AuthState = {
    user: User | null
    token: string | null;
}

const initialState: AuthState = {
    user: null,
    token: null
}

const authSlice = createSlice({
    name: "auth",
    initialState,
    reducers: {
        setCredentials(state, action: PayloadAction<{ token: string, user: User }>) {
            console.log("Set Credentials")
            state.token = action.payload.token;
            state.user = action.payload.user;
        },
        clearCredentials(state) {
            state.token = null
            state.user = null
        }
    }
})

export const { setCredentials, clearCredentials } = authSlice.actions;
export const authReducer = authSlice.reducer;