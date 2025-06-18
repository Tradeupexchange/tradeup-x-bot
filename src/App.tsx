import React from 'react';
import Dashboard from './components/Dashboard';
import Header from './components/Header';

function App() {
  return (
    <div className="min-h-screen w-full">
      <Header />
      <main className="container mx-auto px-6 py-6">
        <Dashboard />
      </main>
    </div>
  );
}

export default App;