import ExcelJS from 'exceljs';

// Excel-specific types for parsing (without test_id)
export interface ExcelCandidateItem {
  email: string;
  name?: string;
  resume_link: string;
}

// Validation result interface
export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

// Excel data validation result
export interface ParsedExcelResult {
  data: ExcelCandidateItem[]; // Changed from BulkApplicationItem to ExcelCandidateItem
  validation: ValidationResult;
  totalRows: number;
  validRows: number;
}

/**
 * Parse Excel file and extract candidate data
 * @param file - Excel file to parse
 * @returns Promise with parsed data and validation results
 */
export const parseExcelFile = async (
  file: File
): Promise<ParsedExcelResult> => {
  try {
    const arrayBuffer = await file.arrayBuffer();
    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.load(arrayBuffer);
    
    // Get first worksheet
    const worksheet = workbook.worksheets[0];
    if (!worksheet) {
      throw new Error('No worksheet found in Excel file');
    }
    
    // Convert to 2D array with proper cell value extraction
    const jsonData: any[][] = [];
    worksheet.eachRow((row) => {
      const rowData: any[] = [];
      row.eachCell((cell, colNumber) => {
        // Handle different cell value types
        let cellValue = cell.value;
        
        // Handle hyperlink objects
        if (cellValue && typeof cellValue === 'object' && 'hyperlink' in cellValue) {
          // Extract hyperlink URL or text
          cellValue = cellValue.hyperlink || cellValue.text || cellValue;
        }
        
        // Handle rich text objects
        if (cellValue && typeof cellValue === 'object' && 'richText' in cellValue) {
          // Extract plain text from rich text
          cellValue = cellValue.richText?.map((part: any) => part.text).join('') || cellValue;
        }
        
        // Handle formula results
        if (cellValue && typeof cellValue === 'object' && 'result' in cellValue) {
          cellValue = cellValue.result;
        }
        
        rowData[colNumber - 1] = cellValue;
      });
      jsonData.push(rowData);
    });
    
    // Process the data (without test_id)
    const result = processExcelData(jsonData);
    return result;
    
  } catch (error) {
    throw new Error(`Failed to parse Excel file: ${error}`);
  }
};

/**
 * Extract string value from potentially complex cell values
 */
const extractStringValue = (cellValue: any): string => {
  if (cellValue === null || cellValue === undefined) {
    return '';
  }
  
  // Handle hyperlink objects
  if (typeof cellValue === 'object' && cellValue.hyperlink) {
    return String(cellValue.hyperlink).trim();
  }
  
  // Handle text property in objects
  if (typeof cellValue === 'object' && cellValue.text) {
    return String(cellValue.text).trim();
  }
  
  // Handle rich text objects
  if (typeof cellValue === 'object' && cellValue.richText) {
    return cellValue.richText.map((part: any) => part.text).join('').trim();
  }
  
  // Handle formula results
  if (typeof cellValue === 'object' && cellValue.result !== undefined) {
    return String(cellValue.result).trim();
  }
  
  // Default: convert to string
  return String(cellValue).trim();
};

/**
 * Process raw Excel data and validate
 * @param rawData - Raw data from Excel sheet
 * @returns Processed and validated data
 */
const processExcelData = (rawData: any[][]): ParsedExcelResult => {
  const errors: string[] = [];
  const warnings: string[] = [];
  const validCandidates: ExcelCandidateItem[] = [];
  
  // Check if data exists
  if (!rawData || rawData.length === 0) {
    errors.push('Excel file is empty');
    return {
      data: [],
      validation: { valid: false, errors, warnings },
      totalRows: 0,
      validRows: 0
    };
  }
  
  // Get headers (first row)
  const headers = rawData[0];
  if (!headers || headers.length === 0) {
    errors.push('No headers found in Excel file');
    return {
      data: [],
      validation: { valid: false, errors, warnings },
      totalRows: 0,
      validRows: 0
    };
  }
  
  // Normalize headers (convert to lowercase and trim)
  const normalizedHeaders = headers.map((header: string) => 
    String(header).toLowerCase().trim()
  );
  
  // Find required column indices (no test_id needed)
  const emailIndex = findColumnIndex(normalizedHeaders, ['email', 'email address', 'e-mail']);
  const nameIndex = findColumnIndex(normalizedHeaders, ['name', 'full name', 'candidate name']);
  const resumeLinkIndex = findColumnIndex(normalizedHeaders, ['resume_link', 'resume link', 'resume url', 'resume']);
  
  // Validate required columns
  if (emailIndex === -1) {
    errors.push('Required column "email" not found. Expected column names: email, email address, e-mail');
  }
  
  if (resumeLinkIndex === -1) {
    errors.push('Required column "resume_link" not found. Expected column names: resume_link, resume link, resume url, resume');
  }
  
  if (errors.length > 0) {
    return {
      data: [],
      validation: { valid: false, errors, warnings },
      totalRows: rawData.length - 1,
      validRows: 0
    };
  }
  
  // Process data rows (skip header row)
  for (let i = 1; i < rawData.length; i++) {
    const row = rawData[i];
    const rowNumber = i + 1;
    
    // Skip empty rows
    if (!row || row.every((cell: any) => !cell || String(cell).trim() === '')) {
      continue;
    }
    
    const email = row[emailIndex] ? extractStringValue(row[emailIndex]) : '';
    const name = nameIndex !== -1 && row[nameIndex] ? extractStringValue(row[nameIndex]) : '';
    const resumeLink = row[resumeLinkIndex] ? extractStringValue(row[resumeLinkIndex]) : '';
    
    // Debug logging for problematic rows
    if (rowNumber <= 5) {
      console.log(`Row ${rowNumber} debug:`, {
        rawResumeCell: row[resumeLinkIndex],
        extractedResumeLink: resumeLink,
        resumeLinkType: typeof resumeLink
      });
    }
    
    // Validate row data
    const rowErrors = validateRowData({ email, name, resumeLink }, rowNumber);
    
    if (rowErrors.length === 0) {
      validCandidates.push({
        email,
        name: name || undefined, // Only include name if provided
        resume_link: resumeLink
      });
    } else {
      errors.push(...rowErrors);
    }
  }
  
  // Add warnings if no name column found
  if (nameIndex === -1) {
    warnings.push('Name column not found. Candidate names will be extracted from email addresses.');
  }
  
  return {
    data: validCandidates,
    validation: { 
      valid: validCandidates.length > 0 && errors.length === 0, 
      errors, 
      warnings 
    },
    totalRows: rawData.length - 1,
    validRows: validCandidates.length
  };
};

