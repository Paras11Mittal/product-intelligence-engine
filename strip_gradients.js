const fs = require('fs');
let css = fs.readFileSync('app/static/style.css', 'utf8');

// 1. Remove the text gradient overrides completely
const gradientMarker = '/* --- TEXT GRADIENT OVERRIDES --- */';
if (css.includes(gradientMarker)) {
    css = css.substring(0, css.indexOf(gradientMarker)).trim();
}

// 2. Replace the :root and body.dark-mode blocks with a sophisticated Zinc minimalist palette
const oldRootRegex = /:root\s*\{[^}]+\}/;
const oldDarkRegex = /body\.dark-mode\s*\{[^}]+\}/;

const newRoot = `:root {
    --bg: #F4F4F5;
    --surface: #FFFFFF;
    --surface-strong: #FAFAFA;
    --text: #27272A;
    --muted: #71717A;
    --line: rgba(39, 39, 42, 0.08);
    --accent: #52525B;
    --accent-2: #52525B;
    --radius: 12px;
    --space: 24px;
}`;

const newDark = `body.dark-mode {
    --bg: #09090B;
    --surface: #18181B;
    --surface-strong: #27272A;
    --text: #F4F4F5;
    --muted: #A1A1AA;
    --line: rgba(244, 244, 245, 0.08);
    --accent: #E4E4E7;
    --accent-2: #E4E4E7;
}`;

css = css.replace(oldRootRegex, newRoot).replace(oldDarkRegex, newDark);

fs.writeFileSync('app/static/style.css', css);
