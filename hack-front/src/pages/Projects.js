import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Table from '../components/ui/Table';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import '../styles/Projects.css';

function Projects() {
  const [projects, setProjects] = useState([]);
  const [newProjectName, setNewProjectName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [totalProjects, setTotalProjects] = useState(0);
  
  // Get the proxy URL from environment variables
  const PROXY_URL = process.env.REACT_APP_PROXY_URL || '';

  // Define table columns
  const columns = [
    { 
      header: 'ID', 
      accessor: 'id' 
    },
    { 
      header: 'Name', 
      accessor: 'name',
      render: (row) => (
        <Link to={`/projects/${row.id}`} className="project-link">
          {row.name}
        </Link>
      )
    },
    { 
      header: 'Created At', 
      accessor: 'created_at',
      render: (row) => new Date(row.created_at).toLocaleDateString()
    },
    { 
      header: 'image count', 
      accessor: 'image count',
      render: (row) => row.count_of_files
    },
    { 
      header: 'status', 
      accessor: 'status',
      render: (row) => {
        const statusClasses = {
          // open временный статус
          'open': 'status-pending', 
          'good': 'status-active',
          'errors': 'status-completed',
          'processing': 'status-pending'
        };
        return <span className={`status-badge ${statusClasses[row.status_files || 'processing']}`}>{row.status_files || 'processing'}</span>;
      }
    }
  ];

  const statusOptions = [
    { label: 'All', value: '' },
    { label: 'Good', value: 'good' },
    { label: 'Errors', value: 'errors' },
    { label: 'In process', value: 'in_process' },
  ];

  // Fetch projects from API
  const fetchProjects = async (filters = {}) => {
    setIsLoading(true);
    setError('');
    
    try {
      // Build query parameters
      const params = new URLSearchParams();
      if (filters.searchTerm) params.append('name', filters.searchTerm);
      
      if (filters.startDate) {
        params.append('start_date', filters.startDate);
      }
      
      if (filters.endDate) {
        params.append('end_date', filters.endDate);
      }
      
      params.append('page', filters.page || 1);
      params.append('size', filters.itemsPerPage || 10);
      
      const token = localStorage.getItem('authToken');
      const response = await fetch(`${PROXY_URL}/api/projects?${params.toString()}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch projects');
      }
      
      const data = await response.json();
      setProjects(data.items);
      setTotalProjects(data.total);
      return data.items;
    } catch (err) {
      setError(err.message);
      console.error('Error fetching projects:', err);
      return [];
    } finally {
      setIsLoading(false);
    }
  };

  // Initial fetch
  useEffect(() => {
    fetchProjects();
  }, []);

  const handleCreateProject = async (e) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    
    setIsLoading(true);
    setError('');
    
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(`${PROXY_URL}/api/projects`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: newProjectName
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to create project');
      }
      
      // Refresh the project list
      fetchProjects();
      setNewProjectName('');
      setShowModal(false);
    } catch (err) {
      setError(err.message);
      console.error('Error creating project:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async (filters) => {
    return await fetchProjects(filters);
  };

  return (
    <div className="projects-container">
      <div className="projects-header">
        <h1>Projects</h1>
        <Button  
          onClick={() => setShowModal(true)}
          variant='small'
        >
          Create Project
        </Button>
      </div>

      {error && <div className="error-message">{error}</div>}
      
      <div className="table-section">
        <Table 
          data={projects}
          columns={columns}
          onSearch={handleSearch}
          statusOptions={statusOptions}
          initialFilters={{
            searchTerm: '',
            startDate: '',
            endDate: '',
            status: '',
            itemsPerPage: 10,
            page: 1
          }}
          isLoading={isLoading}
          totalItems={totalProjects}
        />
      </div>

      {/* Create Project Modal */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2>Create New Project</h2>
            <form onSubmit={handleCreateProject}>
              <Input
                label="Project Name"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                placeholder="Enter project name"
                required
                fullWidth
              />
              <div className="modal-actions">
                <Button 
                  variant="secondary" 
                  onClick={() => setShowModal(false)}
                  type="button"
                >
                  Cancel
                </Button>
                <Button 
                  variant="primary" 
                  type="submit"
                  disabled={isLoading}
                >
                  {isLoading ? 'Creating...' : 'Create'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Projects;
