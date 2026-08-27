let platform = 'github';
const inputArea = document.getElementById('inputArea');
const results = document.getElementById('results');
const statusEl = document.getElementById('status');
const examplesEl = document.getElementById('examples');

const platforms = {
  github: {
    placeholder: 'torvalds',
    label: 'Username',
    btn: 'Lookup',
    examples: ['torvalds', 'octocat', 'vercel/next.js'],
    subTabs: ['profile','emails','repo','search','network','org'],
    color: 'white',
  },
  tiktok: {
    placeholder: 'khaby.lame',
    label: 'Username',
    btn: 'Lookup',
    examples: ['khaby.lame', 'charlidamelio', 'bellapoarch'],
    color: 'white',
  },
  instagram: {
    placeholder: 'cristiano',
    label: 'Username',
    btn: 'Lookup',
    examples: ['cristiano', 'therock', 'kyliejenner'],
    color: 'white',
  },
  twitter: {
    placeholder: 'elonmusk',
    label: 'Username',
    btn: 'Lookup',
    examples: ['elonmusk', 'nasa', 'billgates'],
    color: 'white',
  },
  youtube: {
    placeholder: 'MrBeast',
    label: 'Channel @name or ID',
    btn: 'Lookup',
    examples: ['MrBeast', 'PewDiePie', 'T-Series'],
    color: 'white',
  },
  discord: {
    placeholder: 'discord',
    label: 'Username',
    btn: 'Lookup',
    examples: ['discord', 'nasa', 'spotify'],
    color: 'white',
  },
};

let subTab = 'profile';

function renderInput() {
  const cfg = platforms[platform];
  if (platform === 'github' && (subTab === 'repo' || subTab === 'search' || subTab === 'org')) {
    inputArea.innerHTML = `
      <input id="mainInput" placeholder="${subTab==='repo'?'vercel/next.js':subTab==='org'?'github':'osint language:python'}" class="flex-1 px-4 py-2.5 rounded-xl bg-zinc-800 border border-zinc-700 outline-none text-sm placeholder:text-zinc-500"/>
      <button id="searchBtn" class="px-5 py-2.5 rounded-xl bg-white text-black font-semibold text-sm">${subTab==='search'?'Search':'Lookup'}</button>`;
  } else {
    inputArea.innerHTML = `
      <input id="mainInput" placeholder="${cfg.placeholder}" class="flex-1 px-4 py-2.5 rounded-xl bg-zinc-800 border border-zinc-700 outline-none text-sm placeholder:text-zinc-500"/>
      <button id="searchBtn" class="px-5 py-2.5 rounded-xl bg-white text-black font-semibold text-sm">${cfg.btn}</button>`;
  }
  document.getElementById('searchBtn').onclick = doSearch;
  document.getElementById('mainInput').addEventListener('keydown', e=>{ if(e.key==='Enter') doSearch(); });

  // GitHub subtabs
  if (platform === 'github') {
    const subHtml = `<div class="flex flex-wrap gap-1 mt-2">${cfg.subTabs.map(s=>`<button data-sub="${s}" class="sub-btn px-2.5 py-1 rounded-lg text-[11px] font-medium ${s===subTab?'bg-white text-black':'bg-zinc-800 hover:bg-zinc-700'}">${s}</button>`).join('')}</div>`;
    inputArea.insertAdjacentHTML('beforeend', `<div class="absolute mt-14"></div>`);
    const subDiv = document.createElement('div');
    subDiv.className = 'flex flex-wrap gap-1 mt-2';
    subDiv.innerHTML = cfg.subTabs.map(s=>`<button data-sub="${s}" class="sub-btn px-2.5 py-1 rounded-lg text-[11px] font-medium ${s===subTab?'bg-white text-black':'bg-zinc-800 hover:bg-zinc-700'}">${s}</button>`).join('');
    inputArea.appendChild(subDiv);
    subDiv.querySelectorAll('.sub-btn').forEach(b=>{
      b.onclick = ()=>{ subTab=b.dataset.sub; renderInput(); };
    });
  }

  // Examples
  examplesEl.innerHTML = cfg.examples.map(e=>`<button class="example px-2 py-1 rounded-full border border-zinc-800 hover:bg-zinc-800" data-ex="${e}">${e}</button>`).join('');
  examplesEl.querySelectorAll('.example').forEach(b=>{
    b.onclick = ()=>{ document.getElementById('mainInput').value=b.dataset.ex; doSearch(); };
  });
}

