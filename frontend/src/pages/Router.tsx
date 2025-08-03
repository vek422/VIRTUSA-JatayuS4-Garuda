import { useAppSelector } from "@/store";
import { Navigate } from "react-router-dom";

export default function Router() {
  const { token, user } = useAppSelector((state) => state.auth);
  if (!token) return <Navigate to="/login" />;
  if (user?.role && user.role == "candidate")
    return <Navigate to="/candidate" />;
  if (user?.role && user.role == "recruiter")
    return <Navigate to="/recruiter/dashboard" />;
  return <Navigate to="/login" />;
}
