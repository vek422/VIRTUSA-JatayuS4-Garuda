import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Clock, Calendar, Timer, Eye, EyeOff } from "lucide-react";
import { motion } from "motion/react";

interface AssignedTestCardProps {
  testName: string;
  jobDescription?: string;
  scheduledTime: string;
  duration: string;
  deadline?: string;
  status: string;
  onAction: () => void;
  scheduledAt?: string;
}

export function AssignedTestCard({
  testName,
  jobDescription,
  scheduledTime,
  duration,
  deadline,
  status,
  onAction,
  scheduledAt,
}: AssignedTestCardProps) {
  const [showFullJD, setShowFullJD] = useState(false);
  const getStatusColor = (status: string) => {
    switch (status) {
      case "scheduled":
      case "live":
      case "active":
      case "available":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200";
      case "ongoing":
      case "in-progress":
      case "started":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
      case "completed":
      case "finished":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      case "ended":
      case "expired":
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200";
    }
  };
  const getActionButton = () => {
    if (status === "ended") {
      return (
        <Button disabled className="w-full opacity-60 cursor-not-allowed">
          <Clock className="mr-2 h-4 w-4" />
          Test Ended
        </Button>
      );
    }
    // Only show Start Test if test is live (ongoing)
    if (status === "live") {
      return (
        <Button onClick={onAction} className="w-full">
          <Clock className="mr-2 h-4 w-4" />
          Start Test
        </Button>
      );
    }
    // If test is scheduled and start time is in future, show countdown only
    if (status === "scheduled") {
      return null;
    }
    if (status === "completed") {
      return (
        <Button onClick={onAction} variant="secondary" className="w-full">
          View Results
        </Button>
      );
    }
    return null;
  };

  // Live countdown state
  const [countdown, setCountdown] = useState<string>("");
  useEffect(() => {
    if (status === "scheduled" && scheduledAt) {
      const target = new Date(scheduledAt).getTime();
      const interval = setInterval(() => {
        const now = Date.now();
        const diff = target - now;
        if (diff > 0) {
          const hours = Math.floor(diff / (1000 * 60 * 60));
          const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
          const seconds = Math.floor((diff % (1000 * 60)) / 1000);
          setCountdown(`${hours}h ${minutes}m ${seconds}s until start`);
        } else {
          setCountdown("Starting soon...");
          clearInterval(interval);
        }
      }, 1000);
      return () => clearInterval(interval);
    } else {
      setCountdown("");
    }
  }, [status, scheduledAt]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="relative"
    >
      <Card className="hover:shadow-lg transition-shadow duration-200 bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 dark:from-blue-950 dark:via-purple-950 dark:to-pink-950 border border-primary/20">
        {countdown && status === "scheduled" && (
          <div className="absolute -top-2 -right-2 z-10">
            <Badge variant="destructive" className="text-xs font-medium">
              {countdown}
            </Badge>
          </div>
        )}

        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-semibold truncate">
              {testName}
            </CardTitle>
            <Badge className={getStatusColor(status)}>
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {jobDescription && (
            <div className="text-xs text-muted-foreground mb-2">
              <strong>Job Description:</strong>
              <span>
                {showFullJD
                  ? jobDescription
                  : jobDescription.length > 220
                  ? jobDescription.slice(0, 220) + "..."
                  : jobDescription}
              </span>
              {jobDescription.length > 220 && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="ml-2 px-2 py-0 text-xs text-blue-600 dark:text-purple-300 hover:bg-blue-100 dark:hover:bg-purple-900"
                  onClick={() => setShowFullJD((v) => !v)}
                >
                  {showFullJD ? (
                    <EyeOff className="inline w-4 h-4 mr-1" />
                  ) : (
                    <Eye className="inline w-4 h-4 mr-1" />
                  )}
                  {showFullJD ? "Show less" : "Show more"}
                </Button>
              )}
            </div>
          )}
          <div className="space-y-2">
            <div className="flex items-center text-sm text-muted-foreground">
              <Calendar className="mr-2 h-4 w-4 text-blue-500 dark:text-purple-300" />
              <span className="font-medium text-blue-700 dark:text-purple-200">
                {scheduledTime}
              </span>
            </div>
            <div className="flex items-center text-sm text-muted-foreground">
              <Timer className="mr-2 h-4 w-4 text-pink-500 dark:text-pink-300" />
              <span className="font-medium text-pink-700 dark:text-pink-200">
                {duration}
              </span>
            </div>
            {deadline && (
              <div className="flex items-center text-sm text-muted-foreground">
                <span className="mr-2 text-purple-700 dark:text-purple-300">
                  Deadline:
                </span>
                <span className="font-medium text-purple-700 dark:text-purple-200">
                  {deadline}
                </span>
              </div>
            )}
          </div>

          {getActionButton()}
        </CardContent>
      </Card>
    </motion.div>
  );
}
