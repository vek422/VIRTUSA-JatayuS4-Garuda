import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  type ColumnDef,
  type ColumnFiltersState,
  type SortingState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Search, Filter, ChevronDown } from "lucide-react";
import { type Test } from "@/components/TestTable/columns";
import { cn } from "@/lib/utils";

type FilterStatus = "all" | Test["test_status"];

interface TestsDataTableProps {
  data: Test[];
  columns: ColumnDef<Test>[];
}

export function TestsDataTable({ data, columns }: TestsDataTableProps) {
  const navigate = useNavigate();
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [globalFilter, setGlobalFilter] = useState("");

  const handleRowClick = (testId: string, event: React.MouseEvent) => {
    const target = event.target as HTMLElement;
    const isActionButton = target.closest("button") || target.closest("a");

    if (!isActionButton) {
      navigate(`/recruiter/test/${testId}`);
    }
  };

  const statusOptions: { value: FilterStatus; label: string }[] = [
    { value: "all", label: "All" },
    { value: "draft", label: "Draft" },
    { value: "scheduled", label: "Scheduled" },
    { value: "ongoing", label: "Ongoing" },
    { value: "completed", label: "Completed" },
  ];

  const currentStatusFilter =
    (columnFilters.find((filter) => filter.id === "test_status")
      ?.value as FilterStatus) || "all";

  const handleStatusFilterChange = (status: FilterStatus) => {
    if (status === "all") {
      setColumnFilters((prev) =>
        prev.filter((filter) => filter.id !== "test_status")
      );
    } else {
      setColumnFilters((prev) => [
        ...prev.filter((filter) => filter.id !== "test_status"),
        { id: "test_status", value: status },
      ]);
    }
  };

  const table = useReactTable({
    data,
    columns,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onGlobalFilterChange: setGlobalFilter,
    globalFilterFn: "includesString",
    state: {
      sorting,
      columnFilters,
      globalFilter,
    },
  });

  return (
    <div className="w-full flex flex-col gap-6">
      {/* Filters and Search */}
      <Card className="p-4">
        <div className="flex gap-4 items-center flex-wrap">
          {/* Search Bar */}
          <div className="relative flex-1 min-w-[300px]">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by test name or ID..."
              value={globalFilter ?? ""}
              onChange={(e) => setGlobalFilter(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Status Filter */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="gap-2">
                <Filter className="h-4 w-4" />
                Status:{" "}
                {
                  statusOptions.find((opt) => opt.value === currentStatusFilter)
                    ?.label
                }
                <ChevronDown className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {statusOptions.map((option) => (
                <DropdownMenuItem
                  key={option.value}
                  onClick={() => handleStatusFilterChange(option.value)}
                  className={cn(
                    currentStatusFilter === option.value && "bg-accent"
                  )}
                >
                  {option.label}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </Card>

      {/* Results Summary */}
      <div className="text-sm text-muted-foreground">
        Showing {table.getFilteredRowModel().rows.length} of {data.length} tests
      </div>

      {/* Table */}
      <div className="rounded-md border overflow-hidden">
        <ScrollArea className="h-[70vh]">
          <Table>
            <TableHeader className="bg-secondary text-secondary-foreground sticky top-0 z-10">
              {table.getHeaderGroups().map((headerGroup) => (
                <TableRow key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <TableHead
                      key={header.id}
                      className={cn(
                        header.id === "test_id" && "w-[120px]",
                        header.id === "test_status" && "w-[130px]",
                        header.id === "test_created_at" && "w-[130px]",
                        header.id === "test_duration" && "w-[120px]",
                        header.id === "total_candidate" && "w-[100px]",
                        header.id === "actions" && "w-[150px] text-center"
                      )}
                    >
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                    </TableHead>
                  ))}
                </TableRow>
              ))}
            </TableHeader>
            <TableBody>
              {table.getRowModel().rows?.length ? (
                table.getRowModel().rows.map((row) => (
                  <TableRow
                    key={row.id}
                    data-state={row.getIsSelected() && "selected"}
                    className="hover:bg-muted/80 cursor-pointer transition-all duration-200 hover:shadow-sm"
                    onClick={(event) =>
                      handleRowClick(row.original.test_id, event)
                    }
                  >
                    {row.getVisibleCells().map((cell) => (
                      <TableCell key={cell.id}>
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext()
                        )}
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell
                    colSpan={columns.length}
                    className="h-24 text-center"
                  >
                    {globalFilter || currentStatusFilter !== "all"
                      ? "No tests match your filters."
                      : "No tests found."}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </ScrollArea>
      </div>
    </div>
  );
}
