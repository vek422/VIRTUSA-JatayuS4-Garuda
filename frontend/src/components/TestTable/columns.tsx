import { type ColumnDef } from "@tanstack/react-table";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export type Test = {
  test_id: string;
  test_name: string;
  test_status: "draft" | "ongoing" | "completed" | "scheduled";
  test_created_at: string;
  test_duration: number; // in minutes
  total_candidate: number;
};

export const columns: ColumnDef<Test>[] = [
  {
    accessorKey: "test_id",
    header: "Test ID",
  },
  {
    accessorKey: "test_name",
    header: "Test Name",
  },
  {
    accessorKey: "test_status",
    header: "Status",
    cell: ({ getValue }) => {
      const status = getValue() as string;
      const getStatusBadgeProps = (status: string) => {
        switch (status) {
          case "draft":
            return {
              variant: "outline" as const,
              className: "border-gray-300 text-gray-600 bg-gray-50",
            };
          case "scheduled":
            return {
              variant: "outline" as const,
              className: "border-blue-300 text-blue-700 bg-blue-50",
            };
          case "ongoing":
            return {
              variant: "outline" as const,
              className: "border-yellow-300 text-yellow-700 bg-yellow-50",
            };
          case "completed":
            return {
              variant: "outline" as const,
              className: "border-green-300 text-green-700 bg-green-50",
            };
          default:
            return {
              variant: "outline" as const,
              className: "",
            };
        }
      };

      const { variant, className } = getStatusBadgeProps(status);

      return (
        <Badge variant={variant} className={cn(className)}>
          {status.charAt(0).toUpperCase() + status.slice(1)}
        </Badge>
      );
    },
  },
  {
    accessorKey: "test_created_at",
    header: "Created At",
    cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString(),
  },
  {
    accessorKey: "test_duration",
    header: "Duration (mins)",
  },
  {
    accessorKey: "total_candidate",
    header: "Candidates",
  },
];
