import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { CheckCircle, Download, Loader2, Upload, XCircle } from "lucide-react";
import {
  parseExcelFile,
  downloadSampleTemplate,
  validateFileType,
} from "@/utils/excelParser";
import { useEffect, useRef, useState } from "react";
import type { ExcelCandidateItem } from "@/types/excelTypes";
import { useBulkUploadCandidatesMutation } from "@/api/candidateApi";
import { toast } from "sonner";
import { useParams } from "react-router-dom";
export default function CandidateUpload({
  refetchCandidates,
}: {
  refetchCandidates: () => void;
}) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [uploadStatus, setUploadStatus] = useState<
    "idle" | "uploading" | "success" | "error"
  >("idle");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [parsedData, setParsedData] = useState<ExcelCandidateItem[] | null>(
    null
  );
  const { testId } = useParams<{ testId: string }>();
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errors, setErrors] = useState<string[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [isParsing, setIsParsing] = useState(false);
  const [bulkUpload, { isLoading: isUploading }] =
    useBulkUploadCandidatesMutation();
  useEffect(() => {
    if (uploadStatus === "success" && !isParsing && !isUploading) {
      toast("Candidates uploaded successfully!");
    } else if (uploadStatus === "error" && !isParsing && !isUploading) {
      toast("Error uploading candidates.");
    }
  }, [uploadStatus, isParsing, isUploading]);
  const handleProcessAndUpload = async () => {
    if (!uploadedFile || !testId) return;

    try {
      setUploadStatus("uploading");
      setUploadProgress(0);
      setErrors([]);
      setWarnings([]);
      setIsParsing(true);

      console.log("Starting file parsing and upload for test ID:", testId);

      // First, parse the file
      const result = await parseExcelFile(uploadedFile);

      if (!result.validation.valid) {
        setErrors(result.validation.errors);
        setWarnings(result.validation.warnings);
        setUploadStatus("error");
        setIsParsing(false);
        return;
      }

      setParsedData(result.data);
      setWarnings(result.validation.warnings);
      setIsParsing(false);

      // Show progress simulation for upload
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => Math.min(prev + 10, 90));
      }, 200);

      // Add test_id from URL to each application
      const applicationsWithTestId = result.data.map((candidate) => ({
        ...candidate,
        test_id: Number(testId),
      }));

      const uploadResult = await bulkUpload({
        applications: applicationsWithTestId,
      }).unwrap();

      clearInterval(progressInterval);
      setUploadProgress(100);

      console.log("Upload result:", uploadResult);

      // Reset form and refetch data
      setUploadedFile(null);
      setParsedData(null);
      setUploadProgress(0);
      setUploadStatus("success");
      // Reset file input so user can re-upload the same file
      if (fileInputRef.current) fileInputRef.current.value = "";

      // Refetch candidates to update the table
      if (refetchCandidates) refetchCandidates();

      // Show success message with details
      const successMsg = `Successfully uploaded ${
        uploadResult.success ||
        uploadResult.results?.filter((r) => r.status === "success").length
      } candidates`;
      const failedCount =
        uploadResult.failed ||
        uploadResult.results?.filter((r) => r.status === "error").length;

      if (failedCount > 0) {
        toast(
          `${successMsg}. ${failedCount} failed. Some candidates could not be uploaded.`
        );
      } else {
        toast(successMsg);
      }
    } catch (error: any) {
      console.error("Upload error:", error);
      setUploadProgress(0);
      setIsParsing(false);
      setUploadStatus("error");
      setErrors([
        `Upload failed: ${
          error?.data?.detail ||
          error?.data?.message ||
          error.message ||
          "Unknown error"
        }`,
      ]);
    }
  };

  const handleDownloadTemplate = () => {
    downloadSampleTemplate();
  };
  const handleCsvUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !testId) return;

    setErrors([]);
    setWarnings([]);
    setParsedData(null);
    setUploadStatus("idle");

    // Validate file type
    if (!validateFileType(file)) {
      setErrors([
        "Please select a valid Excel file (.xlsx, .xls) or CSV file (.csv)",
      ]);
      return;
    }

    setUploadedFile(file);
    console.log("File ready for upload:", file.name);
  };
  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload Candidates</CardTitle>
        <CardDescription>
          Upload an Excel or CSV file with candidate information (max 100 rows)
          {uploadedFile && (
            <>
              <br />
              <span className="text-green-600">
                Selected: {uploadedFile.name}
              </span>
            </>
          )}
          {parsedData && (
            <>
              <br />
              <span className="text-blue-600">
                Parsed {parsedData.length} candidates successfully
              </span>
            </>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <Input
              type="file"
              accept=".xlsx,.xls,.csv"
              onChange={handleCsvUpload}
              className="flex-1"
              disabled={isParsing || isUploading}
              ref={fileInputRef}
            />
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownloadTemplate}
            >
              <Download className="h-4 w-4 mr-2" />
              Template
            </Button>
          </div>

          {/* Upload Button - Show when file is selected */}
          {uploadedFile && (
            <div className="flex items-center justify-between p-3 rounded-lg border">
              <div>
                <p className="text-sm font-medium">
                  Ready to upload: {uploadedFile.name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {parsedData
                    ? `${parsedData.length} candidates parsed`
                    : "Click to parse and upload"}
                </p>
              </div>
              <Button
                onClick={handleProcessAndUpload}
                disabled={isParsing || isUploading}
                className="bg-green-600 hover:bg-green-700"
              >
                {isParsing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Parsing...
                  </>
                ) : isUploading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    {parsedData
                      ? `Upload ${parsedData.length} Candidates`
                      : "Parse & Upload"}
                  </>
                )}
              </Button>
            </div>
          )}

          {(isParsing || isUploading) && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              {isParsing ? "Parsing file..." : "Uploading candidates..."}
              {uploadProgress > 0 && <span>({uploadProgress}%)</span>}
            </div>
          )}

          {errors.length > 0 && (
            <div className="flex items-center gap-2 text-sm text-red-600">
              <XCircle className="h-4 w-4" />
              <div>
                {errors.map((error, index) => (
                  <div key={index}>{error}</div>
                ))}
              </div>
            </div>
          )}

          {warnings.length > 0 && (
            <div className="flex items-center gap-2 text-sm text-yellow-600">
              <CheckCircle className="h-4 w-4" />
              <div>
                {warnings.map((warning, index) => (
                  <div key={index}>{warning}</div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
