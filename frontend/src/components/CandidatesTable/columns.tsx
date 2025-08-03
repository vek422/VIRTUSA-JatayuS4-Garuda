import { type ColumnDef } from "@tanstack/react-table";
import { Badge } from "../ui/badge";
import { Avatar, AvatarFallback } from "../ui/avatar";
import { Button } from "../ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import { Eye, MoreHorizontal, ArrowUpDown } from "lucide-react";
import type { Candidate } from "@/api/candidatesApi";

const getStatusBadge = (status: string) => {
  const variants = {
    Completed: "bg-green-100 text-green-800",
    "In Progress": "bg-yellow-100 text-yellow-800",
    "Not Started": "bg-red-100 text-red-800",
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

export const candidateColumns: ColumnDef<Candidate>[] = [
  {
    accessorKey: "name",
    header: "Candidate",
    cell: ({ row }) => {
      const candidate = row.original;
      return (
        <div className="flex items-center gap-2">
          <Avatar className="h-8 w-8">
            <AvatarFallback className="text-xs">
              {getInitials(candidate.name)}
            </AvatarFallback>
          </Avatar>
          <span className="font-medium">{candidate.name}</span>
        </div>
      );
    },
  },
  {
    accessorKey: "email",
    header: "Email",
  },
];
