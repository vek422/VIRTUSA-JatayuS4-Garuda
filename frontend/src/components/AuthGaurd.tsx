import { useAppSelector } from "@/store";
import { Navigate } from "react-router-dom";
export const withAuthGaurd = (
  Component: React.ComponentType,
  role: "candidate" | "recruiter"
) => {
  return () => {
    const { user } = useAppSelector((state) => state.auth);

    if (!user) {
      return <Navigate to={"/login"} />;
    }
    if (user.role !== role) return <Navigate to="/" />;
    return <Component />;
  };
};
