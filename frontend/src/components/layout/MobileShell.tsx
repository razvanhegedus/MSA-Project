import React from 'react';

interface MobileShellProps {
  children: React.ReactNode;
}

const MobileShell: React.FC<MobileShellProps> = ({ children }) => {
  return (
    <div className="max-w-md mx-auto min-h-screen bg-slate-50 relative shadow-2xl border-x border-slate-200 pb-28 flex flex-col">
      {children}
    </div>
  );
};

export default MobileShell;

