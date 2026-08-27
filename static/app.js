let activeTab = 'user';
const inputArea = document.getElementById('inputArea');
const results = document.getElementById('results');
const statusEl = document.getElementById('status');
const docsLink = document.getElementById('docsLink');
docsLink.href = location.origin + '/docs';

const tabs = {
  user: { placeholder: 'torvalds', label: 'Username', btn: 'Lookup User', hint: 'GET /api/github/user/{username}' },
  emails: { placeholder: 'torvalds', label: 'Username', btn: 'Find Emails', hint: 'GET /api/github/emails/{username}' },
  repo: { placeholder: 'vercel/next.js', label: 'owner/repo', btn: 'Analyze Repo', hint: 'GET /api/github/repo/{owner}/{repo}' },
  search: { placeholder: 'osint language:python', label: 'Query', btn: 'Search', hint: 'GET /api/github/search/users or /repos' },
  network: { placeholder: 'torvalds', label: 'Username', btn: 'Map Network', hint: 'GET /api/github/network/{username}' },
  org: { placeholder: 'github', label: 'Org name', btn: 'Lookup Org', hint: 'GET /api/github/org/{org}' },
};

function renderInput() {
  const cfg = tabs[activeTab];
  if (activeTab === 'search') {
    inputArea.innerHTML = `
      <select id="searchType" class="px-3 py-2.5 rounded-xl bg-zinc-800 border border-zinc-700 text-sm">
        <option value="users">Users</option>
        <option value="repos">Repos</option>
      </select>
      <input id="mainInput" placeholder="${cfg.placeholder}" class="flex-1 px-4 py-2.5 rounded-xl bg-zinc-800 border border-zinc-700 outline-none text-sm placeholder:text-zinc-500" />
      <button id="searchBtn" class="px-5 py-2.5 rounded-xl bg-white text-black font-semibold text-sm">${cfg.btn}</button>
    `;
  } else {
    inputArea.innerHTML = `
      <input id="mainInput" placeholder="${cfg.placeholder}" class="flex-1 px-4 py-2.5 rounded-xl bg-zinc-800 border border-zinc-700 outline-none text-sm placeholder:text-zinc-500" />
      <button id="searchBtn" class="px-5 py-2.5 rounded-xl bg-white text-black font-semibold text-sm">${cfg.btn}</button>
    `;
  }
  document.getElementById('searchBtn').onclick = doSearch;
  document.getElementById('mainInput').addEventListener('keydown', e=>{ if(e.key==='Enter') doSearch(); });
}

document.querySelectorAll('.tab-btn').forEach(btn=>{
  btn.addEventListener('click', ()=>{
    document.querySelectorAll('.tab-btn').forEach(b=>{ b.className='tab-btn w-full text-left px-3 py-2.5 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-sm'; });
    btn.className='tab-btn w-full text-left px-3 py-2.5 rounded-xl bg-white text-black font-medium text-sm';
    activeTab = btn.dataset.tab;
    renderInput();
  });
});

document.querySelectorAll('.example').forEach(b=>{
  b.addEventListener('click', ()=>{
    if (b.dataset.example.includes('/')) activeTab='repo';
    document.querySelectorAll('.tab-btn').forEach(x=>{
      if (x.dataset.tab===activeTab) { x.click(); }
    });
    // after tab switch
    setTimeout(()=>{
      const inp = document.getElementById('mainInput');
      if(inp) inp.value = b.dataset.example;
    }, 50);
  });
});

function showStatus(msg, type='info'){
  statusEl.className = 'rounded-xl border px-4 py-3 text-sm ' + (type==='error'?'bg-red-500/10 border-red-500/30 text-red-300':'bg-zinc-900 border-zinc-800 text-zinc-300');
  statusEl.textContent = msg;
  statusEl.classList.remove('hidden');
}
function hideStatus(){ statusEl.classList.add('hidden'); }

