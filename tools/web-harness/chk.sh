#!/bin/bash
# syntax check of every script block
node -e "
const fs=require('fs');const h=fs.readFileSync(process.argv[1],'utf8');const re=/<script(?![^>]*src)[^>]*>([\s\S]*?)<\/script>/g;let m,i=0;while((m=re.exec(h))){fs.writeFileSync('/tmp/ct/sc'+i+'.js',m[1]);i++;}console.log(i);" "$1" | while read n; do for ((i=0;i<n;i++)); do node --check /tmp/ct/sc$i.js 2>&1 | head -5; done; done; echo checked
