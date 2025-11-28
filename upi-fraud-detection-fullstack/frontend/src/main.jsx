import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './styles.css'
import Login from './pages/Login'
import UserDashboard from './pages/UserDashboard'
import MerchantDashboard from './pages/MerchantDashboard'
import AdminPanel from './pages/AdminPanel'

function App(){
  const token = localStorage.getItem('token')
  const role = localStorage.getItem('role')
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login/>} />
        <Route path="/user" element={token && role==='USER' ? <UserDashboard/> : <Navigate to="/"/>} />
        <Route path="/merchant" element={token && role==='MERCHANT' ? <MerchantDashboard/> : <Navigate to="/"/>} />
        <Route path="/admin" element={token && role==='ADMIN' ? <AdminPanel/> : <Navigate to="/"/>} />
      </Routes>
    </BrowserRouter>
  )
}

createRoot(document.getElementById('root')).render(<App/>)