async function doSearch(){
  const inp = document.getElementById('mainInput');
  const val = inp.value.trim();
  if(!val){ showStatus('Enter a value', 'error'); return; }
  hideStatus();
  results.innerHTML = `<div class="rounded-2xl border border-zinc-800 bg-zinc-900 p-8 text-center text-sm text-zinc-400"><i class="fa-solid fa-circle-notch fa-spin mr-2"></i>Querying GitHub API…</div>`;
  let url='';
  if(activeTab==='user') url=`/api/github/user/${encodeURIComponent(val)}`;
  if(activeTab==='emails') url=`/api/github/emails/${encodeURIComponent(val)}`;
  if(activeTab==='repo') {
    const parts = val.split('/');
    if(parts.length!==2){ showStatus('Use format owner/repo e.g. vercel/next.js','error'); results.innerHTML=''; return; }
    url=`/api/github/repo/${encodeURIComponent(parts[0])}/${encodeURIComponent(parts[1])}`;
  }
  if(activeTab==='search'){
    const t = document.getElementById('searchType').value;
    url = t==='users' ? `/api/github/search/users?q=${encodeURIComponent(val)}` : `/api/github/search/repos?q=${encodeURIComponent(val)}`;
  }
  if(activeTab==='network') url=`/api/github/network/${encodeURIComponent(val)}`;
  if(activeTab==='org') url=`/api/github/org/${encodeURIComponent(val)}`;

  try{
    const r = await fetch(url);
    const data = await r.json();
    if(!r.ok){ showStatus(data.detail || 'Error', 'error'); results.innerHTML = `<pre class="rounded-xl bg-zinc-900 border border-zinc-800 p-4 text-xs">${JSON.stringify(data,null,2)}</pre>`; return; }
    renderResult(data);
  }catch(e){
    showStatus(String(e),'error');
  }
}

function renderResult(data){
  if(activeTab==='user') renderUser(data);
  else if(activeTab==='emails') renderEmails(data);
  else if(activeTab==='repo') renderRepo(data);
  else if(activeTab==='search') renderSearch(data);
  else if(activeTab==='network') renderNetwork(data);
  else if(activeTab==='org') renderOrg(data);
}

function card(html){ return `<div class="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-4">${html}</div>`; }

