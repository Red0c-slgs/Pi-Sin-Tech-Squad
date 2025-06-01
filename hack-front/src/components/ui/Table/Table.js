import React, { useState, useEffect } from 'react';
import Button from '../Button';
import Input from '../Input';
import Dropdown from '../Dropdown';
import './Table.css';

const Table = ({
  data = [],
  columns = [],
  onSearch,
  statusOptions = [],
  initialFilters = {
    searchTerm: '',
    startDate: '',
    endDate: '',
    status: '',
    itemsPerPage: 10,
    page: 1
  },
  totalItems,
}) => {
  const [filters, setFilters] = useState(initialFilters);
  const [totalPages, setTotalPages] = useState(1);
  const [displayData, setDisplayData] = useState([]);

  useEffect(() => {}, )

  const itemsPerPageOptions = [
    { label: '10 items', value: 10 },
    { label: '20 items', value: 20 },
    { label: '50 items', value: 50 }
  ];

  useEffect(() => {
    // Calculate total pages based on filtered data and items per page
    let len = totalItems || data.length
    if (len > 0) {
      setTotalPages(Math.ceil(len / filters.itemsPerPage));
      
      // Update display data based on current page and items per page
      const startIndex = (filters.page - 1) * filters.itemsPerPage;
      const endIndex = startIndex + filters.itemsPerPage;
      setDisplayData(data.slice(startIndex, endIndex));
    } else {
      setDisplayData([]);
      setTotalPages(1);
    }
  }, [data, filters.page, filters.itemsPerPage, totalItems]);

  const handleFilterChange = (field, value) => {
    console.log(value)
    const updatedFilters = {
      ...filters,
      [field]: value
    };
    
    setFilters(updatedFilters);
    
    // Apply filters immediately
    if (onSearch) {
      onSearch(updatedFilters);
    }
  };

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      const updatedFilters = {
        ...filters,
        page: newPage
      };
      
      setFilters(updatedFilters);
      
      // Notify parent about page change
      if (onSearch) {
        onSearch(updatedFilters);
      }
    }
  };

  const renderPagination = () => {
    const pages = [];
    const maxVisiblePages = 5;
    
    let startPage = Math.max(1, filters.page - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    // Previous button
    pages.push(
      <button 
        key="prev" 
        className="pagination-button"
        disabled={filters.page === 1}
        onClick={() => handlePageChange(filters.page - 1)}
      >
        &laquo;
      </button>
    );
    
    // Page numbers
    for (let i = startPage; i <= endPage; i++) {
      pages.push(
        <button 
          key={i} 
          className={`pagination-button ${filters.page === i ? 'active' : ''}`}
          onClick={() => handlePageChange(i)}
        >
          {i}
        </button>
      );
    }
    
    // Next button
    pages.push(
      <button 
        key="next" 
        className="pagination-button"
        disabled={filters.page === totalPages}
        onClick={() => handlePageChange(filters.page + 1)}
      >
        &raquo;
      </button>
    );
    
    return pages;
  };

  return (
    <div className="table-container">
      <div className="table-filters">
        <div className="filter-row">
          <div className="filter-item search-input">
            <Input
              label="Search by name"
              value={filters.searchTerm}
              onChange={(value) => handleFilterChange('searchTerm', value.target.value)}
              placeholder="Enter name..."
              fullWidth
            />
          </div>
          
          <div className="date-status-container">
            <Input
              type="date"
              label="Start date"
              value={filters.startDate}
              onChange={(value) => handleFilterChange('startDate', value)}
              fullWidth
            />
            <Input
              type="date"
              label="End date"
              value={filters.endDate}
              onChange={(value) => handleFilterChange('endDate', value)}
              fullWidth
            />
            
            <div className="filter-item status-dropdown">
              <Dropdown
                label="Status"
                options={statusOptions}
                value={filters.status}
                onChange={(value) => handleFilterChange('status', value)}
                placeholder="Select status"
                fullWidth
              />
            </div>
          </div>
        </div>
      </div>
      
      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              {columns.map((column, index) => (
                <th key={index}>{column.header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayData.length > 0 ? (
              displayData.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {columns.map((column, colIndex) => (
                    <td key={colIndex}>
                      {column.render ? column.render(row) : row[column.accessor]}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={columns.length} className="no-data">
                  No data available
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      
      <div className="table-footer">
        <div className="items-per-page">
          <span>Items per page:</span>
          <div className="items-dropdown">
            <Dropdown
              options={itemsPerPageOptions}
              value={filters.itemsPerPage}
              onChange={(value) => {
                const updatedFilters = {
                  ...filters,
                  itemsPerPage: value,
                  page: 1
                };
                
                setFilters(updatedFilters);
                
                // Notify parent about the change
                if (onSearch) {
                  onSearch(updatedFilters);
                }
              }}
              noMargin
              dropUp
            />
          </div>
        </div>
        
        <div className="pagination">
          {renderPagination()}
        </div>
        
        <div className="page-info">
          Page {filters.page} of {totalPages}
        </div>
      </div>
    </div>
  );
};

export default Table;
