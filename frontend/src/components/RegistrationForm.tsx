import { useState } from "react";
import { Input } from "../components/ui/input";
import { Button } from "../components/ui/button";
import { Label } from "../components/ui/label";

export interface RegistrationData {
  role: "recruiter" | "candidate";
  name: string;
  email: string;
  password: string;
}

export interface RegistrationFormProps {
  onSubmit: (data: RegistrationData) => void;
  loading?: boolean;
  error?: string | null;
  title?: string;
  role: "recruiter" | "candidate";
}

export function RegistrationForm({
  onSubmit,
  loading,
  error,
  title,
  role,
}: RegistrationFormProps) {
  const [form, setForm] = useState({
    email: "",
    firstName: "",
    lastName: "",
    password: "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit({
      role,
      name: `${form.firstName} ${form.lastName}`,
      email: form.email,
      password: form.password,
    });
  };

  return (
    <div className="flex flex-col items-center justify-center w-full max-w-md px-8">
      <h2 className="mb-6 text-3xl font-semibold text-center text-primary">
        {title || "Register"}
      </h2>
      <form className="space-y-6 w-full" onSubmit={handleSubmit}>
        <div>
          <Label htmlFor="email" className="mb-1 block">
            Email
          </Label>
          <Input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            className="w-full"
            placeholder="you@example.com"
            value={form.email}
            onChange={handleChange}
          />
        </div>
        <div>
          <Label htmlFor="firstName" className="mb-1 block">
            First Name
          </Label>
          <Input
            id="firstName"
            name="firstName"
            type="text"
            required
            className="w-full"
            placeholder="First Name"
            value={form.firstName}
            onChange={handleChange}
          />
        </div>
        <div>
          <Label htmlFor="lastName" className="mb-1 block">
            Last Name
          </Label>
          <Input
            id="lastName"
            name="lastName"
            type="text"
            required
            className="w-full"
            placeholder="Last Name"
            value={form.lastName}
            onChange={handleChange}
          />
        </div>
        <div>
          <Label htmlFor="password" className="mb-1 block">
            Password
          </Label>
          <Input
            id="password"
            name="password"
            type="password"
            autoComplete="new-password"
            required
            className="w-full"
            placeholder="Password"
            value={form.password}
            onChange={handleChange}
          />
        </div>
        {error && (
          <div className="text-red-500 text-sm text-center">{error}</div>
        )}
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Registering..." : "Register"}
        </Button>
      </form>
    </div>
  );
}
