import React from 'react';

/**
 * Footer component
 * Site footer with links and information
 */
export const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();
  return (
    <footer className="bg-slate-900 text-gray-400 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="text-sm text-center md:text-left">
            <p>&copy; {currentYear} VerifAI. All rights reserved.</p>
          </div>
        </div>
      </div>
    </footer>
  );
};
