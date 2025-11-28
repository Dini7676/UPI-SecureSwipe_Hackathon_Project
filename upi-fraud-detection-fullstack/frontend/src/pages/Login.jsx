import React, { useState } from 'react'
import api from '../api'

export default function Login(){
  const [mobile, setMobile] = useState('')
  const [email, setEmail] = useState('')
  const [otp, setOtp] = useState('')
  const [sent, setSent] = useState(false)
  const [debugOtp, setDebugOtp] = useState('')

  const send = async ()=>{
    const { data } = await api.post('/auth/send-otp', { mobile, email: email || null })
    setSent(true)
    setDebugOtp(data.otp_debug)
  }
  const verify = async ()=>{
    const { data } = await api.post('/auth/verify-otp', { mobile, email: email || null, otp })
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('role', data.role)
    if (data.role === 'ADMIN') window.location.href = '/admin'
    else if (data.role === 'MERCHANT') window.location.href = '/merchant'
    else window.location.href = '/user'
  }

  return (
    <div className="container">
      <h1 className="text-2xl font-bold mb-4">Login via OTP</h1>
      <div className="card">
        <input className="input" placeholder="Mobile" value={mobile} onChange={e=>setMobile(e.target.value)} />
        <input className="input" placeholder="Email (optional)" value={email} onChange={e=>setEmail(e.target.value)} />
        {!sent ? (
          <button className="button" onClick={send}>Send OTP</button>
        ) : (
          <div>
            <input className="input" placeholder="Enter OTP" value={otp} onChange={e=>setOtp(e.target.value)} />
            <button className="button" onClick={verify}>Verify</button>
            <p className="text-sm mt-2 text-gray-500">Debug OTP: {debugOtp}</p>
          </div>
        )}
      </div>
    </div>
  )
}
