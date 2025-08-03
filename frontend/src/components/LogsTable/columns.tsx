import { type ColumnDef } from "@tanstack/react-table";
import type { Log } from "@/api/logsApi";
import { Badge } from "../ui/badge";

export const logColumns: ColumnDef<Log>[] = [
  {
    accessorKey: "timestamp",
    header: "Timestamp",
    cell: ({ row }) => {
      const log = row.original;
      return (
        <span className="font-mono text-xs">{new Date(log.timestamp).toLocaleString()}</span>
      );
    },
  },
  {
    accessorKey: "action",
    header: "Action",
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => {
      const log = row.original;
      let colorClass = "bg-green-100 text-green-800";
      if (log.status.toLowerCase() === "success") colorClass = "bg-green-100 text-green-800";
      else if (log.status.toLowerCase() === "error" || log.status.toLowerCase() === "fail" || log.status.toLowerCase() === "failed") colorClass = "bg-red-100 text-red-800";
      else if (log.status.toLowerCase() === "pending") colorClass = "bg-yellow-100 text-yellow-800";
      else colorClass = "bg-blue-100 text-blue-800";
      return <Badge className={`capitalize text-sm px-3 py-1.5 ${colorClass}`}>{log.status}</Badge>;
    },
  },
  {
    accessorKey: "user",
    header: "User",
    cell: ({ row }) => {
      const log = row.original;
      return <Badge className="text-xs px-2 py-1 bg-blue-100 text-blue-800">{log.user}</Badge>;
    },
  },
  {
    accessorKey: "entity",
    header: "Entity",
    cell: ({ row }) => {
      const log = row.original;
      return <Badge className="text-xs px-2 py-1 bg-purple-100 text-purple-800">{log.entity ?? "-"}</Badge>;
    },
  },
  {
    accessorKey: "details",
    header: "Details",
    cell: ({ row }) => {
      const log = row.original;
      return (
        <span className="truncate max-w-xs inline-block align-top text-xs" title={log.details}>{log.details}</span>
      );
    },
  },
];
