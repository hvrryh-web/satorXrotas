import { useState } from 'react';

export function SatorSphere() {
  const [hoveredFacet, setHoveredFacet] = useState<string | null>(null);

  const facets = [
    { letter: 'S', row: 1, col: 1, color: '#FFD700', type: 'sator' },
    { letter: 'A', row: 2, col: 1, color: '#1E3A5F', type: 'arepo' },
    { letter: 'A', row: 2, col: 2, color: '#1E3A5F', type: 'arepo' },
    { letter: 'T', row: 3, col: 1, color: '#FFFFFF', type: 'tenet' },
    { letter: 'R', row: 3, col: 2, color: '#FF4655', type: 'opera' },
    { letter: 'T', row: 3, col: 3, color: '#FFFFFF', type: 'tenet' },
    { letter: 'O', row: 4, col: 1, color: '#00D4FF', type: 'opera' },
    { letter: 'E', row: 4, col: 2, color: '#1E3A5F', type: 'arepo' },
    { letter: 'E', row: 4, col: 3, color: '#1E3A5F', type: 'arepo' },
    { letter: 'O', row: 4, col: 4, color: '#00D4FF', type: 'opera' },
    { letter: 'R', row: 5, col: 1, color: '#FF4655', type: 'rotas' },
    { letter: 'P', row: 5, col: 2, color: '#00D4FF', type: 'opera' },
    { letter: 'N', row: 5, col: 3, color: '#FFFFFF', type: 'tenet', glow: true },
    { letter: 'P', row: 5, col: 4, color: '#00D4FF', type: 'opera' },
    { letter: 'R', row: 5, col: 5, color: '#FF4655', type: 'rotas' },
  ];

  return (
    <div className="relative w-full aspect-square">
      <svg
        viewBox="0 0 400 400"
        className="w-full h-full"
        style={{ animation: 'sphereRotate 30s linear infinite' }}
      >
        <defs>
          <radialGradient id="sphereDepth" cx="30%" cy="30%">
            <stop offset="0%" stopColor="rgba(255,255,255,0.1)" />
            <stop offset="100%" stopColor="rgba(0,0,0,0.3)" />
          </radialGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Background sphere */}
        <circle
          cx="200"
          cy="200"
          r="170"
          fill="#14141f"
          stroke="#2a2a3a"
          strokeWidth="2"
        />
        <circle cx="200" cy="200" r="170" fill="url(#sphereDepth)" />

        {/* Flow lines */}
        <ellipse
          cx="200"
          cy="200"
          rx="160"
          ry="40"
          fill="none"
          stroke="#ff4655"
          strokeWidth="1"
          opacity="0.3"
          style={{ animation: 'flow 4s linear infinite' }}
        />
        <ellipse
          cx="200"
          cy="200"
          rx="40"
          ry="160"
          fill="none"
          stroke="#00d4ff"
          strokeWidth="1"
          opacity="0.3"
          style={{ animation: 'flow 4s linear infinite', animationDelay: '-1s' }}
        />
        <ellipse
          cx="200"
          cy="200"
          rx="120"
          ry="120"
          fill="none"
          stroke="#ffd700"
          strokeWidth="1"
          opacity="0.2"
          style={{ animation: 'flow 4s linear infinite', animationDelay: '-2s' }}
        />

        {/* Facets */}
        {facets.map((facet, index) => {
          const angle = (index / facets.length) * Math.PI * 2;
          const radius = 80 + facet.row * 15;
          const x = 200 + Math.cos(angle) * radius;
          const y = 200 + Math.sin(angle) * radius;

          return (
            <g
              key={index}
              onMouseEnter={() => setHoveredFacet(facet.letter)}
              onMouseLeave={() => setHoveredFacet(null)}
              style={{
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                filter: hoveredFacet === facet.letter ? 'brightness(1.5)' : 'none',
              }}
            >
              <polygon
                points={`${x},${y - 15} ${x - 13},${y + 8} ${x + 13},${y + 8}`}
                fill={facet.color}
                opacity={hoveredFacet === facet.letter ? 1 : 0.8}
                filter={facet.glow ? 'url(#glow)' : undefined}
              />
              <text
                x={x}
                y={y + 3}
                textAnchor="middle"
                dominantBaseline="middle"
                fill={facet.color === '#FFFFFF' || facet.color === '#FFD700' ? '#0a0a0f' : '#ffffff'}
                fontSize="10"
                fontWeight="bold"
                fontFamily="JetBrains Mono, monospace"
                style={{ pointerEvents: 'none' }}
              >
                {facet.letter}
              </text>
            </g>
          );
        })}

        {/* Center glow */}
        <circle
          cx="200"
          cy="200"
          r="30"
          fill="url(#sphereDepth)"
          style={{ animation: 'pulse 2s ease-in-out infinite' }}
        />
      </svg>

      {/* Label */}
      <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 text-center">
        <p className="text-xs text-radiant-gray font-mono tracking-widest uppercase">
          SATOR Sphere
        </p>
        <p className="text-[10px] text-radiant-gray/60">5-Layer Palindrome Visualization</p>
      </div>

      <style>{`
        @keyframes sphereRotate {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes flow {
          to { stroke-dashoffset: -24; }
        }
        @keyframes pulse {
          0%, 100% { opacity: 0.3; }
          50% { opacity: 0.8; }
        }
      `}</style>
    </div>
  );
}
