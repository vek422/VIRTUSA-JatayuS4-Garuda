import React from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Trash2 } from "lucide-react";
import QuestionCountSettings from "@/components/QuestionCountSettings";

interface SettingsTabProps {
  test: any;
  testId: string;
  scheduleState: {
    scheduled_at: string;
    application_deadline: string;
    assessment_deadline: string;
  };
  setScheduleState: React.Dispatch<
    React.SetStateAction<{
      scheduled_at: string;
      application_deadline: string;
      assessment_deadline: string;
    }>
  >;
  formState: any;
  handleFieldChange: (field: string, value: any) => void;
  handleSchedule: () => Promise<void>;
  isScheduling: boolean;
  updateError: string | null;
  updateSuccess: string | null;
  formatDate: (dateString?: string | null) => string;
  getStatusBadge: (status: string) => React.ReactElement;
  updateTest: any;
  isUpdatingTest: boolean;
  hasUnsavedChanges: (formState: any, test: any) => boolean;
  setUpdateError: React.Dispatch<React.SetStateAction<string | null>>;
  setUpdateSuccess: React.Dispatch<React.SetStateAction<string | null>>;
  setEditMode: React.Dispatch<React.SetStateAction<boolean>>;
  setFormState: React.Dispatch<React.SetStateAction<any>>;
  handleDeleteTest: () => Promise<void>;
}

