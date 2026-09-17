// Developer Control Tower AI Assistant Frontend Logic
let currentSessionId = 'sess-' + Math.random().toString(36).substring(2, 10);
const userId = 'user-dev-01';

// DOM Elements
const messagesContainer = document.getElementById('messages-container');
const messageInput = document.getElementById('message-input');
const chatForm = document.getElementById('chat-form');
const repoSelect = document.getElementById('repo-select');
const routeSelect = document.getElementById('route-select');
const activeRouteDisplay = document.getElementById('active-route-display');
const activeRepoDisplay = document.getElementById('active-repo-display');
const sensorRoutePill = document.getElementById('sensor-route-pill');
const sensorRepoPill = document.getElementById('sensor-repo-pill');
const sessionIdDisplay = document.getElementById('session-id-display');
const telemetryFeed = document.getElementById('telemetry-feed');
const memoryDrawer = document.getElementById('memory-drawer');
const toggleMemoryBtn = document.getElementById('toggle-memory-btn');
const closeDrawerBtn = document.getElementById('close-drawer-btn');
const memoriesList = document.getElementById('memories-list');
const memoryCountBadge = document.getElementById('memory-count-badge');
const purgeAllMemoriesBtn = document.getElementById('purge-all-memories-btn');
const refreshMemoriesBtn = document.getElementById('refresh-memories-btn');
const newSessionBtn = document.getElementById('new-session-btn');
const clearChatBtn = document.getElementById('clear-chat-btn');

sessionIdDisplay.textContent = `Session: ${currentSessionId}`;

function updateAmbientContext() {
  const currentRoute = routeSelect.value;
  const currentRepo = repoSelect.value;

  activeRouteDisplay.textContent = currentRoute;
  activeRepoDisplay.textContent = currentRepo;
  sensorRoutePill.textContent = `Route: ${currentRoute}`;
  sensorRepoPill.textContent = `Repo: ${currentRepo}`;

  loadTelemetry(currentRepo);
}

repoSelect.addEventListener('change', updateAmbientContext);
routeSelect.addEventListener('change', updateAmbientContext);

document.querySelectorAll('.quick-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const q = btn.getAttribute('data-query');
    sendMessage(q);
  });
});

window.sendChip = function(query) {
  sendMessage(query);
};

clearChatBtn.addEventListener('click', () => {
  messagesContainer.innerHTML = '';
});

newSessionBtn.addEventListener('click', async () => {
  try {
    const res = await fetch(`/api/v1/chat/sessions/${currentSessionId}/consolidate`, {
      method: 'POST'
    });
    const data = await res.json();
    alert(`Session consolidated! ${data.consolidated_memories_count} facts distilled into Episodic Memory.`);
    
    currentSessionId = 'sess-' + Math.random().toString(36).substring(2, 10);
    sessionIdDisplay.textContent = `Session: ${currentSessionId}`;
    messagesContainer.innerHTML = `
      <div class="message-turn assistant-turn">
        <div class="message-avatar">🤖</div>
        <div class="message-bubble">
          <p>Started a fresh session! I retained your distilled preferences and project history in my <strong>Episodic Memory</strong>.</p>
        </div>
      </div>
    `;
    loadMemories();
  } catch (err) {
    console.error(err);
  }
});

chatForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const text = messageInput.value.trim();
  if (!text) return;
  messageInput.value = '';
  sendMessage(text);
});

async function sendMessage(text) {
  appendUserMessage(text);

  const payload = {
    session_id: currentSessionId,
    user_id: userId,
    message: text,
    ambient_context: {
      current_route: routeSelect.value,
      repo_id: repoSelect.value,
      active_branch: 'main',
      user_role: 'developer'
    }
  };

  const assistantTurn = createAssistantMessageHolder();
  const bubble = assistantTurn.querySelector('.message-bubble');
  let accumulatedText = '';

  try {
    const response = await fetch('/api/v1/chat/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split('\n');
      buffer = lines.pop();

      let currentEvent = 'message';
      for (const line of lines) {
        if (line.startsWith('event:')) {
          currentEvent = line.replace('event:', '').trim();
        } else if (line.startsWith('data:')) {
          const rawData = line.replace('data:', '').trim();
          if (!rawData) continue;
          try {
            const dataObj = JSON.parse(rawData);
            handleStreamEvent(currentEvent, dataObj, bubble, (delta) => {
              accumulatedText += delta;
              renderMarkdown(bubble, accumulatedText);
            });
          } catch (e) {
            console.error('Error parsing SSE:', e, rawData);
          }
        }
      }
    }
  } catch (err) {
    bubble.innerHTML = `<span style="color: #f87171;">Connection error: ${err.message}</span>`;
  }
  loadMemories();
}

function handleStreamEvent(event, data, bubble, appendDelta) {
  if (event === 'token') {
    appendDelta(data.delta);
  } else if (event === 'action_card') {
    renderActionCard(bubble, data);
  } else if (event === 'suggested_chips') {
    renderChips(bubble, data.chips);
  } else if (event === 'done') {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }
}