// Platform buttons
document.querySelectorAll('.plat-btn').forEach(btn=>{
  btn.onclick = ()=>{
    document.querySelectorAll('.plat-btn').forEach(b=>{ b.className='plat-btn px-4 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2 bg-zinc-900 border border-zinc-800 hover:bg-zinc-800'; });
    btn.className='plat-btn active px-4 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2 bg-white text-black';
    platform=btn.dataset.platform; subTab='profile'; results.innerHTML=''; hideStatus(); renderInput();
  };
});

function showStatus(msg, type='error'){
  statusEl.className='rounded-xl border px-4 py-3 text-sm '+(type==='error'?'bg-red-500/10 border-red-500/30 text-red-300':'bg-emerald-500/10 border-emerald-500/30 text-emerald-300');
  statusEl.textContent=msg; statusEl.classList.remove('hidden');
}
function hideStatus(){ statusEl.classList.add('hidden'); }

function card(html){ return `<div class="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-4">${html}</div>`; }

function badge(text, color='zinc'){ return `<span class="px-2 py-0.5 rounded-full bg-${color}-500/10 border border-${color}-500/20 text-${color}-300 text-xs">${text}</span>`; }

async function doSearch(){
  const val = document.getElementById('mainInput').value.trim();
  if(!val){ showStatus('Enter a value'); return; }
  hideStatus();
  results.innerHTML=`<div class="rounded-2xl border border-zinc-800 bg-zinc-900 p-8 text-center text-sm text-zinc-400"><i class="fa-solid fa-circle-notch fa-spin mr-2"></i>Searching...</div>`;

  let url='';
  if(platform==='github'){
    if(subTab==='profile') url=`/api/github/user/${enc(val)}`;
    else if(subTab==='emails') url=`/api/github/emails/${enc(val)}`;
    else if(subTab==='repo'){ const p=val.split('/'); if(p.length!==2){showStatus('Use owner/repo');results.innerHTML='';return;} url=`/api/github/repo/${enc(p[0])}/${enc(p[1])}`; }
    else if(subTab==='search') url=`/api/github/search/users?q=${enc(val)}`;
    else if(subTab==='network') url=`/api/github/network/${enc(val)}`;
    else if(subTab==='org') url=`/api/github/org/${enc(val)}`;
  }
  if(platform==='tiktok') url=`/api/tiktok/user/${enc(val)}`;
  if(platform==='instagram') url=`/api/instagram/user/${enc(val)}`;
  if(platform==='twitter') url=`/api/twitter/user/${enc(val)}`;
  if(platform==='youtube') url=`/api/youtube/user/${enc(val)}`;
  if(platform==='discord') url=`/api/discord/user/${enc(val)}`;

  try{
    const r=await fetch(url); const data=await r.json();
    if(!r.ok){ showStatus(data.detail||'Error'); results.innerHTML=`<pre class="rounded-xl bg-zinc-900 border border-zinc-800 p-4 text-xs">${JSON.stringify(data,null,2)}</pre>`; return; }
    renderResult(data);
  }catch(e){ showStatus(String(e)); }
}
function enc(s){ return encodeURIComponent(s); }

function renderResult(data){
  if(platform==='github') renderGithub(data);
  else if(platform==='tiktok') renderTikTok(data);
  else if(platform==='instagram') renderInstagram(data);
  else if(platform==='twitter') renderTwitter(data);
  else if(platform==='youtube') renderYouTube(data);
  else if(platform==='discord') renderDiscord(data);
}

