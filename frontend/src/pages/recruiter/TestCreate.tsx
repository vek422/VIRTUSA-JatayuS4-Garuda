import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useEffect } from "react";

import { useCreateTestMutation } from "@/api/testApi";
import { useNavigate } from "react-router-dom";
import { Loader2, CheckCircle, XCircle } from "lucide-react";

// Updated Zod validation schema to match backend
const testCreateSchema = z
  .object({
    testName: z
      .string()
      .min(1, "Test name is required")
      .min(3, "Test name must be at least 3 characters")
      .max(100, "Test name must not exceed 100 characters"),

    jobDescription: z
      .string()
      .min(1, "Job description is required")
      .min(300, "Job description must be at least 300 characters")
      .max(10000, "Job description must not exceed 10000 characters"),

    // Backend fields - all optional except auto_shortlist
    resumeScoreThreshold: z
      .number()
      .min(0, "Resume score threshold must be at least 0")
      .max(100, "Resume score threshold must not exceed 100")
      .optional(),

    maxShortlistedCandidates: z
      .number()
      .min(1, "Must allow at least 1 candidate")
      .max(1000, "Cannot exceed 1000 candidates")
      .optional(),

    autoShortlist: z.boolean(),

    // Removed totalQuestions, timeLimitMinutes, totalMarks from schema
  })
  .refine(
    (data) => {
      // If auto shortlist is enabled, max shortlisted candidates is required
      if (data.autoShortlist && !data.maxShortlistedCandidates) {
        return false;
      }
      return true;
    },
    {
      message:
        "Max shortlisted candidates is required when auto shortlist is enabled",
      path: ["maxShortlistedCandidates"],
    }
  )
  .refine(
    (data) => {
      // If auto shortlist is enabled, resume score threshold is required
      if (data.autoShortlist && data.resumeScoreThreshold === undefined) {
        return false;
      }
      return true;
    },
    {
      message:
        "Resume score threshold is required when auto shortlist is enabled",
      path: ["resumeScoreThreshold"],
    }
  );

type TestCreateFormData = z.infer<typeof testCreateSchema>;

