import { createContext, useContext, useState, useEffect } from 'react';
import { flushSync } from 'react-dom';

const ThemeContext = createContext();

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('app-theme') === 'light' ? 'light' : 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    document.body.setAttribute('data-theme', theme);
    localStorage.setItem('app-theme', theme);
  }, [theme]);

  const toggleTheme = (event) => {
    const updateTheme = () => {
      setTheme(prev => prev === 'dark' ? 'light' : 'dark');
    };

    const button = event?.currentTarget;
    if (
      typeof document.startViewTransition !== 'function'
      || window.matchMedia('(prefers-reduced-motion: reduce)').matches
    ) {
      updateTheme();
      return;
    }

    if (button) {
      const { left, top, width, height } = button.getBoundingClientRect();
      document.documentElement.style.setProperty('--theme-transition-x', `${left + width / 2}px`);
      document.documentElement.style.setProperty('--theme-transition-y', `${top + height / 2}px`);
    }

    document.startViewTransition(() => {
      flushSync(updateTheme);
    });
  };

  return (
    <ThemeContext.Provider value={{ theme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
