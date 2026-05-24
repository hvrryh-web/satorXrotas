export default function HomePage() {
  return (
    <main
      style={{
        minHeight: '100vh',
        background: '#0F172A',
        color: '#F8FAFC',
        fontFamily: 'system-ui, -apple-system, sans-serif',
        padding: '4rem 2rem',
        textAlign: 'center',
      }}
    >
      <h1 style={{ fontSize: '3rem', margin: 0, letterSpacing: '-0.02em' }}>NJZ RAT-OS</h1>
      <p style={{ fontSize: '1.25rem', marginTop: '1rem', opacity: 0.8 }}>
        Your Neural Operating System
      </p>
      <p style={{ marginTop: '0.5rem', opacity: 0.6 }}>Train. Focus. Create. Learn. Grow.</p>

      <hr style={{ border: 'none', borderTop: '1px solid #1E293B', margin: '3rem auto', width: '60%' }} />

      <p style={{ opacity: 0.6 }}>
        Phase 0 — Foundation in progress. Marketing site shell.
      </p>
    </main>
  );
}
