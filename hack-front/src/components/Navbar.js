import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Button } from './ui';
import './Navbar.css';

function Navbar({ 
  isAuthenticated, 
  onLogout,
  variant = 'default' // 'default' or 'minimal'
}) {
  const location = useLocation();
  const navigate = useNavigate();
  const isLoginPage = location.pathname === '/';
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navRef = useRef(null);
  
  // Only check if we're on login page - removed the isAuthenticated check
  // This was causing the navbar to never render
  if (isLoginPage && variant !== 'minimal') {
    return null;
  }

  const handleLogout = () => {
    onLogout();
    navigate('/');
  };

  const isMinimal = variant === 'minimal';
  const navbarClasses = `navbar ${isMinimal ? 'navbar--minimal' : ''}`;

  return (
    <nav className={navbarClasses} ref={navRef}>
      <div className="navbar__container">
        <div className="navbar__brand">
          <Link to="/projects" className="navbar__logo">PI SIN</Link>
        </div>
        
        {!isMinimal && (
          <div className="navbar__mobile-toggle" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
            <span></span>
            <span></span>
            <span></span>
          </div>
        )}
        
        {!isMinimal && isAuthenticated && (
          <div className={`navbar__menu ${mobileMenuOpen ? 'navbar__menu--open' : ''}`}>
            {/* <Link to="/projects" className="navbar__item">
              Projects
            </Link>
            <Link to="/components-demo" className="navbar__item">
              Components
            </Link> */}
            <Button 
              variant="text" 
              onClick={handleLogout}
              className="navbar__logout"
            >
              Logout
            </Button>
          </div>
        )}
      </div>
    </nav>
  );
}

export default Navbar;
