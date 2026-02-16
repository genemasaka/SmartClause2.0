import React from 'react';
import ReactDOM from 'react-dom/client';
import StreamlitDocEditor from './StreamlitDocEditor';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <StreamlitDocEditor />
  </React.StrictMode>
);