export default function SettingsTab({
  test,
  testId,
  scheduleState,
  setScheduleState,
  formState,
  handleFieldChange,
  handleSchedule,
  isScheduling,
  updateError,
  updateSuccess,
  formatDate,
  getStatusBadge,
  updateTest,
  isUpdatingTest,
  hasUnsavedChanges,
  setUpdateError,
  setUpdateSuccess,
  setEditMode,
  setFormState,
  handleDeleteTest,
}: SettingsTabProps) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Schedule Test</CardTitle>
          <CardDescription>
            Set the start time and duration. End time is auto-calculated.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Show current scheduled test time if available */}
          {test?.scheduled_at && (
            <div className="mb-2">
              <span className="font-medium">
                Current Scheduled Test Start:&nbsp;
              </span>
              <span className="text-blue-700">
                {formatDate(test.scheduled_at)}
              </span>
            </div>
          )}
          {test?.assessment_deadline && (
            <div className="mb-2">
              <span className="font-medium">Current Assessment End:&nbsp;</span>
              <span className="text-blue-700">
                {formatDate(test.assessment_deadline)}
              </span>
            </div>
          )}
          <div className="space-y-2">
            <Label htmlFor="scheduledAt">Scheduled At</Label>
            <Input
              id="scheduledAt"
              type="datetime-local"
              value={scheduleState.scheduled_at}
              onChange={(e) =>
                setScheduleState((prev) => ({
                  ...prev,
                  scheduled_at: e.target.value,
                }))
              }
              className="max-w-md"
            />
          </div>
          <div className="space-y-2">
            <Label>Assessment End Time</Label>
            <Input
              type="datetime-local"
              value={scheduleState.assessment_deadline}
              onChange={(e) =>
                setScheduleState((prev) => ({
                  ...prev,
                  assessment_deadline: e.target.value,
                }))
              }
              className="max-w-md"
            />
          </div>
          <div className="flex gap-4 pt-4">
            <Button onClick={handleSchedule} disabled={isScheduling}>
              {isScheduling ? "Scheduling..." : "Schedule"}
            </Button>
          </div>
          {updateError && (
            <div className="text-red-600 text-sm mt-2">{updateError}</div>
          )}
          {updateSuccess && (
            <div className="text-green-600 text-sm mt-2">{updateSuccess}</div>
          )}
        </CardContent>
      </Card>

      {/* Update Test Section */}
      <Card>
        <CardHeader>
          <CardTitle>Test Settings</CardTitle>
          <CardDescription>
            Configure test parameters and preferences
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {formState && (
            <>
              {/* Question Count Settings Section */}
              {test && (
                <div className="mb-8">
                  <QuestionCountSettings
                    testId={test.test_id}
                    highPriorityNodes={test.high_priority_nodes || 0}
                    mediumPriorityNodes={test.medium_priority_nodes || 0}
                    lowPriorityNodes={test.low_priority_nodes || 0}
                    initialHigh={test.high_priority_questions || 0}
                    initialMedium={test.medium_priority_questions || 0}
                    initialLow={test.low_priority_questions || 0}
                    initialTimeLimit={test.time_limit_minutes || 0}
                  />
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="testName">Test Name</Label>
                <Input
                  id="testName"
                  value={formState.test_name}
                  onChange={(e) =>
                    handleFieldChange("test_name", e.target.value)
                  }
                  className="max-w-md"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="jobDesc">Job Description</Label>
                <Textarea
                  id="jobDesc"
                  value={formState.job_description}
                  onChange={(e) =>
                    handleFieldChange("job_description", e.target.value)
                  }
                  rows={4}
                  className="max-w-2xl"
                />
              </div>
              <div className="space-y-2">
                <Label>Status</Label>
                <div className="flex items-center gap-2">
                  {getStatusBadge(test.status)}
                </div>
              </div>
              <div className="space-y-2">
                <Label>Resume Score Threshold</Label>
                <Input
                  value={formState.resume_score_threshold ?? ""}
                  onChange={(e) =>
                    handleFieldChange("resume_score_threshold", e.target.value)
                  }
                  className="max-w-md"
                  disabled={!formState.auto_shortlist}
                />
              </div>
              <div className="space-y-2">
                <Label>Max Shortlisted Candidates</Label>
                <Input
                  value={formState.max_shortlisted_candidates ?? ""}
                  onChange={(e) =>
                    handleFieldChange(
                      "max_shortlisted_candidates",
                      e.target.value
                    )
                  }
                  className="max-w-md"
                  disabled={!formState.auto_shortlist}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="auto-shortlist-toggle">Auto Shortlist</Label>
                <div className="flex items-center gap-3">
                  <Switch
                    id="auto-shortlist-toggle"
                    checked={!!formState.auto_shortlist}
                    onCheckedChange={(checked: boolean) => {
                      handleFieldChange("auto_shortlist", checked);
                      if (!checked) {
                        handleFieldChange("resume_score_threshold", null);
                        handleFieldChange("max_shortlisted_candidates", null);
                      }
                    }}
                  />
                  <span className="text-sm text-muted-foreground">
                    {formState.auto_shortlist ? "Enabled" : "Disabled"}
                  </span>
                </div>
              </div>
              <div className="flex gap-4 pt-4">
                <Button
                  onClick={async () => {
                    setUpdateError(null);
                    setUpdateSuccess(null);
                    try {
                      // Only send allowed fields for update
                      const allowedFields = [
                        "job_description",
                        "resume_score_threshold",
                        "max_shortlisted_candidates",
                        "auto_shortlist",
                      ];
                      const testData: any = {};
                      for (const key of allowedFields) {
                        const value = formState[key];
                        if (
                          value !== undefined &&
                          value !== null &&
                          !(typeof value === "string" && value.trim() === "")
                        ) {
                          testData[key] = value;
                        }
                      }
                      console.log("Updating test with:", testData);
                      await updateTest({
                        testId: Number(testId),
                        testData,
                      }).unwrap();
                      setUpdateSuccess("Test updated successfully!");
                    } catch (e: any) {
                      setUpdateError(
                        e?.data?.message || "Failed to update test"
                      );
                    }
                  }}
                  disabled={
                    isUpdatingTest || !hasUnsavedChanges(formState, test)
                  }
                >
                  {isUpdatingTest ? "Saving..." : "Save Changes"}
                </Button>

                <Button
                  variant="outline"
                  onClick={() => {
                    setEditMode(false);
                    setFormState(null);
                    setUpdateError(null);
                    setUpdateSuccess(null);
                  }}
                >
                  Cancel
                </Button>
              </div>
              {updateError && (
                <div className="text-red-600 text-sm mt-2">{updateError}</div>
              )}
              {updateSuccess && (
                <div className="text-green-600 text-sm mt-2">
                  {updateSuccess}
                </div>
              )}
            </>
          )}
          {!formState && <div>Loading...</div>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-red-600">Danger Zone</CardTitle>
          <CardDescription>
            Irreversible actions. Please be careful.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button variant="destructive" onClick={handleDeleteTest}>
            <Trash2 className="h-4 w-4 mr-2" />
            Delete Test
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
