import React, { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { useUpdateQuestionCountsMutation } from "@/api/testApi";

interface QuestionCountSettingsProps {
  testId: number;
  highPriorityNodes: number;
  mediumPriorityNodes: number;
  lowPriorityNodes: number;
  initialHigh: number;
  initialMedium: number;
  initialLow: number;
  initialTimeLimit: number;
}

const getMinQuestions = (nodes: number, perNode: number) => nodes * perNode;

export const QuestionCountSettings: React.FC<QuestionCountSettingsProps> = ({
  testId,
  highPriorityNodes,
  mediumPriorityNodes,
  lowPriorityNodes,
  initialHigh,
  initialMedium,
  initialLow,
  initialTimeLimit,
}) => {
  const [high, setHigh] = useState(initialHigh);
  const [medium, setMedium] = useState(initialMedium);
  const [low, setLow] = useState(initialLow);
  const [updateQuestionCounts, { isLoading, error, data }] =
    useUpdateQuestionCountsMutation();

  // Minimums
  const minHigh = getMinQuestions(highPriorityNodes, 5);
  const minMedium = getMinQuestions(mediumPriorityNodes, 3);
  const minLow = getMinQuestions(lowPriorityNodes, 3);

  // Per-node
  const perNodeHigh = highPriorityNodes
    ? Math.floor(high / highPriorityNodes)
    : 0;
  const perNodeMedium = mediumPriorityNodes
    ? Math.floor(medium / mediumPriorityNodes)
    : 0;
  const perNodeLow = lowPriorityNodes ? Math.floor(low / lowPriorityNodes) : 0;
  console.log({ perNodeHigh, perNodeLow, perNodeMedium });
  // Total and time
  const totalQuestions = high + medium + low;
  const timeLimitMinutes = useMemo(() => {
    return Math.ceil((high * 90 + medium * 60 + low * 45) / 60);
  }, [high, medium, low]);

  const handleChange = (
    setter: (n: number) => void,
    value: number,
    min: number
  ) => {
    setter(Math.max(min, value));
  };

  const handleSave = async () => {
    await updateQuestionCounts({
      test_id: testId,
      data: {
        high_priority_questions: perNodeHigh,
        medium_priority_questions: perNodeMedium,
        low_priority_questions: perNodeLow,
        total_questions: totalQuestions,
        time_limit_minutes: timeLimitMinutes,
      },
    });
  };

  return (
    <div className="p-4 border rounded-lg bg-muted flex flex-col gap-6 max-w-xl">
      <div className="flex flex-col gap-2">
        <Label>High Priority Questions</Label>
        <div className="flex items-center gap-2">
          <Button
            size="icon"
            variant="outline"
            onClick={() =>
              handleChange(setHigh, high - highPriorityNodes, minHigh)
            }
          >
            -
          </Button>
          <Input
            type="number"
            value={high}
            min={minHigh}
            readOnly
            className="w-20 text-center"
          />
          <Button
            size="icon"
            variant="outline"
            onClick={() => setHigh(high + highPriorityNodes)}
          >
            +
          </Button>
          <span className="ml-2 text-xs text-muted-foreground">
            min: {minHigh} | per node: {perNodeHigh}
          </span>
        </div>
      </div>
      <div className="flex flex-col gap-2">
        <Label>Medium Priority Questions</Label>
        <div className="flex items-center gap-2">
          <Button
            size="icon"
            variant="outline"
            onClick={() =>
              handleChange(setMedium, medium - mediumPriorityNodes, minMedium)
            }
          >
            -
          </Button>
          <Input
            type="number"
            value={medium}
            min={minMedium}
            readOnly
            className="w-20 text-center"
          />
          <Button
            size="icon"
            variant="outline"
            onClick={() => setMedium(medium + mediumPriorityNodes)}
          >
            +
          </Button>
          <span className="ml-2 text-xs text-muted-foreground">
            min: {minMedium} | per node: {perNodeMedium}
          </span>
        </div>
      </div>
      <div className="flex flex-col gap-2">
        <Label>Low Priority Questions</Label>
        <div className="flex items-center gap-2">
          <Button
            size="icon"
            variant="outline"
            onClick={() => handleChange(setLow, low - lowPriorityNodes, minLow)}
          >
            -
          </Button>
          <Input
            type="number"
            value={low}
            min={minLow}
            readOnly
            className="w-20 text-center"
          />
          <Button
            size="icon"
            variant="outline"
            onClick={() => setLow(low + lowPriorityNodes)}
          >
            +
          </Button>
          <span className="ml-2 text-xs text-muted-foreground">
            min: {minLow} | per node: {perNodeLow}
          </span>
        </div>
      </div>
      <div className="flex flex-col gap-2">
        <Label>Total Questions</Label>
        <Input type="number" value={totalQuestions} readOnly className="w-24" />
      </div>
      <div className="flex flex-col gap-2">
        <Label>Time Limit (minutes)</Label>
        <Input
          type="number"
          value={timeLimitMinutes}
          readOnly
          className="w-24"
        />
      </div>
      <Button onClick={handleSave} disabled={isLoading} className="w-fit">
        {isLoading ? "Saving..." : "Save Settings"}
      </Button>
      {error && (
        <div className="text-red-600 text-sm">
          {(error as any)?.data?.message || "Failed to update."}
        </div>
      )}
      {data && <div className="text-green-600 text-sm">{data.message}</div>}
    </div>
  );
};

export default QuestionCountSettings;