// ==================== GITHUB ====================
function renderGithub(d){
  if(subTab==='profile') renderGitHubProfile(d);
  else if(subTab==='emails') renderGitHubEmails(d);
  else if(subTab==='repo') renderGitHubRepo(d);
  else if(subTab==='search') renderGitHubSearch(d);
  else if(subTab==='network') renderGitHubNetwork(d);
  else if(subTab==='org') renderGitHubOrg(d);
}
function renderGitHubProfile(d){
  const p=d.profile;
  results.innerHTML=`
    ${card(`<div class="flex gap-4"><img src="${p.avatar_url}" class="w-20 h-20 rounded-2xl border border-zinc-800"/><div class="flex-1 min-w-0"><h2 class="text-xl font-bold">${p.name||p.login} <span class="text-zinc-500 font-normal text-base">@${p.login}</span></h2><p class="text-sm text-zinc-400 mt-1">${p.bio||'No bio'}</p><div class="mt-2 flex flex-wrap gap-2 text-xs">${p.location?badge('📍 '+p.location):''}${p.blog?`<a href="${p.blog.startsWith('http')?p.blog:'https://'+p.blog}" target="_blank" class="px-2 py-1 rounded-full bg-zinc-800 border border-zinc-700 hover:bg-zinc-700">🔗 ${p.blog}</a>`:''}${p.twitter_username?badge('@'+p.twitter_username):''}${p.company?badge(p.company):''}</div><div class="mt-3 flex gap-4 text-xs"><span><b>${p.followers}</b> followers</span><span><b>${p.following}</b> following</span><span><b>${p.public_repos}</b> repos</span><span class="text-zinc-500">since ${new Date(p.created_at).getFullYear()}</span></div></div><a href="${p.html_url}" target="_blank" class="h-fit px-3 py-2 rounded-xl bg-white text-black text-xs font-semibold">GitHub</a></div>`)}
    <div class="grid md:grid-cols-2 gap-4">
      ${card(`<h3 class="font-semibold text-sm mb-2"><i class="fa-solid fa-envelope mr-2 text-zinc-500"></i>Emails (${d.emails_found.length})</h3>${d.emails_found.length?d.emails_found.map(e=>`<div class="text-xs font-mono bg-zinc-950 border border-zinc-800 rounded-lg px-2 py-1.5 mt-1">${e}</div>`).join(''):`<p class="text-xs text-zinc-500">None found</p>`}`)}
      ${card(`<h3 class="font-semibold text-sm mb-2"><i class="fa-solid fa-share-nodes mr-2 text-zinc-500"></i>Social</h3><pre class="text-xs bg-zinc-950 border border-zinc-800 rounded-xl p-3">${JSON.stringify(d.social_footprint,null,2)}</pre>`)}
    </div>
    ${card(`<h3 class="font-semibold text-sm mb-3">Top Repos (${d.repos_count})</h3><div class="grid md:grid-cols-2 gap-2">${d.repos.slice(0,6).map(r=>`<div class="rounded-xl border border-zinc-800 bg-zinc-950 p-3"><div class="text-sm font-semibold truncate"><a href="${r.html_url}" target="_blank" class="hover:underline">${r.full_name}</a> <span class="text-zinc-500">★${r.stargazers_count}</span></div><div class="text-xs text-zinc-400 line-clamp-2">${r.description||''}</div></div>`).join('')}</div>`)}
    <details class="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-4"><summary class="text-sm font-semibold cursor-pointer">Raw JSON</summary><pre class="mt-3 text-xs bg-zinc-950 border border-zinc-800 rounded-xl p-3 overflow-auto max-h-[400px]">${JSON.stringify(d,null,2)}</pre></details>`;
}
function renderGitHubEmails(d){
  results.innerHTML=`
    ${card(`<h2 class="font-bold">Email finder — @${d.username}</h2>
      <div class="mt-3 grid md:grid-cols-2 gap-3">
        <div><div class="text-xs font-semibold text-emerald-400">Real emails (${d.real_emails.length})</div>${d.real_emails.length?d.real_emails.map(e=>`<div class="mt-1 font-mono text-xs bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-2 py-1.5">${e}</div>`).join(''):`<div class="text-xs text-zinc-500 mt-1">None</div>`}</div>
        <div><div class="text-xs font-semibold text-zinc-400">Noreply (${d.noreply_emails.length})</div>${d.noreply_emails.map(e=>`<div class="mt-1 font-mono text-xs bg-zinc-800 border border-zinc-700 rounded-lg px-2 py-1.5">${e}</div>`).join('')||''}</div>
      </div>`)}
    <details class="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-4"><summary class="text-sm font-semibold cursor-pointer">Raw</summary><pre class="mt-3 text-xs bg-zinc-950 border border-zinc-800 rounded-xl p-3 overflow-auto max-h-[400px]">${JSON.stringify(d,null,2)}</pre></details>`;
}
function renderGitHubRepo(d){
  const m=d.meta;
  results.innerHTML=`
    ${card(`<div class="flex gap-3"><div class="flex-1"><h2 class="font-bold text-lg"><a href="${m.html_url}" target="_blank" class="hover:underline">${m.full_name}</a></h2><p class="text-sm text-zinc-400">${m.description||''}</p><div class="mt-2 flex flex-wrap gap-2 text-xs">${badge('★ '+m.stargazers_count)}${badge('⑂ '+m.forks_count)}${badge(m.language||'')}${badge(m.visibility)}</div></div></div>`)}
    <div class="grid md:grid-cols-3 gap-4">
      ${card(`<h3 class="text-xs font-semibold text-zinc-500">Languages</h3><pre class="mt-2 text-xs bg-zinc-950 border border-zinc-800 rounded-xl p-3">${JSON.stringify(d.languages||{},null,2)}</pre>`)}
      ${card(`<h3 class="text-xs font-semibold text-zinc-500">Emails (${d.emails_in_commits.length})</h3><div class="mt-2 space-y-1">${d.emails_in_commits.map(e=>`<div class="font-mono text-xs bg-zinc-950 border border-zinc-800 rounded-lg px-2 py-1">${e}</div>`).join('')||'<span class="text-zinc-500 text-xs">none</span>'}</div>`)}
      ${card(`<h3 class="text-xs font-semibold text-zinc-500">Contributors</h3><div class="mt-2 space-y-1 max-h-[180px] overflow-auto">${(d.contributors||[]).slice(0,8).map(c=>`<a href="${c.html_url}" target="_blank" class="flex items-center gap-2 text-xs"><img src="${c.avatar_url}" class="w-5 h-5 rounded-full"/>${c.login} (${c.contributions})</a>`).join('')||'<span class="text-zinc-500 text-xs">hidden</span>'}</div>`)}
    </div>`;
}
function renderGitHubSearch(d){
  results.innerHTML=card(`<h3 class="font-semibold text-sm mb-3">Results (${d.total_count})</h3><div class="space-y-2">${d.items.slice(0,10).map(u=>`<a href="${u.html_url}" target="_blank" class="flex items-center gap-3 p-3 rounded-xl bg-zinc-950 border border-zinc-800 hover:bg-zinc-800"><img src="${u.avatar_url}" class="w-10 h-10 rounded-full"/><div><div class="text-sm font-semibold">${u.login}</div><div class="text-xs text-zinc-500">${u.type} • score ${u.score?.toFixed(2)}</div></div></a>`).join('')}</div>`);
}
function renderGitHubNetwork(d){
  results.innerHTML=`
    ${card(`<h2 class="font-bold">Network — @${d.profile.login}</h2><div class="mt-2 flex gap-3 text-xs">${badge(d.followers_count+' followers')}${badge(d.following_count+' following')}${badge(d.mutuals_count+' mutuals','emerald')}</div>${d.mutuals.length?`<div class="mt-3 flex flex-wrap gap-1">${d.mutuals.map(m=>`<span class="text-xs px-2 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">${m}</span>`).join('')}</div>`:''}`)}
    <div class="grid md:grid-cols-2 gap-4">
      ${card(`<h3 class="font-semibold text-sm mb-2">Followers</h3><div class="flex flex-wrap gap-1.5 max-h-[300px] overflow-auto">${d.followers.map(f=>`<a href="${f.html_url}" target="_blank" class="flex items-center gap-1.5 px-2 py-1 rounded-full bg-zinc-800 border border-zinc-700 text-xs"><img src="${f.avatar_url}" class="w-4 h-4 rounded-full"/>${f.login}</a>`).join('')}</div>`)}
      ${card(`<h3 class="font-semibold text-sm mb-2">Following</h3><div class="flex flex-wrap gap-1.5 max-h-[300px] overflow-auto">${d.following.map(f=>`<a href="${f.html_url}" target="_blank" class="flex items-center gap-1.5 px-2 py-1 rounded-full bg-zinc-800 border border-zinc-700 text-xs"><img src="${f.avatar_url}" class="w-4 h-4 rounded-full"/>${f.login}</a>`).join('')}</div>`)}
    </div>`;
}
function renderGitHubOrg(d){
  results.innerHTML=`
    ${card(`<div class="flex gap-4"><img src="${d.org.avatar_url}" class="w-14 h-14 rounded-2xl border border-zinc-800"/><div><h2 class="font-bold">${d.org.login}</h2><p class="text-sm text-zinc-400">${d.org.description||''}</p><div class="text-xs text-zinc-500">${d.org.location||''} • ${d.org.public_repos} repos</div><a href="https://github.com/${d.org.login}" target="_blank" class="inline-block mt-2 text-xs px-3 py-1.5 rounded-lg bg-white text-black font-semibold">View</a></div></div>`)}
    ${card(`<h3 class="font-semibold text-sm mb-2">Repos (${d.repos.length})</h3><div class="grid md:grid-cols-2 gap-2">${d.repos.map(r=>`<a href="${r.html_url}" target="_blank" class="p-3 rounded-xl bg-zinc-950 border border-zinc-800"><div class="text-sm font-semibold">${r.name} ★${r.stargazers_count}</div><div class="text-xs text-zinc-400">${r.description||''}</div></a>`).join('')}</div>`)}`;
}

