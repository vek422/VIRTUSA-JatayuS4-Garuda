import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

export interface LoginFormProps {
  onSubmit: (data: { email: string; password: string }) => void | Promise<void>;
  loading?: boolean;
  error?: string | null;
}

export function LoginForm({ onSubmit, loading, error }: LoginFormProps) {
  const [form, setForm] = useState({ email: "", password: "" });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit(form);
  };

  return (
    <div className="flex flex-col items-center justify-center w-full max-w-md px-8">
      <h2 className="mb-6 text-3xl font-semibold text-center text-primary">Login</h2>
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
            disabled={loading}
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
            autoComplete="current-password"
            required
            className="w-full"
            placeholder=""
            value={form.password}
            onChange={handleChange}
            disabled={loading}
          />
        </div>
        {error && <div className="text-red-500 text-sm text-center">{error}</div>}
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Logging in..." : "Login"}
        </Button>
      </form>
    </div>
  );
}
