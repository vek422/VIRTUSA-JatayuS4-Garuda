import { useState, useRef, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { Upload, Download, FileText, XCircle, Eye, AlertCircle, Users } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { useBulkUploadCandidatesMutation, useGetCandidatesByTestQuery } from '@/api/candidateApi';
import { parseExcelFile, downloadSampleTemplate, validateFileType } from '@/utils/excelParser';
import type { CandidateWithUserInfo } from '@/api/candidateApi';
import type { ExcelCandidateItem } from '@/utils/excelParser';

export default function CandidateUpload() {
  const { testId } = useParams<{ testId: string }>();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // State management
  const [dragActive, setDragActive] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [parsedData, setParsedData] = useState<ExcelCandidateItem[] | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateWithUserInfo | null>(null);
  const [errors, setErrors] = useState<string[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [isParsing, setIsParsing] = useState(false);

  // RTK Query hooks
  const [bulkUpload, { isLoading: isUploading }] = useBulkUploadCandidatesMutation();
  const { data: candidates, refetch: refetchCandidates } = useGetCandidatesByTestQuery(
    Number(testId!),
    { skip: !testId }
  );

  // File handling
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  }, []);

  const handleFileSelection = (file: File) => {
    console.log('=== FILE SELECTION DEBUG ===');
    console.log('File:', file.name, file.type, file.size);
    
    setErrors([]);
    setWarnings([]);
    setParsedData(null); // Reset parsed data
    
    if (!validateFileType(file)) {
      console.log('File validation failed');
      setErrors(['Please select a valid Excel file (.xlsx, .xls) or CSV file (.csv)']);
      return;
    }

    console.log('File validation passed, setting uploadedFile');
    setUploadedFile(file);
    console.log('uploadedFile state should now be:', file.name);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    console.log('File input triggered', e.target.files);
    if (e.target.files && e.target.files[0]) {
      console.log('Selected file:', e.target.files[0].name, e.target.files[0].type);
      handleFileSelection(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!uploadedFile || !testId) return;

    try {
      setUploadProgress(0);
      setErrors([]);
      setWarnings([]);
      setIsParsing(true);

      console.log('Starting file parsing and upload for test ID:', testId);
      
      // First, parse the file
      const result = await parseExcelFile(uploadedFile);
      
      if (!result.validation.valid) {
        setErrors(result.validation.errors);
        setWarnings(result.validation.warnings);
        setIsParsing(false);
        return;
      }
      
      setParsedData(result.data);
      setWarnings(result.validation.warnings);
      setIsParsing(false);

      // Show progress simulation for upload
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 200);
      
      // Add test_id from URL to each application
      const applicationsWithTestId = result.data.map(candidate => ({
        ...candidate,
        test_id: Number(testId)
      }));
      
      console.log('Upload data:', { applications: applicationsWithTestId });

      const uploadResult = await bulkUpload({
        applications: applicationsWithTestId
      }).unwrap();

      clearInterval(progressInterval);
      setUploadProgress(100);

      console.log('Upload result:', uploadResult);

      // Reset form and refetch data
      setUploadedFile(null);
      setParsedData(null);
      setUploadProgress(0);
      
      // Refetch candidates to update the table
      refetchCandidates();

      // Show success message with details
      const successMsg = `Successfully uploaded ${uploadResult.success || uploadResult.results?.filter(r => r.status === 'success').length} candidates`;
      const failedCount = uploadResult.failed || uploadResult.results?.filter(r => r.status === 'error').length;
      
      if (failedCount > 0) {
        setWarnings([`${successMsg}. ${failedCount} failed.`]);
      } else {
        setWarnings([successMsg]);
      }
      
    } catch (error: any) {
      console.error('Upload error:', error);
      setUploadProgress(0);
      setIsParsing(false);
      setErrors([`Upload failed: ${error?.data?.detail || error?.data?.message || error.message || 'Unknown error'}`]);
    }
  };

  const openFileDialog = () => {
    console.log('Opening file dialog...');
    console.log('File input ref:', fileInputRef.current);
    console.log('Accept attribute:', fileInputRef.current?.accept);
    fileInputRef.current?.click();
  };

  const handleDownloadTemplate = () => {
    downloadSampleTemplate();
  };

  const getScoreBadge = (score: number | null) => {
    if (score === null || score === undefined) {
      return <Badge variant="secondary">Not Taken</Badge>;
    }
    
    if (score >= 80) return <Badge className="bg-green-500">Excellent ({score}%)</Badge>;
    if (score >= 60) return <Badge className="bg-blue-500">Good ({score}%)</Badge>;
    if (score >= 40) return <Badge className="bg-yellow-500">Average ({score}%)</Badge>;
    return <Badge variant="destructive">Poor ({score}%)</Badge>;
  };

  const getStatusBadge = (isShortlisted: boolean, score: number | null) => {
    if (score === null) return <Badge variant="outline">Pending</Badge>;
    return isShortlisted ? 
      <Badge className="bg-green-500">Shortlisted</Badge> : 
      <Badge variant="destructive">Not Shortlisted</Badge>;
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Candidate Upload</h1>
          <p className="text-muted-foreground">Upload candidates for Test ID: {testId}</p>
        </div>
        <Button onClick={handleDownloadTemplate} variant="outline">
          <Download className="mr-2 h-4 w-4" />
          Download Template
        </Button>
      </div>

      {/* Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Upload Candidates
          </CardTitle>
          <CardDescription>
            Upload an Excel file with candidate data. Required columns: name, email, resume_link
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Drag & Drop Area */}
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive 
                ? 'border-primary bg-primary/5' 
                : 'border-muted-foreground/25 hover:border-primary/50'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <FileText className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-lg font-medium mb-2">
              {uploadedFile ? `Selected: ${uploadedFile.name}` : 'Drag & drop your Excel file here'}
            </p>
            {uploadedFile && (
              <p className="text-sm text-green-600 mb-2">
                ✓ File selected: {uploadedFile.type} ({uploadedFile.size} bytes)
              </p>
            )}
            <p className="text-muted-foreground mb-4">
              or click to browse files (Excel: .xlsx, .xls, CSV: .csv)
              <br />
              <small className="text-xs text-orange-600">
                Having trouble? Try "Browse All Files" or "Excel (MIME)" buttons below
              </small>
            </p>
            <Button onClick={openFileDialog} variant="outline">
              Select Excel File
            </Button>
            <Button 
              onClick={() => document.getElementById('fallback-file-input')?.click()} 
              variant="ghost" 
              size="sm"
              className="ml-2 text-xs"
            >
              Browse All Files
            </Button>
            <Button 
              onClick={() => document.getElementById('mime-file-input')?.click()} 
              variant="ghost" 
              size="sm"
              className="ml-2 text-xs"
            >
              Excel (MIME)
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xls"
              onChange={handleFileInput}
              className="hidden"
            />
            {/* Alternative file input for troubleshooting */}
            <input
              type="file"
              onChange={handleFileInput}
              className="hidden"
              id="fallback-file-input"
            />
            {/* MIME type based input */}
            <input
              type="file"
              accept="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel"
              onChange={handleFileInput}
              className="hidden"
              id="mime-file-input"
            />
          </div>

          {/* Upload Progress */}
          {(isParsing || isUploading) && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>{isParsing ? 'Parsing file...' : 'Uploading candidates...'}</span>
                <span>{uploadProgress}%</span>
              </div>
              <Progress value={uploadProgress} />
            </div>
          )}

          {/* Upload Button - Show when file is selected */}
          {uploadedFile && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-medium">Selected File: {uploadedFile.name}</h3>
                  <p className="text-sm text-muted-foreground">
                    {parsedData ? `${parsedData.length} candidates parsed and ready` : 'Click to parse and upload'}
                  </p>
                </div>
                <Button 
                  onClick={handleUpload} 
                  disabled={isParsing || isUploading}
                  size="lg"
                  className="bg-green-600 hover:bg-green-700 disabled:opacity-50"
                >
                  {isParsing ? (
                    <>
                      <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-background border-t-transparent" />
                      Parsing...
                    </>
                  ) : isUploading ? (
                    <>
                      <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-background border-t-transparent" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="mr-2 h-4 w-4" />
                      {parsedData ? `Upload ${parsedData.length} Candidates` : 'Parse & Upload File'}
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}

          {/* Parsed Data Preview */}
          {parsedData && parsedData.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium">Preview ({parsedData.length} candidates)</h3>
              
              <div className="border rounded-lg">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Resume Link</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {parsedData.slice(0, 5).map((candidate, index) => (
                      <TableRow key={index}>
                        <TableCell className="font-medium">{candidate.name}</TableCell>
                        <TableCell>{candidate.email}</TableCell>
                        <TableCell className="truncate max-w-xs">
                          <a 
                            href={candidate.resume_link} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline"
                          >
                            {candidate.resume_link}
                          </a>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {parsedData.length > 5 && (
                  <p className="text-center text-muted-foreground py-2">
                    ... and {parsedData.length - 5} more candidates
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Errors and Warnings */}
          {errors.length > 0 && (
            <Alert variant="destructive">
              <XCircle className="h-4 w-4" />
              <AlertDescription>
                <ul className="list-disc list-inside space-y-1">
                  {errors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </AlertDescription>
            </Alert>
          )}

          {warnings.length > 0 && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                <ul className="list-disc list-inside space-y-1">
                  {warnings.map((warning, index) => (
                    <li key={index}>{warning}</li>
                  ))}
                </ul>
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Candidates Table */}
      {candidates && candidates.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Uploaded Candidates ({candidates.length})
            </CardTitle>
            <CardDescription>
              Click on any candidate to view detailed information
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Score</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Applied At</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {candidates.map((candidate) => (
                    <TableRow 
                      key={candidate.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => setSelectedCandidate(candidate)}
                    >
                      <TableCell className="font-medium">{candidate.name}</TableCell>
                      <TableCell>{candidate.email}</TableCell>
                      <TableCell>{getScoreBadge(candidate.score)}</TableCell>
                      <TableCell>{getStatusBadge(candidate.is_shortlisted, candidate.score)}</TableCell>
                      <TableCell>{new Date(candidate.created_at).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e: React.MouseEvent) => {
                            e.stopPropagation();
                            setSelectedCandidate(candidate);
                          }}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Candidate Detail Modal */}
      <Dialog open={!!selectedCandidate} onOpenChange={() => setSelectedCandidate(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Candidate Details</DialogTitle>
            <DialogDescription>
              Detailed information for the selected candidate
            </DialogDescription>
          </DialogHeader>
          
          {selectedCandidate && (
            <div className="space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Name</label>
                  <p className="text-lg font-semibold">{selectedCandidate.name}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Email</label>
                  <p className="text-lg">{selectedCandidate.email}</p>
                </div>
              </div>

              {/* Resume Link */}
              <div>
                <label className="text-sm font-medium text-muted-foreground">Resume</label>
                <div className="mt-1">
                  <a 
                    href={selectedCandidate.resume_link} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline flex items-center gap-2"
                  >
                    <FileText className="h-4 w-4" />
                    View Resume
                  </a>
                </div>
              </div>

              {/* Status & Score */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Test Score</label>
                  <div className="mt-1">{getScoreBadge(selectedCandidate.score)}</div>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Status</label>
                  <div className="mt-1">{getStatusBadge(selectedCandidate.is_shortlisted, selectedCandidate.score)}</div>
                </div>
              </div>

              {/* Timestamps */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Applied At</label>
                  <p>{new Date(selectedCandidate.created_at).toLocaleString()}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Last Updated</label>
                  <p>{new Date(selectedCandidate.updated_at).toLocaleString()}</p>
                </div>
              </div>

              {/* Test Details */}
              <div>
                <label className="text-sm font-medium text-muted-foreground">Test ID</label>
                <p>{selectedCandidate.test_id}</p>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
