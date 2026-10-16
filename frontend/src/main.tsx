import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { takeInviteToken } from './api/client';
import './styles/global.css';

takeInviteToken();
// An invite link pasted into a tab that already has the app open only changes
// the part after the #, which doesn't reload the page; reload to sign in with it
window.addEventListener('hashchange', () => {
  if (window.location.hash.startsWith('#invite=')) window.location.reload();
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);