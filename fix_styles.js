const fs = require('fs');
let css = fs.readFileSync('app/static/style.css', 'utf8');

// Replace the peach gradient with a slight rainbowmized gradient
const oldGradient = 'linear-gradient(90deg, #FFB085 0%, var(--text-gradient-end) 100%)';
const newGradient = 'linear-gradient(90deg, #FF9A9E 0%, #FECFEF 25%, #C2E9FB 55%, var(--text-gradient-end) 100%)';

css = css.split(oldGradient).join(newGradient);

// Optional: Make it flow diagonally and fade to black in the top right
const blobCss = `
/* Ambient Rainbow Blob */
body::before {
    content: '';
    position: fixed;
    top: -15vh;
    right: -15vw;
    width: 60vw;
    height: 70vh;
    border-radius: 50%;
    /* Subtle rainbow gradient, flowing diagonally (225deg = top right to bottom left), fading to dark/transparent */
    background: linear-gradient(225deg, rgba(255, 154, 158, 0.3) 0%, rgba(254, 207, 239, 0.25) 20%, rgba(161, 196, 253, 0.2) 40%, rgba(194, 233, 251, 0.15) 60%, rgba(0, 0, 0, 0) 90%);
    filter: blur(120px);
    z-index: -1;
    pointer-events: none;
}
`;

if (!css.includes('Ambient Rainbow Blob')) {
    css += blobCss;
}

fs.writeFileSync('app/static/style.css', css);
