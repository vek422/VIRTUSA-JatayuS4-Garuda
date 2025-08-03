import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import { CircleAlert } from "lucide-react";

export default function TestInstructionPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [instructionsRead, setInstructionsRead] = useState(false);
  const test_instructions: string[] = [
    "The test must be completed in one sitting.",
    "Do not refresh or close the tab once the test has started.",
    "You cannot go back to a question once answered.",
    "The timer will start immediately after you begin.",
    "Answers are auto-saved and cannot be changed later",
    "Avoid switching tabs; it may be flagged",
  ];

  const handleStartTest = () => {
    if (!instructionsRead) {
      alert(
        "Please read and accept all instructions before starting the test."
      );
      return;
    }

    if (!id) {
      alert("Test ID is missing. Please try again.");
      return;
    }

    // Navigate to the test interface
    navigate(`/candidate/test/${id}`);
  };
  return (
    <ScrollArea className="h-screen w-screen px-10 py-10 flex flex-col gap-5">
      {/* Header Section */}
      <div className="flex justify-between">
        <div>
          <h1 className="text-4xl font-bold ">Test Title</h1>
          <h2 className="text-2xl ">test_id</h2>
        </div>
        <div>
          <h1 className="text-right">You can start test in 12:00 min</h1>
          <h1 className="text-right">Test Duration 180 Min</h1>
        </div>
      </div>
      <div className="col-span-3 mt-5">
        <Card className=" ">
          <CardHeader>
            <h1 className="text-xl font-bold">Instructions</h1>
            <p>Please read all instructions carefully before starting</p>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {test_instructions.map((value) => (
              <div className="p-2 bg-primary/20 rounded-md">{value}</div>
            ))}
          </CardContent>
        </Card>
      </div>
      <div className="col-span-2">
        <Card className="bg-amber-300/10 mt-5 p-2">
          <span className="flex gap-2 font-bold">
            <CircleAlert /> Disclamer
          </span>
          <p>
            The number, type, and difficulty of questions may vary depending on
            the role and skills being evaluated. You will be allotted sufficient
            time based on the nature and complexity of the questions. The system
            ensures fairness and consistency for all candidates.
          </p>
        </Card>
      </div>
      <div className="my-5">
        <div className="flex gap-2 items-center">
          <Checkbox
            className="border-2 border-primary"
            checked={instructionsRead}
            onCheckedChange={(checked) => setInstructionsRead(!!checked)}
          />
          <p> I have read all instructions </p>
        </div>
      </div>
      <div className=" flex justify-center">
        <Button
          className="m-auto"
          onClick={handleStartTest}
          disabled={!instructionsRead}
        >
          Start Test
        </Button>
      </div>
    </ScrollArea>
  );
}
