import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, Lock, User, ArrowRight, Eye, EyeOff } from 'lucide-react';

const LandingPage = ({ setIsAuthenticated }) => {
    const [isLogin, setIsLogin] = useState(true);
    const [formData, setFormData] = useState({ email: '', password: '', full_name: '' });
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        const endpoint = isLogin ? '/login' : '/register';
        const body = isLogin
            ? { email: formData.email, password: formData.password }
            : { email: formData.email, password: formData.password, full_name: formData.full_name };

        try {
            // Using 127.0.0.1 to avoid localhost resolution issues (IPv4 vs IPv6)
            const res = await fetch(`http://127.0.0.1:8000${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            const data = await res.json();

            if (!res.ok) throw new Error(data.detail || 'Authentication failed');

            if (isLogin) {
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('user', data.user_name);
                setIsAuthenticated(true);
                navigate('/dashboard');
            } else {
                setIsLogin(true); // Switch to login after signup
                setError('Registration successful! Please login.');
            }
        } catch (err) {
            setError(err.message === 'Failed to fetch' ? 'Cannot connect to server. Is backend running?' : err.message);
        }
    };

    return (
        <div className="landing-container">
            <div className="landing-card-wrapper">
                {/* Left Side - Minimalist Illustration */}
                <div className="landing-left">
                    <h1 className="brand-logo">TheTOP</h1>
                    <div className="illustration">
                        <svg viewBox="0 0 500 500" className="line-art">
                            <path d="M150,400 L350,400" stroke="black" strokeWidth="2" fill="none" />
                            <circle cx="350" cy="150" r="40" stroke="black" strokeWidth="2" fill="none" />
                            <path d="M300,400 L300,300 L280,280" stroke="black" strokeWidth="2" fill="none" />
                            <circle cx="280" cy="260" r="15" stroke="black" strokeWidth="2" fill="none" />
                            <path d="M100,450 Q250,350 400,450" stroke="#ccc" strokeWidth="1" fill="none" />
                        </svg>
                        <h2>Bring Yourself To The Top</h2>
                        <p>Stop looking for a secret trick. The best version of yourself is your vision.</p>
                    </div>
                </div>

                {/* Right Side - Auth Form */}
                <div className="landing-right">
                    <div className="auth-form-container">
                        <h2>{isLogin ? 'Welcome Back' : 'Create Account'}</h2>
                        {error && <p className="auth-error">{error}</p>}

                        <form onSubmit={handleSubmit}>
                            {!isLogin && (
                                <div className="input-group">
                                    <User size={20} />
                                    <input
                                        type="text"
                                        placeholder="Full Name"
                                        value={formData.full_name}
                                        onChange={e => setFormData({ ...formData, full_name: e.target.value })}
                                        required
                                    />
                                </div>
                            )}

                            <div className="input-group">
                                <Mail size={20} />
                                <input
                                    type="email"
                                    placeholder="Email Address"
                                    value={formData.email}
                                    onChange={e => setFormData({ ...formData, email: e.target.value })}
                                    required
                                />
                            </div>

                            <div className="input-group">
                                <Lock size={20} />
                                <input
                                    type={showPassword ? "text" : "password"}
                                    placeholder="Password"
                                    value={formData.password}
                                    onChange={e => setFormData({ ...formData, password: e.target.value })}
                                    required
                                />
                                <div
                                    onClick={() => setShowPassword(!showPassword)}
                                    style={{ cursor: 'pointer', marginLeft: '10px' }}
                                >
                                    {showPassword ? <EyeOff size={20} color="#666" /> : <Eye size={20} color="#666" />}
                                </div>
                            </div>

                            <button type="submit" className="auth-btn">
                                {isLogin ? 'Login' : 'Sign Up'} <ArrowRight size={18} />
                            </button>
                        </form>

                        <p className="toggle-auth">
                            {isLogin ? "Don't have an account? " : "Already have an account? "}
                            <span onClick={() => { setIsLogin(!isLogin); setError(''); }}>
                                {isLogin ? 'Sign Up' : 'Login'}
                            </span>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default LandingPage;
