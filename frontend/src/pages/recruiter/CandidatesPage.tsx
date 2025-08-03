import React, { useState } from "react";
import {
  useGetCandidatesQuery,
  useGetCandidateTestsQuery,
} from "../../api/candidatesApi";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { DataTable } from "../../components/CandidatesTable/data-table";
import { candidateColumns } from "../../components/CandidatesTable/columns";
import { ScrollArea } from "@/components/ui/scroll-area";

const CandidatesPage: React.FC = () => {
  const { data: candidates = [] } = useGetCandidatesQuery();
  const [selectedCandidate, setSelectedCandidate] = useState<null | {
    user_id: number;
    name: string;
  }>();
  const [search, setSearch] = useState("");

  const filteredCandidates = search
    ? candidates.filter((candidate) =>
        [candidate.name, candidate.email].some(
          (field) =>
            typeof field === "string" &&
            field.toLowerCase().includes(search.toLowerCase())
        )
      )
    : candidates;

  const { data: tests = [], isLoading: testsLoading } =
    useGetCandidateTestsQuery(selectedCandidate?.user_id!, {
      skip: !selectedCandidate,
    });

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <DataTable
        columns={candidateColumns}
        data={filteredCandidates}
        onRowClick={setSelectedCandidate}
        onSearchChange={setSearch}
        searchPlaceholder="Search candidates..."
      />

      <Dialog
        open={!!selectedCandidate}
        onOpenChange={() => setSelectedCandidate(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Tests for {selectedCandidate?.name}</DialogTitle>
          </DialogHeader>
          {testsLoading ? (
            <div className="space-y-2">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-10 rounded" />
              ))}
            </div>
          ) : tests.length === 0 ? (
            <p className="text-muted-foreground">
              No tests found for this candidate.
            </p>
          ) : (
            <div className="space-y-2">
              <ScrollArea className="h-96 flex flex-col gap-4">
                {tests.map((test) => (
                  <Card key={test.test_id} className="p-3 border">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-semibold">{test.test_name}</div>
                        <div className="text-xs text-muted-foreground">
                          Status: {test.status}
                        </div>
                      </div>
                      <Badge variant="secondary">
                        {new Date(test.scheduled_at).toLocaleDateString()}
                      </Badge>
                    </div>
                  </Card>
                ))}
              </ScrollArea>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CandidatesPage;
