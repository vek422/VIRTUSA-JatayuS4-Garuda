# Frontend Integration Guide: Assessment Candidates API

## Overview

This guide provides complete documentation for frontend integration with the assessment candidates and report generation endpoints. These APIs allow you to display candidate lists, assessment statuses, and generate/retrieve AI-powered assessment reports.

## API Endpoints

### 1. Get Assessment Candidates for a Test

**Endpoint**: `GET /tests/{test_id}/assessments`
**Purpose**: Retrieve all candidates and their assessment details for a specific test

#### Request

```http
GET /tests/20/assessments
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json
```

#### Response Structure

```json
{
  "success": true,
  "data": {
    "test_id": 20,
    "total_candidates": 1,
    "assessments": [
      {
        "assessment_id": 22,
        "candidate_id": 4,
        "candidate_name": "Vedant Kotkar",
        "candidate_email": "vedant@example.com",
        "status": "completed",
        "percentage_score": 23.8,
        "start_time": "2025-07-28T08:30:00",
        "end_time": "2025-07-28T09:00:00",
        "time_taken_seconds": 1800,
        "created_at": "2025-07-28T08:29:45",
        "updated_at": "2025-07-28T09:00:15",
        "application_id": 15
      }
    ]
  }
}
```

### 2. Generate Assessment Report

**Endpoint**: `POST /tests/assessments/{assessment_id}/generate-report`
**Purpose**: Generate an AI-powered assessment report for a specific assessment

#### Request

```http
POST /tests/assessments/22/generate-report
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json
```

#### Response Structure

```json
{
  "success": true,
  "data": {
    "assessment_id": 22,
    "report_generated": true,
    "generated_at": "2025-07-28T09:12:02.971749",
    "report": {
      "candidate_name": "Vedant Kotkar",
      "technical_score": 23.8,
      "passed_H": 1,
      "passed_M": 0,
      "strengths": [],
      "weaknesses": [
        "React.js implementation and optimization",
        "Redux state management",
        "Webpack build tooling configuration"
      ],
      "recommendation": "Not Recommended",
      "domain_mastery": "Novice",
      "alignment_with_jd": "Poor",
      "curiosity_and_learning": "Low",
      "summary_text": "Detailed performance analysis...",
      "skill_gap_analysis": "Skill gap analysis text...",
      "learning_path_recommendations": ["Recommendation 1", "Recommendation 2"],
      "interview_focus_areas": ["Focus area 1", "Focus area 2"],
      "confidence_intervals": "Confidence analysis text..."
    }
  }
}
```

### 3. Get Existing Assessment Report

**Endpoint**: `GET /tests/assessments/{assessment_id}/report`
**Purpose**: Retrieve an existing assessment report

#### Request

```http
GET /tests/assessments/22/report
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json
```

#### Response Structure

```json
{
  "success": true,
  "data": {
    "assessment_id": 22,
    "report": {
      // Same report structure as generate endpoint
    },
    "status": "completed",
    "report_generated": true,
    "last_updated": "2025-07-28T09:12:02.956194"
  }
}
```

## Frontend Implementation Examples

### React/JavaScript Implementation

#### 1. Fetch Assessment Candidates

```javascript
// API service function
export const getAssessmentCandidates = async (testId, token) => {
  try {
    const response = await fetch(`/api/tests/${testId}/assessments`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error fetching assessment candidates:", error);
    throw error;
  }
};

// React component usage
import React, { useState, useEffect } from "react";

const AssessmentCandidatesTable = ({ testId, token }) => {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCandidates = async () => {
      try {
        setLoading(true);
        const response = await getAssessmentCandidates(testId, token);

        if (response.success) {
          setCandidates(response.data.assessments);
        } else {
          throw new Error("Failed to fetch candidates");
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (testId && token) {
      fetchCandidates();
    }
  }, [testId, token]);

  if (loading) return <div>Loading candidates...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="candidates-table">
      <h2>Assessment Candidates (Test ID: {testId})</h2>
      <table>
        <thead>
          <tr>
            <th>Candidate Name</th>
            <th>Email</th>
            <th>Status</th>
            <th>Score (%)</th>
            <th>Time Taken</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {candidates.map((candidate) => (
            <tr key={candidate.assessment_id}>
              <td>{candidate.candidate_name}</td>
              <td>{candidate.candidate_email}</td>
              <td>
                <span className={`status ${candidate.status}`}>
                  {candidate.status}
                </span>
              </td>
              <td>
                {candidate.percentage_score !== null
                  ? `${candidate.percentage_score}%`
                  : "N/A"}
              </td>
              <td>
                {candidate.time_taken_seconds
                  ? formatDuration(candidate.time_taken_seconds)
                  : "N/A"}
              </td>
              <td>
                <button
                  onClick={() => generateReport(candidate.assessment_id)}
                  disabled={candidate.status !== "completed"}
                >
                  Generate Report
                </button>
                <button onClick={() => viewReport(candidate.assessment_id)}>
                  View Report
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// Utility function to format duration
const formatDuration = (seconds) => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  } else {
    return `${secs}s`;
  }
};
```

