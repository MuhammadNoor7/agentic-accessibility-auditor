import Sidebar from '../../components/Sidebar';

export default function Placeholder({ name, activePage }) {
  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#f4f6fb' }}>
      <Sidebar activePage={activePage} />
      <main style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <p style={{ fontSize: 18, fontWeight: 700, color: '#0f1422', margin: '0 0 8px' }}>{name}</p>
          <p style={{ fontSize: 14, color: '#5a6a8a', margin: 0 }}>This screen is coming in the next build phase.</p>
        </div>
      </main>
    </div>
  );
}
