import React, { useState } from 'react';
import Table from '../components/ui/Table';
import '../styles/Projects.css';

const TableDemo = () => {
  const [tableData, setTableData] = useState([
    { id: 1, name: 'Project Alpha', status: 'active', date: '2023-01-15', progress: 75 },
    { id: 2, name: 'Project Beta', status: 'completed', date: '2023-02-20', progress: 100 },
    { id: 3, name: 'Project Gamma', status: 'pending', date: '2023-03-10', progress: 30 },
    { id: 4, name: 'Project Delta', status: 'active', date: '2023-04-05', progress: 60 },
    { id: 5, name: 'Project Epsilon', status: 'on-hold', date: '2023-05-12', progress: 45 },
    { id: 6, name: 'Project Zeta', status: 'completed', date: '2023-06-18', progress: 100 },
    { id: 7, name: 'Project Eta', status: 'active', date: '2023-07-22', progress: 80 },
    { id: 8, name: 'Project Theta', status: 'pending', date: '2023-08-30', progress: 15 },
    { id: 9, name: 'Project Iota', status: 'on-hold', date: '2023-09-05', progress: 50 },
    { id: 10, name: 'Project Kappa', status: 'active', date: '2023-10-10', progress: 70 },
    { id: 11, name: 'Project Lambda', status: 'completed', date: '2023-11-15', progress: 100 },
    { id: 12, name: 'Project Mu', status: 'pending', date: '2023-12-20', progress: 25 },
  ]);
  
  const [filteredData, setFilteredData] = useState(tableData);
  const [appliedFilters, setAppliedFilters] = useState({});
  
  const columns = [
    { header: 'ID', accessor: 'id' },
    { header: 'Name', accessor: 'name' },
    { 
      header: 'Status', 
      accessor: 'status',
      render: (row) => {
        const statusClasses = {
          'active': 'status-active',
          'completed': 'status-completed',
          'pending': 'status-pending',
          'on-hold': 'status-onhold'
        };
        return <span className={`status-badge ${statusClasses[row.status]}`}>{row.status}</span>;
      }
    },
    { header: 'Date', accessor: 'date' }
  ];
  
  const statusOptions = [
    { label: 'All', value: '' },
    { label: 'Active', value: 'active' },
    { label: 'Completed', value: 'completed' },
    { label: 'Pending', value: 'pending' },
    { label: 'On Hold', value: 'on-hold' },
  ];
  
  const getProgressColor = (progress) => {
    if (progress < 30) return 'var(--error-color)';
    if (progress < 70) return 'orange';
    return 'var(--success-color)';
  };
  
  const handleSearch = (filters) => {
    setAppliedFilters(filters);
    
    // Filter the data based on the search criteria
    let filtered = [...tableData];
    
    // Filter by name
    if (filters.searchTerm) {
      filtered = filtered.filter(item => 
        item.name.toLowerCase().includes(filters.searchTerm.toLowerCase())
      );
    }
    
    // Filter by status
    if (filters.status) {
      filtered = filtered.filter(item => item.status === filters.status);
    }
    
    // Filter by date range
    if (filters.startDate) {
      filtered = filtered.filter(item => new Date(item.date) >= new Date(filters.startDate));
    }
    
    if (filters.endDate) {
      filtered = filtered.filter(item => new Date(item.date) <= new Date(filters.endDate));
    }
    
    setFilteredData(filtered);
    
    console.log('Applied filters:', filters);
  };
  
  return (
    <div className="table-demo-container">
      <h1>Table Component Demo</h1>
      
      <div className="demo-section">
        <h2>Data Table with Filters</h2>
        <p>This table demonstrates search, filtering, and pagination capabilities.</p>
        
        <Table 
          data={filteredData}
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
        />
        
        <div className="applied-filters">
          <h3>Applied Filters:</h3>
          <pre>{JSON.stringify(appliedFilters, null, 2)}</pre>
        </div>
      </div>
      
      <style jsx>{`
        .table-demo-container {
          padding: 20px;
          max-width: 1200px;
          margin: 0 auto;
        }
        
        .demo-section {
          margin-bottom: 40px;
        }
        
        .status-badge {
          padding: 4px 8px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 500;
          text-transform: uppercase;
        }
        
        .status-active {
          background-color: rgba(76, 175, 80, 0.2);
          color: var(--success-color);
        }
        
        .status-completed {
          background-color: rgba(138, 43, 226, 0.2);
          color: var(--primary-color);
        }
        
        .status-pending {
          background-color: rgba(255, 152, 0, 0.2);
          color: orange;
        }
        
        .status-onhold {
          background-color: rgba(255, 107, 107, 0.2);
          color: var(--error-color);
        }
        
        .progress-bar-container {
          width: 100%;
          height: 20px;
          background-color: #f0f0f0;
          border-radius: 10px;
          overflow: hidden;
          position: relative;
        }
        
        .progress-bar {
          height: 100%;
          border-radius: 10px;
          transition: width 0.3s ease;
        }
        
        .progress-bar-container span {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          color: var(--text-dark);
          font-size: 12px;
          font-weight: 500;
        }
        
        .applied-filters {
          margin-top: 20px;
          padding: 16px;
          background-color: #f5f5f5;
          border-radius: var(--border-radius);
        }
        
        .applied-filters pre {
          background-color: #fff;
          padding: 12px;
          border-radius: var(--border-radius);
          overflow: auto;
        }
      `}</style>
    </div>
  );
};

export default TableDemo;
