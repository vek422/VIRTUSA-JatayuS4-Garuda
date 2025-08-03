import React, { useState, useEffect } from "react";
import { useAssessmentWebSocket } from "../../hooks/useAssessmentWebSocket";
import { useAppSelector } from "../../store";

interface AssessmentWebSocketExampleProps {
  testId: number;
}

const AssessmentWebSocketExample: React.FC<AssessmentWebSocketExampleProps> = ({
  testId,
}) => {
  const [selectedOption, setSelectedOption] = useState<string>("");

  // Use the WebSocket hook
  const {
    connectionStatus,
    assessmentStarted,
    assessmentCompleted,
    currentQuestion,
    progress,
    currentError,
    reconnectAttempts,
    submitAnswer,
    requestQuestion,
    completeAssessment,
    startAssessment,
    resetAssessment,
    isConnected,
    isConnecting,
    hasError,
  } = useAssessmentWebSocket({
    testId,
    autoStart: true,
  });

  // Get additional state from Redux if needed
  const { responses, past_questions, final_score } = useAppSelector(
    (state) => state.assessment
  );

  // Handle answer submission
  const handleSubmitAnswer = () => {
    if (currentQuestion && selectedOption) {
      submitAnswer(currentQuestion.question_id, selectedOption);
      setSelectedOption("");
    }
  };

  // Auto-scroll to top when new question arrives
  useEffect(() => {
    if (currentQuestion) {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }, [currentQuestion?.question_id]);

  // Connection status display
  const renderConnectionStatus = () => {
    switch (connectionStatus) {
      case "connecting":
        return (
          <div className="status connecting">
            🔄 Connecting to assessment...
          </div>
        );
      case "connected":
        return <div className="status connected">✅ Connected</div>;
      case "reconnecting":
        return (
          <div className="status reconnecting">
            🔄 Reconnecting... (Attempt {reconnectAttempts})
          </div>
        );
      case "error":
        return <div className="status error">❌ Connection Error</div>;
      case "disconnected":
        return <div className="status disconnected">⭕ Disconnected</div>;
      default:
        return null;
    }
  };

  // Error display
  if (hasError && currentError) {
    return (
      <div className="assessment-error">
        <h2>Assessment Error</h2>
        <p>{currentError}</p>
        <button onClick={() => window.location.reload()}>Reload Page</button>
      </div>
    );
  }

  // Assessment completed
  if (assessmentCompleted) {
    return (
      <div className="assessment-completed">
        <h2>🎉 Assessment Completed!</h2>
        {final_score !== null && (
          <div className="results">
            <p>
              <strong>Final Score:</strong> {final_score}%
            </p>
            <p>
              <strong>Questions Answered:</strong>{" "}
              {Object.keys(responses).length}
            </p>
            <p>
              <strong>Total Questions:</strong>{" "}
              {past_questions.length + (currentQuestion ? 1 : 0)}
            </p>
          </div>
        )}
        <button onClick={resetAssessment} className="restart-btn">
          Start New Assessment
        </button>
      </div>
    );
  }

  // Not connected yet
  if (!isConnected) {
    return (
      <div className="assessment-loading">
        {renderConnectionStatus()}
        {isConnecting && (
          <p>Please wait while we establish a secure connection...</p>
        )}
      </div>
    );
  }

  // Assessment not started
  if (!assessmentStarted) {
    return (
      <div className="assessment-waiting">
        {renderConnectionStatus()}
        <h2>Starting Assessment...</h2>
        <p>Please wait while we prepare your assessment.</p>
        <button onClick={startAssessment} className="manual-start-btn">
          Start Assessment Manually
        </button>
      </div>
    );
  }

  // No current question yet
  if (!currentQuestion) {
    return (
      <div className="assessment-loading">
        {renderConnectionStatus()}
        <h2>Loading Question...</h2>
        <p>Please wait while we fetch your next question.</p>
        {progress && (
          <div className="progress-info">
            Progress: {progress.answered_questions}/{progress.total_questions} (
            {(
              (progress.answered_questions / progress.total_questions) *
              100
            ).toFixed(1)}
            %)
          </div>
        )}
        <button onClick={requestQuestion} className="retry-btn">
          Request Question
        </button>
      </div>
    );
  }

  // Main assessment interface
  return (
    <div className="assessment-interface">
      {/* Header */}
      <div className="assessment-header">
        {renderConnectionStatus()}

        {progress && (
          <div className="progress-bar">
            <div className="progress-info">
              Question {progress.answered_questions + 1} of{" "}
              {progress.total_questions} (
              {(
                (progress.answered_questions / progress.total_questions) *
                100
              ).toFixed(1)}
              % Complete)
            </div>
            <div className="progress-track">
              <div
                className="progress-fill"
                style={{
                  width: `${
                    (progress.answered_questions / progress.total_questions) *
                    100
                  }%`,
                }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Question */}
      <div className="question-container">
        <div className="question-meta">
          <span className="skill">{currentQuestion.skill}</span>
          <span className="difficulty">{currentQuestion.difficulty}</span>
          {currentQuestion.time_limit > 0 && (
            <span className="time-limit">⏱️ {currentQuestion.time_limit}s</span>
          )}
        </div>

        <h2 className="question-text">{currentQuestion.text}</h2>

        <div className="options-container">
          {currentQuestion.options.map((option) => (
            <label key={option.option_id} className="option-label">
              <input
                type="radio"
                name="answer"
                value={option.option_id}
                checked={selectedOption === option.option_id}
                onChange={(e) => setSelectedOption(e.target.value)}
                className="option-input"
              />
              <span className="option-content">
                <span className="option-id">{option.option_id}</span>
                <span className="option-text">{option.option}</span>
              </span>
            </label>
          ))}
        </div>

        <div className="action-buttons">
          <button
            onClick={handleSubmitAnswer}
            disabled={!selectedOption}
            className="submit-btn"
          >
            Submit Answer
          </button>

          {progress &&
            progress.answered_questions >= progress.total_questions && (
              <button onClick={completeAssessment} className="complete-btn">
                Complete Assessment
              </button>
            )}
        </div>
      </div>

      {/* Debug info (remove in production) */}
      {import.meta.env.DEV && (
        <div className="debug-info">
          <details>
            <summary>Debug Info</summary>
            <pre>
              {JSON.stringify(
                {
                  connectionStatus,
                  assessmentStarted,
                  questionId: currentQuestion.question_id,
                  responsesCount: Object.keys(responses).length,
                  reconnectAttempts,
                },
                null,
                2
              )}
            </pre>
          </details>
        </div>
      )}
    </div>
  );
};

export default AssessmentWebSocketExample;
