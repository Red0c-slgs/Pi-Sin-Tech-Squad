import React, { useState, useRef, useEffect } from 'react';
import './Dropdown.css';

const Dropdown = ({
  options = [],
  value,
  onChange,
  placeholder = 'Select an option',
  disabled = false,
  error,
  label,
  required = false,
  fullWidth = false,
  noMargin = false,
  dropUp = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);
  
  const selectedOption = options.find(option => option.value === value);
  
  const dropdownClasses = [
    'ui-dropdown',
    isOpen ? 'ui-dropdown--open' : '',
    error ? 'ui-dropdown--error' : '',
    disabled ? 'ui-dropdown--disabled' : '',
    fullWidth ? 'ui-dropdown--full-width' : '',
    noMargin ? 'ui-dropdown--no-margin' : '',
    dropUp ? 'ui-dropdown--drop-up' : '',
  ].filter(Boolean).join(' ');

  const handleOptionClick = (option) => {
    onChange(option.value);
    setIsOpen(false);
  };

  const toggleDropdown = () => {
    if (!disabled) {
      setIsOpen(!isOpen);
    }
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <div className={dropdownClasses} ref={dropdownRef}>
      {label && (
        <label className="ui-dropdown__label">
          {label} {required && <span className="ui-dropdown__required">*</span>}
        </label>
      )}
      <div className="ui-dropdown__wrapper">
        <div className="ui-dropdown__selected" onClick={toggleDropdown}>
          <span className="ui-dropdown__text">
            {selectedOption ? selectedOption.label : placeholder}
          </span>
          <span className={`ui-dropdown__arrow ${isOpen ? 'ui-dropdown__arrow--open' : ''}`}>
            ▼
          </span>
        </div>
        {isOpen && (
          <ul className="ui-dropdown__options">
            {options.map((option) => (
              <li
                key={option.value}
                className={`ui-dropdown__option ${option.value === value ? 'ui-dropdown__option--selected' : ''}`}
                onClick={() => handleOptionClick(option)}
              >
                {option.label}
              </li>
            ))}
          </ul>
        )}
      </div>
      {error && <div className="ui-dropdown__error">{error}</div>}
    </div>
  );
};

export default Dropdown;
