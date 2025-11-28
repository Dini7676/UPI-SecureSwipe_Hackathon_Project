import React, { useEffect, useState } from 'react'
import api from '../api'

export default function AdminPanel(){
  const [stats, setStats] = useState(null)
  const [logs, setLogs] = useState([])

  useEffect(()=>{
    const role = localStorage.getItem('role')
    if (role !== 'ADMIN') window.location.href = '/'
    api.get('/admin/stats').then(r=>setStats(r.data))
    api.get('/admin/fraud-logs').then(r=>setLogs(r.data))
  },[])

  return (
    <div className="container">
      <h2 className="text-xl font-bold">Admin Panel</h2>
      <div className="card">
        <h3 className="font-semibold mb-2">Stats</h3>
        {stats ? (
          <ul className="text-sm">
            <li>Transactions: {stats.transactions}</li>
            <li>Fraud Logs: {stats.frauds}</li>
            <li>OTP Logs: {stats.otp_logs}</li>
          </ul>
        ) : <p>Loading...</p>}
      </div>

      <div className="card">
        <h3 className="font-semibold mb-2">Recent Fraud Logs</h3>
        {logs.map(l=>(
          <div key={l.id} className="border-b py-2 text-sm">
            <div>Tx #{l.transaction_id} • Score {l.risk_score.toFixed(2)} • {l.level}</div>
            <div className="text-gray-500">{l.reason} • {new Date(l.ts).toLocaleString()}</div>
          </div>
        ))}
        {logs.length===0 && <p className="text-gray-500">No logs yet.</p>}
      </div>
    </div>
  )
}
