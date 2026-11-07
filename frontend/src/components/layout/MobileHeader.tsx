import React from 'react';
import { ChevronLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface MobileHeaderProps {
  title: string;
  showBack?: boolean;
  rightElement?: React.ReactNode;
  className?: string;
}

const MobileHeader: React.FC<MobileHeaderProps> = ({
  title,
  showBack = false,
  rightElement,
  className = '',
}) => {
  const navigate = useNavigate();

  return (
    <header
      className={`sticky top-0 z-30 bg-white/95 backdrop-blur-sm border-b border-slate-200 px-4 py-3 flex items-center gap-3 lg:hidden ${className}`}
    >
      {showBack && (
        <button
          onClick={() => navigate(-1)}
          className="flex items-center justify-center w-9 h-9 rounded-xl bg-slate-100 text-slate-600 hover:bg-slate-200 active:scale-95 transition-all"
          aria-label="Go back"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
      )}
      <h1 className="flex-1 text-base font-bold text-slate-900 truncate">{title}</h1>
      {rightElement && <div className="flex-shrink-0">{rightElement}</div>}
    </header>
  );
};

export default MobileHeader;
