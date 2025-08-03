import { DataTable } from "../CandidatesTable/data-table";
import { logColumns } from "./columns";
import type { Log } from "@/api/logsApi";

interface LogsTableProps {
  data: Log[];
  isLoading?: boolean;
  onSearchChange?: (value: string) => void;
}

export function LogsTable({ data, isLoading, onSearchChange }: LogsTableProps) {
  return (
    <div>
      <DataTable
        columns={logColumns}
        data={data}
        onSearchChange={onSearchChange}
        searchPlaceholder="Search logs..."
        rowClassName="min-h-[44px]"
      />
    </div>
  );
}
