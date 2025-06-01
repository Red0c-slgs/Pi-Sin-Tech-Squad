import React from 'react';
import './Form.css';

const Form = ({
  children,
  onSubmit,
  className = '',
}) => {
  const handleSubmit = (e) => {
    e.preventDefault();
    if (onSubmit) {
      onSubmit(e);
    }
  };

  return (
    <form className={`ui-form ${className}`} onSubmit={handleSubmit}>
      {children}
    </form>
  );
};

export default Form;
