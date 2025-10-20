export async function createCheckoutSession(priceId: string) {
  const base = (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '')
  const url = `${base}/api/v1/billing/create-checkout-session/`

  const token = typeof window !== 'undefined' ? localStorage.getItem('accessToken') : null

  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify({
      price_id: priceId,
      success_url: typeof window !== 'undefined' ? window.location.origin + '/billing/success' : undefined,
      cancel_url: typeof window !== 'undefined' ? window.location.origin + '/billing/cancel' : undefined
    })
  })

  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`createCheckoutSession failed: ${res.status} ${text}`)
  }

  return res.json()
}