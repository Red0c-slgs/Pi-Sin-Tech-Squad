import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FaEdit, FaTrash, FaSort, FaSortUp, FaSortDown, FaChevronDown } from 'react-icons/fa';
import '../styles/ProjectPhotos.css';
import { Button } from '../components/ui';

function ProjectPhotos() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [totalPhotos, setTotalPhotos] = useState(0)
  const [project, setProject] = useState(null);
  const [photos, setPhotos] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  const [showModelDropdown, setShowModelDropdown] = useState(false);
  const [selectedModel, setSelectedModel] = useState('Default Model');
  
  // Sorting states
  const [sortField, setSortField] = useState('name');
  const [sortDirection, setSortDirection] = useState('asc');
  
  // Filter states
  const [filters, setFilters] = useState({
    name: '',
    date_start: '',
    date_end: '',
    status: ''
  });
  
  // Use refs to track if initial fetch has been done
  const initialFetchDone = useRef(false);
  const fetchInProgress = useRef(false);
  
  // Mock models for dropdown
  const availableModels = [
    'Default Model',
    'Fast Processing Model',
    'High Accuracy Model',
    'Experimental Model'
  ];
  
  // Get the proxy URL from environment variables
  const PROXY_URL = process.env.REACT_APP_PROXY_URL || '';
  
  const photosPerPage = 100;
  
  // Fetch project details
  const fetchProject = async () => {
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(`${PROXY_URL}/api/projects/${projectId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch project details');
      }
      
      const data = await response.json();
      setProject(data);
      setNewProjectName(data.name);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching project:', err);
    }
  };
  
  // Fetch project photos with pagination and sorting
  const fetchPhotos = useCallback(async () => {
    // Prevent multiple simultaneous fetches
    if (fetchInProgress.current) return;
    
    fetchInProgress.current = true;
    setIsLoading(true);
    setError('');
    
    try {
      const token = localStorage.getItem('authToken');
      
      // Build query parameters
      const params = new URLSearchParams();
      params.append('page', 1);
      params.append('size', photosPerPage);

      
      // Add filters if they exist
      if (filters.name) params.append('filename', filters.name);
      if (filters.date_start) params.append('date_start', filters.date_start);
      if (filters.date_end) params.append('date_end', filters.date_end);
      if (filters.status) params.append('status', filters.status);
      
      const response = await fetch(`${PROXY_URL}/projects/${projectId}/files?${params.toString()}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch photos');
      }
      
      const data = await response.json();
      setPhotos(data.items);
      setTotalPhotos(data.total);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching photos:', err);
    } finally {
      setIsLoading(false);
      fetchInProgress.current = false;
    }
  }, [projectId, sortField, sortDirection, filters]);
  
  // Initial data fetch - only run once when component mounts
  useEffect(() => {
    if (!initialFetchDone.current) {
      fetchProject();
      fetchPhotos();
      initialFetchDone.current = true;
    }
  }, [fetchPhotos]);
  
  // Handle changes to sort or filter - create a separate effect
  useEffect(() => {
    // Skip the initial render
    if (initialFetchDone.current) {
      // Fetch with new parameters
      fetchPhotos();
    }
  }, [sortField, sortDirection, fetchPhotos]);
  
  // Handle file upload
  const handleUpload = async (e) => {
    const files = e.target.files;
    if (files.length === 0) return;
    
    setIsUploading(true);
    setError('');
    
    try {
      const token = localStorage.getItem('authToken');
      
      for (let i = 0; i < files.length; i++) {
        const formData = new FormData();
        formData.append('file', files[i]);
        
        const response = await fetch(`${PROXY_URL}/projects/${projectId}/files`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        });
        
        if (!response.ok) {
          throw new Error(`Failed to upload ${files[i].name}`);
        }
      }
      
      // Refresh the photos list after upload
      fetchPhotos();
    } catch (err) {
      setError(err.message);
      console.error('Error uploading files:', err);
    } finally {
      setIsUploading(false);
    }
  };
  
  // Handle project name update
  const handleUpdateProjectName = async () => {
    if (!newProjectName.trim() || newProjectName === project.name) {
      setIsEditing(false);
      return;
    }
    
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(`${PROXY_URL}/api/projects/${projectId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: newProjectName
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to update project name');
      }
      
      const updatedProject = await response.json();
      setProject(updatedProject);
      setIsEditing(false);
    } catch (err) {
      setError(err.message);
      console.error('Error updating project name:', err);
    }
  };
  
  // Handle project deletion
  const handleDeleteProject = async () => {
    if (!window.confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
      return;
    }
    
    setIsDeleting(true);
    
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(`${PROXY_URL}/api/projects/${projectId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to delete project');
      }
      
      // Navigate back to projects list
      navigate('/projects');
    } catch (err) {
      setError(err.message);
      console.error('Error deleting project:', err);
      setIsDeleting(false);
    }
  };

  // Get the appropriate image URL from the photo object
  const getPhotoUrl = (photo) => {
    // Use s3_icon_url for thumbnails in the grid
    if (photo.s3_icon_url) {
      return photo.s3_icon_url;
    } else if (photo.s3_url) {
      return photo.s3_url;
    } else if (photo.url) {
      return photo.url;
    }
    // Fallback to the old method
    return `${PROXY_URL}/files/${photo.id}`;
  };

  // Handle sorting
  const handleSort = (field) => {
    if (sortField === field) {
      // Toggle direction if same field
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      // New field, default to ascending
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Get sort icon based on current sort state
  const getSortIcon = (field) => {
    if (sortField !== field) {
      return <FaSort className="sort-icon" />;
    }
    return sortDirection === 'asc' ? <FaSortUp className="sort-icon" /> : <FaSortDown className="sort-icon" />;
  };

  // Handle filter changes
  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Apply filters
  const applyFilters = (e) => {
    e.preventDefault();
    fetchPhotos();
  };

  // Format date for display
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  // Get status class for styling
  const getStatusClass = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return 'status-completed';
      case 'processing':
        return 'status-processing';
      case 'failed':
        return 'status-failed';
      case 'pending':
        return 'status-pending';
      default:
        return 'status-unknown';
    }
  };

  if (!project) {
    return <div className="loading">Loading project...</div>;
  }

  const triggerProjectAction = async () => {
  try {
    const response = await fetch(`${PROXY_URL}/api/projects/${projectId}`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Error ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    console.log('Project triggered:', data);
    alert('Обработка началась!');
  } catch (error) {
    console.error('Trigger failed:', error);
    alert('Failed to trigger project 8.');
  }
};

  return (
    <div className="project-photos-container">
      <div className="project-header">
        <div className="project-header-left">
          {isEditing ? (
            <div className="edit-project-name">
              <input
                type="text"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                autoFocus
              />
              <button className="btn-save" onClick={handleUpdateProjectName}>Save</button>
              <button className="btn-cancel" onClick={() => {
                setIsEditing(false);
                setNewProjectName(project.name);
              }}>Cancel</button>
            </div>
          ) : (
            <div className="project-title-container">
              <h1>{project.name}</h1>
              <div className="project-actions">
                <button 
                  className="btn-icon"
                  onClick={() => setIsEditing(true)}
                  title="Edit project name"
                >
                  <FaEdit />
                </button>
                <button 
                  className="btn-icon btn-delete"
                  onClick={handleDeleteProject}
                  disabled={isDeleting}
                  title="Delete project"
                >
                  <FaTrash />
                </button>
              </div>
            </div>
          )}
        </div>
        
        <div className="project-header-right">
          <div className="model-dropdown">
            <div style={{ marginTop: '20px' }}>
              <Button onClick={triggerProjectAction} >
                Разметить проект
              </Button>
            </div>
            {showModelDropdown && (
              <div className="dropdown-menu">
                {availableModels.map(model => (
                  <div 
                    key={model} 
                    className="dropdown-item"
                    onClick={() => {
                      setSelectedModel(model);
                      setShowModelDropdown(false);
                    }}
                  >
                    {model}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="controls-section">
        <div className="upload-section">
          <label className="upload-btn">
            {isUploading ? 'Uploading...' : 'Upload Photos'}
            <input
              type="file"
              multiple
              accept="image/*"
              onChange={handleUpload}
              disabled={isUploading}
              style={{ display: 'none' }}
            />
          </label>
        </div>
        
        <form className="filters-form" onSubmit={applyFilters}>
          <div className="filter-group">
            <input
              type="text"
              name="name"
              placeholder="Filter by name"
              value={filters.name}
              onChange={handleFilterChange}
            />
          </div>
          <div className="filter-group">
            <select
              name="status"
              value={filters.status}
              onChange={handleFilterChange}
            >
              <option value="">All statuses</option>
              <option value="pending">Pending</option>
              <option value="processing">Processing</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
          </div>
          <button type="submit" className="btn-apply-filters">Apply Filters</button>
        </form>
      </div>
      
      <div className="photos-table-container">
        <div className="photos-table-header">
          <div className="header-cell header-thumbnail">Thumbnail</div>
          <div 
            className="header-cell header-filename"
            onClick={() => handleSort('name')}
          >
            Filename {getSortIcon('name')}
          </div>
          <div 
            className="header-cell header-created"
            onClick={() => handleSort('created_at')}
          >
            Created {getSortIcon('created_at')}
          </div>
          <div 
            className="header-cell header-status"
            onClick={() => handleSort('status')}
          >
            Status {getSortIcon('status')}
          </div>
        </div>
        
        {photos.length === 0 && !isLoading ? (
          <div className="no-photos">No photos in this project yet. Upload some!</div>
        ) : (
          <div className="photos-table-body">
            {isLoading ? (
              <div className="loading-photos">Loading photos...</div>
            ) : (
              photos.map(photo => (
                <div 
                  key={photo.id} 
                  className="photo-row"
                  onClick={() => navigate(`/projects/${projectId}/photos/${photo.id}`)}
                >
                  <div className="cell cell-thumbnail">
                    <img src={getPhotoUrl(photo)} alt={photo.filename || 'Photo'} />
                  </div>
                  <div className="cell cell-filename">
                    {photo.filename || `Photo ${photo.id}`}
                  </div>
                  <div className="cell cell-created">
                    {formatDate(photo.created_at)}
                  </div>
                  <div className="cell cell-status">
                    <span className={`status-badge ${getStatusClass(photo.status)}`}>
                      {photo.status || 'Unknown'}
                    </span>
                  </div>
                </div>
              ))
            )}
            {totalPhotos > 0 && (
              <div className="photos-count">
                Showing {photos.length} of {totalPhotos} photos
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default ProjectPhotos;
