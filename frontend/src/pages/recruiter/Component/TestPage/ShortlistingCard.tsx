import { useShortlistBulkCandidatesMutation } from "@/api/candidateApi";
import { useBulkAddShortlistedToAssessmentsMutation } from "@/api/testApi";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import axios from "axios";
import { Loader2 } from "lucide-react";
import { useState } from "react";
import { useParams } from "react-router-dom";
import { Label } from "recharts";
import { toast } from "sonner";

export default function ShortlistingCard({
  refetchCandidates,
  normalizedCandidates,
}: {
  refetchCandidates: () => void;
  normalizedCandidates: any[];
}) {
  const { testId } = useParams<{ testId: string }>();

  const [bulkAddAssessments, { isLoading: isBulkAddingAssessments }] =
    useBulkAddShortlistedToAssessmentsMutation();
  const [minScore, setMinScore] = useState<number>(60);

  const [shortlistBulk, { isLoading: isShortlisting }] =
    useShortlistBulkCandidatesMutation();
  const handleShortlistBulk = async () => {
    if (!testId) return;
    try {
      const result = await shortlistBulk({
        test_id: Number(testId),
        min_score: minScore,
      }).unwrap();
      if (
        result &&
        result.message &&
        result.message.toLowerCase().includes("shortlisted") &&
        result.message.toLowerCase().includes("notified")
      ) {
        toast(`Shortlisted ${result.shortlisted.length} candidates`);
      }
      refetchCandidates();
    } catch (err: any) {
      console.log(err);
      toast(`Error while shortlisting`);
    }
  };

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle>Manual Shortlisting</CardTitle>
        <CardDescription>
          Select a minimum resume score to shortlist candidates for assessment.
          All candidates with a score above or equal to this threshold will be
          shortlisted and notified.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col md:flex-row items-center gap-4">
        <div className="flex items-center gap-2">
          <Label htmlFor="min-score">Minimum Resume Score</Label>
          <Input
            id="min-score"
            type="number"
            min={0}
            max={100}
            value={minScore}
            onChange={(e) => setMinScore(Number(e.target.value))}
            className="w-24"
          />
        </div>
        <Button
          onClick={handleShortlistBulk}
          disabled={isShortlisting || !testId}
          className="ml-0 md:ml-4"
        >
          {isShortlisting ? (
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
          ) : null}
          Shortlist Candidates
        </Button>
        <Button
          variant="secondary"
          className="ml-0 md:ml-4"
          onClick={async () => {
            try {
              const res = await bulkAddAssessments(Number(testId)).unwrap();
              toast(res.message);
            } catch (err: any) {
              toast("Error while shortlisting Candidate");
            }
            refetchCandidates();
          }}
          disabled={
            isBulkAddingAssessments ||
            normalizedCandidates.filter((c) => c.is_shortlisted).length === 0
          }
        >
          {isBulkAddingAssessments
            ? "Adding..."
            : "Add them to assessment list"}
        </Button>
      </CardContent>
    </Card>
  );
}
