import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { takeInviteToken } from './api/client';
import './styles/global.css';

takeInviteToken();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);