import { useState, useEffect } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import MCQCanvas from "./components/MCQCanvas";
import { Button } from "@/components/ui/button";
import { useAssessmentWebSocket } from "@/hooks/useAssessmentWebSocket";
import { useAppSelector } from "@/store";
import { useParams } from "react-router-dom";

export default function TestInterface() {
  const { id } = useParams<{ id: string }>();
  const [selectedOption, setSelectedOption] = useState<string>("");

  return (
    <ScrollArea className="w-screen h-screen p-5 px-5 flex">
      {/* Test Button for debugging */}
      {isConnected && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-yellow-800">
              Debug Test:
            </span>
            <Button
              onClick={handleTestGetInfo}
              size="sm"
              variant="outline"
              className="text-xs"
            >
              Send get_test_info
            </Button>
            <span className="text-xs text-yellow-600">
              Check console for response
            </span>
          </div>
        </div>
      )}

      {/* Header Section */}
      <div className="flex justify-between">
        <div>
          <h1 className="font-bold text-2xl">Assessment</h1>
          <h1 className="text-gray-600">Test ID: {id}</h1>
          <div className="text-sm text-gray-500">
            Status:{" "}
            <span
              className={`font-medium ${
                connectionStatus === "connected"
                  ? "text-green-600"
                  : "text-yellow-600"
              }`}
            >
              {connectionStatus}
            </span>
          </div>
        </div>
        <div>
          {progress && (
            <div className="text-right">
              <h1 className="font-semibold">
                Question {progress.answered_questions + 1} of{" "}
                {progress.total_questions}
              </h1>
              <div className="text-sm text-gray-600">
                {(
                  (progress.answered_questions / progress.total_questions) *
                  100
                ).toFixed(1)}
                % Complete
              </div>
              {/* Progress bar */}
              <div className="w-32 h-2 bg-gray-200 rounded-full mt-2">
                <div
                  className="h-full bg-blue-500 rounded-full transition-all duration-300"
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
      </div>

      <div>
        <MCQCanvas
          question={currentQuestion}
          selectedOption={selectedOption}
          onOptionSelect={setSelectedOption}
        />
      </div>

      <div className="py-10 flex gap-4">
        <Button onClick={handleSubmitAnswer} disabled={!selectedOption}>
          Submit and Next
        </Button>

        {/* {progress &&
          progress.answered_questions >= progress.total_questions && (
            <Button onClick={handleCompleteAssessment} variant="secondary">
              Complete Assessment
            </Button>
          )} */}
      </div>
    </ScrollArea>
  );
}