export default function TestCreate() {
  // Default values for question distribution
  const totalQuestions = 15;
  const lowCount = 5;
  const medCount = 5;
  const highCount = 5;
  const totalTime = Math.ceil(
    (lowCount * 45 + medCount * 60 + highCount * 90) / 60
  );
  // RTK Query hook for API call with built-in loading states
  const [createTest, { isLoading, error, isSuccess }] = useCreateTestMutation();
  const navigate = useNavigate();

  const form = useForm<TestCreateFormData>({
    resolver: zodResolver(testCreateSchema),
    defaultValues: {
      testName: "",
      jobDescription: "",
      resumeScoreThreshold: undefined,
      maxShortlistedCandidates: undefined,
      autoShortlist: false,
      // Removed totalQuestions, timeLimitMinutes, totalMarks from defaultValues
    },
  });

  // Transform form data to API format and submit
  const onSubmit = async (data: TestCreateFormData) => {
    try {
      // Always send these fields for test creation
      const payload = {
        test_name: data.testName,
        job_description: data.jobDescription,
        resume_score_threshold: data.autoShortlist
          ? data.resumeScoreThreshold
          : null,
        max_shortlisted_candidates: data.autoShortlist
          ? data.maxShortlistedCandidates
          : null,
        auto_shortlist: data.autoShortlist,
      };
      console.log("Submitting test data:", payload);
      const result = await createTest(payload).unwrap();
      console.log("Test created successfully:", result);
      form.reset();
    } catch (error) {
      console.error("Failed to create test:", error);
    }
  };

  // Auto-redirect on success after showing message
  useEffect(() => {
    if (isSuccess) {
      const timer = setTimeout(() => {
        navigate("/recruiter/tests");
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [isSuccess, navigate]);

  const jobDescriptionValue = form.watch("jobDescription");
  const characterCount = jobDescriptionValue ? jobDescriptionValue.length : 0;
  const autoShortlistEnabled = form.watch("autoShortlist");
  useEffect(() => {
    if (!autoShortlistEnabled) {
      form.setValue("maxShortlistedCandidates", undefined);
      form.setValue("resumeScoreThreshold", undefined);
    }
  }, [autoShortlistEnabled, form]);

  return (
    <div className="container mx-auto py-6 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight">Create New Test</h1>
        <p className="text-muted-foreground mt-2">
          Set up a new assessment for candidates
        </p>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          {/* Basic Information Card */}
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Test Name Field */}
              <FormField
                control={form.control}
                name="testName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-base font-semibold">
                      Test Name *
                    </FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Enter test name (e.g., Frontend Developer Assessment)"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      A clear and descriptive name for your test
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Job Description Field */}
              <FormField
                control={form.control}
                name="jobDescription"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-base font-semibold">
                      Job Description *
                    </FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Provide a detailed job description including required skills, responsibilities, and qualifications..."
                        className="min-h-32 resize-y"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription className="flex flex-col gap-1">
                      <span>
                        Ensure required skills and responsibilities are properly
                        mentioned.
                      </span>
                      <span
                        className={
                          characterCount >= 300
                            ? "text-green-600"
                            : "text-orange-600"
                        }
                      >
                        Character count: {characterCount}/300 minimum
                      </span>
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          {/* Assessment Configuration Card */}
          <Card>
            <CardHeader>
              <CardTitle>Assessment Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Auto Shortlist */}
              <FormField
                control={form.control}
                name="autoShortlist"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                    <div className="space-y-0.5">
                      <FormLabel className="text-base font-semibold">
                        Auto Shortlist Candidates
                      </FormLabel>
                      <FormDescription>
                        Automatically shortlist candidates based on resume score
                      </FormDescription>
                    </div>
                    <FormControl>
                      <Switch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />

              {/* Resume Score Threshold - Show after Auto Shortlist toggle */}
              {autoShortlistEnabled && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <FormField
                    control={form.control}
                    name="resumeScoreThreshold"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-base font-semibold">
                          Resume Score Threshold (%) *
                        </FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            placeholder="70"
                            min="0"
                            max="100"
                            value={field.value ?? ""}
                            onChange={(e) => {
                              const value = e.target.value;
                              field.onChange(
                                value === "" ? undefined : Number(value)
                              );
                            }}
                          />
                        </FormControl>
                        <FormDescription>
                          Minimum resume score to qualify (0-100%) - Required
                          when auto shortlist is enabled
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/* Max Shortlisted Candidates */}
                  <FormField
                    control={form.control}
                    name="maxShortlistedCandidates"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-base font-semibold">
                          Max Shortlisted Candidates *
                        </FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            placeholder="50"
                            min="1"
                            max="1000"
                            value={field.value ?? ""}
                            onChange={(e) => {
                              const value = e.target.value;
                              field.onChange(
                                value === "" ? undefined : Number(value)
                              );
                            }}
                          />
                        </FormControl>
                        <FormDescription>
                          Maximum number of candidates to shortlist (1-1000) -
                          Required when auto shortlist is enabled
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              )}
            </CardContent>
          </Card>
          {error && (
            <Card className="border-red-200 bg-red-50">
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-red-700">
                  <XCircle className="h-5 w-5" />
                  <div>
                    <p className="font-semibold">Failed to create test</p>
                    <p className="text-sm">
                      {(error as any)?.data?.message ||
                        "An unexpected error occurred. Please try again."}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {isSuccess && (
            <Card className="border-green-200 bg-green-50">
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-green-700">
                  <CheckCircle className="h-5 w-5" />
                  <div>
                    <p className="font-semibold">Test created successfully!</p>
                    <p className="text-sm">Redirecting to tests list...</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Form Actions */}
          <div className="flex gap-4 pt-6">
            <Button
              type="submit"
              className="flex-1 sm:flex-none"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating Test...
                </>
              ) : (
                "Create Test"
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => form.reset()}
              disabled={isLoading}
            >
              Reset Form
            </Button>
          </div>
        </form>
      </Form>
    </div>
  );
}