// ==================== TIKTOK ====================
function renderTikTok(d){
  const p=d.profile; const s=d.stats||{};
  results.innerHTML=`
    ${card(`<div class="flex gap-4">${p.avatar?`<img src="${p.avatar}" class="w-20 h-20 rounded-2xl border border-zinc-800"/>`:`<div class="w-20 h-20 rounded-2xl bg-zinc-800 flex items-center justify-center text-2xl">♪</div>`}<div class="flex-1"><h2 class="text-xl font-bold">${p.nickname||p.unique_id||d.username} ${p.verified?'<span class="text-blue-400 text-sm">✓ Verified</span>':''}</h2><p class="text-zinc-400 text-sm">@${p.unique_id||d.username}</p><p class="text-zinc-500 text-sm mt-1">${p.signature||'No bio'}</p><div class="mt-2 flex flex-wrap gap-2 text-xs">${p.language?badge(p.language):''}${p.url?`<a href="${p.url}" target="_blank" class="px-2 py-1 rounded-full bg-zinc-800 border border-zinc-700 hover:bg-zinc-700">TikTok Profile →</a>`:''}</div></div></div>`)}
    ${Object.keys(s).length?card(`<h3 class="font-semibold text-sm mb-2">Stats</h3><div class="grid grid-cols-2 md:grid-cols-4 gap-3">${Object.entries(s).map(([k,v])=>`<div class="text-center"><div class="text-lg font-bold">${typeof v==='number'?v.toLocaleString():v||'—'}</div><div class="text-[11px] text-zinc-500 capitalize">${k.replace(/([A-Z])/g,' $1')}</div></div>`).join('')}</div>`):''}
    ${d.note?card(`<p class="text-xs text-zinc-400">${d.note}</p>`):''}
    <details class="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-4"><summary class="text-sm font-semibold cursor-pointer">Raw JSON</summary><pre class="mt-3 text-xs bg-zinc-950 border border-zinc-800 rounded-xl p-3 overflow-auto max-h-[400px]">${JSON.stringify(d,null,2)}</pre></details>`;
}

