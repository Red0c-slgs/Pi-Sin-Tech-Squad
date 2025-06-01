import React, { useState } from 'react';
import './Input.css';

const Input = ({
  type = 'text',
  label,
  placeholder,
  value,
  onChange,
  error,
  disabled = false,
  fullWidth = false,
  required = false,
  name,
  id,
}) => {
  const [focused, setFocused] = useState(false);
  
  const inputClasses = [
    'ui-input',
    focused ? 'ui-input--focused' : '',
    error ? 'ui-input--error' : '',
    disabled ? 'ui-input--disabled' : '',
    fullWidth ? 'ui-input--full-width' : '',
  ].filter(Boolean).join(' ');

  return (
    <div className={inputClasses}>
      {label && (
        <label className="ui-input__label" htmlFor={id}>
          {label} {required && <span className="ui-input__required">*</span>}
        </label>
      )}
      <div className="ui-input__wrapper">
        <input
          type={type}
          className="ui-input__field"
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          disabled={disabled}
          required={required}
          name={name}
          id={id}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
        />
      </div>
      {error && <div className="ui-input__error">{error}</div>}
    </div>
  );
};

export default Input;
