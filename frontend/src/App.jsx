import React, { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import './App.css';
import Navbar from './Navbar';
import JobSearch from './JobSearch';
import Login from './Login';
import Register from './Register';
import Dashboard from './Dashboard';
import JobDetails from './JobDetails';
import ForgotPassword from './ForgotPassword';
import ResetPassword from './ResetPassword';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './AuthContext';

function App() {
  const [theme, setTheme] = useState('light');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  return (
    <div className={`app-layout ${theme}`}>
      <AuthProvider>
        <Navbar theme={theme} toggleTheme={toggleTheme} />
        <Toaster position="bottom-right" />

        <main className="container-fluid" style={{ padding: '0 2rem' }}>
          <Routes>
            <Route path="/" element={<JobSearch theme={theme} />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/job/:id" element={<JobDetails />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password/:token" element={<ResetPassword />} />
          </Routes>
        </main>

        <footer>
          <p>&copy; 2024 Ai Job Aggregator. All rights reserved. <span style={{ opacity: 0.5, fontSize: '0.8em' }}>v3.0 (UX Polish)</span></p>
        </footer>
      </AuthProvider>
    </div>
  );
}

export default App;
