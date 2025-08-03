import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import type { ChatMessage } from "@/store/slices/assessmentSlice";

interface ChatMessageProps {
  message: ChatMessage;
  onOptionSelect?: (optionId: string) => void;
  selectedOption?: string;
}

export const ChatMessageComponent = ({
  message,
  onOptionSelect,
  selectedOption,
}: ChatMessageProps) => {
  switch (message.type) {
    case "ai_question":
      return (
        <AIQuestionMessage
          message={message}
          onOptionSelect={onOptionSelect}
          selectedOption={selectedOption}
        />
      );
    case "user_response":
      return <UserResponseMessage message={message} />;
    case "ai_feedback":
      return <AIFeedbackMessage message={message} />;
    case "ai_process":
      return <AIProcessMessage message={message} />;
    case "system":
      return <SystemMessage message={message} />;
    default:
      return null;
  }
};

const AIQuestionMessage = ({
  message,
  onOptionSelect,
  selectedOption,
}: ChatMessageProps) => {
  return (
    <div className="flex items-start gap-3 mb-4">
      <Avatar>
        <AvatarFallback className="bg-blue-100 text-blue-600">
          AI
        </AvatarFallback>
      </Avatar>
      <div className="bg-primary/10 p-4 rounded-lg mr-10 flex-1">
        <p className="font-semibold  mb-2">Question</p>
        <p className=" mb-4 leading-relaxed">{message.content}</p>

        {message.metadata && (
          <div className="flex gap-2 mb-4">
            {message.metadata.skill && (
              <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                {message.metadata.skill}
              </span>
            )}
            {message.metadata.difficulty && (
              <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded-full">
                {message.metadata.difficulty}
              </span>
            )}
          </div>
        )}

        {message.options && message.options.length > 0 && (
          <div className="space-y-2">
            <p className="font-medium  text-sm">Choose your answer:</p>
            {message.options.map((option) => (
              <Button
                key={option.option_id}
                variant={
                  selectedOption === option.option_id ? "default" : "outline"
                }
                className={`w-full justify-start p-3 h-auto text-left transition-all ${
                  selectedOption === option.option_id
                    ? "bg-accent text-white hover:bg-accent"
                    : "hover:bg-gray-50 border-gray-200"
                }`}
                onClick={() => onOptionSelect?.(option.option_id)}
              >
                <span
                  className={`font-bold mr-3 min-w-[24px] ${
                    selectedOption === option.option_id
                      ? "text-white"
                      : "text-blue-600"
                  }`}
                >
                  {option.option_id}.
                </span>
                <span className="flex-1 whitespace-normal text-sm">
                  {option.option}
                </span>
              </Button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const UserResponseMessage = ({ message }: ChatMessageProps) => {
  return (
    <div className="flex items-start gap-3 mb-4 justify-end">
      <div className="bg-secondary  p-3 rounded-lg max-w-md">
        <p className="font-semibold mb-1">Your Answer</p>
        <p className="">{message.content}</p>
      </div>
      <Avatar>
        <AvatarFallback className="bg-green-100 text-green-600">
          U
        </AvatarFallback>
      </Avatar>
    </div>
  );
};

const AIFeedbackMessage = ({ message }: ChatMessageProps) => {
  return (
    <div className="flex items-start gap-3 mb-4">
      <Avatar>
        <AvatarFallback className="bg-purple-100 text-purple-600">
          AI
        </AvatarFallback>
      </Avatar>
      <div className="bg-purple-50 border border-purple-200 p-4 rounded-lg mr-10 flex-1">
        <p className="font-semibold text-purple-800 mb-2">Feedback</p>
        <p className="text-gray-800 leading-relaxed">{message.content}</p>
        {message.metadata?.feedbackMessage && (
          <p className="text-sm text-gray-600 mt-2 italic">
            {message.metadata.feedbackMessage}
          </p>
        )}
      </div>
    </div>
  );
};

const AIProcessMessage = ({ message }: ChatMessageProps) => {
  return (
    <div className="flex items-start gap-3 mb-4">
      <Avatar>
        <AvatarFallback className="bg-gray-100 text-gray-600">
          AI
        </AvatarFallback>
      </Avatar>
      <div className="bg-gray-100 p-3 rounded-lg">
        <span className="text-gray-600 italic text-sm animate-pulse flex items-center gap-2">
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
            <div
              className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
              style={{ animationDelay: "0.1s" }}
            ></div>
            <div
              className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
              style={{ animationDelay: "0.2s" }}
            ></div>
          </div>
          {message.content}
        </span>
      </div>
    </div>
  );
};

const SystemMessage = ({ message }: ChatMessageProps) => {
  return (
    <div className="flex justify-center mb-4">
      <div className="bg-yellow-50 border border-yellow-200 px-3 py-2 rounded-md">
        <span className="text-yellow-700 text-sm font-medium">
          {message.content}
        </span>
      </div>
    </div>
  );
};
