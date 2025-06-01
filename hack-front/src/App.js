import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import './App.css';
import Login from './pages/Login';
import Projects from './pages/Projects';
import ProjectPhotos from './pages/ProjectPhotos';
import PhotoDetail from './pages/PhotoDetail';
import Navbar from './components/Navbar';
import ComponentsDemo from './pages/ComponentsDemo';
import { AuthProvider, useAuth } from './store/authContext';
import './styles/variables.css';
import TableDemo from './pages/TableDemo';

// Protected route component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) {
    return <div className="loading">Loading...</div>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }
  
  return children;
};

// Redirect authenticated users away from login
const PublicRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) {
    return <div className="loading">Loading...</div>;
  }
  
  if (isAuthenticated) {
    return <Navigate to="/projects" replace />;
  }
  
  return children;
};

function AppContent() {
  const [navbarVariant, setNavbarVariant] = useState('default');
  const { isAuthenticated, logout } = useAuth();
  const location = useLocation();
  
  // Set navbar variant based on current route
  useEffect(() => {
    if (location.pathname === '/') {
      setNavbarVariant('minimal');
    } else {
      setNavbarVariant('default');
    }
  }, [location.pathname]);

  return (
    <div className="App">
      {/* Always render the Navbar, let the component decide when to show */}
      <Navbar 
        isAuthenticated={isAuthenticated} 
        onLogout={logout} 
        variant={navbarVariant}
      />
      <Routes>
        <Route path="/" element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        } />
        <Route path="/test" element={
            <TableDemo />
        } />
        <Route path="/components-demo" element={
          <ComponentsDemo />
        } />
        <Route 
          path="/projects" 
          element={
            <ProtectedRoute>
              <Projects />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/projects/:projectId" 
          element={
            <ProtectedRoute>
              <ProjectPhotos />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/projects/:projectId/photos/:photoId" 
          element={
            <ProtectedRoute>
              <PhotoDetail />
            </ProtectedRoute>
          } 
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
}

export default App;