// ==================== INSTAGRAM ====================
function renderInstagram(d){
  const p=d.profile; const s=d.stats||{}; const risk=d.risk||{};
  results.innerHTML=`
    ${card(`<div class="flex gap-4">${p.profile_pic_url?`<img src="${p.profile_pic_url}" class="w-20 h-20 rounded-2xl border border-zinc-800" referrerpolicy="no-referrer"/>`:`<div class="w-20 h-20 rounded-2xl bg-gradient-to-br from-pink-500 to-purple-600 flex items-center justify-center text-2xl">📸</div>`}<div class="flex-1"><h2 class="text-xl font-bold">${p.full_name||p.username||d.username} ${p.is_verified?'<span class="text-blue-400 text-sm">✓</span>':''}</h2><p class="text-zinc-400 text-sm">@${p.username||d.username}</p><p class="text-zinc-500 text-sm mt-1">${p.biography||'No bio'}</p><div class="mt-2 flex flex-wrap gap-2 text-xs">${p.external_url?`<a href="${p.external_url}" target="_blank" class="px-2 py-1 rounded-full bg-zinc-800 border border-zinc-700 hover:bg-zinc-700">🔗 ${p.external_url}</a>`:''}${p.category?badge(p.category):''}${p.url?`<a href="${p.url}" target="_blank" class="px-2 py-1 rounded-full bg-zinc-800 border border-zinc-700 hover:bg-zinc-700">Instagram →</a>`:''}</div></div></div>`)}
    ${Object.keys(s).length?card(`<h3 class="font-semibold text-sm mb-2">Stats</h3><div class="grid grid-cols-3 gap-3 text-center">${Object.entries(s).map(([k,v])=>`<div><div class="text-lg font-bold">${typeof v==='number'?v.toLocaleString():v||'—'}</div><div class="text-[11px] text-zinc-500 capitalize">${k.replace(/_/g,' ')}</div></div>`).join('')}</div>`):''}
    ${Object.keys(risk).length?card(`<h3 class="font-semibold text-sm mb-2">OSINT Flags</h3><div class="flex flex-wrap gap-2">${Object.entries(risk).map(([k,v])=>`<div class="px-3 py-2 rounded-xl bg-zinc-950 border border-zinc-800 text-xs"><span class="text-zinc-500">${k}:</span> <b>${v||'—'}</b></div>`).join('')}</div>`):''}
    ${d.recent_posts&&d.recent_posts.length?card(`<h3 class="font-semibold text-sm mb-2">Recent Posts</h3><div class="space-y-2">${d.recent_posts.map(p=>`<div class="rounded-xl bg-zinc-950 border border-zinc-800 p-3 text-xs"><div class="text-zinc-400 line-clamp-2">${p.caption||'(no caption)'}</div><div class="text-zinc-500 mt-1">❤️ ${p.likes||0} • 💬 ${p.comments||0}</div></div>`).join('')}</div>`):''}
    <details class="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-4"><summary class="text-sm font-semibold cursor-pointer">Raw JSON</summary><pre class="mt-3 text-xs bg-zinc-950 border border-zinc-800 rounded-xl p-3 overflow-auto max-h-[400px]">${JSON.stringify(d,null,2)}</pre></details>`;
}

