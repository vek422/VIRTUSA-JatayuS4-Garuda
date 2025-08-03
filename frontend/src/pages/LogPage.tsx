import React, { useState } from 'react';
import { useGetLogsQuery } from '../api/logsApi';
import { LogsTable } from '../components/LogsTable/data-table';

const LogPage: React.FC = () => {
  const [search, setSearch] = useState('');
  const { data: logs = [], isLoading } = useGetLogsQuery({ limit: 1000 });
  const filteredLogs = search
    ? logs.filter((log) =>
        [log.action, log.status, log.user, log.entity, log.source, log.details]
          .some((field) => {
            if (typeof field === 'string') {
              return field.toLowerCase().includes(search.toLowerCase());
            }
            return false;
          })
      )
    : logs;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold tracking-tight mb-6">🧾 System Logs</h1>
      <LogsTable data={filteredLogs} isLoading={isLoading} onSearchChange={setSearch} />
    </div>
  );
};

export default LogPage;
