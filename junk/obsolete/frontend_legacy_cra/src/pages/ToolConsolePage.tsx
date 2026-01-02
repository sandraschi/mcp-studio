import React from 'react';
import { ToolConsole } from '../components/tools/ToolConsole';
import { AppLayout } from '../components/layout/AppLayout';

export const ToolConsolePage: React.FC = () => {
  return (
    <AppLayout>
      <div className="h-full flex flex-col">
        <ToolConsole />
      </div>
    </AppLayout>
  );
};

export default ToolConsolePage;
