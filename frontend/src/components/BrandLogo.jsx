export default function BrandLogo({ className = '', showTagline = false }) {
  return (
    <span className={`brand-logo ${className}`.trim()}>
      <img src="/logo.png" alt="PROVEXA" />
      {showTagline && <span className="brand-tagline">From potential to proof</span>}
    </span>
  );
}