function renderUser(d){
  const p = d.profile;
  const emails = d.emails_found;
  results.innerHTML = `
    ${card(`
      <div class="flex gap-4">
        <img src="${p.avatar_url}" class="w-20 h-20 rounded-2xl border border-zinc-800"/>
        <div class="flex-1 min-w-0">
          <h2 class="text-xl font-bold">${p.name || p.login} <span class="text-zinc-500 font-normal">@${p.login}</span></h2>
          <p class="text-sm text-zinc-400 mt-1">${p.bio || 'No bio'}</p>
          <div class="mt-2 flex flex-wrap gap-2 text-xs">
            ${p.location?`<span class="px-2 py-1 rounded-full bg-zinc-800 border border-zinc-700"><i class="fa-solid fa-location-dot mr-1"></i>${p.location}</span>`:''}
            ${p.blog?`<a href="${p.blog.startsWith('http')?p.blog:'https://'+p.blog}" target="_blank" class="px-2 py-1 rounded-full bg-zinc-800 border border-zinc-700 hover:bg-zinc-700"><i class="fa-solid fa-link mr-1"></i>${p.blog}</a>`:''}
            ${p.twitter_username?`<span class="px-2 py-1 rounded-full bg-zinc-800 border border-zinc-700">@${p.twitter_username}</span>`:''}
            ${p.company?`<span class="px-2 py-1 rounded-full bg-zinc-800 border border-zinc-700">${p.company}</span>`:''}
          </div>
          <div class="mt-3 flex gap-4 text-xs">
            <span><b>${p.followers}</b> followers</span><span><b>${p.following}</b> following</span><span><b>${p.public_repos}</b> repos</span>
            <span class="text-zinc-500">created ${new Date(p.created_at).toLocaleDateString()}</span>
          </div>
        </div>
        <a href="${p.html_url}" target="_blank" class="h-fit px-3 py-2 rounded-xl bg-white text-black text-xs font-semibold">View GitHub</a>
      </div>
    `)}
    <div class="grid md:grid-cols-2 gap-4">
      ${card(`<h3 class="font-semibold text-sm mb-2"><i class="fa-solid fa-envelope mr-2 text-zinc-500"></i>Emails found (${emails.length})</h3>${emails.length?emails.map(e=>`<div class="text-xs font-mono bg-zinc-950 border border-zinc-800 rounded-lg px-2 py-1.5 mt-1">${e}</div>`).join(''):`<p class="text-xs text-zinc-500">No public emails — user hides email or uses noreply.</p>`}<p class="text-[11px] text-zinc-500 mt-2">From commit patches across top 3 repos + public API. noreply = anonymized.</p>`)}
      ${card(`<h3 class="font-semibold text-sm mb-2"><i class="fa-solid fa-share-nodes mr-2 text-zinc-500"></i>Social footprint</h3><pre class="text-xs bg-zinc-950 border border-zinc-800 rounded-xl p-3">${JSON.stringify(d.social_footprint,null,2)}</pre>`)}
    </div>
    ${card(`<h3 class="font-semibold text-sm mb-3">Top Repositories (${d.repos_count})</h3><div class="grid md:grid-cols-2 gap-2">${d.repos.slice(0,8).map(r=>`
      <div class="rounded-xl border border-zinc-800 bg-zinc-950 p-3">
        <div class="text-sm font-semibold truncate"><a href="${r.html_url}" target="_blank" class="hover:underline">${r.full_name}</a> <span class="text-zinc-500 font-normal">★ ${r.stargazers_count}</span></div>
        <div class="text-xs text-zinc-400 line-clamp-2">${r.description||''}</div>
        <div class="text-[11px] text-zinc-500 mt-1">${r.language||''} • updated ${new Date(r.updated_at).toLocaleDateString()}</div>
      </div>`).join('')}</div>`)}
    <div class="grid md:grid-cols-2 gap-4">
      ${card(`<h3 class="font-semibold text-sm mb-2">Followers sample (${d.followers_sample.length})</h3><div class="flex flex-wrap gap-2">${d.followers_sample.map(f=>`<a href="${f.html_url}" target="_blank" class="flex items-center gap-2 px-2 py-1.5 rounded-full bg-zinc-800 border border-zinc-700 text-xs"><img src="${f.avatar_url}" class="w-5 h-5 rounded-full"/>${f.login}</a>`).join('')||'<span class="text-xs text-zinc-500">none</span>'}</div>`)}
      ${card(`<h3 class="font-semibold text-sm mb-2">Following sample (${d.following_sample.length})</h3><div class="flex flex-wrap gap-2">${d.following_sample.map(f=>`<a href="${f.html_url}" target="_blank" class="flex items-center gap-2 px-2 py-1.5 rounded-full bg-zinc-800 border border-zinc-700 text-xs"><img src="${f.avatar_url}" class="w-5 h-5 rounded-full"/>${f.login}</a>`).join('')||'<span class="text-xs text-zinc-500">none</span>'}</div>`)}
    </div>
    ${card(`<h3 class="font-semibold text-sm mb-2">Recent commit samples</h3><pre class="text-xs bg-zinc-950 border border-zinc-800 rounded-xl p-3">${JSON.stringify(d.commit_samples,null,2)}</pre>`)}
    <details class="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-4"><summary class="text-sm font-semibold cursor-pointer">Raw JSON</summary><pre class="mt-3 text-xs bg-zinc-950 border border-zinc-800 rounded-xl p-3 overflow-auto max-h-[500px]">${JSON.stringify(d,null,2)}</pre></details>
  `;
}

function renderEmails(d){
  results.innerHTML = `
    ${card(`<h2 class="font-bold">Email finder — @${d.username}</h2><p class="text-xs text-zinc-500">Aggregated from last 5 repos, 10 commits each</p>
      <div class="mt-3 grid md:grid-cols-2 gap-3">
        <div><div class="text-xs font-semibold text-emerald-400">Real emails (${d.real_emails.length})</div>${d.real_emails.length?d.real_emails.map(e=>`<div class="mt-1 font-mono text-xs bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-2 py-1.5">${e}</div>`).join(''):`<div class="text-xs text-zinc-500 mt-1">None found</div>`}</div>
        <div><div class="text-xs font-semibold text-zinc-400">Noreply (anonymized) (${d.noreply_emails.length})</div>${d.noreply_emails.map(e=>`<div class="mt-1 font-mono text-xs bg-zinc-800 border border-zinc-700 rounded-lg px-2 py-1.5">${e}</div>`).join('')||'<div class="text-xs text-zinc-500 mt-1">none</div>'}</div>
      </div>
      <p class="text-[11px] text-zinc-500 mt-2">${d.note}</p>
    `)}
    ${card(`<h3 class="font-semibold text-sm mb-2">Details (${d.details.length})</h3><div class="space-y-2 max-h-[400px] overflow-auto">${d.details.map(x=>`<div class="rounded-xl bg-zinc-950 border border-zinc-800 p-2.5 text-xs"><div class="font-mono">${x.email} <span class="text-zinc-500">— ${x.repo} • ${x.sha}</span></div><div class="text-zinc-400">${x.message}</div><div class="text-zinc-500">${x.date||''}</div></div>`).join('')||'<span class="text-xs text-zinc-500">no commits found for this author</span>'}</div>`)}
  `;
}

