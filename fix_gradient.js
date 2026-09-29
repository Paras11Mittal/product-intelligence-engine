const fs = require('fs');
let css = fs.readFileSync('app/static/style.css', 'utf8');

css = css.replace('.brand, .eyebrow {', '.eyebrow {');

fs.writeFileSync('app/static/style.css', css);