// ==================== TWITTER ====================
function renderTwitter(d){
  const p=d.profile;
  results.innerHTML=`
    ${card(`<div class="flex gap-4"><div class="w-20 h-20 rounded-2xl bg-zinc-800 flex items-center justify-center text-3xl"><i class="fa-brands fa-x-twitter"></i></div><div class="flex-1"><h2 class="text-xl font-bold">@${p.username||d.username}</h2>${p.bio?`<p class="text-zinc-400 text-sm mt-1">${p.bio}</p>`:''}<div class="mt-2 flex flex-wrap gap-2 text-xs">${p.url?`<a href="${p.url}" target="_blank" class="px-2 py-1 rounded-full bg-zinc-800 border border-zinc-700 hover:bg-zinc-700">X / Twitter →</a>`:''}${p.nitter_url?`<a href="${p.nitter_url}" target="_blank" class="px-2 py-1 rounded-full bg-zinc-800 border border-zinc-700 hover:bg-zinc-700">Nitter →</a>`:''}</div></div></div>`)}
    ${d.stats&&Object.keys(d.stats).length?card(`<h3 class="font-semibold text-sm mb-2">Stats</h3><div class="flex flex-wrap gap-3 text-xs">${Object.entries(d.stats).map(([k,v])=>`<div><b>${v}</b> <span class="text-zinc-500">${k}</span></div>`).join('')}</div>`):''}
    ${d.note?card(`<p class="text-xs text-zinc-400"><i class="fa-solid fa-circle-info mr-1"></i>${d.note}</p>`):''}
    <details class="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-4"><summary class="text-sm font-semibold cursor-pointer">Raw JSON</summary><pre class="mt-3 text-xs bg-zinc-950 border border-zinc-800 rounded-xl p-3 overflow-auto max-h-[400px]">${JSON.stringify(d,null,2)}</pre></details>`;
}

