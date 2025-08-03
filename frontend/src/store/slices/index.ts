import { authReducer } from "./authSlice";
import { assessmentReducer } from "./assessmentSlice";
import { combineReducers } from "@reduxjs/toolkit";

export const rootReducer = combineReducers({
    auth: authReducer,
    assessment: assessmentReducer
})