#### 2. Generate Assessment Report

```javascript
// API service function
export const generateAssessmentReport = async (assessmentId, token) => {
  try {
    const response = await fetch(
      `/api/tests/assessments/${assessmentId}/generate-report`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error generating assessment report:", error);
    throw error;
  }
};

// React component for report generation
const ReportGenerator = ({ assessmentId, token, onReportGenerated }) => {
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);

  const handleGenerateReport = async () => {
    try {
      setGenerating(true);
      setError(null);

      const response = await generateAssessmentReport(assessmentId, token);

      if (response.success) {
        onReportGenerated(response.data);
        alert("Report generated successfully!");
      } else {
        throw new Error("Failed to generate report");
      }
    } catch (err) {
      setError(err.message);
      alert(`Error generating report: ${err.message}`);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <button
      onClick={handleGenerateReport}
      disabled={generating}
      className="generate-report-btn"
    >
      {generating ? "Generating..." : "Generate Report"}
    </button>
  );
};
```

#### 3. Display Assessment Report

```javascript
// React component for displaying report
const AssessmentReportView = ({ report }) => {
  if (!report) {
    return <div>No report available</div>;
  }

  return (
    <div className="assessment-report">
      <div className="report-header">
        <h2>Assessment Report: {report.candidate_name}</h2>
        <div className="score-badge">
          Technical Score: {report.technical_score}%
        </div>
      </div>

      <div className="report-summary">
        <div className="summary-grid">
          <div className="summary-item">
            <label>Recommendation:</label>
            <span
              className={`recommendation ${report.recommendation
                .toLowerCase()
                .replace(" ", "-")}`}
            >
              {report.recommendation}
            </span>
          </div>
          <div className="summary-item">
            <label>Domain Mastery:</label>
            <span>{report.domain_mastery}</span>
          </div>
          <div className="summary-item">
            <label>JD Alignment:</label>
            <span>{report.alignment_with_jd}</span>
          </div>
          <div className="summary-item">
            <label>Learning Curiosity:</label>
            <span>{report.curiosity_and_learning}</span>
          </div>
        </div>
      </div>

      <div className="report-sections">
        <section className="strengths-weaknesses">
          <div className="strengths">
            <h3>Strengths</h3>
            {report.strengths.length > 0 ? (
              <ul>
                {report.strengths.map((strength, index) => (
                  <li key={index}>{strength}</li>
                ))}
              </ul>
            ) : (
              <p>No specific strengths identified</p>
            )}
          </div>

          <div className="weaknesses">
            <h3>Weaknesses</h3>
            {report.weaknesses.length > 0 ? (
              <ul>
                {report.weaknesses.map((weakness, index) => (
                  <li key={index}>{weakness}</li>
                ))}
              </ul>
            ) : (
              <p>No specific weaknesses identified</p>
            )}
          </div>
        </section>

        <section className="summary">
          <h3>Summary</h3>
          <p>{report.summary_text}</p>
        </section>

        <section className="skill-gap">
          <h3>Skill Gap Analysis</h3>
          <p>{report.skill_gap_analysis}</p>
        </section>

        <section className="learning-path">
          <h3>Learning Path Recommendations</h3>
          <ol>
            {report.learning_path_recommendations.map(
              (recommendation, index) => (
                <li key={index}>{recommendation}</li>
              )
            )}
          </ol>
        </section>

        <section className="interview-focus">
          <h3>Interview Focus Areas</h3>
          <ul>
            {report.interview_focus_areas.map((area, index) => (
              <li key={index}>{area}</li>
            ))}
          </ul>
        </section>

        <section className="confidence">
          <h3>Confidence Analysis</h3>
          <p>{report.confidence_intervals}</p>
        </section>
      </div>
    </div>
  );
};
```

