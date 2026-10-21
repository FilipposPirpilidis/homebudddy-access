class HomeBuddyAccessPanel extends HTMLElement {
 set hass(value){this._hass=value;if(!this.root)this.mount();}
 disconnectedCallback(){this.clearQR();}
 $(id){return this.root.getElementById(id);}
 clearQR(){if(this.qrURL)URL.revokeObjectURL(this.qrURL);this.qrURL=null;if(this.root){if(this.$('result').open)this.$('result').close();this.$('qr').removeAttribute('src');}}
 mount(){
  this.root=this.attachShadow({mode:'open'});
  this.root.innerHTML=`<link rel="stylesheet" href="/homebuddy-access-assets/owner.css?v=1.0.5"><main><header><img src="/homebuddy-access-assets/logo.png" alt="HomeBuddy"><div><small>HOME ASSISTANT × HOMEBUDDY</small><h1>Connect HomeBuddy</h1><p>Scan to connect your HomeBuddy app.</p></div></header><section class="mobile-apps"><h2>Get the HomeBuddy app</h2><p>HomeBuddy is a voice-powered companion for Home Assistant, available for iOS and Android. Control your home from your phone and supported wearables.</p><div class="store-links"><a href="https://apps.apple.com/app/id6738934960" target="_blank" rel="noopener noreferrer">iOS · App Store ↗</a><a href="https://play.google.com/store/apps/details?id=com.fpirpilidis.homebuddyandroid" target="_blank" rel="noopener noreferrer">Android · Google Play ↗</a></div><p>Install HomeBuddy on your phone, then use its Home Assistant QR scanner to connect. Features and QR filter support depend on your app version.</p></section><section><h2>Connection addresses</h2><label>Local address<input id="local" type="url" maxlength="2048" placeholder="http://homeassistant.local:8123"></label><label>External HTTPS address <span>(optional)</span><input id="remote" type="url" placeholder="https://your-home.example.com" maxlength="2048"></label><fieldset><legend>Use in the app</legend><label><input id="use-local" type="radio" name="mode" checked> Local</label><label><input id="use-remote" type="radio" name="mode"> Remote</label></fieldset><p id="hint"></p><h2>Entities shown in the app</h2><p>Optional: select entities to show. Leave all unchecked to show all. These are display filters, not access restrictions.</p><div id="entity-groups"></div><h2>Long-lived access token</h2><p id="token-info"></p><button id="create">Create token &amp; generate QR</button><p>Creates a new HomeBuddy token valid for up to 10 years. You can revoke it anytime in your Home Assistant profile → Security → Long-lived access tokens.</p><details><summary>Use an existing token instead</summary><ol><li>Open your Home Assistant profile (your name in the sidebar), then Security.</li><li>Find Long-lived access tokens and choose Create token. Name it HomeBuddy.</li><li>Copy the token shown once, return here and paste it below.</li></ol><p>If you already saved a token, paste that instead. Home Assistant cannot display its original value again.</p><label>Token<input id="token" type="password" autocomplete="off" spellcheck="false" placeholder="Paste your long-lived access token" maxlength="4096"></label><button id="generate">Generate QR with pasted token</button></details><p class="note">This QR contains a private token with your account’s full access. Scan it only with your own app. It is not a limited guest invitation. Home Assistant manages the token; this integration does not keep an extra copy. Local HTTP sends it unencrypted; use a trusted network.</p><p id="status" role="status"></p></section><dialog id="result"><button id="close-qr" autofocus>Close</button><h2>Scan with HomeBuddy</h2><img id="qr" alt="HomeBuddy connection QR"><p id="qr-mode"></p><p id="created-token"></p><p>Open the Home Assistant QR scanner in HomeBuddy, accept the connection settings. Your token connects the app without another login. Revoke it in your HA profile whenever needed.</p></dialog></main>`;
  this.$('close-qr').onclick=()=>this.$('result').close();
  this.$('local').oninput=()=>{this.clearQR();this.updateMode();};
  this.$('token').oninput=()=>{this.clearQR();this.updateMode();};
  this.$('remote').oninput=()=>{this.clearQR();this.updateMode();};
  for(const id of ['use-local','use-remote'])this.$(id).onchange=()=>{this.clearQR();this.updateMode();};
  this.$('generate').onclick=()=>this.generate();
  this.$('create').onclick=()=>this.generate(true);
  this.load();
 }
 renderEntities(groups){
  const root=this.$('entity-groups');root.replaceChildren();
  for(const [domain,title] of Object.entries({switch:'Switches',light:'Lights',script:'Scripts',humidifier:'Humidifiers',fan:'Fans',automation:'Automations'})){
   const group=document.createElement('details'),heading=document.createElement('summary');
   const items=groups[domain]||[];heading.textContent=title+' ('+items.length+')';group.append(heading);
   for(const item of items){const label=document.createElement('label'),input=document.createElement('input');input.type='checkbox';input.value=item.entity_id;input.onchange=()=>this.clearQR();label.append(input,document.createTextNode(' '+item.name+' ('+item.entity_id+')'));group.append(label);}
   root.append(group);
  }
 }
 selectedFilters(){return [...this.$('entity-groups').querySelectorAll('input:checked')].map(input=>input.value).sort();}
 updateMode(){
  this.localURL=this.$('local').value.trim();this.$('local').disabled=!!this.busy;
  for(const input of this.$('entity-groups').querySelectorAll('input'))input.disabled=!!this.busy;
  this.$('remote').disabled=!!this.busy;this.$('token').disabled=!!this.busy;
  this.$('use-local').disabled=this.busy||!this.localURL;
  this.$('use-remote').disabled=this.busy||!this.$('remote').value.trim();
  if(this.$('use-remote').checked&&!this.$('remote').value.trim())this.$('use-local').checked=true;
  this.$('hint').textContent=this.$('use-local').checked?'Your phone must be on the same local network as Home Assistant. For use away from home, enter an external HTTPS address and choose Remote.':'Your phone needs an internet connection. The HTTPS address must already provide access to Home Assistant; this does not create a tunnel.';
  this.$('create').disabled=this.busy||(this.$('use-local').checked?!this.localURL:!this.$('remote').value.trim());
  this.$('generate').disabled=this.busy||!this.$('token').value.trim()||(this.$('use-local').checked?!this.localURL:!this.$('remote').value.trim());
 }
 async load(){try{const data=await this._hass.callApi('GET','homebuddy_access/v1/owner');this.renderEntities(data.entities||{});this.localURL=data.local_url;this.$('local').value=data.local_url||'';this.$('remote').value='';this.$('token-info').textContent=data.first_token_name?'First existing token: '+data.first_token_name+'. Create a new token automatically, or use its saved value below.':'No long-lived access token found. Use the button below to create one automatically.';this.$(data.use_local?'use-local':'use-remote').checked=true;if(!this.localURL&&data.external_url)this.$('use-remote').checked=true;this.updateMode();}catch(error){this.$('status').textContent=error?.message||'Could not load settings. Use the Home Assistant owner account.';this.$('generate').disabled=true;this.$('create').disabled=true;}}
 async generate(create=false){
  if(this.busy)return;this.busy=true;this.clearQR();this.updateMode();this.$('status').textContent='';
  const local_url=this.$('local').value.trim(),filter_items=this.selectedFilters();
  const external_url=this.$('remote').value.trim(),use_local=this.$('use-local').checked,long_lived_token=this.$('token').value.trim();
  try{
   const data=create?{operation:'create_and_generate',external_url,use_local}:{operation:'generate',external_url,use_local,long_lived_token};
   Object.assign(data,{local_url,filter_items});
   const result=await this._hass.callApi('POST','homebuddy_access/v1/owner',data);
   // Do not show an outdated QR if the owner edited settings while generating.
   if(long_lived_token!==this.$('token').value.trim()||external_url!==this.$('remote').value.trim()||use_local!==this.$('use-local').checked)return;
   this.qrURL=URL.createObjectURL(new Blob([result.qr_svg],{type:'image/svg+xml'}));this.$('qr').src=this.qrURL;this.$('qr-mode').textContent=use_local?'Local connection — keep your phone on the same network.':'Remote connection — uses your external HTTPS address.';this.$('created-token').textContent=(create?'Created token: ':'Token: ')+(result.token_name||'HomeBuddy');this.$('result').showModal();
  }catch(error){this.$('status').textContent=error?.body?.error||error?.message||'Could not generate QR.';if(create)this.$('status').textContent+=' If the connection was interrupted, check your HA profile for a newly created HomeBuddy token before trying again.';}
  finally{this.busy=false;this.updateMode();}
 }
}
customElements.define('homebuddy-access-panel',HomeBuddyAccessPanel);
