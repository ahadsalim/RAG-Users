import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'https://admin.tejarat.chat'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Forward User-Agent and IP from original request
    const userAgent = request.headers.get('user-agent') || ''
    const forwardedFor = request.headers.get('x-forwarded-for') || request.headers.get('x-real-ip') || ''
    
    const response = await fetch(`${BACKEND_URL}/api/v1/auth/verify-otp/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': userAgent,
        'X-Forwarded-For': forwardedFor,
        'X-Real-IP': forwardedFor.split(',')[0]?.trim() || '',
      },
      body: JSON.stringify(body),
    })
    
    const data = await response.json()
    
    return NextResponse.json(data, { status: response.status })
  } catch (error: any) {
    return NextResponse.json(
      { message: 'خطا در تایید کد' },
      { status: 500 }
    )
  }
}