## CSS Styling Examples

```css
/* Assessment Candidates Table Styles */
.candidates-table {
  width: 100%;
  margin: 20px 0;
}

.candidates-table table {
  width: 100%;
  border-collapse: collapse;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.candidates-table th,
.candidates-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.candidates-table th {
  background-color: #f8f9fa;
  font-weight: 600;
}

/* Status badges */
.status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
}

.status.completed {
  background-color: #d4edda;
  color: #155724;
}

.status.in-progress {
  background-color: #fff3cd;
  color: #856404;
}

.status.not-started {
  background-color: #f8d7da;
  color: #721c24;
}

/* Report styles */
.assessment-report {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #eee;
}

.score-badge {
  background-color: #007bff;
  color: white;
  padding: 10px 15px;
  border-radius: 8px;
  font-weight: 600;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-bottom: 30px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.summary-item label {
  font-weight: 600;
  color: #666;
  font-size: 14px;
}

.recommendation.recommended {
  color: #28a745;
  font-weight: 600;
}

.recommendation.not-recommended {
  color: #dc3545;
  font-weight: 600;
}

.report-sections section {
  margin-bottom: 30px;
}

.report-sections h3 {
  color: #333;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
  margin-bottom: 15px;
}

.strengths-weaknesses {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
}

.strengths ul,
.weaknesses ul {
  list-style-type: none;
  padding: 0;
}

.strengths li {
  background-color: #d4edda;
  color: #155724;
  padding: 8px 12px;
  margin-bottom: 8px;
  border-radius: 4px;
  border-left: 4px solid #28a745;
}

.weaknesses li {
  background-color: #f8d7da;
  color: #721c24;
  padding: 8px 12px;
  margin-bottom: 8px;
  border-radius: 4px;
  border-left: 4px solid #dc3545;
}
```

## Error Handling

### Common Error Scenarios

1. **Unauthorized Access (401)**

```javascript
if (response.status === 401) {
  // Redirect to login or refresh token
  window.location.href = "/login";
}
```

2. **Assessment Not Found (404)**

```javascript
if (response.status === 404) {
  setError("Assessment not found");
}
```

3. **Server Error (500)**

```javascript
if (response.status >= 500) {
  setError("Server error. Please try again later.");
}
```

## Best Practices

### 1. Loading States

- Always show loading indicators during API calls
- Disable buttons during report generation to prevent multiple requests

### 2. Error Handling

- Display user-friendly error messages
- Implement retry logic for network failures
- Log errors for debugging

### 3. Data Refresh

- Refresh candidate list after report generation
- Implement auto-refresh for real-time updates
- Cache reports to avoid unnecessary API calls

### 4. Performance

- Implement pagination for large candidate lists
- Use lazy loading for report details
- Optimize re-renders with React.memo or similar

### 5. Accessibility

- Use semantic HTML elements
- Provide proper ARIA labels
- Ensure keyboard navigation support

## Testing Examples

### Unit Test Example (Jest + React Testing Library)

```javascript
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import AssessmentCandidatesTable from "./AssessmentCandidatesTable";

// Mock API
jest.mock("../services/api", () => ({
  getAssessmentCandidates: jest.fn(),
}));

test("displays candidates correctly", async () => {
  const mockCandidates = {
    success: true,
    data: {
      assessments: [
        {
          assessment_id: 22,
          candidate_name: "John Doe",
          candidate_email: "john@example.com",
          status: "completed",
          percentage_score: 85.5,
        },
      ],
    },
  };

  require("../services/api").getAssessmentCandidates.mockResolvedValue(
    mockCandidates
  );

  render(<AssessmentCandidatesTable testId={20} token="mock-token" />);

  await waitFor(() => {
    expect(screen.getByText("John Doe")).toBeInTheDocument();
    expect(screen.getByText("john@example.com")).toBeInTheDocument();
    expect(screen.getByText("85.5%")).toBeInTheDocument();
  });
});
```

## Security Considerations

This documentation provides everything needed for frontend integration with the assessment candidates and reporting system. The endpoints are fully tested and ready for production use.
follow this

given above is doucmentation provided by frontend for getting the repor details it is named as test/testId/asssessment but has the data that we need follow the input and output and intergrate it in the report.tsx folloow the proper structure of rtk as we have did for other requests
