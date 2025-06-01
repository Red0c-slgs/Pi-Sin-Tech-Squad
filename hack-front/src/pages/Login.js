import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../store/authContext';
import { Button, Input, Dropdown, Form } from '../components/ui';
import '../styles/Login.css';

function Login() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [formErrors, setFormErrors] = useState({});
  
  const navigate = useNavigate();
  const { login, register, isAuthenticated, isLoading, error } = useAuth();
  
  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/projects');
    }
  }, [isAuthenticated, navigate]);

  const validateForm = () => {
    const errors = {};
    
    if (!email) {
      errors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      errors.email = 'Email is invalid';
    }
    
    if (!password) {
      errors.password = 'Password is required';
    } else if (password.length < 8) {
      errors.password = 'Password must be at least 8 characters';
    }
    
    if (!isLogin && !name) {
      errors.name = 'Name is required';
    } else if (!isLogin && name.length < 4) {
      errors.name = 'Name must be at least 4 characters';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    let success;
    
    if (isLogin) {
      success = await login(email, password);
    } else {
      success = await register(email, name, password);
    }
    
    if (success) {
      navigate('/projects');
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <Form onSubmit={handleSubmit}>
          <div className="ui-form__title">{!isLogin ? 'Register' : 'Login'}</div>
          
          <Input
            type="email"
            label="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={formErrors.email}
            required
            fullWidth
          />
          {!isLogin && (
              <div className="form-group">
                <Input
                  type="text"
                  label="Name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  error={formErrors.name}
                  required
                  fullWidth
                />
              </div>
            )}
            
            <div className="form-group">
              <Input
                type="password"
                label="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                error={formErrors.password}
                required
                fullWidth
              />
            </div>
                    
          <div className="ui-form__footer">
            <Button variant="primary" fullWidth type="submit">{isLoading ? 'Processing...' : (isLogin ? 'Login' : 'Register')}</Button>
          </div>

          <div className="login-toggle">
            <p>
              {isLogin ? "Don't have an account? " : "Already have an account? "}
              <Button 
                variant="text"
                onClick={() => {
                  setIsLogin(!isLogin);
                  setFormErrors({});
                }}
                disabled={isLoading}
              >
                {isLogin ? 'Register' : 'Login'}
              </Button>
            </p>
          </div>
        </Form>
          
      </div>
    </div>
  );
}

export default Login;
