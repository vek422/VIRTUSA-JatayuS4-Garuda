import { type ColumnDef } from "@tanstack/react-table";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Eye, MoreHorizontal, ArrowUpDown } from "lucide-react";
import { type Assessment } from "@/api/assessmentApi";
import { format, parseISO, differenceInSeconds, isValid } from "date-fns";

const getStatusBadge = (status: string) => {
  const variants = {
    completed: "bg-green-100 text-green-800",
    unknown: "bg-gray-100 text-gray-800",
  };
  return (
    variants[status as keyof typeof variants] || "bg-gray-100 text-gray-800"
  );
};

const getInitials = (name: string) => {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase();
};

const formatTime = (seconds: number) => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
};

const calculateTimeDifference = (
  startTime: Date | string | number | null | undefined,
  endTime: Date | string | number | null | undefined
): number => {
  if (!startTime || !endTime) return 0;

  try {
    const start =
      typeof startTime === "string" ? parseISO(startTime) : new Date(startTime);
    const end =
      typeof endTime === "string" ? parseISO(endTime) : new Date(endTime);

    if (!isValid(start) || !isValid(end)) return 0;

    const diff = differenceInSeconds(end, start);
    return diff > 0 ? diff : 0;
  } catch {
    return 0;
  }
};

const formatDate = (dateInput: Date | string | number | null | undefined) => {
  if (!dateInput) return "No Date";

  try {
    const date =
      typeof dateInput === "string" ? parseISO(dateInput) : new Date(dateInput);

    if (!isValid(date)) return "Invalid Date";

    return format(date, "MMM d, yyyy 'at' h:mm a");
  } catch {
    return "Invalid Date";
  }
};

export const columns: ColumnDef<Assessment>[] = [
  {
    accessorKey: "candidate_name",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="hover:bg-transparent p-0 h-auto font-bold"
        >
          Candidate
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      );
    },
    cell: ({ row }) => {
      const name = row.getValue("candidate_name") as string;
      return (
        <div className="flex items-center space-x-3">
          <Avatar className="h-8 w-8">
            <AvatarFallback className="text-xs">
              {getInitials(name)}
            </AvatarFallback>
          </Avatar>
          <div className="font-medium">{name}</div>
        </div>
      );
    },
  },
  {
    accessorKey: "status",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="hover:bg-transparent p-0 h-auto font-bold"
        >
          Status
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      );
    },
    cell: ({ row }) => {
      const status = row.getValue("status") as string;
      return (
        <Badge className={getStatusBadge(status)} variant="secondary">
          {status === "completed" ? "Completed" : "In Progress"}
        </Badge>
      );
    },
  },
  {
    accessorKey: "percentage_score",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="hover:bg-transparent p-0 h-auto font-bold"
        >
          Score
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      );
    },
    cell: ({ row }) => {
      const score = row.getValue("percentage_score") as number;
      const status = row.getValue("status") as string;

      if (status !== "completed") {
        return <span className="text-muted-foreground">-</span>;
      }

      return <div className="font-medium">{score?.toFixed(1)}%</div>;
    },
  },
  {
    id: "calculated_time",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="hover:bg-transparent p-0 h-auto font-bold"
        >
          Time Taken
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      );
    },
    cell: ({ row }) => {
      const assessment = row.original;
      const status = assessment.status;

      if (
        status !== "completed" ||
        !assessment.created_at ||
        !assessment.end_time
      ) {
        return <span className="text-muted-foreground">-</span>;
      }

      const timeDifferenceSeconds = calculateTimeDifference(
        assessment.created_at,
        assessment.end_time
      );
      return (
        <div className="font-medium">{formatTime(timeDifferenceSeconds)}</div>
      );
    },
  },
  {
    accessorKey: "created_at",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="hover:bg-transparent p-0 h-auto font-bold"
        >
          Started At
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      );
    },
    cell: ({ row }) => {
      const createdAt = row.getValue("created_at") as
        | Date
        | string
        | number
        | null;
      return <div className="text-sm">{formatDate(createdAt)}</div>;
    },
  },
  {
    id: "actions",
    header: "Actions",
    cell: ({ row }) => {
      const assessment = row.original;

      return (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <span className="sr-only">Open menu</span>
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem
              onClick={() => {
                window.location.href = `/recruiter/assessments/${assessment.assessment_id}/report`;
              }}
            >
              <Eye className="mr-2 h-4 w-4" />
              View Report
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
    },
  },
];
