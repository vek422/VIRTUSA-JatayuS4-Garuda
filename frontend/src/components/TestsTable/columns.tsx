import { type ColumnDef } from "@tanstack/react-table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Edit,
  FileText,
  Trash2,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
} from "lucide-react";
import { Link } from "react-router-dom";
import { type Test } from "@/components/TestTable/columns";
import { cn } from "@/lib/utils";

// Get status badge properties for all possible statuses
const getStatusBadgeProps = (status: string) => {
  switch (status) {
    case "draft":
      return { variant: "outline" as const, className: "border-gray-300 text-gray-600 bg-gray-50" };
    case "scheduled":
      return { variant: "outline" as const, className: "border-blue-300 text-blue-700 bg-blue-50" };
    case "ongoing":
      return { variant: "outline" as const, className: "border-yellow-300 text-yellow-700 bg-yellow-50" };
    case "completed":
      return { variant: "outline" as const, className: "border-green-300 text-green-700 bg-green-50" };
    case "ended":
      return { variant: "outline" as const, className: "border-red-300 text-red-700 bg-red-50" };
    case "published":
      return { variant: "outline" as const, className: "border-purple-300 text-purple-700 bg-purple-50" };
    default:
      return { variant: "outline" as const, className: "border-gray-300 text-gray-600 bg-gray-50" };
  }
};

type ColumnsProps = {
  onDelete: (testId: string) => void;
};

export const createColumns = ({ onDelete }: ColumnsProps): ColumnDef<Test>[] => [
  {
    accessorKey: "test_id",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="h-8 p-0 font-bold text-left justify-start hover:bg-transparent"
        >
          Test ID
          {column.getIsSorted() === "asc" ? (
            <ArrowUp className="ml-2 h-4 w-4" />
          ) : column.getIsSorted() === "desc" ? (
            <ArrowDown className="ml-2 h-4 w-4" />
          ) : (
            <ArrowUpDown className="ml-2 h-4 w-4" />
          )}
        </Button>
      );
    },
    cell: ({ row }) => (
      <div className="font-medium">{row.getValue("test_id")}</div>
    ),
  },
// ...existing code...

// Add this column INSIDE the exported array if you want to show job description:
// {
//   accessorKey: "job_description",
//   header: "Job Description",
//   cell: ({ row }) => {
//     const desc = row.getValue("job_description") as string;
//     return <span title={desc}>{desc?.slice(0, 60)}{desc && desc.length > 60 ? '...' : ''}</span>;
//   }
// },
  {
    accessorKey: "test_name",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="h-8 p-0 font-bold text-left justify-start hover:bg-transparent"
        >
          Test Name
          {column.getIsSorted() === "asc" ? (
            <ArrowUp className="ml-2 h-4 w-4" />
          ) : column.getIsSorted() === "desc" ? (
            <ArrowDown className="ml-2 h-4 w-4" />
          ) : (
            <ArrowUpDown className="ml-2 h-4 w-4" />
          )}
        </Button>
      );
    },
    cell: ({ row }) => (
      <div className="font-medium hover:text-primary transition-colors">
        {row.getValue("test_name")}
      </div>
    ),
  },
  {
    accessorKey: "test_status",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="h-8 p-0 font-bold text-left justify-start hover:bg-transparent"
        >
          Status
          {column.getIsSorted() === "asc" ? (
            <ArrowUp className="ml-2 h-4 w-4" />
          ) : column.getIsSorted() === "desc" ? (
            <ArrowDown className="ml-2 h-4 w-4" />
          ) : (
            <ArrowUpDown className="ml-2 h-4 w-4" />
          )}
        </Button>
      );
    },
    cell: ({ row }) => {
      const status = row.getValue("test_status") as string;
      const { variant, className } = getStatusBadgeProps(status);
      return (
        <Badge variant={variant} className={cn(className)}>
          {status.charAt(0).toUpperCase() + status.slice(1)}
        </Badge>
      );
    },
    filterFn: (row, id, value) => {
      return value === "all" || row.getValue(id) === value;
    },
  },
  {
    accessorKey: "test_created_at",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="h-8 p-0 font-bold text-left justify-start hover:bg-transparent"
        >
          Created At
          {column.getIsSorted() === "asc" ? (
            <ArrowUp className="ml-2 h-4 w-4" />
          ) : column.getIsSorted() === "desc" ? (
            <ArrowDown className="ml-2 h-4 w-4" />
          ) : (
            <ArrowUpDown className="ml-2 h-4 w-4" />
          )}
        </Button>
      );
    },
    cell: ({ row }) => {
      return new Date(row.getValue("test_created_at")).toLocaleDateString();
    },
  },
  {
    accessorKey: "test_duration",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="h-8 p-0 font-bold text-left justify-start hover:bg-transparent"
        >
          Duration
          {column.getIsSorted() === "asc" ? (
            <ArrowUp className="ml-2 h-4 w-4" />
          ) : column.getIsSorted() === "desc" ? (
            <ArrowDown className="ml-2 h-4 w-4" />
          ) : (
            <ArrowUpDown className="ml-2 h-4 w-4" />
          )}
        </Button>
      );
    },
    cell: ({ row }) => {
      return `${row.getValue("test_duration")} mins`;
    },
  },
  {
    accessorKey: "total_candidate",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="h-8 p-0 font-bold text-left justify-start hover:bg-transparent"
        >
          Candidates
          {column.getIsSorted() === "asc" ? (
            <ArrowUp className="ml-2 h-4 w-4" />
          ) : column.getIsSorted() === "desc" ? (
            <ArrowDown className="ml-2 h-4 w-4" />
          ) : (
            <ArrowUpDown className="ml-2 h-4 w-4" />
          )}
        </Button>
      );
    },
    cell: ({ row }) => {
      return row.getValue("total_candidate");
    },
  },
  {
    id: "actions",
    header: () => <div className="text-center font-bold">Actions</div>,
    cell: ({ row }) => {
      const test = row.original;
      return (
        <div className="flex items-center gap-1">
          <Link 
            to={`/recruiter/test/edit/${test.test_id}`}
            onClick={(e) => e.stopPropagation()} // Prevent row click when clicking edit
          >
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              title="Edit Test"
            >
              <Edit className="h-4 w-4" />
            </Button>
          </Link>

          <Link 
            to={`/recruiter/test/${test.test_id}/report`}
            onClick={(e) => e.stopPropagation()} // Prevent row click when clicking report
          >
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              title="View Report"
            >
              <FileText className="h-4 w-4" />
            </Button>
          </Link>



          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-destructive hover:text-destructive"
            onClick={(e) => {
              e.stopPropagation(); // Prevent row click when clicking delete
              onDelete(test.test_id);
            }}
            title="Delete Test"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      );
    },
  },
];
