import React, { useState } from 'react';
import { Button, Input, Dropdown, Form } from '../components/ui';
import '../styles/variables.css';
import './ComponentsDemo.css';

const ComponentsDemo = () => {
  const [inputValue, setInputValue] = useState('');
  const [dropdownValue, setDropdownValue] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    role: '',
  });
  
  const dropdownOptions = [
    { value: 'option1', label: 'Option 1' },
    { value: 'option2', label: 'Option 2' },
    { value: 'option3', label: 'Option 3' },
    { value: 'option4', label: 'Option 4' },
  ];
  
  const roleOptions = [
    { value: 'admin', label: 'Administrator' },
    { value: 'user', label: 'Regular User' },
    { value: 'editor', label: 'Editor' },
  ];
  
  const handleFormChange = (field, value) => {
    setFormData({
      ...formData,
      [field]: value
    });
  };
  
  const handleFormSubmit = (e) => {
    e.preventDefault();
    alert(JSON.stringify(formData, null, 2));
  };

  return (
    <div className="components-demo">
      <div className="components-demo__header">
        <h1>UI Components Demo</h1>
        <p>A showcase of UI components with the specified color theme</p>
      </div>
      
      <section className="demo-section">
        <h2>Buttons</h2>
        <div className="demo-grid">
          <div className="demo-item">
            <h3>Primary</h3>
            <Button variant="primary">Primary Button</Button>
          </div>
          <div className="demo-item">
            <h3>Secondary</h3>
            <Button variant="secondary">Secondary Button</Button>
          </div>
          <div className="demo-item">
            <h3>Text</h3>
            <Button variant="text">Text Button</Button>
          </div>
          <div className="demo-item">
            <h3>Success</h3>
            <Button variant="success">Success Button</Button>
          </div>
          <div className="demo-item">
            <h3>Error</h3>
            <Button variant="error">Error Button</Button>
          </div>
          <div className="demo-item">
            <h3>Disabled</h3>
            <Button variant="primary" disabled>Disabled Button</Button>
          </div>
          <div className="demo-item">
            <h3>Small</h3>
            <Button variant="primary" size="small">Small Button</Button>
          </div>
          <div className="demo-item">
            <h3>Medium (Default)</h3>
            <Button variant="primary" size="medium">Medium Button</Button>
          </div>
          <div className="demo-item">
            <h3>Large</h3>
            <Button variant="primary" size="large">Large Button</Button>
          </div>
          <div className="demo-item">
            <h3>Full Width</h3>
            <Button variant="primary" fullWidth>Full Width Button</Button>
          </div>
          <div className="demo-item">
            <h3>Animated Gradient</h3>
            <Button variant="primary" animated>Animated Button</Button>
          </div>
        </div>
      </section>
      
      <section className="demo-section">
        <h2>Inputs</h2>
        <div className="demo-grid">
          <div className="demo-item demo-item--full">
            <h3>Basic Input</h3>
            <Input 
              label="Basic Input"
              placeholder="Enter some text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
            />
          </div>
          <div className="demo-item demo-item--full">
            <h3>Required Input</h3>
            <Input 
              label="Required Input"
              placeholder="This field is required"
              required
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
            />
          </div>
          <div className="demo-item demo-item--full">
            <h3>With Error</h3>
            <Input 
              label="Input with Error"
              placeholder="Enter some text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              error="This field has an error"
            />
          </div>
          <div className="demo-item demo-item--full">
            <h3>Disabled Input</h3>
            <Input 
              label="Disabled Input"
              placeholder="This input is disabled"
              disabled
              value="Disabled value"
              onChange={(e) => {}}
            />
          </div>
        </div>
      </section>
      
      <section className="demo-section">
        <h2>Dropdowns</h2>
        <div className="demo-grid">
          <div className="demo-item demo-item--full">
            <h3>Basic Dropdown</h3>
            <Dropdown 
              label="Basic Dropdown"
              options={dropdownOptions}
              value={dropdownValue}
              onChange={setDropdownValue}
              placeholder="Select an option"
            />
          </div>
          <div className="demo-item demo-item--full">
            <h3>Required Dropdown</h3>
            <Dropdown 
              label="Required Dropdown"
              options={dropdownOptions}
              value={dropdownValue}
              onChange={setDropdownValue}
              placeholder="Select an option"
              required
            />
          </div>
          <div className="demo-item demo-item--full">
            <h3>With Error</h3>
            <Dropdown 
              label="Dropdown with Error"
              options={dropdownOptions}
              value={dropdownValue}
              onChange={setDropdownValue}
              placeholder="Select an option"
              error="This field has an error"
            />
          </div>
          <div className="demo-item demo-item--full">
            <h3>Disabled Dropdown</h3>
            <Dropdown 
              label="Disabled Dropdown"
              options={dropdownOptions}
              value={dropdownValue}
              onChange={setDropdownValue}
              placeholder="This dropdown is disabled"
              disabled
            />
          </div>
        </div>
      </section>
      
      <section className="demo-section">
        <h2>Form Example</h2>
        <Form onSubmit={handleFormSubmit}>
          <div className="ui-form__title">User Registration</div>
          
          <Input 
            label="Full Name"
            placeholder="Enter your full name"
            value={formData.name}
            onChange={(e) => handleFormChange('name', e.target.value)}
            required
          />
          
          <Input 
            type="email"
            label="Email Address"
            placeholder="Enter your email"
            value={formData.email}
            onChange={(e) => handleFormChange('email', e.target.value)}
            required
          />
          
          <Dropdown 
            label="User Role"
            options={roleOptions}
            value={formData.role}
            onChange={(value) => handleFormChange('role', value)}
            placeholder="Select a role"
            required
          />
          
          <div className="ui-form__footer">
            <Button variant="secondary" type="button">Cancel</Button>
            <Button variant="primary" type="submit">Register</Button>
          </div>
        </Form>
      </section>
    </div>
  );
};

export default ComponentsDemo;
