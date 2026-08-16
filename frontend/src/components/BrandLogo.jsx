export default function BrandLogo({ className = '', showTagline = false, src = '/logo.png', alt = 'PROVEXA' }) {
  return (
    <span className={`brand-logo ${className}`.trim()}>
      <img src={src} alt={alt} />
      {showTagline && <span className="brand-tagline">From potential to proof</span>}
    </span>
  );
}
