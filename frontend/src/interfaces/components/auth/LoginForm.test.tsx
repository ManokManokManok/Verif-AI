import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { LoginForm } from './LoginForm';

describe('LoginForm Component', () => {
  const renderLoginForm = () => {
    return render(
      <BrowserRouter>
        <LoginForm />
      </BrowserRouter>
    );
  };

  it('should render login form with email and password fields', () => {
    renderLoginForm();
    
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it('should render submit button', () => {
    renderLoginForm();
    
    const submitButton = screen.getByRole('button', { name: /login/i });
    expect(submitButton).toBeInTheDocument();
  });


  it('should render email input with correct type', () => {
    renderLoginForm();
    
    const emailInput = screen.getByLabelText(/email/i);
    expect(emailInput).toHaveAttribute('type', 'email');
  });

  it('should render password input with correct type', () => {
    renderLoginForm();
    
    const passwordInput = screen.getByLabelText(/password/i);
    expect(passwordInput).toHaveAttribute('type', 'password');
  });
});
