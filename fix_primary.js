const fs = require('fs');
let css = fs.readFileSync('app/static/style.css', 'utf8');

css = css.replace('background:#111111;color:#EDEDED;', 'background: var(--text); color: var(--bg);');
css = css.replace('background:#EDEDED;color:#111111', 'background: var(--text); color: var(--bg)');

fs.writeFileSync('app/static/style.css', css);
