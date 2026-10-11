import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { ThemeProvider, useTheme } from '../src/context/ThemeContext';

function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return <button onClick={toggleTheme}>{theme}</button>;
}

describe('ThemeContext', () => {
  let boundingClientRectSpy;

  beforeEach(() => {
    localStorage.getItem.mockReturnValue(null);
    localStorage.setItem.mockClear();
  });

  afterEach(() => {
    delete document.startViewTransition;
    document.documentElement.style.removeProperty('--theme-transition-x');
    document.documentElement.style.removeProperty('--theme-transition-y');
    boundingClientRectSpy?.mockRestore();
  });

  it('restores and persists the selected theme', () => {
    localStorage.getItem.mockReturnValueOnce('light');

    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>,
    );

    expect(screen.getByRole('button')).toHaveTextContent('light');
    expect(document.documentElement).toHaveAttribute('data-theme', 'light');
    expect(localStorage.setItem).toHaveBeenLastCalledWith('app-theme', 'light');
  });

  it('uses the view transition from the toggle position when available', () => {
    const startViewTransition = vi.fn((update) => update());
    document.startViewTransition = startViewTransition;
    boundingClientRectSpy = vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue({
      left: 10,
      top: 20,
      width: 40,
      height: 40,
      right: 50,
      bottom: 60,
      x: 10,
      y: 20,
      toJSON: () => ({}),
    });

    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>,
    );

    fireEvent.click(screen.getByRole('button'));

    expect(startViewTransition).toHaveBeenCalledOnce();
    expect(screen.getByRole('button')).toHaveTextContent('light');
    expect(document.documentElement.style.getPropertyValue('--theme-transition-x')).toBe('30px');
    expect(document.documentElement.style.getPropertyValue('--theme-transition-y')).toBe('40px');
  });
});
