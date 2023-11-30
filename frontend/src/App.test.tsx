import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('submit file button', () => {
  render(<App />);
  const linkElement = screen.getByText(/Upload/i);
  expect(linkElement).toBeInTheDocument();
});
