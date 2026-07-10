import logoMark from '../../assets/axion-logo-mark.png';

export default function Logo({ size = 'md', showTagline = true, light = false, align = 'left' }) {
  const sizes = {
    sm: { icon: 34, word: 'text-xl', tagline: 'text-[10px]', gap: 'gap-2' },
    md: { icon: 40, word: 'text-2xl', tagline: 'text-[11px]', gap: 'gap-2.5' },
    lg: { icon: 140, word: 'text-4xl', tagline: 'text-sm', gap: 'gap-3.5' },
  };
  const s = sizes[size];
  const wordColor = light ? 'text-white' : 'text-[var(--color-navy)]';
  const taglineColor = light ? 'text-[var(--color-light-gray-text)]' : 'text-[var(--color-gray-text)]';
  const alignClass = align === 'center' ? 'items-center text-center' : 'items-start text-left';

  return (
    <div className={`flex flex-col ${s.gap} ${alignClass}`}>
      <img src={logoMark} alt="" aria-hidden="true" width={s.icon} height={s.icon} style={{ width: s.icon, height: s.icon }} />
      <div>
        <div className={`font-bold tracking-[0.15em] leading-none ${s.word} ${wordColor}`}>AXION</div>
        {showTagline && (
          <div className={`font-medium tracking-[0.2em] uppercase mt-1.5 ${s.tagline} ${taglineColor}`}>
            AI Accessibility Auditor
          </div>
        )}
      </div>
    </div>
  );
}
