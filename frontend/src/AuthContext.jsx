import React, { createContext, useState, useEffect } from 'react';
import toast from 'react-hot-toast';

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(localStorage.getItem('token') || null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (token) {
            localStorage.setItem('token', token);
            fetchUser(token);
        } else {
            localStorage.removeItem('token');
            setUser(null);
            setLoading(false);
        }
    }, [token]);

    const fetchUser = async (authToken) => {
        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/user/me`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            });
            if (response.ok) {
                const userData = await response.json();
                setUser(userData);
            } else {
                // Token invalid or expired
                setToken(null);
            }
        } catch (error) {
            console.error("Error fetching user", error);
        } finally {
            setLoading(false);
        }
    };

    const login = async (email, password) => {
        try {
            const formData = new URLSearchParams();
            formData.append('username', email); // OAuth2PasswordRequestForm expects 'username'
            formData.append('password', password);

            const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData.toString()
            });

            if (response.ok) {
                const data = await response.json();
                setToken(data.access_token);
                localStorage.setItem('token', data.access_token);
                // Also setting early user state to bypass immediate loader blink
                setUser({ email, full_name: data.user_name });
                toast.success(`Welcome back, ${data.user_name || email.split('@')[0]}!`);
                return { success: true };
            } else {
                const data = await response.json();
                toast.error(data.detail || 'Login failed');
                return { success: false, error: data.detail || 'Login failed' };
            }
        } catch (error) {
            console.error('Login error:', error);
            toast.error('Network error occurred');
            return { success: false, error: 'Network error occurred' };
        }
    };

    const register = async (email, password, fullName) => {
        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password, full_name: fullName })
            });

            if (response.ok) {
                // Auto-login after register
                return login(email, password);
            } else {
                const data = await response.json();
                return { success: false, error: data.detail };
            }
        } catch (error) {
            return { success: false, error: 'Network error' };
        }
    };

    const logout = () => {
        setToken(null);
    };

    return (
        <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
            {children}
        </AuthContext.Provider>
    );
};
