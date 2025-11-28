import React, { useEffect, useState } from 'react'
import api from '../api'

function QR({ upiId }){
  const data = `upi://pay?pa=${upiId}&pn=Merchant&am=1&cu=INR`
  return (
    <div className="card">
      <h3 className="font-semibold">QR Code</h3>
      <p className="text-xs text-gray-500">UPI URI: {data}</p>
      <div className="bg-gray-200 p-8 text-center">[ Render QR here ]</div>
    </div>
  )
}

export default function MerchantDashboard(){
  const [merchant, setMerchant] = useState(null)
  const [txs, setTxs] = useState([])

  useEffect(()=>{
    const role = localStorage.getItem('role')
    if (role !== 'MERCHANT') window.location.href = '/'
    api.get('/merchants/').then(r=>{
      const m = r.data[0]
      if (m) {
        setMerchant(m)
        api.get(`/merchants/${m.id}/transactions`).then(t=>setTxs(t.data))
      }
    })
  },[])

  return (
    <div className="container">
      <h2 className="text-xl font-bold">Merchant Dashboard</h2>
      {merchant && <p className="mb-4">Welcome, {merchant.name} ({merchant.upi_id})</p>}
      {merchant && <QR upiId={merchant.upi_id} />}
      <div className="card">
        <h3 className="font-semibold mb-2">Transactions</h3>
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