function renderRepo(d){
  const m = d.meta;
  results.innerHTML = `
    ${card(`<div class="flex gap-3"><div class="flex-1"><h2 class="font-bold text-lg"><a href="${m.html_url}" target="_blank" class="hover:underline">${m.full_name}</a></h2><p class="text-sm text-zinc-400">${m.description||''}</p><div class="mt-2 flex flex-wrap gap-2 text-xs"><span class="px-2 py-1 rounded-full bg-zinc-800 border border-zinc-700">★ ${m.stargazers_count}</span><span class="px-2 py-1 rounded-full bg-zinc-800 border border-zinc-700">⑂ ${m.forks_count}</span><span class="px-2 py-1 rounded-full bg-zinc-800 border border-zinc-700">${m.language||''}</span><span class="px-2 py-1 rounded-full bg-zinc-800 border border-zinc-700">${m.visibility}</span></div></div><a href="${m.html_url}" target="_blank" class="h-fit px-3 py-2 rounded-xl bg-white text-black text-xs font-semibold">Open Repo</a></div>`)}
    <div class="grid md:grid-cols-3 gap-4">
      ${card(`<h3 class="text-xs font-semibold uppercase tracking-widest text-zinc-500">Languages</h3><pre class="mt-2 text-xs bg-zinc-950 border border-zinc-800 rounded-xl p-3">${JSON.stringify(d.languages||{},null,2)}</pre>`)}
      ${card(`<h3 class="text-xs font-semibold uppercase tracking-widest text-zinc-500">Emails in commits</h3><div class="mt-2 space-y-1">${(d.emails_in_commits||[]).map(e=>`<div class="font-mono text-xs bg-zinc-950 border border-zinc-800 rounded-lg px-2 py-1">${e}</div>`).join('')||'<span class="text-xs text-zinc-500">none</span>'}</div>`)}
      ${card(`<h3 class="text-xs font-semibold uppercase tracking-widest text-zinc-500">Contributors</h3><div class="mt-2 space-y-1 max-h-[180px] overflow-auto">${(d.contributors||[]).slice(0,10).map(c=>`<a href="${c.html_url}" target="_blank" class="flex items-center gap-2 text-xs"><img src="${c.avatar_url}" class="w-6 h-6 rounded-full"/>${c.login} (${c.contributions})</a>`).join('')||'<span class="text-xs text-zinc-500">hidden</span>'}</div>`)}
    </div>
    ${card(`<h3 class="text-sm font-semibold mb-2">Root contents sample</h3><div class="grid md:grid-cols-2 gap-1 text-xs font-mono">${(Array.isArray(d.contents_sample)?d.contents_sample:[]).slice(0,20).map(f=>`<div class="px-2 py-1 rounded bg-zinc-950 border border-zinc-800 truncate">${f.type==='dir'?'📁':'📄'} ${f.name}</div>`).join('')||'<span class="text-zinc-500">none or private</span>'}</div>`)}
    <details class="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-4"><summary class="text-sm font-semibold cursor-pointer">Raw JSON</summary><pre class="mt-3 text-xs bg-zinc-950 border border-zinc-800 rounded-xl p-3 overflow-auto max-h-[500px]">${JSON.stringify(d,null,2)}</pre></details>
  `;
}

function renderSearch(d){
  const isUsers = !!d.items && d.items[0] && d.items[0].login !== undefined && d.items[0].full_name === undefined;
  if(isUsers){
    results.innerHTML = card(`<h3 class="font-semibold text-sm mb-3">Users (${d.total_count} total, showing ${d.items.length})</h3><div class="grid md:grid-cols-2 gap-2">${d.items.map(u=>`<a href="${u.html_url}" target="_blank" class="flex items-center gap-3 p-3 rounded-xl bg-zinc-950 border border-zinc-800 hover:bg-zinc-800"><img src="${u.avatar_url}" class="w-10 h-10 rounded-full"/><div><div class="text-sm font-semibold">${u.login}</div><div class="text-xs text-zinc-500">score ${u.score?.toFixed(2)}</div></div></a>`).join('')}</div>`);
  } else {
    results.innerHTML = card(`<h3 class="font-semibold text-sm mb-3">Repos (${d.total_count} total)</h3><div class="space-y-2">${d.items.map(r=>`<a href="${r.html_url}" target="_blank" class="block p-3 rounded-xl bg-zinc-950 border border-zinc-800 hover:bg-zinc-800"><div class="text-sm font-semibold">${r.full_name} <span class="text-zinc-500">★ ${r.stargazers_count}</span></div><div class="text-xs text-zinc-400">${r.description||''}</div><div class="text-[11px] text-zinc-500">${r.language||''} • ${r.html_url}</div></a>`).join('')}</div>`);
  }
}

