import React, { useState } from 'react';
import Dashboard from './components/Dashboard';
import Header from './components/Header';
import SettingsModal from './components/SettingsModal';

console.log('API URL:', import.meta.env.VITE_RAILWAY_API_URL);

function App() {
  const [showSettings, setShowSettings] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Header onSettingsClick={() => setShowSettings(true)} />
      <main className="container mx-auto px-4 py-8">
        <Dashboard />
      </main>
      {showSettings && (
        <SettingsModal onClose={() => setShowSettings(false)} />
      )}
    </div>
  );
}

export default App;