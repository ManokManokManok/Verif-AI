import { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

const DEFAULT_FONT_SCALE = 100;

function getStoredFontScale() {
  const stored = Number(localStorage.getItem('app-font-scale'));
  return [90, 100, 110, 120].includes(stored) ? stored : DEFAULT_FONT_SCALE;
}

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('app-theme') || 'dark';
  });
  const [fontScale, setFontScale] = useState(getStoredFontScale);

  useEffect(() => {
    document.body.setAttribute('data-theme', theme);
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('app-theme', theme);
  }, [theme]);

  useEffect(() => {
    document.documentElement.style.setProperty('--font-scale', String(fontScale / 100));
    localStorage.setItem('app-font-scale', String(fontScale));
  }, [fontScale]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  return (
    <ThemeContext.Provider value={{ theme, setTheme, toggleTheme, fontScale, setFontScale }}>
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
