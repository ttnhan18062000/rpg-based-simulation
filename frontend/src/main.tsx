import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { MetadataProvider } from './contexts/MetadataContext.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <MetadataProvider>
      <App />
    </MetadataProvider>
  </StrictMode>,
)
