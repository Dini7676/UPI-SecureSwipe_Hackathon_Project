import React, { useEffect, useState } from 'react'
import api from '../api'

export default function UserDashboard(){
  const [user, setUser] = useState(null)
  const [txs, setTxs] = useState([])

  useEffect(()=>{
    const role = localStorage.getItem('role')
    if (role !== 'USER') window.location.href = '/'
    api.get('/users/').then(r=>{
      const me = r.data.find(u=>u.role==='USER')
      if (me) {
        setUser(me)
        api.get(`/users/${me.id}/transactions`).then(t=>setTxs(t.data))
      }
    })
  },[])

  return (
    <div className="container">
      <h2 className="text-xl font-bold">User Dashboard</h2>
      {user && <p className="mb-4">Welcome, {user.name} ({user.mobile})</p>}
      <div className="card">
        <h3 className="font-semibold mb-2">Transaction History</h3>
        {txs.map(t=>(
          <div key={t.id} className="border-b py-2 text-sm flex justify-between">
            <span>₹{t.amount} • {new Date(t.ts).toLocaleString()}</span>
            <span>Risk: {t.risk_score.toFixed(2)} {t.is_fraud? '⚠️':''}</span>
          </div>
        ))}
        {txs.length===0 && <p className="text-gray-500">No transactions yet.</p>}
      </div>
    </div>
  )
}
