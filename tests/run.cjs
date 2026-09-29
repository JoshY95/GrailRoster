const {spawn} = require('node:child_process');
const server=spawn('python',['-m','http.server','8767','--bind','127.0.0.1'],{stdio:'ignore'});
async function run(file){
 return new Promise((resolve,reject)=>{
  const child=spawn(process.execPath,[file],{stdio:'inherit',env:{...process.env,GRAILROSTER_BASE_URL:'http://127.0.0.1:8767'}});
  child.on('exit',code=>code===0?resolve():reject(Error(`${file} failed (${code})`)));
 });
}
(async()=>{
 try {
  for(let i=0;i<50;i++){try{await fetch('http://127.0.0.1:8767');break;}catch{await new Promise(r=>setTimeout(r,100));}}
  for(const file of process.argv.slice(2))await run(file);
 }finally{server.kill();}
})().catch(e=>{console.error(e);process.exitCode=1;});
