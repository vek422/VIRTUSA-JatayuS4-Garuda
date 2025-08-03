import { Card } from "@/components/ui/card";
import { RegistrationForm } from "../../components/RegistrationForm";
import { Link, useNavigate } from "react-router-dom";
import { useRegisterMutation } from "@/api/authApi";
import { ModeToggle } from "@/components/mode-toggle";
import { useState } from "react";

export default function CandidateRegister() {
  const [register, { isLoading }] = useRegisterMutation();
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleRegister = async (data) => {
    setError(null);
    try {
      await register(data).unwrap();
      navigate("/login");
    } catch (err) {
      if (err?.data?.detail && Array.isArray(err.data.detail)) {
        const messages = err.data.detail.map((d) => d.msg).filter(Boolean);
        setError(messages.join("\n"));
      } else {
        setError(err?.data?.message || "Registration failed");
      }
    }
  };

  return (
    <div className="flex w-screen h-screen items-center justify-center bg-background">
      <div className="absolute top-0 left-0 w-full flex items-center justify-between px-8 py-2 bg-transparent backdrop-blur-md ">
        <div className="text-2xl font-bold text-primary">Skill Sync</div>
        <ModeToggle />
      </div>
      <Card>
        <RegistrationForm
          onSubmit={handleRegister}
          loading={isLoading}
          error={error}
          title="Candidate Registration"
          role="candidate"
        />
        <p className="mt-6 text-sm text-center text-gray-600">
          Already have an account?{" "}
          <Link to="/login" className="text-primary hover:underline">
            Login
          </Link>
        </p>
      </Card>
    </div>
  );
}