/**
 * Find column index by possible names
 * @param headers - Array of header names
 * @param possibleNames - Array of possible column names
 * @returns Index of found column or -1 if not found
 */
const findColumnIndex = (headers: string[], possibleNames: string[]): number => {
  for (const name of possibleNames) {
    const index = headers.findIndex(header => header === name);
    if (index !== -1) return index;
  }
  return -1;
};

/**
 * Validate individual row data
 * @param data - Row data to validate
 * @param rowNumber - Row number for error reporting
 * @returns Array of validation errors
 */
const validateRowData = (
  data: { email: string; name: string; resumeLink: string }, 
  rowNumber: number
): string[] => {
  const errors: string[] = [];
  
  // Validate email
  if (!data.email) {
    errors.push(`Row ${rowNumber}: Email is required`);
  } else if (!isValidEmail(data.email)) {
    errors.push(`Row ${rowNumber}: Invalid email format "${data.email}"`);
  }
  
  // Validate resume link
  if (!data.resumeLink) {
    errors.push(`Row ${rowNumber}: Resume link is required`);
  } else {
    // Check if the value is actually a string and not an object
    const resumeLinkType = typeof data.resumeLink;
    if (resumeLinkType !== 'string') {
      errors.push(`Row ${rowNumber}: Invalid resume link format "[object Object]" - got ${resumeLinkType}, expected string. Raw value: ${JSON.stringify(data.resumeLink)}`);
    } else if (!isValidUrl(data.resumeLink)) {
      errors.push(`Row ${rowNumber}: Invalid resume link format "${data.resumeLink}" - must be a valid URL starting with http:// or https://`);
    }
  }
  
  return errors;
};

/**
 * Validate email format
 * @param email - Email to validate
 * @returns True if valid email format
 */
const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Validate URL format
 * @param url - URL to validate
 * @returns True if valid URL format
 */
const isValidUrl = (url: string): boolean => {
  // Basic checks first
  if (!url || typeof url !== 'string') {
    return false;
  }
  
  const trimmedUrl = url.trim();
  
  // Check if it's a valid URL pattern
  const urlPattern = /^https?:\/\/[^\s]+/i;
  if (urlPattern.test(trimmedUrl)) {
    return true;
  }
  
  // Also accept URLs that might be missing protocol
  const domainPattern = /^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.[a-zA-Z]{2,}[^\s]*$/;
  if (domainPattern.test(trimmedUrl)) {
    return true;
  }
  
  // Try to create a URL object for final validation
  try {
    new URL(trimmedUrl.startsWith('http') ? trimmedUrl : `https://${trimmedUrl}`);
    return true;
  } catch {
    return false;
  }
};

/**
 * Download sample Excel template
 * @param testId - Test ID to include in filename
 */
export const downloadSampleExcel = async (testId?: number): Promise<void> => {
  // Create sample data
  const sampleData = [
    ['name', 'email', 'resume_link'],
    ['John Doe', 'john.doe@example.com', 'https://drive.google.com/file/d/1gLpMQFOu56de5NbaLPuL-5e5ICbYbCMv/view'],
    ['Jane Smith', 'jane.smith@gmail.com', 'https://drive.google.com/file/d/1hMpNRGPv67ef6OcbMQvM-6f6JDcZcDNw/view'],
    ['Bob Wilson', 'bob.wilson@yahoo.com', 'https://drive.google.com/file/d/1iNqOSHQw78fg7PdcNRwN-7g7KEd0dEOx/view']
  ];
  
  // Create workbook and worksheet
  const workbook = new ExcelJS.Workbook();
  const worksheet = workbook.addWorksheet('Candidates');
  
  // Add data
  sampleData.forEach((row, index) => {
    worksheet.addRow(row);
    if (index === 0) {
      // Style header row
      worksheet.getRow(1).font = { bold: true };
    }
  });
  
  // Auto-fit columns
  worksheet.columns.forEach(column => {
    column.width = 20;
  });
  
  // Generate filename
  const filename = testId 
    ? `candidate_template_test_${testId}.xlsx`
    : 'candidate_template.xlsx';
  
  // Download file
  const buffer = await workbook.xlsx.writeBuffer();
  const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
};

/**
 * Validate file type
 * @param file - File to validate
 * @returns True if valid Excel file
 */
export const isValidExcelFile = (file: File): boolean => {
  const validTypes = [
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
    'application/vnd.ms-excel', // .xls
    'text/csv' // .csv
  ];
  
  const validExtensions = ['.xlsx', '.xls', '.csv'];
  const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
  
  return validTypes.includes(file.type) || validExtensions.includes(fileExtension);
};

// Export aliases for consistency
export const downloadSampleTemplate = downloadSampleExcel;
export const validateFileType = isValidExcelFile;
