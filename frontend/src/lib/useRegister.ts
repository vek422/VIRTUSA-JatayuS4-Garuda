import { useState } from "react";

export interface RegistrationData {
    email: string;
    firstName: string;
    lastName: string;
    password: string;
}

export function useRegister(role: "candidate" | "recruiter") {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const submitRegister = async (data: RegistrationData) => {
        setLoading(true);
        setError(null);
        try {
            // // Replace with your actual API endpoint
            // const response = await fetch(`/api/register/${role}`, {
            //     method: "POST",
            //     headers: { "Content-Type": "application/json" },
            //     body: JSON.stringify(data),
            // });
            // if (!response.ok) {
            //     throw new Error("Registration failed");
            // }
            // Optionally handle response
            // return await response.json();
            console.log("Registering user:", { role, ...data });
        } catch (err: any) {
            setError(err.message || "Unknown error");
            throw err;
        } finally {
            setLoading(false);
        }
    };

    return { submitRegister, loading, error, role };
}
