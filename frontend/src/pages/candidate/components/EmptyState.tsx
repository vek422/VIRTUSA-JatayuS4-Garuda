import { Card, CardContent } from "@/components/ui/card";
import { ClipboardList, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface EmptyStateProps {
  onRefresh?: () => void;
}

export function EmptyState({ onRefresh }: EmptyStateProps) {
  return (
    <Card className="max-w-md mx-auto">
      <CardContent className="flex flex-col items-center justify-center py-12 text-center">
        <div className="mb-6 rounded-full bg-muted p-4">
          <ClipboardList className="h-12 w-12 text-muted-foreground" />
        </div>

        <h3 className="text-lg font-semibold mb-2">No Assessments Scheduled</h3>

        <p className="text-muted-foreground mb-6 max-w-sm">
          You don't have any assessments scheduled right now. Please check again
          later.
        </p>

        {onRefresh && (
          <Button onClick={onRefresh} variant="outline" className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
