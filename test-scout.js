const fs = require('fs');
const path = require('path');
try {
  const dirents = fs.readdirSync('/Users/rishit/Coding/ses-emailer', { withFileTypes: true });
  console.log(dirents.map(d => `${d.name} isDir=${d.isDirectory()}`));
} catch (e) {
  console.error(e);
}
