const fs = require('fs');
let css = fs.readFileSync('app/static/style.css', 'utf8');

// Undo the text gradient rainbow change
const currentGradient = 'linear-gradient(90deg, #FF9A9E 0%, #FECFEF 25%, #C2E9FB 55%, var(--text-gradient-end) 100%)';
const originalGradient = 'linear-gradient(90deg, #FFB085 0%, var(--text-gradient-end) 100%)';

css = css.split(currentGradient).join(originalGradient);

// Undo the ambient blob
const blobStartMarker = '/* Ambient Rainbow Blob */';
if (css.includes(blobStartMarker)) {
    // Slice off everything from the Ambient Rainbow Blob to the end of the file
    css = css.substring(0, css.indexOf(blobStartMarker)).trim();
    // Add a trailing newline to keep the file format clean
    css += '\n';
}

fs.writeFileSync('app/static/style.css', css);
