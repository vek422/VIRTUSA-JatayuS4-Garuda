// Excel-specific types for parsing (without test_id)
export interface ExcelCandidateItem {
  email: string;
  name?: string;
  resume_link: string;
}

// This will be converted to BulkApplicationItem by adding test_id from URL
