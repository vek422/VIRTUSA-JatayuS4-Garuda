import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Loader2, RefreshCw, Users, XCircle } from "lucide-react";

export default function CandidateTable({
  refetchCandidates,
  candidatesLoading,
  sortedCandidates,
  candidatesError,
}: {
  refetchCandidates: () => void;
  candidatesLoading: boolean;
  sortedCandidates: any[];
  candidatesError: string;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Candidate List
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetchCandidates()}
            disabled={candidatesLoading}
          >
            <RefreshCw
              className={`h-4 w-4 mr-2 ${
                candidatesLoading ? "animate-spin" : ""
              }`}
            />
            Refresh
          </Button>
        </CardTitle>
        <CardDescription>
          Manage candidates for this test ({sortedCandidates?.length || 0}{" "}
          total)
        </CardDescription>
      </CardHeader>
      <CardContent>
        {candidatesLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span className="ml-2">Loading candidates...</span>
          </div>
        ) : candidatesError ? (
          <div className="flex items-center justify-center py-8 text-red-600">
            <XCircle className="h-6 w-6" />
            <span className="ml-2">
              Failed to load candidates. Please try refreshing the page.
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetchCandidates()}
              className="ml-4"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        ) : sortedCandidates && sortedCandidates.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Rank</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Resume Link</TableHead>
                <TableHead>Score</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Screening Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedCandidates.map((candidate, index) => (
                <TableRow key={candidate.key}>
                  <TableCell className="font-medium">
                    <div className="flex items-center">
                      {candidate.resume_score !== null &&
                      candidate.resume_score !== undefined ? (
                        <span
                          className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-semibold ${
                            index === 0
                              ? "bg-yellow-100 text-yellow-800"
                              : index === 1
                              ? "bg-gray-100 text-gray-800"
                              : index === 2
                              ? "bg-orange-100 text-orange-800"
                              : "bg-blue-100 text-blue-800"
                          }`}
                        >
                          {index + 1}
                        </span>
                      ) : (
                        <span className="inline-flex items-center justify-center w-8 h-8 rounded-full text-sm bg-gray-50 text-gray-400">
                          -
                        </span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="font-medium">
                    {candidate.name}
                  </TableCell>
                  <TableCell>{candidate.email}</TableCell>
                  <TableCell>
                    <a
                      href={candidate.resume_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline text-sm"
                    >
                      View Resume
                    </a>
                  </TableCell>
                  <TableCell>
                    {candidate.resume_score !== null &&
                    candidate.resume_score !== undefined ? (
                      <span
                        className={`px-2 py-1 rounded text-xs ${
                          candidate.resume_score >= 80
                            ? "bg-green-100 text-green-800"
                            : candidate.resume_score >= 60
                            ? "bg-blue-100 text-blue-800"
                            : candidate.resume_score >= 40
                            ? "bg-yellow-100 text-yellow-800"
                            : "bg-red-100 text-red-800"
                        }`}
                      >
                        {candidate.resume_score}%
                      </span>
                    ) : (
                      
                    )}
                  </TableCell>
                  <TableCell>
                    {candidate.is_shortlisted ? (
                      <span className="px-2 py-1 rounded text-xs bg-green-100 text-green-800">
                        Shortlisted
                      </span>
                    ) : (
                      <span className="px-2 py-1 rounded text-xs bg-red-100 text-red-800">
                        Not Shortlisted
                      </span>
                    )}
                  </TableCell>
                  <TableCell>
                    {candidate.screening_status === "completed" ? (
                      <span className="px-2 py-1 rounded text-xs bg-green-100 text-green-800">
                        Completed
                      </span>
                    ) : candidate.screening_status === "pending" ? (
                      <span className="px-2 py-1 rounded text-xs bg-yellow-100 text-yellow-800">
                        Pending
                      </span>
                    ) : candidate.screening_status === "failed" ? (
                      <span className="px-2 py-1 rounded text-xs bg-red-100 text-red-800">
                        Failed
                      </span>
                    ) : (
                      <span className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-800">
                        N/A
                      </span>
                    )}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <Settings className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent>
                        <DropdownMenuItem
                          onClick={() =>
                            handleShortlistSingle(candidate.application_id)
                          }
                          disabled={isShortlistingSingle}
                        >
                          <Mail className="h-4 w-4 mr-2" />
                          {isShortlistingSingle
                            ? "Shortlisting..."
                            : "Shortlist & Send Invite"}
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Download className="h-4 w-4 mr-2" />
                          Download Resume
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() =>
                            handleViewResult(candidate.application_id)
                          }
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          View Results
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          className="text-red-600"
                          onClick={() =>
                            handleDeleteCandidate(
                              candidate.application_id,
                              candidate
                            )
                          }
                          disabled={isDeletingCandidate}
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          {isDeletingCandidate ? "Removing..." : "Remove"}
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            <Users className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No candidates uploaded yet</p>
            <p className="text-sm">Upload an Excel file to add candidates</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
