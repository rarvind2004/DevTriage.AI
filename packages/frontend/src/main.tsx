import React from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import App from './App'
import Dashboard from './pages/Dashboard'
import Status from './pages/Status'
import History from './pages/History'
import Inputs from './pages/Inputs'
import Runs from './pages/Runs'
import './index.css'

const router = createBrowserRouter([
  { path: '/', element: <App />, children: [
    { path: '/', element: <Dashboard /> },
    { path: '/status', element: <Status /> },
    { path: '/history', element: <History /> },
    { path: '/inputs', element: <Inputs /> },
    { path: '/runs', element: <Runs /> },
  ]}
])

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>
)
