import { siteConfig } from "../config/site";

function escapeXml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

export function GET() {
  const title = escapeXml(siteConfig.productName);
  const tagline = escapeXml(siteConfig.tagline);

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#07111f"/>
      <stop offset="55%" stop-color="#10243f"/>
      <stop offset="100%" stop-color="#4f9cff"/>
    </linearGradient>
    <radialGradient id="glow" cx="25%" cy="20%" r="70%">
      <stop offset="0%" stop-color="#79b8ff" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="#79b8ff" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  <rect width="1200" height="630" fill="url(#glow)"/>
  <rect x="80" y="80" width="1040" height="470" rx="42" fill="rgba(255,255,255,0.08)" stroke="rgba(255,255,255,0.22)"/>
  <circle cx="148" cy="148" r="32" fill="#4f9cff"/>
  <text x="148" y="160" text-anchor="middle" font-family="Arial, sans-serif" font-size="36" font-weight="800" fill="#ffffff">V</text>
  <text x="110" y="275" font-family="Arial, sans-serif" font-size="76" font-weight="800" fill="#eef5ff">${title}</text>
  <text x="110" y="348" font-family="Arial, sans-serif" font-size="34" fill="#c6d4e5">${tagline}</text>
  <text x="110" y="440" font-family="Arial, sans-serif" font-size="28" fill="#9fb2ca">Download • Transcribe • Organize • Audit</text>
</svg>`;

  return new Response(svg, {
    headers: {
      "Content-Type": "image/svg+xml; charset=utf-8"
    }
  });
}