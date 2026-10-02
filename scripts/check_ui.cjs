// DOM behavior check without a browser. Visual layout still needs a browser rehearsal.
const fs=require('node:fs'), vm=require('node:vm'), assert=require('node:assert/strict');
class Element {
  constructor(){this.children=[];this.textContent='';this.hidden=false;this.disabled=false;this.value='';}
  replaceChildren(...items){this.children=items;}
  append(...items){this.children.push(...items);}
}
const ids=['form','run','error','proposals','receipt','trace','answer','message','scenario','commit'];
const elements=Object.fromEntries(ids.map(id=>[id,new Element()]));
elements.message.value='KE-1042 damaged';elements.scenario.value='normal';elements.commit.value='commit_failure';
const fixture=JSON.parse(fs.readFileSync('artifacts/sdk-rehearsal.json','utf8'));
fixture.proposals[0].token='test-only-token';
const responses=[];
const context=vm.createContext({document:{getElementById:id=>elements[id],createElement:()=>new Element()},fetch:async()=>{const next=responses.shift();assert.ok(next,'unexpected fetch');return {ok:next.ok,json:async()=>next.body};}});
const html=fs.readFileSync('static/index.html','utf8');
vm.runInContext(html.split('<script>')[1].split('</script>')[0],context);
(async()=>{
  responses.push({ok:true,body:fixture});
  await elements.form.onsubmit({preventDefault(){}});
  assert.equal(elements.trace.children.length,8);
  assert.equal(elements.run.disabled,false);
  assert.equal(elements.proposals.children.length,1);
  const button=elements.proposals.children[0].children[1];
  responses.push({ok:false,body:{detail:'Demo refund backend unavailable.'}});
  await button.onclick();
  assert.match(elements.error.textContent,/unavailable/);
  assert.equal(button.disabled,false);
  assert.equal(elements.receipt.hidden,true);
  responses.push({ok:true,body:{receipt_id:'DEMO-TEST',money_moved:false}});
  await button.onclick();
  assert.equal(elements.receipt.hidden,false);
  assert.match(elements.receipt.textContent,/DEMO-TEST/);
  responses.push({ok:false,body:{detail:'Agent unavailable.'}});
  await elements.form.onsubmit({preventDefault(){}});
  assert.equal(elements.proposals.children.length,0);
  assert.equal(elements.receipt.hidden,true);
  assert.equal(elements.run.disabled,false);
  assert.match(elements.error.textContent,/unavailable/);
  assert.equal(responses.length,0);
  console.log('UI DOM checks passed: trace, proposal, confirmation failure/recovery and request failure.');
})().catch(err=>{console.error(err);process.exit(1)});
