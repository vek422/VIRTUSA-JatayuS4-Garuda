import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import type { Question } from "@/store/slices/assessmentSlice";

interface MCQCanvasProps {
  question: Question;
  selectedOption: string;
  onOptionSelect: (option: string) => void;
}

export default function MCQCanvas({
  question,
  selectedOption,
  onOptionSelect,
}: MCQCanvasProps) {
  return (
    <div>
      {/* Question */}
      <div className="flex flex-col gap-10">
        <Card className="gap-0">
          {/* <CardHeader className="pb-2"></CardHeader> */}
          <CardContent className="pt-0">
            <p className="text-lg leading-relaxed">{question.text}</p>
          </CardContent>
        </Card>

        {/* Options */}
        <div className="flex flex-col gap-5 max-w-full">
          {question.options.map((option) => (
            <Button
              key={option.option_id}
              variant={
                selectedOption === option.option_id ? "default" : "outline"
              }
              className={`justify-start cursor-pointer p-4 h-auto text-left ${
                selectedOption === option.option_id
                  ? "bg-blue-500 text-white hover:bg-blue-600"
                  : "hover:bg-gray-50"
              }`}
              onClick={() => onOptionSelect(option.option_id)}
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
              <span className="flex-1 whitespace-normal">{option.option}</span>
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
}
