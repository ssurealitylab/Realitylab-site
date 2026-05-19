(function(){
'use strict';
const API = '/api';

// ═══════════════════════════════════════
// UTILITIES
// ═══════════════════════════════════════

function esc(s){ if(s==null)return''; const d=document.createElement('div'); d.textContent=String(s); return d.innerHTML; }

function adminToast(msg,type){
  const t=document.getElementById('admin-toast');
  t.textContent=msg; t.className='admin-toast '+(type||'info')+' show';
  setTimeout(()=>t.classList.remove('show'),4000);
}

function adminShowLoading(t){
  document.getElementById('admin-loading-text').textContent=t||'Processing...';
  document.getElementById('admin-loading').classList.add('show');
}
function adminHideLoading(){document.getElementById('admin-loading').classList.remove('show')}

window.adminClosePanel=function(){
  document.getElementById('admin-panel').classList.remove('open');
  document.getElementById('admin-panel-backdrop').classList.remove('open');
};

function openPanel(title,html){
  document.getElementById('admin-panel-title').textContent=title;
  document.getElementById('admin-panel-body').innerHTML=html;
  document.getElementById('admin-panel').classList.add('open');
  document.getElementById('admin-panel-backdrop').classList.add('open');
}

async function apiGet(p){const r=await fetch(API+p);if(!r.ok)throw new Error(r.status);return r.json();}
async function apiCall(p,method,data){
  const r=await fetch(API+p,{method,headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  return r.json();
}

// ═══════════════════════════════════════
// MARK EDITABLE ELEMENTS
// ═══════════════════════════════════════

function markEditables(){
  // ─── Member Cards (students, faculty, alumni) ───
  document.querySelectorAll('.member-card').forEach(card=>{
    if(card.hasAttribute('data-admin-editable')) return;
    card.setAttribute('data-admin-editable','member');
  });

  // Faculty cards have different class
  document.querySelectorAll('.faculty-card').forEach(card=>{
    if(card.hasAttribute('data-admin-editable')) return;
    card.setAttribute('data-admin-editable','faculty');
  });

  // ─── News Cards (news page) ───
  document.querySelectorAll('.news-card').forEach((card,i)=>{
    if(card.hasAttribute('data-admin-editable')) return;
    card.setAttribute('data-admin-editable','news');
    card.setAttribute('data-admin-index',i);
  });

  // ─── News Cards (homepage) ───
  document.querySelectorAll('.news-card-home').forEach((card,i)=>{
    if(card.hasAttribute('data-admin-editable')) return;
    card.setAttribute('data-admin-editable','news-home');
    card.setAttribute('data-admin-index',i);
  });

  // ─── Publication Items ───
  document.querySelectorAll('.publication-list-item').forEach(item=>{
    if(item.hasAttribute('data-admin-editable')) return;
    // Skip if inside domestic list (handled separately below)
    if(item.closest('#domestic-pub-list')) return;
    // International items have onclick="openPublicationModal('...')"
    const onclick=item.getAttribute('onclick')||'';
    const match=onclick.match(/openPublicationModal\('([^']+)'\)/);
    if(match){
      item.setAttribute('data-admin-editable','publication');
      item.setAttribute('data-admin-pub-id',match[1]);
    }
  });

  // ─── Publication Cards (homepage) ───
  document.querySelectorAll('.publication-card-home').forEach(item=>{
    if(item.hasAttribute('data-admin-editable')) return;
    item.setAttribute('data-admin-editable','publication');
    const onclick=item.getAttribute('onclick')||'';
    const match=onclick.match(/openPublicationModal\('([^']+)'\)/);
    if(match) item.setAttribute('data-admin-pub-id',match[1]);
  });

  // ─── AI Chat trigger (nav dropdown item) ───
  document.querySelectorAll('.ai-chat-trigger').forEach(el=>{
    if(el.hasAttribute('data-admin-editable')) return;
    el.setAttribute('data-admin-editable','chatbot-qa');
    // Change the text to indicate edit mode
    el.innerHTML = '<i class="fas fa-edit"></i> Edit AI Knowledge';
  });
  // Also the AI nav dropdown toggle itself
  document.querySelectorAll('.ai-menu-circular').forEach(el=>{
    if(el.hasAttribute('data-admin-editable')) return;
    el.setAttribute('data-admin-editable','chatbot-qa');
  });

  // ─── Slider (homepage) ───
  const sliderContainer = document.querySelector('.image-slider-container');
  if(sliderContainer && !sliderContainer.hasAttribute('data-admin-editable')){
    sliderContainer.setAttribute('data-admin-editable','slider');
  }

  // ─── Robot cards ───
  document.querySelectorAll('.robots-grid .member-card').forEach(card=>{
    if(card.getAttribute('data-admin-editable')==='robot') return;
    card.setAttribute('data-admin-editable','robot');
    const onclick = card.getAttribute('onclick')||'';
    const m = onclick.match(/openMemberModal\('(robot-[^']+)'\)/);
    if(m) card.setAttribute('data-admin-robot-id', m[1]);
  });

  // ─── Domestic publications ───
  document.querySelectorAll('#domestic-pub-list .publication-list-item').forEach(item=>{
    if(item.hasAttribute('data-admin-editable')) return;
    item.setAttribute('data-admin-editable','domestic-pub');
    item.setAttribute('data-admin-pub-id', item.getAttribute('data-pub-id')||'');
  });

  // ─── Course rows ───
  document.querySelectorAll('.course-table tbody tr').forEach((row,i)=>{
    if(row.hasAttribute('data-admin-editable')) return;
    const table = row.closest('.graduate-table') ? 'graduate' : 'undergraduate';
    // Recalculate index within this table
    const tbody = row.closest('tbody');
    const rowIdx = Array.from(tbody.children).indexOf(row);
    row.setAttribute('data-admin-editable','course');
    row.setAttribute('data-admin-course-type', table);
    row.setAttribute('data-admin-index', rowIdx);
  });

  // ─── Add Buttons ───
  insertAddButtons();
}

// ═══════════════════════════════════════
// ADD BUTTONS (inserted after section headers)
// ═══════════════════════════════════════

let addButtonsInserted = false;

function insertAddButtons(){
  if(addButtonsInserted) return;
  addButtonsInserted = true;

  // Students page - add buttons after each section
  const sections = [
    {heading:'phd-students', label:'+ Add PhD Student', path:'students.phd_students'},
    {heading:'masters-students', label:'+ Add MS Student', path:'students.ms_students'},
    {heading:'research-interns', label:'+ Add Intern', path:'students.interns'},
  ];
  sections.forEach(sec=>{
    const h = document.getElementById(sec.heading);
    if(!h) return;
    const btn = document.createElement('div');
    btn.className='admin-add-btn';
    btn.textContent=sec.label;
    btn.onclick=()=>addMemberForm(sec.path);
    const row = h.closest('.container')?.querySelector('.row.member-row') || h.parentElement;
    if(row) row.after(btn);
  });

  // Courses page - add buttons after each table
  document.querySelectorAll('.course-table').forEach(table=>{
    if(table.nextElementSibling?.classList.contains('admin-add-btn')) return;
    const isGrad = table.classList.contains('graduate-table');
    const type = isGrad ? 'graduate' : 'undergraduate';
    const btn = document.createElement('div');
    btn.className='admin-add-btn';
    btn.textContent=`+ Add ${isGrad?'Graduate':'Undergraduate'} Course`;
    btn.onclick=()=>{
      openPanel('Add Course', `
        <div class="admin-fg"><label>Course Name (Korean) *</label><input id="af-cname-ko" value=""></div>
        <div class="admin-fg"><label>Course Name (English) *</label><input id="af-cname-en" value=""></div>
        ${!isGrad?'<div class="admin-fg"><label>Year/Semester</label><input id="af-cyear" value="-"></div>':''}
        <div class="admin-fg"><label>Content</label>
          <textarea id="af-ccontent" style="min-height:120px" placeholder="• Topic 1\n• Topic 2\n• Topic 3"></textarea></div>
        <div class="admin-btn-row">
          <button class="admin-btn admin-btn-cancel" onclick="adminClosePanel()">Cancel</button>
          <button class="admin-btn admin-btn-primary" onclick="window._adminSaveCourse('${type}',-1)">Add</button>
        </div>
      `);
    };
    table.after(btn);
  });

  // News page
  const newsRow = document.querySelector('.news-row');
  if(newsRow){
    const btn = document.createElement('div');
    btn.className='admin-add-btn';
    btn.textContent='+ Add News';
    btn.onclick=()=>addNewsForm();
    newsRow.before(btn);
  }

  // Robots section (students page)
  const robotsHeading = document.getElementById('research-robots');
  if(robotsHeading){
    const btn = document.createElement('div');
    btn.className='admin-add-btn';
    btn.textContent='+ Add Robot';
    btn.onclick=()=>addRobotForm();
    const grid = robotsHeading.parentElement?.querySelector('.robots-grid')
              || robotsHeading.nextElementSibling;
    if(grid) grid.after(btn);
  }

  // International publications page - button at TOP
  const intlList = document.querySelector('.publications-content');
  if(intlList && window.location.pathname.includes('international')){
    const container = intlList.querySelector('.container');
    if(container && !container.querySelector('.admin-add-btn')){
      const btn = document.createElement('div');
      btn.className='admin-add-btn';
      btn.textContent='+ Add International Publication';
      btn.onclick=()=>addIntlPubForm();
      container.prepend(btn);
    }
  }

  // Domestic publications page - button at TOP
  const domList = document.getElementById('domestic-pub-list');
  if(domList){
    const section = domList.closest('.category-section') || domList.parentElement;
    if(section && !section.querySelector('.admin-add-btn')){
      const btn = document.createElement('div');
      btn.className='admin-add-btn';
      btn.textContent='+ Add Domestic Publication';
      btn.onclick=()=>addDomesticPubForm();
      section.prepend(btn);
    }
  }
}

// ═══════════════════════════════════════
// CLICK HANDLER (captures all clicks on editable elements)
// ═══════════════════════════════════════

document.addEventListener('click', async function(e){
  const editable = e.target.closest('[data-admin-editable]');
  if(!editable) return;

  const type = editable.getAttribute('data-admin-editable');

  // Prevent original onclick (e.g., openMemberModal)
  e.preventDefault();
  e.stopPropagation();
  e.stopImmediatePropagation();

  if(type==='member') await editMember(editable);
  else if(type==='faculty') await editFaculty(editable);
  else if(type==='news'||type==='news-home') await editNews(editable);
  else if(type==='publication') await editPublication(editable);
  else if(type==='slider') await editSlider();
  else if(type==='course') await editCourse(editable);
  else if(type==='chatbot-qa') await editChatbotQA();
  else if(type==='robot') await editRobot(editable);
  else if(type==='domestic-pub') await editDomesticPub(editable);
}, true);

// ═══════════════════════════════════════
// MEMBER EDITING
// ═══════════════════════════════════════

async function editMember(el){
  const data = await apiGet('/data/members');
  const nameEl = el.querySelector('.member-name');
  const cardName = nameEl ? nameEl.textContent.trim() : '';

  // Search through all sections
  let found=null, foundPath='', foundIdx=-1;
  const searchSections = [
    {path:'students.phd_students', list:(data.students||{}).phd_students||[]},
    {path:'students.ms_students', list:(data.students||{}).ms_students||[]},
    {path:'students.interns', list:(data.students||{}).interns||[]},
    {path:'alumni.former_ms_students', list:(data.alumni||{}).former_ms_students||[]},
    {path:'alumni.former_interns', list:(data.alumni||{}).former_interns||[]},
  ];

  for(const sec of searchSections){
    const idx = sec.list.findIndex(m=> m.name===cardName || m.name_ko===cardName);
    if(idx>=0){ found=sec.list[idx]; foundPath=sec.path; foundIdx=idx; break; }
  }

  if(!found){ adminToast('Member not found: '+cardName,'error'); return; }
  showMemberForm(found, foundPath, foundIdx);
}

async function editFaculty(el){
  const data = await apiGet('/data/members');
  const nameEl = el.querySelector('.member-name');
  const nameKoEl = el.querySelector('.member-name-ko');
  const rawName = nameEl ? nameEl.textContent.trim() : '';
  const strippedName = rawName.replace(/^Prof\.\s*/, '').trim();
  const koName = nameKoEl ? nameKoEl.textContent.trim().replace(/\s*교수$/,'').trim() : '';
  const faculty = data.faculty || [];
  // Try multiple matching strategies
  const idx = faculty.findIndex(m=> {
    const fName = (m.name||'').trim();
    const fKo = (m.name_ko||'').trim();
    const fNameStripped = fName.replace(/^Prof\.\s*/, '').trim();
    const fKoStripped = fKo.replace(/\s*교수$/,'').trim();
    return fName === rawName || fName === strippedName ||
           fNameStripped === strippedName || fNameStripped === rawName ||
           fKo === koName || fKoStripped === koName;
  });

  if(idx<0){ adminToast('Faculty not found: '+rawName+' / '+koName,'error'); return; }
  const f = faculty[idx];

  openPanel('Edit Faculty: '+(f.name_ko||f.name), `
    <div class="admin-fg"><label>Name (English)</label><input id="af-name" value="${esc(f.name||'')}"></div>
    <div class="admin-fg"><label>Name (Korean)</label><input id="af-name_ko" value="${esc(f.name_ko||'')}"></div>
    <div class="admin-fg"><label>Position</label><input id="af-position" value="${esc(f.position||'')}"></div>
    <div class="admin-fg"><label>Affiliation</label><input id="af-affiliation" value="${esc(f.affiliation||'')}"></div>
    <div class="admin-fg"><label>Email</label><input id="af-email" value="${esc(f.email||'')}"></div>
    <div class="admin-fg"><label>Phone</label><input id="af-phone" value="${esc(f.phone||'')}"></div>
    <div class="admin-fg"><label>Photo</label>
      <input id="af-photo" value="${esc(f.photo||'')}" readonly style="cursor:pointer" onclick="window._adminImagePicker('members','af-photo')">
      ${f.photo?`<img src="/${esc(f.photo)}" class="photo-preview">`:''}
      <div class="hint">Click to browse/upload</div></div>
    <div class="admin-fg"><label>Bio URL</label><input id="af-bio" value="${esc(f.bio||'')}"></div>
    <div class="admin-fg"><label>Google Scholar URL</label><input id="af-scholar" value="${esc(f.scholar||'')}"></div>
    <div class="admin-btn-row">
      <button class="admin-btn admin-btn-cancel" onclick="adminClosePanel()">Cancel</button>
      <button class="admin-btn admin-btn-primary" onclick="window._adminSaveFaculty(${idx})">Save</button>
    </div>
  `);
}

function showMemberForm(member, path, idx){
  const isAlumni = path.includes('alumni');
  const photoPreview = member.photo ? `<img src="/${esc(member.photo)}" class="photo-preview">` : '';

  let extraFields = '';
  if(isAlumni){
    extraFields = `
      <div class="admin-fg"><label>Period</label><input id="af-period" value="${esc(member.period||'')}"></div>
      <div class="admin-fg"><label>Current Position</label><input id="af-current_position" value="${esc(member.current_position||'')}"></div>
    `;
  }

  openPanel((idx>=0?'Edit':'Add')+': '+(member.name_ko||member.name||'New Member'), `
    <div class="admin-fg"><label>Name (English) *</label><input id="af-name" value="${esc(member.name||'')}"></div>
    <div class="admin-fg"><label>Name (Korean) *</label><input id="af-name_ko" value="${esc(member.name_ko||'')}"></div>
    <div class="admin-fg"><label>Email</label><input id="af-email" value="${esc(member.email||'')}"></div>
    <div class="admin-fg"><label>University / Affiliation</label><input id="af-university" value="${esc(member.university||'')}"></div>
    <div class="admin-fg"><label>Research *</label><input id="af-research" value="${esc(member.research||'')}"></div>
    <div class="admin-fg"><label>Photo</label>
      <input id="af-photo" value="${esc(member.photo||'')}" readonly style="cursor:pointer" onclick="window._adminImagePicker('members','af-photo')">
      ${photoPreview}
      <div class="hint">Click to browse/upload</div></div>
    <div class="admin-fg"><label>GitHub</label><input id="af-github" value="${esc(member.github||'')}"></div>
    <div class="admin-fg"><label>LinkedIn</label><input id="af-linkedin" value="${esc(member.linkedin||'')}"></div>
    ${extraFields}
    <div class="admin-btn-row">
      <button class="admin-btn admin-btn-cancel" onclick="adminClosePanel()">Cancel</button>
      <button class="admin-btn admin-btn-primary" onclick="window._adminSaveMember('${path}',${idx})">${idx>=0?'Save':'Add'}</button>
    </div>
    ${idx>=0?`<button class="admin-btn-danger" onclick="window._adminDeleteMember('${path}',${idx},'${esc(member.name_ko||member.name)}')">Delete this member</button>`:''}
  `);
}

function addMemberForm(path){
  showMemberForm({}, path, -1);
}

window._adminSaveMember = async function(path,idx){
  const d = {
    name:document.getElementById('af-name').value.trim(),
    name_ko:document.getElementById('af-name_ko').value.trim(),
    email:document.getElementById('af-email').value.trim(),
    university:document.getElementById('af-university').value.trim(),
    research:document.getElementById('af-research').value.trim(),
    photo:document.getElementById('af-photo').value.trim(),
    github:document.getElementById('af-github').value.trim(),
    linkedin:document.getElementById('af-linkedin').value.trim(),
  };
  // Alumni extra fields
  const periodEl = document.getElementById('af-period');
  if(periodEl) d.period = periodEl.value.trim();
  const posEl = document.getElementById('af-current_position');
  if(posEl) d.current_position = posEl.value.trim();

  if(!d.name||!d.name_ko){ adminToast('Name is required','error'); return; }

  adminShowLoading('Saving & deploying...');
  try{
    const endpoint = idx>=0 ? `/deploy/members/${path}.${idx}` : `/deploy/members/${path}`;
    const method = idx>=0 ? 'PUT' : 'POST';
    const res = await apiCall(endpoint, method, d);
    adminHideLoading();
    if(res.status==='success'){ adminToast('Saved! Click "Apply" to publish.','success'); checkUnpushed(); adminClosePanel(); setTimeout(()=>location.reload(),1500); }
    else{ adminToast(res.message||JSON.stringify(res.errors),'error'); }
  }catch(e){ adminHideLoading(); adminToast(e.message,'error'); }
};

window._adminSaveFaculty = async function(idx){
  const d = {
    name:document.getElementById('af-name').value.trim(),
    name_ko:document.getElementById('af-name_ko').value.trim(),
    position:document.getElementById('af-position').value.trim(),
    affiliation:document.getElementById('af-affiliation').value.trim(),
    email:document.getElementById('af-email').value.trim(),
    phone:document.getElementById('af-phone').value.trim(),
    photo:document.getElementById('af-photo').value.trim(),
    bio:document.getElementById('af-bio').value.trim(),
    scholar:document.getElementById('af-scholar').value.trim(),
  };
  adminShowLoading('Deploying...');
  try{
    const res = await apiCall(`/deploy/members/faculty.${idx}`,'PUT',d);
    adminHideLoading();
    if(res.status==='success'){ adminToast('Saved! Click "Apply" to publish.','success'); checkUnpushed(); adminClosePanel(); setTimeout(()=>location.reload(),1500); }
    else adminToast(res.message||JSON.stringify(res.errors),'error');
  }catch(e){ adminHideLoading(); adminToast(e.message,'error'); }
};

window._adminDeleteMember = async function(path,idx,name){
  if(!confirm('Delete '+name+'? This will deploy to the live site.')) return;
  adminShowLoading('Deleting & deploying...');
  try{
    const res = await apiCall(`/deploy/members/${path}.${idx}`,'DELETE');
    adminHideLoading();
    if(res.status==='success'){ adminToast('Deleted! Click "Apply" to publish.','success'); checkUnpushed(); setTimeout(()=>location.reload(),1500); }
    else adminToast(res.message,'error');
  }catch(e){ adminHideLoading(); adminToast(e.message,'error'); }
};

// ═══════════════════════════════════════
// NEWS EDITING
// ═══════════════════════════════════════

async function editNews(el){
  const data = await apiGet('/data/news');
  const newsList = data.news || [];

  // Match by title text
  const titleEl = el.querySelector('.card-title') || el.querySelector('.card-title-home');
  const cardTitle = titleEl ? titleEl.textContent.trim() : '';
  let idx = newsList.findIndex(n => n.title === cardTitle);

  // Fallback: use data-admin-index (position on page)
  if(idx<0){
    const pageIdx = parseInt(el.getAttribute('data-admin-index'));
    if(!isNaN(pageIdx) && pageIdx < newsList.length) idx = pageIdx;
  }

  if(idx<0){ adminToast('News not found: '+cardTitle,'error'); return; }
  showNewsForm(newsList[idx], idx);
}

function showNewsForm(news, idx){
  const cats = ['Publication','Awards','Internship','Grants','Event','General'];
  const isNew = idx < 0;

  openPanel(isNew ? 'Add News' : 'Edit News', `
    <div class="admin-fg"><label>Title *</label><input id="af-title" value="${esc(news.title||'')}"></div>
    <div class="admin-fg"><label>Date *</label><input id="af-date" type="date" value="${esc(news.date||new Date().toISOString().split('T')[0])}"></div>
    <div class="admin-fg"><label>Category</label>
      <select id="af-category">${cats.map(c=>`<option${c===news.category?' selected':''}>${c}</option>`).join('')}</select></div>
    <div class="admin-fg"><label>Participants (comma separated)</label>
      <input id="af-participants" value="${esc((news.participants||[]).join(', '))}"></div>
    <div class="admin-fg"><label>Description *</label>
      <textarea id="af-description">${esc(news.description||'')}</textarea></div>
    <div class="admin-fg"><label>Image</label>
      <input id="af-image" value="${esc(news.image||'')}" readonly style="cursor:pointer" onclick="window._adminImagePicker('news','af-image')">
      ${news.image?`<img src="/img/news/${esc(news.image)}" class="photo-preview" style="border-radius:4px;width:80px;height:auto">`:''}
      <div class="hint">Click to browse/upload (filename only)</div></div>
    <div class="admin-btn-row">
      <button class="admin-btn admin-btn-cancel" onclick="adminClosePanel()">Cancel</button>
      <button class="admin-btn admin-btn-primary" onclick="window._adminSaveNews(${idx})">${isNew?'Add':'Save'}</button>
    </div>
    ${!isNew?`<button class="admin-btn-danger" onclick="window._adminDeleteNews(${idx})">Delete this news</button>`:''}
  `);
}

function addNewsForm(){ showNewsForm({}, -1); }

window._adminSaveNews = async function(idx){
  const d = {
    title:document.getElementById('af-title').value.trim(),
    date:document.getElementById('af-date').value.trim(),
    category:document.getElementById('af-category').value,
    participants:document.getElementById('af-participants').value.split(',').map(s=>s.trim()).filter(s=>s),
    description:document.getElementById('af-description').value.trim(),
    image:document.getElementById('af-image').value.trim(),
  };
  if(!d.title||!d.date){ adminToast('Title and date are required','error'); return; }
  adminShowLoading('Deploying...');
  try{
    const endpoint = idx>=0 ? `/deploy/news/news.${idx}` : `/deploy/news/news`;
    const method = idx>=0 ? 'PUT' : 'POST';
    const res = await apiCall(endpoint, method, d);
    adminHideLoading();
    if(res.status==='success'){ adminToast('Saved! Click "Apply" to publish.','success'); checkUnpushed(); adminClosePanel(); setTimeout(()=>location.reload(),1500); }
    else adminToast(res.message||JSON.stringify(res.errors),'error');
  }catch(e){ adminHideLoading(); adminToast(e.message,'error'); }
};

window._adminDeleteNews = async function(idx){
  if(!confirm('Delete this news entry?')) return;
  adminShowLoading('Deleting...');
  try{
    const res = await apiCall(`/deploy/news/news.${idx}`,'DELETE');
    adminHideLoading();
    if(res.status==='success'){ adminToast('Deleted! Click "Apply" to publish.','success'); checkUnpushed(); setTimeout(()=>location.reload(),1500); }
    else adminToast(res.message,'error');
  }catch(e){ adminHideLoading(); adminToast(e.message,'error'); }
};

// ═══════════════════════════════════════
// PUBLICATION EDITING
// ═══════════════════════════════════════

async function editPublication(el){
  const pubId = el.getAttribute('data-admin-pub-id');
  if(!pubId){ adminToast('Publication ID not found','error'); return; }

  const data = await apiGet('/data/publications');
  const pubs = data.publications || [];
  const idx = pubs.findIndex(p => p.id === pubId);
  if(idx<0){ adminToast('Publication not found: '+pubId,'error'); return; }

  const pub = pubs[idx];
  const types = ['conference','journal','workshop'];
  const statuses = ['accepted','published','award'];
  const links = pub.links || {};

  openPanel('Edit: '+(pub.venue_short||'')+' - '+pub.title?.substring(0,30)+'...', `
    <div class="admin-fg"><label>ID</label><input id="af-id" value="${esc(pub.id||'')}" readonly style="background:#334155"></div>
    <div class="admin-fg"><label>Title *</label><textarea id="af-title" style="min-height:60px">${esc(pub.title||'')}</textarea></div>
    <div class="admin-fg"><label>Authors *</label><input id="af-authors" value="${esc(pub.authors||'')}"></div>
    <div class="admin-fg"><label>Venue *</label><input id="af-venue" value="${esc(pub.venue||'')}"></div>
    <div class="admin-fg"><label>Venue Short</label><input id="af-venue_short" value="${esc(pub.venue_short||'')}"></div>
    <div class="admin-fg"><label>Year</label><input id="af-year" type="number" value="${pub.year||2026}"></div>
    <div class="admin-fg"><label>Type</label>
      <select id="af-type">${types.map(t=>`<option${t===pub.type?' selected':''}>${t}</option>`).join('')}</select></div>
    <div class="admin-fg"><label>Status</label>
      <select id="af-status">${statuses.map(s=>`<option${s===pub.status?' selected':''}>${s}</option>`).join('')}</select></div>
    <div class="admin-fg"><label>PDF Link</label><input id="af-link-pdf" value="${esc(links.pdf||'')}"></div>
    <div class="admin-fg"><label>Website Link</label><input id="af-link-website" value="${esc(links.website||'')}"></div>
    <div class="admin-fg"><label>GitHub Link</label><input id="af-link-github" value="${esc(links.github||'')}"></div>
    <div class="admin-fg"><label>Architecture Image</label>
      <input id="af-pub-image" value="${esc(pub.image||'')}" readonly style="cursor:pointer" onclick="window._adminImagePicker('publications','af-pub-image')">
      ${pub.image?`<img src="/${esc(pub.image)}" style="width:100%;max-height:150px;object-fit:contain;border-radius:8px;margin-top:8px;background:#0f172a" onerror="this.style.display='none'">`:''}
      <div class="hint">Click to upload architecture/framework figure</div></div>
    <div class="admin-fg"><label>Abstract</label><textarea id="af-abstract" style="min-height:120px">${esc(pub.abstract||'')}</textarea></div>
    <div class="admin-btn-row">
      <button class="admin-btn admin-btn-cancel" onclick="adminClosePanel()">Cancel</button>
      <button class="admin-btn admin-btn-primary" onclick="window._adminSavePub(${idx})">Save</button>
    </div>
  `);
}

window._adminSavePub = async function(idx){
  const d = {
    id:document.getElementById('af-id').value.trim(),
    title:document.getElementById('af-title').value.trim(),
    authors:document.getElementById('af-authors').value.trim(),
    venue:document.getElementById('af-venue').value.trim(),
    venue_short:document.getElementById('af-venue_short').value.trim(),
    year:parseInt(document.getElementById('af-year').value)||2026,
    type:document.getElementById('af-type').value,
    status:document.getElementById('af-status').value,
    image:document.getElementById('af-pub-image').value.trim()||undefined,
    abstract:document.getElementById('af-abstract').value.trim(),
    links:{
      pdf:document.getElementById('af-link-pdf').value.trim()||undefined,
      website:document.getElementById('af-link-website').value.trim()||undefined,
      github:document.getElementById('af-link-github').value.trim()||undefined,
    }
  };
  // Remove empty links
  Object.keys(d.links).forEach(k=>{if(!d.links[k])delete d.links[k]});
  if(!Object.keys(d.links).length) delete d.links;

  adminShowLoading('Deploying...');
  try{
    const res = await apiCall(`/deploy/publications/publications.${idx}`,'PUT',d);
    adminHideLoading();
    if(res.status==='success'){ adminToast('Saved! Click "Apply" to publish.','success'); checkUnpushed(); adminClosePanel(); setTimeout(()=>location.reload(),1500); }
    else adminToast(res.message||JSON.stringify(res.errors),'error');
  }catch(e){ adminHideLoading(); adminToast(e.message,'error'); }
};

// ═══════════════════════════════════════
// CHATBOT Q&A EDITING
// ═══════════════════════════════════════

window.editChatbotQA = async function(){
  const data = await apiGet('/data/chatbot_knowledge');
  const qaKo = data.custom_qa?.ko || [];
  const qaEn = data.custom_qa?.en || [];

  const pending = (data.pending_qa?.ko) || [];

  let html = '<div style="margin-bottom:16px;color:#94a3b8;font-size:13px">AI chatbot knowledge base. Korean only — chatbot auto-translates for English users.</div>';

  // ─── Active Q&A ───
  html += `<div style="font-size:14px;font-weight:700;color:#60a5fa;margin:16px 0 8px">✓ 작성된 Q&A (${qaKo.length})</div>`;
  qaKo.forEach((qa,i)=>{
    html += `<div style="padding:10px;margin-bottom:6px;background:#0f172a;border-radius:8px;border:1px solid #334155;cursor:pointer"
      onclick="window._adminEditQA('ko',${i})">
      <div style="font-size:13px;font-weight:600;color:#e2e8f0;margin-bottom:4px">Q: ${esc(qa.question)}</div>
      <div style="font-size:12px;color:#94a3b8;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">A: ${esc(qa.answer)}</div>
    </div>`;
  });
  html += `<button class="admin-btn admin-btn-cancel" onclick="window._adminAddQA('ko')" style="width:100%;margin-top:8px;border:2px dashed #334155;background:none;color:#94a3b8">+ Add Q&A</button>`;

  // ─── Pending Q&A (questions waiting for answers) ───
  if(pending.length){
    html += `<div style="font-size:14px;font-weight:700;color:#fbbf24;margin:24px 0 8px">📝 미작성 답변 (${pending.length})</div>`;
    html += `<div style="font-size:12px;color:#94a3b8;margin-bottom:8px">클릭하면 답변을 작성하여 활성화할 수 있습니다.</div>`;
    pending.forEach((q,i)=>{
      html += `<div style="padding:10px;margin-bottom:6px;background:rgba(251,191,36,.05);border-radius:8px;border:1px dashed #92400e;cursor:pointer"
        onclick="window._adminAnswerPending(${i})">
        <div style="font-size:13px;font-weight:600;color:#fbbf24;margin-bottom:4px">Q: ${esc(q.question)}</div>
        <div style="font-size:11px;color:#94a3b8">→ 클릭하여 답변 작성</div>
      </div>`;
    });
  }

  openPanel('AI Chatbot Knowledge', html);
}

window._adminAnswerPending = async function(idx){
  const data = await apiGet('/data/chatbot_knowledge');
  const pending = data.pending_qa?.ko || [];
  if(idx<0 || idx>=pending.length){ adminToast('Question not found','error'); return; }
  const q = pending[idx];

  openPanel('답변 작성', `
    <div class="admin-fg"><label>Question (질문)</label>
      <textarea id="af-qa-question" style="min-height:60px">${esc(q.question||'')}</textarea></div>
    <div class="admin-fg"><label>Answer (답변) *</label>
      <textarea id="af-qa-answer" style="min-height:140px" placeholder="답변을 입력하세요"></textarea></div>
    <div class="admin-fg"><label>Keywords (쉼표로 구분)</label>
      <input id="af-qa-keywords" placeholder="키워드1, 키워드2"></div>
    <div class="admin-btn-row">
      <button class="admin-btn admin-btn-cancel" onclick="editChatbotQA()">Back</button>
      <button class="admin-btn admin-btn-primary" onclick="window._adminSavePendingAnswer(${idx})">활성화 (답변 저장)</button>
    </div>
    <button class="admin-btn-danger" onclick="window._adminDeletePending(${idx})">이 질문 삭제</button>
  `);
};

window._adminSavePendingAnswer = async function(idx){
  const newQA = {
    question: document.getElementById('af-qa-question').value.trim(),
    answer: document.getElementById('af-qa-answer').value.trim(),
    keywords: document.getElementById('af-qa-keywords').value.split(',').map(s=>s.trim()).filter(s=>s),
  };
  if(!newQA.question || !newQA.answer){ adminToast('질문과 답변 모두 필수입니다','error'); return; }

  adminShowLoading('Activating Q&A...');
  try{
    // Step 1: Add to active Q&A
    const r1 = await apiCall('/deploy/chatbot_knowledge/custom_qa.ko', 'POST', newQA);
    if(r1.status !== 'success'){ adminHideLoading(); adminToast(r1.message||'Add failed','error'); return; }

    // Step 2: Remove from pending
    const r2 = await apiCall(`/deploy/chatbot_knowledge/pending_qa.ko.${idx}`, 'DELETE');
    adminHideLoading();
    if(r2.status === 'success'){
      adminToast('답변 활성화 완료! Apply로 배포하세요.','success');
      checkUnpushed();
      editChatbotQA();
    } else adminToast(r2.message,'error');
  }catch(e){ adminHideLoading(); adminToast(e.message,'error'); }
};

window._adminDeletePending = async function(idx){
  if(!confirm('이 미작성 질문을 삭제하시겠습니까?')) return;
  adminShowLoading('Deleting...');
  try{
    const res = await apiCall(`/deploy/chatbot_knowledge/pending_qa.ko.${idx}`, 'DELETE');
    adminHideLoading();
    if(res.status === 'success'){
      adminToast('Deleted!','success');
      checkUnpushed();
      editChatbotQA();
    } else adminToast(res.message,'error');
  }catch(e){ adminHideLoading(); adminToast(e.message,'error'); }
};

window._adminEditQA = async function(lang, idx){
  const data = await apiGet('/data/chatbot_knowledge');
  const qa = data.custom_qa[lang][idx];

  openPanel('Q&A Edit', `
    <div class="admin-fg"><label>Question *</label>
      <textarea id="af-qa-question" style="min-height:60px">${esc(qa.question||'')}</textarea></div>
    <div class="admin-fg"><label>Answer *</label>
      <textarea id="af-qa-answer" style="min-height:120px">${esc(qa.answer||'')}</textarea></div>
    <div class="admin-fg"><label>Keywords (comma separated)</label>
      <input id="af-qa-keywords" value="${esc((qa.keywords||[]).join(', '))}"></div>
    <div class="admin-btn-row">
      <button class="admin-btn admin-btn-cancel" onclick="editChatbotQA()">Back</button>
      <button class="admin-btn admin-btn-primary" onclick="window._adminSaveQA('${lang}',${idx})">Save</button>
    </div>
    <button class="admin-btn-danger" onclick="window._adminDeleteQA('${lang}',${idx})">Delete this Q&A</button>
  `);
};

window._adminAddQA = function(lang){
  openPanel('Add Q&A', `
    <div class="admin-fg"><label>Question *</label>
      <textarea id="af-qa-question" style="min-height:60px" placeholder="질문을 입력하세요"></textarea></div>
    <div class="admin-fg"><label>Answer *</label>
      <textarea id="af-qa-answer" style="min-height:120px" placeholder="답변을 입력하세요"></textarea></div>
    <div class="admin-fg"><label>Keywords (comma separated)</label>
      <input id="af-qa-keywords" placeholder="키워드1, 키워드2"></div>
    <div class="admin-btn-row">
      <button class="admin-btn admin-btn-cancel" onclick="editChatbotQA()">Back</button>
      <button class="admin-btn admin-btn-primary" onclick="window._adminSaveQA('${lang}',-1)">Add</button>
    </div>
  `);
};

window._adminSaveQA = async function(lang, idx){
  const d = {
    question: document.getElementById('af-qa-question').value.trim(),
    answer: document.getElementById('af-qa-answer').value.trim(),
    keywords: document.getElementById('af-qa-keywords').value.split(',').map(s=>s.trim()).filter(s=>s),
  };
  if(!d.question||!d.answer){ adminToast('Question and answer are required','error'); return; }

  adminShowLoading('Saving...');
  try{
    const endpoint = idx>=0 ? `/deploy/chatbot_knowledge/custom_qa.${lang}.${idx}` : `/deploy/chatbot_knowledge/custom_qa.${lang}`;
    const method = idx>=0 ? 'PUT' : 'POST';
    const res = await apiCall(endpoint, method, d);
    adminHideLoading();
    if(res.status==='success'){
      adminToast('Saved! Click "Apply" to publish.','success');
      checkUnpushed();
      editChatbotQA(); // Back to list
    } else adminToast(res.message||JSON.stringify(res.errors),'error');
  }catch(e){ adminHideLoading(); adminToast(e.message,'error'); }
};

window._adminDeleteQA = async function(lang, idx){
  if(!confirm('Delete this Q&A?')) return;
  adminShowLoading('Deleting...');
  try{
    const res = await apiCall(`/deploy/chatbot_knowledge/custom_qa.${lang}.${idx}`,'DELETE');
    adminHideLoading();
    if(res.status==='success'){
      adminToast('Deleted! Click "Apply" to publish.','success');
      checkUnpushed();
      editChatbotQA();
    } else adminToast(res.message,'error');
  }catch(e){ adminHideLoading(); adminToast(e.message,'error'); }
};

// ═══════════════════════════════════════
// COURSE EDITING
// ═══════════════════════════════════════

async function editCourse(el){
  const courseType = el.getAttribute('data-admin-course-type');
  const idx = parseInt(el.getAttribute('data-admin-index'));
  const data = await apiGet('/data/courses');
  const list = data[courseType] || [];
  if(idx<0||idx>=list.length){ adminToast('Course not found','error'); return; }
  const course = list[idx];
  const isGrad = courseType === 'graduate';

  openPanel('Edit Course: '+course.name_ko, `
    <div class="admin-fg"><label>Course Name (Korean) *</label><input id="af-cname-ko" value="${esc(course.name_ko||'')}"></div>
    <div class="admin-fg"><label>Course Name (English) *</label><input id="af-cname-en" value="${esc(course.name_en||'')}"></div>
    ${!isGrad?`<div class="admin-fg"><label>Year/Semester</label><input id="af-cyear" value="${esc(course.year||'-')}"></div>`:''}
    <div class="admin-fg"><label>Content (use • for bullets, one per line)</label>
      <textarea id="af-ccontent" style="min-height:120px">${esc((course.content||'').replace(/\\n/g,'\n'))}</textarea></div>
    <div class="admin-btn-row">
      <button class="admin-btn admin-btn-cancel" onclick="adminClosePanel()">Cancel</button>
      <button class="admin-btn admin-btn-primary" onclick="window._adminSaveCourse('${courseType}',${idx})">Save</button>
    </div>
    <button class="admin-btn-danger" onclick="window._adminDeleteCourse('${courseType}',${idx})">Delete this course</button>
  `);
}

window._adminSaveCourse = async function(courseType, idx){
  const d = {
    name_ko: document.getElementById('af-cname-ko').value.trim(),
    name_en: document.getElementById('af-cname-en').value.trim(),
    content: document.getElementById('af-ccontent').value.trim(),
  };
  const yearEl = document.getElementById('af-cyear');
  if(yearEl) d.year = yearEl.value.trim() || '-';
  if(!d.name_ko||!d.name_en){ adminToast('Course name is required','error'); return; }

  adminShowLoading('Saving...');
  try{
    const endpoint = idx>=0 ? `/deploy/courses/${courseType}.${idx}` : `/deploy/courses/${courseType}`;
    const method = idx>=0 ? 'PUT' : 'POST';
    const res = await apiCall(endpoint, method, d);
    adminHideLoading();
    if(res.status==='success'){ adminToast('Saved! Click "Apply" to publish.','success'); checkUnpushed(); adminClosePanel(); setTimeout(()=>location.reload(),1500); }
    else adminToast(res.message||JSON.stringify(res.errors),'error');
  }catch(e){ adminHideLoading(); adminToast(e.message,'error'); }
};

window._adminDeleteCourse = async function(courseType, idx){
  if(!confirm('Delete this course?')) return;
  adminShowLoading('Deleting...');
  try{
    const res = await apiCall(`/deploy/courses/${courseType}.${idx}`,'DELETE');
    adminHideLoading();
    if(res.status==='success'){ adminToast('Deleted! Click "Apply" to publish.','success'); checkUnpushed(); setTimeout(()=>location.reload(),1500); }
    else adminToast(res.message,'error');
  }catch(e){ adminHideLoading(); adminToast(e.message,'error'); }
};

// ═══════════════════════════════════════
// ROBOT EDITING
// ═══════════════════════════════════════

async function editRobot(el){
  const data = await apiGet('/data/members');
  const robots = data.robots?.members || [];
  const nameEl = el.querySelector('.member-name');
  const cardName = nameEl ? nameEl.textContent.trim() : '';
  const idx = robots.findIndex(r=> r.name===cardName || r.name_ko===cardName);
  if(idx<0){ adminToast('Robot not found: '+cardName,'error'); return; }
  showRobotForm(robots[idx], idx);
}

function addRobotForm(){ showRobotForm({}, -1); }

function showRobotForm(robot, idx){
  const isNew = idx < 0;
  const specs = robot.specs || {};
  const photoPreview = robot.photo ? `<img src="/${esc(robot.photo)}" class="photo-preview">` : '';
  openPanel((isNew?'Add':'Edit')+' Robot: '+(robot.name||'New Robot'), `
    <div class="admin-fg"><label>Name *</label><input id="af-rname" value="${esc(robot.name||'')}"></div>
    <div class="admin-fg"><label>Korean Name</label><input id="af-rname_ko" value="${esc(robot.name_ko||'')}"></div>
    <div class="admin-fg"><label>Model</label><input id="af-rmodel" value="${esc(robot.model||'')}"></div>
    <div class="admin-fg"><label>Joined Date</label><input id="af-rjoined" value="${esc(robot.joined||'')}" placeholder="e.g. January 2026"></div>
    <div class="admin-fg"><label>Photo</label>
      <input id="af-rphoto" value="${esc(robot.photo||'')}" readonly style="cursor:pointer" onclick="window._adminImagePicker('members','af-rphoto')">
      ${photoPreview}
      <div class="hint">Click to upload</div></div>
    <div class="admin-fg"><label>Bio</label><textarea id="af-rbio">${esc(robot.bio||'')}</textarea></div>
    <hr style="margin:16px 0;border-color:#334155">
    <div style="font-size:13px;font-weight:600;color:#94a3b8;margin-bottom:8px">Specifications</div>
    <div class="admin-fg"><label>Height</label><input id="af-rheight" value="${esc(specs.height||'')}"></div>
    <div class="admin-fg"><label>Weight</label><input id="af-rweight" value="${esc(specs.weight||'')}"></div>
    <div class="admin-fg"><label>DOF</label><input id="af-rdof" value="${esc(specs.dof||'')}"></div>
    <div class="admin-fg"><label>Speed</label><input id="af-rspeed" value="${esc(specs.speed||'')}"></div>
    <div class="admin-fg"><label>Battery</label><input id="af-rbattery" value="${esc(specs.battery||'')}"></div>
    <div class="admin-fg"><label>Payload</label><input id="af-rpayload" value="${esc(specs.payload||'')}"></div>
    <div class="admin-btn-row">
      <button class="admin-btn admin-btn-cancel" onclick="adminClosePanel()">Cancel</button>
      <button class="admin-btn admin-btn-primary" onclick="window._adminSaveRobot(${idx})">${isNew?'Add':'Save'}</button>
    </div>
    ${!isNew?`<button class="admin-btn-danger" onclick="window._adminDeleteRobot(${idx},'${esc(robot.name||'')}')">Delete this robot</button>`:''}
  `);
}

window._adminSaveRobot = async function(idx){
  const d = {
    name:document.getElementById('af-rname').value.trim(),
    name_ko:document.getElementById('af-rname_ko').value.trim(),
    model:document.getElementById('af-rmodel').value.trim(),
    joined:document.getElementById('af-rjoined').value.trim(),
    photo:document.getElementById('af-rphoto').value.trim(),
    bio:document.getElementById('af-rbio').value.trim(),
    specs:{
      height:document.getElementById('af-rheight').value.trim(),
      weight:document.getElementById('af-rweight').value.trim(),
      dof:document.getElementById('af-rdof').value.trim(),
      speed:document.getElementById('af-rspeed').value.trim(),
      battery:document.getElementById('af-rbattery').value.trim(),
      payload:document.getElementById('af-rpayload').value.trim(),
    }
  };
  Object.keys(d.specs).forEach(k=>{if(!d.specs[k])delete d.specs[k]});
  if(!Object.keys(d.specs).length) delete d.specs;
  if(!d.name){ adminToast('Robot name is required','error'); return; }

  adminShowLoading('Saving...');
  try{
    const endpoint = idx>=0 ? `/deploy/members/robots.members.${idx}` : `/deploy/members/robots.members`;
    const method = idx>=0 ? 'PUT' : 'POST';
    const res = await apiCall(endpoint, method, d);
    adminHideLoading();
    if(res.status==='success'){ adminToast('Saved! Click "Apply" to publish.','success'); checkUnpushed(); adminClosePanel(); setTimeout(()=>location.reload(),1500); }
    else adminToast(res.message||JSON.stringify(res.errors),'error');
  }catch(e){ adminHideLoading(); adminToast(e.message,'error'); }
};

window._adminDeleteRobot = async function(idx, name){
  if(!confirm('Delete robot '+name+'?')) return;
  adminShowLoading('Deleting...');
  try{
    const res = await apiCall(`/deploy/members/robots.members.${idx}`,'DELETE');
    adminHideLoading();
    if(res.status==='success'){ adminToast('Deleted!','success'); checkUnpushed(); setTimeout(()=>location.reload(),1500); }
    else adminToast(res.message,'error');
  }catch(e){ adminHideLoading(); adminToast(e.message,'error'); }
};

// ═══════════════════════════════════════
// INTERNATIONAL PUBLICATION ADD
// ═══════════════════════════════════════

function addIntlPubForm(){
  const types = ['conference','journal','workshop'];
  const statuses = ['accepted','published','award'];
  openPanel('Add International Publication', `
    <div class="admin-fg"><label>ID *</label><input id="af-id" placeholder="e.g. c27 (must be unique)"></div>
    <div class="admin-fg"><label>Title *</label><textarea id="af-title" style="min-height:60px"></textarea></div>
    <div class="admin-fg"><label>Authors *</label><input id="af-authors"></div>
    <div class="admin-fg"><label>Venue *</label><input id="af-venue" placeholder="Full name"></div>
    <div class="admin-fg"><label>Venue Short</label><input id="af-venue_short" placeholder="e.g. CVPR"></div>
    <div class="admin-fg"><label>Year</label><input id="af-year" type="number" value="2026"></div>
    <div class="admin-fg"><label>Type</label>
      <select id="af-type">${types.map(t=>`<option>${t}</option>`).join('')}</select></div>
    <div class="admin-fg"><label>Status</label>
      <select id="af-status">${statuses.map(s=>`<option>${s}</option>`).join('')}</select></div>
    <div class="admin-fg"><label>PDF Link</label><input id="af-link-pdf"></div>
    <div class="admin-fg"><label>Website Link</label><input id="af-link-website"></div>
    <div class="admin-fg"><label>GitHub Link</label><input id="af-link-github"></div>
    <div class="admin-fg"><label>Architecture Image</label>
      <input id="af-pub-image" value="" readonly style="cursor:pointer" onclick="window._adminImagePicker('publications','af-pub-image')">
      <div class="hint">Click to upload</div></div>
    <div class="admin-fg"><label>Abstract</label><textarea id="af-abstract" style="min-height:120px"></textarea></div>
    <div class="admin-btn-row">
      <button class="admin-btn admin-btn-cancel" onclick="adminClosePanel()">Cancel</button>
      <button class="admin-btn admin-btn-primary" onclick="window._adminAddIntlPub()">Add</button>
    </div>
  `);
}

window._adminAddIntlPub = async function(){
  const d = {
    id:document.getElementById('af-id').value.trim(),
    title:document.getElementById('af-title').value.trim(),
    authors:document.getElementById('af-authors').value.trim(),
    venue:document.getElementById('af-venue').value.trim(),
    venue_short:document.getElementById('af-venue_short').value.trim(),
    year:parseInt(document.getElementById('af-year').value)||2026,
    type:document.getElementById('af-type').value,
    status:document.getElementById('af-status').value,
    image:document.getElementById('af-pub-image').value.trim()||undefined,
    abstract:document.getElementById('af-abstract').value.trim()||undefined,
    links:{
      pdf:document.getElementById('af-link-pdf').value.trim()||undefined,
      website:document.getElementById('af-link-website').value.trim()||undefined,
      github:document.getElementById('af-link-github').value.trim()||undefined,
    }
  };
  Object.keys(d.links).forEach(k=>{if(!d.links[k])delete d.links[k]});
  if(!Object.keys(d.links).length) delete d.links;
  Object.keys(d).forEach(k=>{if(d[k]===undefined)delete d[k]});
  if(!d.id||!d.title||!d.authors||!d.venue){ adminToast('ID, title, authors, venue are required','error'); return; }

  adminShowLoading('Adding publication...');
  try{
    const res = await apiCall('/deploy/publications/publications','POST',d);
    adminHideLoading();
    if(res.status==='success'){ adminToast('Added! Click "Apply" to publish.','success'); checkUnpushed(); adminClosePanel(); setTimeout(()=>location.reload(),1500); }
    else adminToast(res.message||JSON.stringify(res.errors),'error');
  }catch(e){ adminHideLoading(); adminToast(e.message,'error'); }
};

// ═══════════════════════════════════════
// DOMESTIC PUBLICATION EDITING
// ═══════════════════════════════════════

async function editDomesticPub(el){
  const pubId = el.getAttribute('data-admin-pub-id');
  const data = await apiGet('/data/domestic_publications');
  const pubs = data.publications || [];
  const idx = pubs.findIndex(p=> p.id === pubId);
  if(idx<0){ adminToast('Publication not found','error'); return; }
  showDomesticPubForm(pubs[idx], idx);
}

function addDomesticPubForm(){ showDomesticPubForm({}, -1); }

function showDomesticPubForm(pub, idx){
  const isNew = idx < 0;
  openPanel((isNew?'Add':'Edit')+' Domestic Publication', `
    <div class="admin-fg"><label>ID *</label><input id="af-did" value="${esc(pub.id||'')}" ${isNew?'placeholder="e.g. d8"':'readonly style="background:#334155"'}></div>
    <div class="admin-fg"><label>Title (Korean) *</label><textarea id="af-dtitle" style="min-height:60px">${esc(pub.title||'')}</textarea></div>
    <div class="admin-fg"><label>Authors *</label><input id="af-dauthors" value="${esc(pub.authors||'')}"></div>
    <div class="admin-fg"><label>Venue (학회/저널) *</label><input id="af-dvenue" value="${esc(pub.venue||'')}"></div>
    <div class="admin-btn-row">
      <button class="admin-btn admin-btn-cancel" onclick="adminClosePanel()">Cancel</button>
      <button class="admin-btn admin-btn-primary" onclick="window._adminSaveDomesticPub(${idx})">${isNew?'Add':'Save'}</button>
    </div>
    ${!isNew?`<button class="admin-btn-danger" onclick="window._adminDeleteDomesticPub(${idx})">Delete this publication</button>`:''}
  `);
}

window._adminSaveDomesticPub = async function(idx){
  const d = {
    id:document.getElementById('af-did').value.trim(),
    title:document.getElementById('af-dtitle').value.trim(),
    authors:document.getElementById('af-dauthors').value.trim(),
    venue:document.getElementById('af-dvenue').value.trim(),
  };
  if(!d.id||!d.title||!d.authors||!d.venue){ adminToast('All fields required','error'); return; }

  adminShowLoading('Saving...');
  try{
    const endpoint = idx>=0 ? `/deploy/domestic_publications/publications.${idx}` : `/deploy/domestic_publications/publications`;
    const method = idx>=0 ? 'PUT' : 'POST';
    const res = await apiCall(endpoint, method, d);
    adminHideLoading();
    if(res.status==='success'){ adminToast('Saved! Click "Apply" to publish.','success'); checkUnpushed(); adminClosePanel(); setTimeout(()=>location.reload(),1500); }
    else adminToast(res.message||JSON.stringify(res.errors),'error');
  }catch(e){ adminHideLoading(); adminToast(e.message,'error'); }
};

window._adminDeleteDomesticPub = async function(idx){
  if(!confirm('Delete this domestic publication?')) return;
  adminShowLoading('Deleting...');
  try{
    const res = await apiCall(`/deploy/domestic_publications/publications.${idx}`,'DELETE');
    adminHideLoading();
    if(res.status==='success'){ adminToast('Deleted!','success'); checkUnpushed(); setTimeout(()=>location.reload(),1500); }
    else adminToast(res.message,'error');
  }catch(e){ adminHideLoading(); adminToast(e.message,'error'); }
};

// ═══════════════════════════════════════
// SLIDER EDITING (Home slider + Archive)
// ═══════════════════════════════════════
//
// Two parallel lists live under en.header:
//   - slider           : items shown in the home hero rotation
//   - slider_archive   : items shown ONLY inside the "More Images" modal
// Admins can move slides between them to retire/restore without deleting.
// API path conventions follow the dotted-path scheme used elsewhere.

const _SLIDER_KEYS = {
  slider:         { label: '🏠 Home',    path: 'en.header.slider'         },
  slider_archive: { label: '📦 Archive', path: 'en.header.slider_archive' },
};

function _renderSliderSection(sectionKey, slides){
  const meta = _SLIDER_KEYS[sectionKey];
  const otherKey = (sectionKey === 'slider') ? 'slider_archive' : 'slider';
  const otherLabel = _SLIDER_KEYS[otherKey].label;
  const sectionHint = (sectionKey === 'slider')
    ? 'Shown on the home page hero. Drag to reorder.'
    : 'Hidden from the hero — visible only inside the More Images modal.';

  let html = `<div style="margin-top:18px;margin-bottom:8px">
      <div style="display:flex;align-items:center;justify-content:space-between">
        <h4 style="margin:0;font-size:14px;color:#e2e8f0">${meta.label} <span style="color:#94a3b8;font-weight:400">(${slides.length})</span></h4>
      </div>
      <div style="color:#64748b;font-size:11px;margin-top:2px">${sectionHint}</div>
    </div>`;
  html += `<div id="admin-slider-list-${sectionKey}" data-section="${sectionKey}">`;

  if (slides.length === 0) {
    html += `<div style="padding:14px;background:#0f172a;border:1px dashed #334155;border-radius:8px;color:#64748b;font-size:12px;text-align:center">No items.</div>`;
  } else {
    slides.forEach((s, i) => {
      html += `<div class="admin-slider-item" draggable="true" data-idx="${i}" data-section="${sectionKey}"
        style="display:flex;align-items:center;gap:10px;padding:10px;margin-bottom:6px;background:#0f172a;
        border-radius:8px;border:1px solid #334155;cursor:grab;transition:transform .15s,opacity .15s">
        <span style="color:#94a3b8;font-size:16px;cursor:grab;padding:0 2px;flex-shrink:0">&#9776;</span>
        <img src="/${esc(s.image)}" style="width:60px;height:40px;object-fit:cover;border-radius:4px;flex-shrink:0"
             onerror="this.style.display='none'">
        <div style="flex:1;min-width:0">
          <div style="font-size:13px;font-weight:600;color:#e2e8f0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(s.title)}</div>
          <div style="font-size:11px;color:#94a3b8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(s.description)}</div>
        </div>
        <div style="display:flex;gap:6px;flex-shrink:0;align-items:center">
          <button class="admin-row-btn row-move"   title="Move to ${otherLabel}"
            onclick="event.stopPropagation();window._adminMoveSlide('${sectionKey}',${i})">${sectionKey === 'slider' ? '→ 📦' : '→ 🏠'}</button>
          <button class="admin-row-btn row-edit"
            onclick="event.stopPropagation();window._adminEditSlide('${sectionKey}',${i})">Edit</button>
          <button class="admin-row-btn row-delete" title="Delete"
            onclick="event.stopPropagation();window._adminDeleteSlide('${sectionKey}',${i})">&times;</button>
        </div>
      </div>`;
    });
  }
  html += '</div>';
  html += `<button class="admin-btn admin-btn-primary" onclick="window._adminAddSlide('${sectionKey}')"
            style="width:100%;margin-top:8px">+ Add to ${meta.label}</button>`;
  return html;
}

window.editSlider = async function(){
  const data = await apiGet('/data/sitetext');
  const mainSlides    = data?.en?.header?.slider          || [];
  const archiveSlides = data?.en?.header?.slider_archive  || [];

  let html = '<div style="margin-bottom:8px;color:#94a3b8;font-size:13px">Drag to reorder within a section. Use → buttons to move between Home and Archive.</div>';
  html += _renderSliderSection('slider',         mainSlides);
  html += _renderSliderSection('slider_archive', archiveSlides);

  openPanel('Edit Slider (' + mainSlides.length + ' home + ' + archiveSlides.length + ' archive)', html);

  setTimeout(() => {
    initSliderDrag('slider');
    initSliderDrag('slider_archive');
  }, 100);
};

function initSliderDrag(sectionKey){
  const list = document.getElementById('admin-slider-list-' + sectionKey);
  if(!list) return;

  list.querySelectorAll('.admin-slider-item').forEach(item=>{
    item.addEventListener('dragstart', (e)=>{
      item.style.opacity = '0.4';
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', item.dataset.idx);
    });

    item.addEventListener('dragend', ()=>{
      item.style.opacity = '1';
      list.querySelectorAll('.admin-slider-item').forEach(el=>{
        el.style.borderTop = '1px solid #334155';
        el.style.borderBottom = 'none';
      });
    });

    item.addEventListener('dragover', (e)=>{
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      const rect = item.getBoundingClientRect();
      const midY = rect.top + rect.height / 2;
      list.querySelectorAll('.admin-slider-item').forEach(el=>{
        el.style.borderTop = '1px solid #334155';
        el.style.borderBottom = 'none';
      });
      if(e.clientY < midY){ item.style.borderTop = '2px solid #3b82f6'; }
      else { item.style.borderBottom = '2px solid #3b82f6'; }
    });

    item.addEventListener('drop', async (e)=>{
      e.preventDefault();
      const fromIdx = parseInt(e.dataTransfer.getData('text/plain'));
      const toEl = item;
      let toIdx = parseInt(toEl.dataset.idx);
      const rect = toEl.getBoundingClientRect();
      const midY = rect.top + rect.height / 2;
      if(e.clientY >= midY) toIdx += 1;
      if(fromIdx === toIdx || fromIdx === toIdx - 1) return;
      await reorderSlide(sectionKey, fromIdx, toIdx > fromIdx ? toIdx - 1 : toIdx);
    });
  });
}

async function reorderSlide(sectionKey, fromIdx, toIdx){
  adminShowLoading('Reordering...');
  try{
    const data = await apiGet('/data/sitetext');
    const slides = data.en.header[sectionKey] || [];
    const [moved] = slides.splice(fromIdx, 1);
    slides.splice(toIdx, 0, moved);

    const res = await apiCall('/deploy/sitetext/' + _SLIDER_KEYS[sectionKey].path, 'PUT', slides);
    adminHideLoading();
    if(res.status==='success'){
      adminToast('Reordered! Click "Apply" to publish.','success');
      checkUnpushed();
      editSlider();
    } else {
      adminToast(res.message||'Error','error');
    }
  }catch(e){ adminHideLoading(); adminToast(e.message,'error'); }
}

window._adminEditSlide = async function(sectionKey, idx){
  const data = await apiGet('/data/sitetext');
  const slide = (data.en.header[sectionKey] || [])[idx];
  if (!slide) { adminToast('Slide not found','error'); return; }
  const sectionLabel = _SLIDER_KEYS[sectionKey].label;

  openPanel('Edit Slide ['+sectionLabel+']: '+slide.title, `
    <div class="admin-fg"><label>Title</label><input id="af-slide-title" value="${esc(slide.title||'')}"></div>
    <div class="admin-fg"><label>Description</label><input id="af-slide-desc" value="${esc(slide.description||'')}"></div>
    <div class="admin-fg"><label>Image</label>
      <input id="af-slide-image" value="${esc(slide.image||'')}" readonly style="cursor:pointer" onclick="window._adminImagePicker('slider','af-slide-image')">
      <img src="/${esc(slide.image)}" style="width:100%;max-height:150px;object-fit:cover;border-radius:8px;margin-top:8px" onerror="this.style.display='none'">
      <div class="hint">Click to upload new image</div></div>
    <div class="admin-btn-row">
      <button class="admin-btn admin-btn-cancel" onclick="editSlider()">Back</button>
      <button class="admin-btn admin-btn-primary" onclick="window._adminSaveSlide('${sectionKey}',${idx})">Save</button>
    </div>
  `);
};

window._adminSaveSlide = async function(sectionKey, idx){
  const data = await apiGet('/data/sitetext');
  const slide = (data.en.header[sectionKey] || [])[idx];
  if (!slide) { adminToast('Slide not found','error'); return; }
  slide.title       = document.getElementById('af-slide-title').value.trim();
  slide.description = document.getElementById('af-slide-desc').value.trim();
  slide.image       = document.getElementById('af-slide-image').value.trim();

  adminShowLoading('Saving slider...');
  try{
    const res = await apiCall(`/deploy/sitetext/${_SLIDER_KEYS[sectionKey].path}.${idx}`,'PUT', slide);
    adminHideLoading();
    if(res.status==='success'){ adminToast('Saved! Click "Apply" to publish.','success'); checkUnpushed(); editSlider(); }
    else adminToast(res.message||'Error','error');
  }catch(e){ adminHideLoading(); adminToast(e.message,'error'); }
};

window._adminAddSlide = function(sectionKey){
  const sectionLabel = _SLIDER_KEYS[sectionKey].label;
  openPanel('Add to ' + sectionLabel, `
    <div class="admin-fg"><label>Title <span style="color:#f87171">*</span></label>
      <input id="af-slide-title" placeholder="Slide title (required)"></div>
    <div class="admin-fg"><label>Description</label>
      <input id="af-slide-desc" placeholder="Short description (optional)"></div>
    <div class="admin-fg"><label>Image <span style="color:#f87171">*</span></label>
      <input id="af-slide-image" value="" readonly placeholder="Click here to upload an image (required)"
        style="cursor:pointer" onclick="window._adminImagePicker('slider','af-slide-image')">
      <div class="hint" style="color:#fbbf24">Required — click the field above to upload, then come back and click Add.</div></div>
    <div id="af-slide-error" style="display:none;margin:8px 0;padding:10px 12px;background:#7f1d1d;border-radius:8px;color:#fecaca;font-size:13px;font-weight:600"></div>
    <div class="admin-btn-row">
      <button class="admin-btn admin-btn-cancel" onclick="editSlider()">Back</button>
      <button class="admin-btn admin-btn-primary" onclick="window._adminSaveNewSlide('${sectionKey}')">Add to ${sectionLabel}</button>
    </div>
  `);
};

function _showSlideError(msg){
  const box = document.getElementById('af-slide-error');
  if (box) { box.textContent = msg; box.style.display = 'block'; }
  adminToast(msg, 'error');
}

window._adminSaveNewSlide = async function(sectionKey){
  const slide = {
    image:       document.getElementById('af-slide-image').value.trim(),
    title:       document.getElementById('af-slide-title').value.trim(),
    description: document.getElementById('af-slide-desc').value.trim(),
  };
  // Distinguish the two required fields so the user knows which one to fill.
  if(!slide.title && !slide.image){ _showSlideError('Title and Image are both required.'); return; }
  if(!slide.title){ _showSlideError('Title is required.'); return; }
  if(!slide.image){ _showSlideError('Image is required — click the Image field to upload one.'); return; }

  adminShowLoading('Adding to ' + _SLIDER_KEYS[sectionKey].label + '...');
  try{
    let res = await apiCall('/deploy/sitetext/' + _SLIDER_KEYS[sectionKey].path, 'POST', slide);
    // Older sitetext.yml without slider_archive: POST will 404; seed via PUT.
    if (res.status !== 'success' && sectionKey === 'slider_archive') {
      res = await apiCall('/deploy/sitetext/' + _SLIDER_KEYS[sectionKey].path, 'PUT', [slide]);
    }
    adminHideLoading();
    if(res.status==='success'){
      adminToast('Saved to ' + _SLIDER_KEYS[sectionKey].label + '! Click "Apply" to publish.','success');
      checkUnpushed();
      editSlider();
    } else {
      _showSlideError(res.message || res.error || 'Server rejected the request.');
    }
  }catch(e){ adminHideLoading(); _showSlideError(e.message || 'Network error'); }
};

window._adminDeleteSlide = async function(sectionKey, idx){
  if(!confirm('Delete this slide? This is permanent — use the → button to archive instead if you want to keep it.')) return;
  adminShowLoading('Deleting...');
  try{
    const res = await apiCall(`/deploy/sitetext/${_SLIDER_KEYS[sectionKey].path}.${idx}`,'DELETE');
    adminHideLoading();
    if(res.status==='success'){ adminToast('Deleted! Click "Apply" to publish.','success'); checkUnpushed(); editSlider(); }
    else adminToast(res.message,'error');
  }catch(e){ adminHideLoading(); adminToast(e.message,'error'); }
};

window._adminMoveSlide = async function(fromSection, idx){
  const toSection = (fromSection === 'slider') ? 'slider_archive' : 'slider';
  adminShowLoading('Moving...');
  try{
    const data = await apiGet('/data/sitetext');
    const src = data.en.header[fromSection] || [];
    const dst = data.en.header[toSection]   || [];
    if (idx < 0 || idx >= src.length) { adminHideLoading(); adminToast('Slide not found','error'); return; }
    const [moved] = src.splice(idx, 1);
    dst.push(moved);

    // Two PUTs; if the destination list was missing/empty before this is also
    // the moment it gets seeded as a real list rather than nil.
    let res1 = await apiCall('/deploy/sitetext/' + _SLIDER_KEYS[fromSection].path, 'PUT', src);
    if (res1.status !== 'success') { adminHideLoading(); adminToast(res1.message||'Error','error'); return; }
    let res2 = await apiCall('/deploy/sitetext/' + _SLIDER_KEYS[toSection].path,   'PUT', dst);
    adminHideLoading();
    if (res2.status === 'success') {
      adminToast(fromSection === 'slider' ? 'Moved to Archive — hidden from home.' : 'Moved to Home — now in hero rotation.','success');
      checkUnpushed();
      editSlider();
    } else {
      adminToast(res2.message||'Error','error');
    }
  }catch(e){ adminHideLoading(); adminToast(e.message,'error'); }
};

// ═══════════════════════════════════════
// IMAGE PICKER
// ═══════════════════════════════════════

window._adminImagePicker = function(category, inputId){
  const isNewsImage = (inputId === 'af-image');
  const modal = document.createElement('div');
  modal.className='admin-img-modal';
  modal.onclick=function(e){if(e.target===modal)modal.remove()};

  modal.innerHTML=`<div class="admin-img-modal-body">
    <h3 style="margin:0 0 16px;font-size:18px">Upload Image</h3>

    <!-- Drag & Drop Zone -->
    <div id="admin-drop-zone" style="border:2px dashed #94a3b8;border-radius:12px;padding:40px 20px;text-align:center;
      cursor:pointer;transition:all .2s;background:#0f172a;border-color:#475569;margin-bottom:16px">
      <div style="font-size:36px;margin-bottom:8px">📷</div>
      <p style="font-size:15px;font-weight:600;color:#cbd5e1;margin:0 0 4px">Drag & drop image here</p>
      <p style="font-size:13px;color:#94a3b8;margin:0">or click to browse files</p>
      <input type="file" accept="image/*" id="admin-file-input" style="display:none">
    </div>

    <!-- Upload preview -->
    <div id="admin-upload-preview" style="display:none;text-align:center;margin-bottom:16px">
      <img id="admin-preview-img" style="max-width:200px;max-height:200px;border-radius:8px;border:1px solid #e2e8f0">
      <p id="admin-preview-name" style="font-size:13px;color:#94a3b8;margin-top:6px"></p>
    </div>

    <!-- Upload button -->
    <button id="admin-upload-confirm" style="display:none;width:100%;padding:12px;background:#3b82f6;color:#fff;border:none;
      border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;margin-bottom:12px">Upload & Select</button>

    <div style="display:flex;gap:8px">
      <button onclick="this.closest('.admin-img-modal').remove()"
        style="flex:1;padding:10px;background:#334155;color:#cbd5e1;border:none;border-radius:8px;cursor:pointer;font-size:13px">Cancel</button>
    </div>
  </div>`;
  document.body.appendChild(modal);

  const dropZone = document.getElementById('admin-drop-zone');
  const fileInput = document.getElementById('admin-file-input');
  const preview = document.getElementById('admin-upload-preview');
  const previewImg = document.getElementById('admin-preview-img');
  const previewName = document.getElementById('admin-preview-name');
  const confirmBtn = document.getElementById('admin-upload-confirm');
  let selectedFile = null;

  // Click to browse
  dropZone.onclick = () => fileInput.click();

  // Drag & Drop
  dropZone.ondragover = (e) => { e.preventDefault(); dropZone.style.borderColor='#3b82f6'; dropZone.style.background='#1e293b'; };
  dropZone.ondragleave = () => { dropZone.style.borderColor='#475569'; dropZone.style.background='#0f172a'; };
  dropZone.ondrop = (e) => {
    e.preventDefault();
    dropZone.style.borderColor='#475569'; dropZone.style.background='#0f172a';
    const file = e.dataTransfer.files[0];
    if(file && file.type.startsWith('image/')) handleFileSelect(file);
    else adminToast('Please drop an image file','error');
  };

  // File input change
  fileInput.onchange = () => { if(fileInput.files[0]) handleFileSelect(fileInput.files[0]); };

  function handleFileSelect(file){
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      previewImg.src = e.target.result;
      previewName.textContent = file.name + ' (' + (file.size/1024).toFixed(0) + 'KB)';
      preview.style.display = 'block';
      confirmBtn.style.display = 'block';
      dropZone.style.display = 'none';
    };
    reader.readAsDataURL(file);
  }

  // Upload & select
  confirmBtn.onclick = async () => {
    if(!selectedFile) return;
    confirmBtn.textContent = 'Uploading...';
    confirmBtn.disabled = true;
    const fd = new FormData();
    fd.append('file', selectedFile);
    try{
      const r = await fetch(API+'/images/'+category+'/upload', {method:'POST', body:fd});
      const res = await r.json();
      if(res.path){
        document.getElementById(inputId).value = isNewsImage ? res.filename : res.path;
        modal.remove();
        adminToast('Image uploaded!','success');
      } else {
        adminToast(res.error||'Upload failed','error');
        confirmBtn.textContent = 'Upload & Select';
        confirmBtn.disabled = false;
      }
    }catch(e){
      adminToast(e.message,'error');
      confirmBtn.textContent = 'Upload & Select';
      confirmBtn.disabled = false;
    }
  };
};

// ═══════════════════════════════════════
// APPLY (PUSH) TO LIVE SITE
// ═══════════════════════════════════════

async function checkUnpushed(){
  try{
    const data = await apiGet('/unpushed');
    const btn = document.getElementById('admin-apply-btn');
    const badge = document.getElementById('admin-unpushed-count');
    const status = document.getElementById('admin-status');
    if(data.unpushed > 0){
      btn.classList.add('has-changes');
      badge.textContent = data.unpushed;
      status.textContent = `${data.unpushed} unsaved change${data.unpushed>1?'s':''} (click Apply to publish)`;
      status.style.color = '#fbbf24';
    } else {
      btn.classList.remove('has-changes');
      status.textContent = 'All changes published';
      status.style.color = '#94a3b8';
    }
  }catch(e){}
}

window._adminApplyChanges = async function(){
  if(!confirm('Apply all changes to the live site? This will update reality.ssu.ac.kr.')) return;
  adminShowLoading('Pushing to live site...');
  try{
    const res = await apiCall('/push','POST',{});
    adminHideLoading();
    if(res.status==='success'){
      adminToast('Applied to live site! Changes will appear in ~1 min.','success');
      checkUnpushed();
    } else {
      adminToast(res.message||'Push failed','error');
    }
  }catch(e){ adminHideLoading(); adminToast(e.message,'error'); }
};

// ═══════════════════════════════════════
// INIT
// ═══════════════════════════════════════

setTimeout(markEditables, 500);
const observer = new MutationObserver(()=>setTimeout(markEditables,300));
observer.observe(document.body, {childList:true, subtree:true});

// Check for unpushed changes on load and periodically
checkUnpushed();
setInterval(checkUnpushed, 15000);

// Audit log viewer
window._adminShowAudit = async function(){
  try{
    const entries = await apiGet('/audit?limit=200');
    let html = '<div style="margin-bottom:12px;color:#94a3b8;font-size:13px">최근 편집 이력 (최대 200건)</div>';
    if(!entries.length){
      html += '<div style="color:#64748b;text-align:center;padding:20px">기록이 없습니다.</div>';
    } else {
      const actionColors = {
        'LOGIN':'#60a5fa', 'UPDATE':'#fbbf24', 'ADD':'#34d399',
        'DELETE':'#f87171', 'APPLY (push)':'#a78bfa'
      };
      entries.forEach(e=>{
        const color = actionColors[e.action] || '#94a3b8';
        const dt = e.ts.replace('T',' ');
        html += `<div style="padding:8px 10px;margin-bottom:4px;background:#0f172a;border-radius:6px;border-left:3px solid ${color}">
          <div style="display:flex;justify-content:space-between;align-items:center;font-size:11px;color:#64748b;margin-bottom:2px">
            <span>${esc(dt)}</span>
            <span style="background:${color};color:#0f172a;padding:1px 6px;border-radius:3px;font-weight:700">${esc(e.action)}</span>
          </div>
          <div style="font-size:13px;color:#e2e8f0">
            <strong>${esc(e.user)}</strong>${e.target?' &middot; <span style="color:#94a3b8">'+esc(e.target)+'</span>':''}
          </div>
          ${e.details?`<div style="font-size:11px;color:#64748b;margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(e.details)}</div>`:''}
        </div>`;
      });
    }
    openPanel('Edit Log ('+entries.length+')', html);
  }catch(e){ adminToast('Failed to load log: '+e.message,'error'); }
};


(async function showEditorName(){
  try{
    const res = await apiGet('/whoami');
    const status = document.getElementById('admin-status');
    if(status && res.name){
      status.textContent = '✏️ ' + res.name;
      status.title = 'Logged in as ' + res.name;
    }
  }catch(e){}
})();

})();
