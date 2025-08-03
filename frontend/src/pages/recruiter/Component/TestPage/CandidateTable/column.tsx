import { useDeleteCandidateMutation } from "@/api/candidateApi";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogDescription,
  DialogFooter,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import type { ColumnDef } from "@tanstack/react-table";
import { Loader2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

export type TestCandidate = {
  name: string;
  email: string;
  resume_link: string;
  score: number;
  is_shortlisted: boolean;
  screening_status: string;
  application_id: string;
};

export const columns: ColumnDef<TestCandidate>[] = [
  {
    header: "Rank",
    cell: ({ row }) => <span>{row.index + 1}</span>,
  },
  {
    accessorKey: "name",
    header: "Name",
  },
  {
    accessorKey: "email",
    header: "Email",
  },
  {
    accessorKey: "resume_link",
    header: "Resume Link",
    cell: ({ getValue }) => {
      const link = getValue() as string;
      return (
        <a href={link} target="_blank">
          View Resume
        </a>
      );
    },
  },
  {
    accessorKey: "score",
    header: "Score",
    cell: ({ getValue }) => {
      const resume_score = getValue() as number;
      if (!resume_score)
        return (
          <span className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-800">
            Not Taken
          </span>
        );
      return (
        <span
          className={`px-2 py-1 rounded text-xs ${
            resume_score >= 80
              ? "bg-green-100 text-green-800"
              : resume_score >= 60
              ? "bg-blue-100 text-blue-800"
              : resume_score >= 40
              ? "bg-yellow-100 text-yellow-800"
              : "bg-red-100 text-red-800"
          }`}
        >
          {resume_score}%
        </span>
      );
    },
  },
  {
    accessorKey: "is_shortlisted",
    header: "Status",
    cell: ({ getValue }) => {
      const isShortlisted = getValue() as boolean;
      if (isShortlisted)
        return (
          <span className="px-2 py-1 rounded text-xs bg-green-100 text-green-800">
            Shortlisted
          </span>
        );
      return (
        <span className="px-2 py-1 rounded text-xs bg-red-100 text-red-800">
          Not Shortlisted
        </span>
      );
    },
  },
  {
    accessorKey: "screening_status",
    header: "Screening Status",
    cell: ({ getValue }) => {
      const screeningStatus = getValue();
      if (screeningStatus === "completed")
        return (
          <span className="px-2 py-1 rounded text-xs bg-green-100 text-green-800">
            Completed
          </span>
        );
      if (screeningStatus === "pending")
        return (
          <span className="px-2 py-1 rounded text-xs bg-yellow-100 text-yellow-800">
            Pending
          </span>
        );
      if (screeningStatus === "failed")
        return (
          <span className="px-2 py-1 rounded text-xs bg-red-100 text-red-800">
            Failed
          </span>
        );
      return (
        <span className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-800">
          N/A
        </span>
      );
    },
  },
  {
    accessorKey: "application_id",
    header: "Action",
    cell: ({ getValue }) => {
      const application_id = getValue();
      return <DeleteCandidate application_id={application_id as number} />;
    },
  },
];

const DeleteCandidate = ({ application_id }: { application_id: number }) => {
  const [deleteCandidate, { isLoading, error }] = useDeleteCandidateMutation();
  const [isOpen, setIsOpen] = useState(false);
  const handleDeleteCandidate = async () => {
    try {
      await deleteCandidate(application_id).unwrap();
      toast("Deleted Candidate");
    } catch (err) {
      toast("Error while removing the candidate");
    } finally {
      setIsOpen(false);
    }
  };
  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger className="text-destructive cursor-pointer">
        Remove
      </PopoverTrigger>
      <PopoverContent>
        <div>Are you sure you want to delete the candidate?</div>

        <div className="flex justify-end gap-2">
          <Button variant={"outline"} onClick={() => setIsOpen(false)}>
            Cancel
          </Button>

          <Button onClick={handleDeleteCandidate} variant={"destructive"}>
            {isLoading ? <Loader2 className="animate-spin" /> : "Remove"}
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
};
