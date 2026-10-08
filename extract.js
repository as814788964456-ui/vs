const fs = require('fs');
const pdf = require('pdf-parse');
let dataBuffer = fs.readFileSync('/Users/chengtechang/Desktop/vs/台積暑期intern_北大企管所張政德拷貝.pdf');
pdf(dataBuffer).then(function(data) {
    console.log(data.text);
});
