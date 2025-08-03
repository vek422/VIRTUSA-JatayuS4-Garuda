import { Link } from "react-router-dom";

const routes = [
	{ path: "/login", label: "Login" },
	{ path: "/recruiter/dashboard", label: "Recruiter Dashboard" },
	{ path: "/recruiter/test/create", label: "Create Test" },
	{ path: "/recruiter/candidates/upload", label: "Upload Candidates" },
	{ path: "/candidate/tests", label: "Candidate Assessments" },
	{ path: "/candidate/completed", label: "Assessment Completed" },
];

export default function FallbackPage() {
	return (
		<div className="min-h-screen flex flex-col items-center justify-center bg-background">
			<h1 className="text-5xl font-bold text-destructive mb-4">
				404 - Page Not Found
			</h1>
			<p className="text-xl text-muted-foreground mb-8 text-center">
				Oops! The page you are looking for does not exist.
				<br />
				Please use one of the links below to navigate:
			</p>
			<ul className="list-none p-0 mb-8">
				{routes.map((route) => (
					<li key={route.path} className="my-3">
						<Link
							to={route.path}
							className="text-primary text-lg underline"
						>
							{route.label}
						</Link>
					</li>
				))}
			</ul>
			<Link
				to="/"
				className="text-white bg-primary px-6 py-2 rounded-lg text-lg no-underline"
			>
				Go to Home
			</Link>
		</div>
	);
}