function renderMarkdown(container, markdown) {
  let html = markdown
    .replace(/^### (.*$)/gim, '<h3 style="margin: 6px 0; color: #60a5fa;">$1</h3>')
    .replace(/^#### (.*$)/gim, '<h4 style="margin: 4px 0; color: #93c5fd;">$1</h4>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/```([a-z]*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br/>');

  const textHolder = container.querySelector('.text-content') || createTextHolder(container);
  textHolder.innerHTML = html;
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function createTextHolder(container) {
  const div = document.createElement('div');
  div.className = 'text-content';
  container.appendChild(div);
  return div;
}

function renderActionCard(container, card) {
  const existing = container.querySelector('.action-card');
  if (existing) existing.remove();

  const cardEl = document.createElement('div');
  cardEl.className = 'action-card';
  cardEl.innerHTML = `
    <div class="action-card-header">
      <div class="action-card-title">🎯 ${card.title}</div>
      ${card.status ? `<span class="badge-role">${card.status}</span>` : ''}
    </div>
    ${card.breadcrumbs && card.breadcrumbs.length ? `<div class="action-breadcrumbs">${card.breadcrumbs.join(' &gt; ')}</div>` : ''}
    <button class="action-card-btn" onclick="simulateNavigation('${card.route}')">
      <span>${card.action_label || 'Go to Feature'}</span>
      <span>&rarr;</span>
    </button>
  `;
  container.appendChild(cardEl);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function renderChips(container, chips) {
  if (!chips || !chips.length) return;
  const chipsDiv = document.createElement('div');
  chipsDiv.className = 'suggested-chips';
  chips.forEach(chip => {
    const btn = document.createElement('button');
    btn.className = 'chip-btn';
    btn.textContent = chip;
    btn.onclick = () => sendMessage(chip);
    chipsDiv.appendChild(btn);
  });
  container.appendChild(chipsDiv);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

window.simulateNavigation = function(route) {
  alert(`Navigating to route: ${route}`);
  for (let opt of routeSelect.options) {
    if (opt.value === route || opt.value.replace(':repoId', repoSelect.value) === route) {
      routeSelect.value = opt.value;
      updateAmbientContext();
      break;
    }
  }
};

function appendUserMessage(text) {
  const turn = document.createElement('div');
  turn.className = 'message-turn user-turn';
  turn.innerHTML = `
    <div class="message-avatar">👤</div>
    <div class="message-bubble">
      <p>${escapeHtml(text)}</p>
    </div>
  `;
  messagesContainer.appendChild(turn);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function createAssistantMessageHolder() {
  const turn = document.createElement('div');
  turn.className = 'message-turn assistant-turn';
  turn.innerHTML = `
    <div class="message-avatar">🤖</div>
    <div class="message-bubble">
      <div class="text-content"><span style="color: #64748b;">Thinking...</span></div>
    </div>
  `;
  messagesContainer.appendChild(turn);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
  return turn;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

async function loadTelemetry(repoId) {
  try {
    const res = await fetch(`/api/v1/telemetry/projects/${repoId}`);
    if (!res.ok) return;
    const data = await res.json();
    
    let itemsHtml = '';
    for (const [agentKey, agentInfo] of Object.entries(data.agents_summary)) {
      const statusClass = `status-badge-${agentInfo.status || 'success'}`;
      const agentTitle = agentKey.replace('_', ' ').toUpperCase();
      itemsHtml += `
        <div class="telemetry-item">
          <div class="telemetry-item-header">
            <span>${agentTitle}</span>
            <span class="${statusClass}">${(agentInfo.status || 'IDLE').toUpperCase()}</span>
          </div>
          <div style="color: #94a3b8;">${agentInfo.last_build ? `Build ${agentInfo.last_build}` : (agentInfo.cve_count !== undefined ? `${agentInfo.cve_count} CVEs` : `Active`)}</div>
        </div>
      `;
    }
    telemetryFeed.innerHTML = itemsHtml;
  } catch (e) {
    console.error('Error loading telemetry:', e);
  }
}

toggleMemoryBtn.addEventListener('click', () => {
  memoryDrawer.classList.remove('hidden');
  loadMemories();
});

closeDrawerBtn.addEventListener('click', () => {
  memoryDrawer.classList.add('hidden');
});

refreshMemoriesBtn.addEventListener('click', loadMemories);

purgeAllMemoriesBtn.addEventListener('click', async () => {
  if (!confirm('Are you sure you want to purge all stored memories?')) return;
  await fetch(`/api/v1/memories?user_id=${userId}`, { method: 'DELETE' });
  loadMemories();
});

async function loadMemories() {
  try {
    const res = await fetch(`/api/v1/memories?user_id=${userId}`);
    const data = await res.json();
    memoryCountBadge.textContent = data.length;

    if (!data.length) {
      memoriesList.innerHTML = `<div style="color: #64748b; font-size: 12px; text-align: center; padding: 20px;">No episodic memories stored yet. Converse with the bot to create memories!</div>`;
      return;
    }

    let html = '';
    data.forEach(mem => {
      html += `
        <div class="memory-card">
          <div class="memory-card-header">
            <span class="badge-mem-type">${mem.memory_type}</span>
            <button class="btn-del-mem" onclick="deleteMemory('${mem.id}')">Delete &times;</button>
          </div>
          <div class="memory-fact-text">${escapeHtml(mem.fact_text)}</div>
          <div class="memory-meta">
            <span>Importance: ${mem.importance_score}</span>
            <span>Decay: ${(mem.decay_factor || 1.0).toFixed(2)}</span>
            <span>Accessed: ${mem.access_count}x</span>
          </div>
        </div>
      `;
    });
    memoriesList.innerHTML = html;
  } catch (err) {
    console.error('Error loading memories:', err);
  }
}

window.deleteMemory = async function(id) {
  await fetch(`/api/v1/memories/${id}?user_id=${userId}`, { method: 'DELETE' });
  loadMemories();
};

updateAmbientContext();
loadMemories();