// ==================== YOUTUBE ====================
function renderYouTube(d){
  const p=d.profile; const s=d.stats||{}; const risk=d.risk||{};
  results.innerHTML=`
    ${card(`<div class="flex gap-4"><div class="w-20 h-20 rounded-2xl bg-red-500/20 border border-red-500/30 flex items-center justify-center text-3xl text-red-400"><i class="fa-brands fa-youtube"></i></div><div class="flex-1"><h2 class="text-xl font-bold">${p.channel_title||d.username}</h2>${p.description?`<p class="text-zinc-400 text-sm mt-1 line-clamp-2">${p.description}</p>`:''}<div class="mt-2 flex flex-wrap gap-2 text-xs">${p.url?`<a href="${p.url}" target="_blank" class="px-2 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-red-300 hover:bg-red-500/20">YouTube →</a>`:''}${p.country?badge(p.country):''}${p.join_date?badge('Joined '+p.join_date):''}${p.channel_id?badge(p.channel_id.substring(0,12)+'...'):''}</div></div></div>`)}
    ${Object.keys(s).length?card(`<h3 class="font-semibold text-sm mb-2">Stats</h3><div class="grid grid-cols-3 gap-3 text-center">${Object.entries(s).map(([k,v])=>`<div><div class="text-lg font-bold">${v||'—'}</div><div class="text-[11px] text-zinc-500 capitalize">${k.replace(/_/g,' ')}</div></div>`).join('')}</div>`):''}
    ${Object.keys(risk).length?card(`<h3 class="font-semibold text-sm mb-2">OSINT Flags</h3><div class="flex flex-wrap gap-2">${Object.entries(risk).map(([k,v])=>`<div class="px-3 py-2 rounded-xl bg-zinc-950 border border-zinc-800 text-xs"><span class="text-zinc-500">${k}:</span> <b>${v||'—'}</b></div>`).join('')}</div>`):''}
    <details class="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-4"><summary class="text-sm font-semibold cursor-pointer">Raw JSON</summary><pre class="mt-3 text-xs bg-zinc-950 border border-zinc-800 rounded-xl p-3 overflow-auto max-h-[400px]">${JSON.stringify(d,null,2)}</pre></details>`;
}

// ==================== DISCORD ====================
function renderDiscord(d){
  const p=d.profile;
  results.innerHTML=`
    ${card(`<div class="flex gap-4"><div class="w-20 h-20 rounded-2xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-3xl text-indigo-400"><i class="fa-brands fa-discord"></i></div><div class="flex-1"><h2 class="text-xl font-bold">${p.global_name||p.username||d.username}</h2><p class="text-zinc-400 text-sm">@${p.username||d.username}${p.discrimriminator&&p.discrimriminator!=='0'?`#${p.discriminator}`:''}</p><div class="mt-2 flex flex-wrap gap-2 text-xs">${p.url?`<a href="${p.url}" target="_blank" class="px-2 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 hover:bg-indigo-500/20">Discord →</a>`:''}${p.id?badge('ID: '+p.id):''}${p.created_at?badge('Created: '+new Date(p.created_at).toLocaleDateString()):''}</div></div></div>`)}
    ${p.id?card(`<h3 class="font-semibold text-sm mb-2">Avatar URL</h3><div class="text-xs font-mono bg-zinc-950 border border-zinc-800 rounded-xl p-3">https://cdn.discordapp.com/avatars/${p.id}/${p.avatar}.png</div>`):''}
    ${d.note?card(`<p class="text-xs text-zinc-400"><i class="fa-solid fa-circle-info mr-1"></i>${d.note}</p>`):''}
    <details class="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-4"><summary class="text-sm font-semibold cursor-pointer">Raw JSON</summary><pre class="mt-3 text-xs bg-zinc-950 border border-zinc-800 rounded-xl p-3 overflow-auto max-h-[400px]">${JSON.stringify(d,null,2)}</pre></details>`;
}

renderInput();
