import React from 'react';

const Header: React.FC = () => {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-center">
          <div className="flex items-center space-x-4">
            <div className="bg-white p-2 rounded-lg">
              <img 
                src="/tradeup-logo.png" 
                alt="TradeUp Logo" 
                className="h-8 w-8 rounded-lg"
                onError={(e) => {
                  // Fallback to a placeholder if logo image fails to load
                  e.currentTarget.style.display = 'none';
                  e.currentTarget.nextElementSibling.style.display = 'block';
                }}
              />
              <div 
                className="h-8 w-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center hidden"
              >
                <span className="text-white font-bold text-sm">TU</span>
              </div>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">TradeUp X Bot Control Dashboard</h1>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;