function renderNetwork(d){
  results.innerHTML = `
    ${card(`<h2 class="font-bold">Network — @${d.profile.login}</h2><div class="mt-2 flex gap-3 text-xs"><span class="px-3 py-1 rounded-full bg-zinc-800 border border-zinc-700">${d.followers_count} followers (sample)</span><span class="px-3 py-1 rounded-full bg-zinc-800 border border-zinc-700">${d.following_count} following (sample)</span><span class="px-3 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/30 text-emerald-300">${d.mutuals_count} mutuals</span></div>${d.mutuals.length?`<div class="mt-3 flex flex-wrap gap-1">${d.mutuals.map(m=>`<span class="text-xs px-2 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">${m}</span>`).join('')}</div>`:''}`)}
    <div class="grid md:grid-cols-2 gap-4">
      ${card(`<h3 class="font-semibold text-sm mb-2">Followers</h3><div class="flex flex-wrap gap-1.5 max-h-[350px] overflow-auto">${d.followers.map(f=>`<a href="${f.html_url}" target="_blank" class="flex items-center gap-1.5 px-2 py-1 rounded-full bg-zinc-800 border border-zinc-700 text-xs"><img src="${f.avatar_url}" class="w-5 h-5 rounded-full"/>${f.login}</a>`).join('')}</div>`)}
      ${card(`<h3 class="font-semibold text-sm mb-2">Following</h3><div class="flex flex-wrap gap-1.5 max-h-[350px] overflow-auto">${d.following.map(f=>`<a href="${f.html_url}" target="_blank" class="flex items-center gap-1.5 px-2 py-1 rounded-full bg-zinc-800 border border-zinc-700 text-xs"><img src="${f.avatar_url}" class="w-5 h-5 rounded-full"/>${f.login}</a>`).join('')}</div>`)}
    </div>
  `;
}

function renderOrg(d){
  results.innerHTML = `
    ${card(`<div class="flex gap-4"><img src="${d.org.avatar_url}" class="w-16 h-16 rounded-2xl border border-zinc-800"/><div><h2 class="font-bold">${d.org.login} — ${d.org.name||''}</h2><p class="text-sm text-zinc-400">${d.org.description||''}</p><div class="text-xs text-zinc-500 mt-1">${d.org.location||''} • ${d.org.blog||''} • ${d.org.public_repos} repos</div><a href="https://github.com/${d.org.login}" target="_blank" class="inline-block mt-2 text-xs px-3 py-1.5 rounded-lg bg-white text-black font-semibold">View on GitHub</a></div></div>`)}
    ${card(`<h3 class="font-semibold text-sm mb-2">Repos (${d.repos.length})</h3><div class="grid md:grid-cols-2 gap-2">${d.repos.map(r=>`<a href="${r.html_url}" target="_blank" class="p-3 rounded-xl bg-zinc-950 border border-zinc-800"><div class="text-sm font-semibold">${r.name} ★ ${r.stargazers_count}</div><div class="text-xs text-zinc-400">${r.description||''}</div></a>`).join('')}</div>`)}
    ${card(`<h3 class="font-semibold text-sm mb-2">Members sample</h3>${Array.isArray(d.members)?`<div class="flex flex-wrap gap-2">${d.members.map(m=>`<a href="${m.html_url}" target="_blank" class="flex items-center gap-2 px-2 py-1.5 rounded-full bg-zinc-800 border border-zinc-700 text-xs"><img src="${m.avatar_url}" class="w-5 h-5 rounded-full"/>${m.login}</a>`).join('')}</div>`:`<pre class="text-xs bg-zinc-950 border border-zinc-800 rounded-xl p-3">${JSON.stringify(d.members,null,2)}</pre>`}`)}
  `;
}

renderInput();
