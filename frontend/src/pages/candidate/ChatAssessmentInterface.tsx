import { useState, useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { useAssessmentWebSocket } from "@/hooks/useAssessmentWebSocket";
import { useParams } from "react-router-dom";
import { ChatMessageComponent } from "./components/ChatMessages";
import SubmitTest from "./components/SubmitTest";

export default function ChatAssessmentInterface() {
  const { id } = useParams<{ id: string }>();
  const [selectedOption, setSelectedOption] = useState<string>("");
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const {
    test_name,
    connectionStatus,
    assessmentStarted,
    assessmentCompleted,
    currentQuestion,
    progress,
    currentError,
    submitAnswer,
    completeAssessment,
    startAssessment,
    isConnected,
    hasError,
    chatHistory,
    interactionType,
    sendDebugMessage,
    processMessage,
  } = useAssessmentWebSocket({
    testId: id ? parseInt(id) : 0,
    autoStart: false,
  });
  // auto scroll logic
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      );
      if (scrollContainer) {
        scrollContainer.scrollTo({
          top: scrollContainer.scrollHeight,
          behavior: "smooth",
        });
      }
    }
  }, [chatHistory]);

  const handleOptionSelect = (optionId: string) => {
    if (interactionType !== "waiting_response") return;
    setSelectedOption(optionId);
  };

  const handleSubmitAnswer = () => {
    if (
      !selectedOption ||
      !currentQuestion ||
      interactionType !== "waiting_response"
    )
      return;

    submitAnswer(currentQuestion.question_id, selectedOption);
    setSelectedOption("");
  };

  const canSubmit =
    selectedOption && interactionType === "waiting_response" && currentQuestion;

  if (hasError) {
    return (
      <div className="w-screen h-screen flex justify-center  overflow-hidden">
        <div className="flex flex-col gap-2 w-[80%] max-w-4xl">
          <Header testName={test_name || ""} />
          <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
            <h1 className="font-bold text-2xl text-red-600">
              Connection Error
            </h1>
            <p className="">{currentError}</p>
            <Button onClick={() => window.location.reload()}>
              Reload Page
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (assessmentCompleted) {
    return (
      <div className="w-screen h-screen flex justify-center bg-gradient-to-br from-green-50 to-blue-50 overflow-hidden">
        <div className="flex flex-col gap-2 w-[80%] max-w-4xl">
          <Header testName={test_name || ""} testId={id} />
          <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
            <h1 className="font-bold text-3xl text-green-600">
              Assessment Completed!
            </h1>
            <p className="text-gray-600 text-center">
              Thank you for completing the assessment. Your responses have been
              recorded.
            </p>
            {progress && (
              <div className="p-4 rounded-lg shadow-sm">
                <p className="text-sm">
                  Final Progress: {Number(progress).toFixed(1)}%
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (!isConnected) {
    return (
      <div className="w-screen h-screen flex justify-center bg-gradient-to-br from-gray-50 to-blue-50 overflow-hidden">
        <div className="flex flex-col gap-2 w-[80%] max-w-4xl">
          <Header />
          <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
            <h1 className="font-bold text-2xl">Connecting...</h1>
            <div className="text-sm text-gray-600">
              Status: {connectionStatus}
            </div>
            <div className="flex space-x-1">
              <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce"></div>
              <div
                className="w-3 h-3 bg-blue-500 rounded-full animate-bounce"
                style={{ animationDelay: "0.1s" }}
              ></div>
              <div
                className="w-3 h-3 bg-blue-500 rounded-full animate-bounce"
                style={{ animationDelay: "0.2s" }}
              ></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!assessmentStarted) {
    return (
      <div className="w-screen h-screen flex justify-center bg-gradient-to-br overflow-hidden">
        <div className="flex flex-col gap-2 w-[80%] max-w-4xl">
          <Header />
          <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
            <h1 className="font-bold text-3xl">Ready to Start Assessment?</h1>
            <p className="text-center max-w-md">
              Your assessment is ready to begin. You'll have a
              conversation-style experience where questions and feedback will
              appear as chat messages.
            </p>
            <Button onClick={startAssessment} size="lg" className="mt-4">
              Start Assessment
            </Button>
            <div className="text-sm">
              Test ID: {id} | Status: {connectionStatus}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-screen h-screen flex justify-center bg-gradient-to-br  overflow-hidden">
      <div className="flex flex-col gap-2 w-[80%] max-w-4xl">
        {/* <Button
          onClick={() => {
            sendDebugMessage();
          }}
        >
          debug
        </Button> */}
        <Header
          progress={progress}
          testId={id}
          connectionStatus={connectionStatus}
          testName={test_name || ""}
        />

        <ScrollArea ref={scrollAreaRef} className="flex-1 p-6 pt-0  h-[40vh]">
          <div className="flex flex-col gap-4 pb-20">
            {chatHistory.map((message) => (
              <ChatMessageComponent
                key={message.id}
                message={message}
                onOptionSelect={handleOptionSelect}
                selectedOption={
                  message.question_id === currentQuestion?.question_id
                    ? selectedOption
                    : undefined
                }
              />
            ))}
            {processMessage && (
              <div className="transition-all duration-300 ease-in-out opacity-100 transform translate-y-0">
                <ChatMessageComponent
                  message={{
                    type: "ai_process",
                    content: processMessage,
                    id: "-1",
                    timestamp: "none",
                  }}
                />
              </div>
            )}
            {canSubmit && (
              <div className="flex justify-end gap-2 mt-4">
                <Button onClick={handleSubmitAnswer} variant={"default"}>
                  Submit Answer
                </Button>
              </div>
            )}
          </div>
        </ScrollArea>

        {assessmentStarted && (
          <div className="p-4  flex justify-end">
            <SubmitTest completeAssessment={completeAssessment} />
          </div>
        )}
      </div>
    </div>
  );
}

const Header = ({
  progress,
  testId,
  connectionStatus,
  testName,
}: {
  progress?: number;
  testId?: string;
  connectionStatus?: string;
  testName: string;
}) => {
  return (
    <div className="w-full bg-background border-bp-4 flex justify-between items-center">
      <div>
        <h1 className="font-bold text-2xl ">{testName}</h1>
        {testId && <p className="text-sm ">Test ID: {testId}</p>}
        {connectionStatus && (
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
        )}
      </div>
      {progress !== undefined && (
        <div className="text-right">
          <div className="text-sm mb-1">
            {Number(progress).toFixed(1)}% Complete
          </div>
          <div className="w-32 h-2 bg-gray-200 rounded-full">
            <div
              className="h-full bg-blue-500 rounded-full transition-all duration-300"
              style={{
                width: `${progress}%`,
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
};
