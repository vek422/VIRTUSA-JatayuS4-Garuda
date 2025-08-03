import { Link } from "react-router-dom";

export default function RegisterSelect() {
  return (
    <div className="flex w-screen h-screen items-center justify-center bg-background">
      <div className="flex flex-col items-center justify-center w-full max-w-md p-8 bg-white rounded-lg shadow-md">
        <h2 className="mb-6 text-3xl font-semibold text-center text-primary">Register As</h2>
        <div className="flex flex-col gap-4 w-full">
          <Link
            to="/register/candidate"
            className="w-full py-2 px-4 bg-primary text-white rounded-md text-center hover:bg-primary/90 transition-colors"
          >
            Candidate
          </Link>
          <Link
            to="/register/recruiter"
            className="w-full py-2 px-4 bg-primary text-white rounded-md text-center hover:bg-primary/90 transition-colors"
          >
            Recruiter
          </Link>
        </div>
        <p className="mt-6 text-sm text-center text-gray-600">
          Already have an account?{' '}
          <Link to="/login" className="text-primary hover:underline">Login</Link>
        </p>
      </div>
    </div>
  );
}
