const appState = {
    mode: 'custom',
    year: '2026',
    volatility: 0,
    filter: {
        region: 'all',
        round: 'all'
    },
    locks: {
        regions: {},
        final_four: {},
        championship: {}
    },
    optimalWeights: {},
    perfectWeights: {
        // Placeholder: To be tuned for upset hunting
        efficiency: 0.25,
        momentum: 0.15,
        sos: 0.4,
        intuition_factor_weight: 0.8,
        upset_delta_weight: 0.9,
        composure_index_weight: 0.7
    },
    teams: {},
    currentData: null,
    simTimer: null
};

// --- Core Logic ---

function debounceSim() {
    clearTimeout(appState.simTimer);
    appState.simTimer = setTimeout(runSimulation, 400);
}

function resetToOptimal() {
    const weights = appState.optimalWeights;
    // Map API weight names to UI input IDs
    const mapping = {
        'weight-sos': weights.sos,
        'weight-trb': weights.trb,
        'weight-to': weights.to,
        'weight-eff': weights.efficiency,
        'weight-momentum': weights.momentum,
        'weight-ft': weights.ft,
        'weight-def-premium': weights.def_premium,
        'weight-intuition-factor': weights.intuition_factor_weight,
        'weight-composure-index-weight': weights.composure_index_weight,
        'weight-upset-delta-weight': weights.upset_delta_weight
    };

    for (const [id, val] of Object.entries(mapping)) {
        if (val === undefined) continue;
        const slider = document.getElementById(id);
        const statName = id.replace('weight-', '');
        const numInput = document.getElementById('num-' + statName);
        const valLabel = document.getElementById('val-' + statName);

        if (slider) slider.value = val;
        if (numInput) numInput.value = val;
        if (valLabel) valLabel.textContent = val;
    }
    runSimulation();
}

function applyWeights(weights) {
    // Map internal key names to UI weight IDs
    const mapping = {
        'weight-eff': weights.efficiency,
        'weight-sos': weights.sos,
        'weight-trb': weights.trb,
        'weight-momentum': weights.momentum,
        'weight-intuition-factor': weights.intuition_factor_weight,
        'weight-composure-index-weight': weights.composure_index_weight,
        'weight-upset-delta-weight': weights.upset_delta_weight
    };

    for (const [id, val] of Object.entries(mapping)) {
        if (val === undefined) continue;
        const slider = document.getElementById(id);
        const statName = id.replace('weight-', '');
        const numInput = document.getElementById('num-' + statName);
        const valLabel = document.getElementById('val-' + statName);

        if (slider) {
            slider.value = val;
            // Trigger input event to update color/glow if any
            slider.dispatchEvent(new Event('input'));
        }
        if (numInput) numInput.value = val;
        if (valLabel) valLabel.textContent = val;
    }
}

function toggleLock(region, round, teamName) {
    if (region === 'final_four' || region === 'championship') {
        if (appState.locks[region][teamName]) {
            delete appState.locks[region][teamName];
        } else {
            appState.locks[region] = { [teamName]: true };
        }
    } else {
        if (!appState.locks.regions[region]) appState.locks.regions[region] = {};
        if (!appState.locks.regions[region][round]) appState.locks.regions[region][round] = {};
        
        if (appState.locks.regions[region][round][teamName]) {
            delete appState.locks.regions[region][round][teamName];
        } else {
            appState.locks.regions[region][round][teamName] = true;
        }
    }
    runSimulation();
}

function isLocked(region, round, teamName) {
    if (region === 'final_four' || region === 'championship') {
        return !!(appState.locks[region] && appState.locks[region][teamName]);
    }
    return !!(appState.locks.regions[region] && 
              appState.locks.regions[region][round] && 
              appState.locks.regions[region][round][teamName]);
}

// --- API Calls ---

async function initWeights() {
    try {
        const response = await fetch('/api/weights/optimal');
        const weights = await response.json();
        appState.optimalWeights = weights;
        resetToOptimal();
    } catch (err) {
        console.error("Failed to fetch optimal weights", err);
    }
}

async function fetchTeams(year) {
    const teamList = document.getElementById('team-list');
    teamList.innerHTML = '<div class="loading-spinner"></div>';
    
    try {
        const response = await fetch(`/api/teams/${year}`);
        const teams = await response.json();
        
        teamList.innerHTML = '';
        appState.teams = {};
        teams.forEach(t => appState.teams[t.name] = t);

        teams.sort((a, b) => a.seed - b.seed).forEach(team => {
            const item = document.createElement('div');
            item.className = 'team-item';
            item.innerHTML = `
                <div class="team-info">
                    <span class="seed-num">${team.seed || '?'}</span>
                    <div>
                        <div style="font-weight: 600; font-size: 0.9rem; display: flex; align-items: center;">
                            ${team.name}
                            ${team.archetype !== 'Standard' ? `<span class="archetype-tag ${team.archetype.toLowerCase().replace(' ', '-')}">${team.archetype}</span>` : ''}
                        </div>
                        <div class="stat-tag">Eff: ${team.off_efficiency || 'N/A'} | Mom: ${team.momentum ? team.momentum.toFixed(2) : '0.00'}</div>
                    </div>
                </div>
                ${team.intuition_score ? `<div class="intuition-bubble">I: +${team.intuition_score.toFixed(1)}</div>` : ''}
            `;
            teamList.appendChild(item);
        });
    } catch (err) {
        teamList.innerHTML = `<div class="error">Failed to load teams: ${err.message}</div>`;
    }
}

async function runSimulation() {
    const bracketContainer = document.getElementById('bracket-container');
    
    const weights = {};
    const weightInputs = document.querySelectorAll('input[id^="weight-"]');
    weightInputs.forEach(input => {
        const id = input.id.replace('weight-', '').replace(/-/g, '_');
        let key = id;
        if (key === 'eff') key = 'efficiency';
        if (key === 'rust_rhythm') key = 'rust';
        
        weights[key] = parseFloat(input.value);
    });
    
    try {
        const response = await fetch(`/api/simulation/full`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                year: parseInt(appState.year),
                mode: appState.mode,
                volatility: appState.volatility / 100, // Scale to 0-1
                weights: weights,
                locks: appState.locks
            })
        });
        const data = await response.json();
        
        if (data.error) {
            bracketContainer.innerHTML = `<div class="error-card"><h3>Simulation Error</h3><p>${data.error}</p></div>`;
            return;
        }
        
        appState.currentData = data;
        renderBracketWaterfall(data);
    } catch (err) {
        console.error("Simulation failed", err);
    }
}

// --- Rendering ---

function renderBracketWaterfall(data) {
    const container = document.getElementById('bracket-container');
    container.innerHTML = '';
    
    const regionsOrder = ['East', 'West', 'South', 'Midwest'];
    
    regionsOrder.forEach(regionName => {
        const rounds = data.regions[regionName];
        if (!rounds) return;

        const regionBlock = document.createElement('div');
        regionBlock.className = 'region-block';
        regionBlock.setAttribute('data-region', regionName);
        
        // Handle Filtering
        if (appState.filter.region !== 'all' && appState.filter.region !== regionName && appState.filter.region !== 'final-four') {
            regionBlock.classList.add('hidden');
        }

        regionBlock.innerHTML = `<h3 class="region-title">${regionName}</h3>`;
        
        const displayArea = document.createElement('div');
        displayArea.className = 'region-display';
        
        const roundsContainer = document.createElement('div');
        roundsContainer.className = 'rounds-flex';
        
        rounds.forEach((r, roundIdx) => {
            const roundDiv = document.createElement('div');
            roundDiv.className = `round-column round-${r.round}`;
            
            r.matchups.forEach((m) => {
                const mCard = document.createElement('div');
                mCard.className = 'matchup-card';
                
                const prob = m.probability ? (m.probability * 100).toFixed(0) : null;
                
                mCard.appendChild(createTeamLine(regionName, r.round, m.team_a, m.seed_a, m.winner === m.team_a, prob));
                mCard.appendChild(createTeamLine(regionName, r.round, m.team_b, m.seed_b, m.winner === m.team_b, prob ? 100 - prob : null));
                
                roundDiv.appendChild(mCard);
            });
            
            roundsContainer.appendChild(roundDiv);
        });
        
        displayArea.appendChild(roundsContainer);
        regionBlock.appendChild(displayArea);
        container.appendChild(regionBlock);
    });

    renderFinalFourBlock(data.final_four, data.championship, container);
}

function renderFinalFourBlock(ff, champ, container) {
    const ffBlock = document.createElement('div');
    ffBlock.className = 'region-block final-four-block';
    if (appState.filter.region !== 'all' && appState.filter.region !== 'final-four') {
        ffBlock.classList.add('hidden');
    }
    
    ffBlock.innerHTML = `<h3>Final Four</h3>`;
    
    const displayArea = document.createElement('div');
    displayArea.className = 'region-display';
    
    const roundsContainer = document.createElement('div');
    roundsContainer.className = 'rounds-flex';
    
    // Semis
    const ffDiv = document.createElement('div');
    ffDiv.className = 'round-column round-5';
    ff.forEach(m => {
        const mDiv = document.createElement('div');
        mDiv.className = 'matchup-card';
        mDiv.appendChild(createTeamLine('final_four', 1, m.team_a, m.seed_a, m.winner === m.team_a, ''));
        mDiv.appendChild(createTeamLine('final_four', 1, m.team_b, m.seed_b, m.winner === m.team_b, ''));
        ffDiv.appendChild(mDiv);
    });
    
    // Champ
    const champDiv = document.createElement('div');
    champDiv.className = 'round-column round-6';
    const cCard = document.createElement('div');
    cCard.className = 'matchup-card';
    cCard.appendChild(createTeamLine('championship', 1, champ.team_a, champ.seed_a, champ.winner === champ.team_a, ''));
    cCard.appendChild(createTeamLine('championship', 1, champ.team_b, champ.seed_b, champ.winner === champ.team_b, ''));
    
    if (champ.winner) {
        const trophy = document.createElement('div');
        trophy.className = 'champ-winner-glow';
        trophy.style = "margin-top: 1.5rem; font-size: 1.2rem; font-weight: 800; color: var(--accent-gold); text-align: center;";
        trophy.innerHTML = `🏆 ${champ.winner} 🏆`;
        cCard.appendChild(trophy);
    }
    
    champDiv.appendChild(cCard);
    roundsContainer.appendChild(ffDiv);
    roundsContainer.appendChild(champDiv);
    displayArea.appendChild(roundsContainer);
    ffBlock.appendChild(displayArea);
    container.appendChild(ffBlock);
}

function createTeamLine(region, round, teamName, seed, isWinner, prob) {
    const line = document.createElement('div');
    const team = teamName || "TBD";
    const locked = isLocked(region, round, team) ? 'locked' : '';
    line.className = `team-line ${isWinner ? 'winner' : ''} ${locked} ${team === "TBD" ? 'tbd' : ''}`;
    
    // First Four Check (Seeding logic)
    let firstFourTag = "";
    if (seed === 11 || seed === 16) {
        // Simple heuristic: if the year is 2026 and we are in R64, these might be play-ins
        // In a real scenario, this would come from the API
        // firstFourTag = `<span class="first-four-tag">FF</span>`;
    }

    line.innerHTML = `
        <span class="team-content">
            <span class="seed">${seed || '?'}</span>
            <span class="name">${team}</span>
            ${team !== "TBD" ? `<span class="lock-icon ${locked ? 'active' : ''}" title="Lock team to advance">🔒</span>` : ''}
        </span>
        ${isWinner && prob ? `<span class="prob-tag">${prob}%</span>` : ''}
    `;

    if (team !== "TBD") {
        line.onclick = (e) => {
            if (e.target.classList.contains('lock-icon')) {
                toggleLock(region, round, team);
            } else {
                let opponent = "TBD";
                const currentRound = appState.currentData?.regions[region]?.[round-1];
                if (currentRound) {
                    const matchup = currentRound.matchups.find(m => m.team_a === team || m.team_b === team);
                    if (matchup) {
                        opponent = matchup.team_a === team ? matchup.team_b : matchup.team_a;
                    }
                }
                openMatchupModal(team, opponent);
            }
        };
    }
    return line;
}

// --- Modals ---
async function openMatchupModal(teamA, teamB) {
    if (!teamA || !teamB || teamA === "TBD" || teamB === "TBD") return;
    const modal = document.getElementById('matchup-modal');
    modal.classList.add('active');
    document.getElementById('why-list').innerHTML = '<div class="loading-spinner"></div>';
    
    const weights = {};
    document.querySelectorAll('input[id^="weight-"]').forEach(i => {
        weights[i.id.replace('weight-', '')] = i.value;
    });

    try {
        const query = new URLSearchParams({ team_a: teamA, team_b: teamB, year: appState.year, ...weights });
        const response = await fetch(`/api/matchup/detail?${query.toString()}`);
        const data = await response.json();
        renderModalData(data);
    } catch (err) {
        console.error(err);
    }
}

function renderModalData(data) {
    const probVal = data.probability !== null && data.probability !== undefined ? (data.probability * 100).toFixed(0) : '??';
    document.getElementById('modal-prob').textContent = `${probVal}% Win Prob`;
    const renderTeam = (id, team) => {
        const div = document.getElementById(id);
        const offEff = team.off_eff ? team.off_eff.toFixed(1) : 'N/A';
        const defEff = team.def_eff ? team.def_eff.toFixed(1) : 'N/A';
        const sosVal = team.sos ? team.sos.toFixed(1) : 'N/A';
        div.innerHTML = `
            <div class="name">(${team.seed || '?'}) ${team.name}</div>
            <div class="stat-bubbles">
                <div class="stat-bubble">Off: ${offEff}</div>
                <div class="stat-bubble">Def: ${defEff}</div>
                <div class="stat-bubble">SOS: ${sosVal}</div>
            </div>
        `;
    };
    renderTeam('modal-team-a', data.team_a);
    renderTeam('modal-team-b', data.team_b);
    
    const whyList = document.getElementById('why-list');
    whyList.innerHTML = data.analysis.map(item => `
        <div class="why-item">
            <strong>${item.factor}</strong>
            <p>${item.description}</p>
        </div>
    `).join('') || '<p>Dead-locked statistical profile.</p>';
}

function closeMatchupModal() {
    document.getElementById('matchup-modal').classList.remove('active');
}

// --- Initialization ---

document.addEventListener('DOMContentLoaded', () => {
    // Year Selection
    const yearSelect = document.getElementById('year-select');
    appState.year = yearSelect.value;
    fetchTeams(appState.year);
    yearSelect.addEventListener('change', (e) => {
        appState.year = e.target.value;
        fetchTeams(appState.year);
        runSimulation();
    });

    // Simulation Mode / Flows
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            appState.mode = btn.getAttribute('data-mode');
            
            if (appState.mode === 'average') {
                resetToOptimal();
            } else if (appState.mode === 'perfect') {
                applyWeights(appState.perfectWeights);
                runSimulation();
            } else {
                runSimulation();
            }
        });
    });

    // Volatility Slider
    const volSlider = document.getElementById('weight-volatility');
    const volVal = document.getElementById('val-volatility');
    if (volSlider && volVal) {
        volSlider.addEventListener('input', (e) => {
            appState.volatility = parseInt(e.target.value);
            volVal.textContent = e.target.value;
            debounceSim();
        });
    }

    // Region Filtering
    document.querySelectorAll('.region-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.region-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            appState.filter.region = btn.getAttribute('data-region');
            if (appState.currentData) renderBracketWaterfall(appState.currentData);
        });
    });

    // Collapsibles
    document.querySelectorAll('.group-header').forEach(header => {
        header.addEventListener('click', () => {
            header.parentElement.classList.toggle('expanded');
        });
    });

    // Sync Sliders
    document.querySelectorAll('input[type="range"][id^="weight-"]').forEach(slider => {
        const id = slider.id.replace('weight-', '');
        const numInput = document.getElementById(`num-${id}`);
        slider.addEventListener('input', (e) => {
            if (numInput) numInput.value = e.target.value;
            const label = document.getElementById(`val-${id}`);
            if (label) label.textContent = e.target.value;
            debounceSim();
        });
        if (numInput) {
            numInput.addEventListener('input', (e) => {
                slider.value = e.target.value;
                debounceSim();
            });
        }
    });

    document.getElementById('run-sim-btn').onclick = runSimulation;
    document.getElementById('reset-optimal').onclick = resetToOptimal;
    document.getElementById('close-modal').onclick = closeMatchupModal;

    // Toggle Panels
    const panels = {
        'settings-toggle-btn': 'settings-panel',
        'field-stats-toggle-btn': 'field-stats-panel',
        'research-lab-toggle-btn': 'research-lab-panel'
    };

    Object.entries(panels).forEach(([btnId, panelId]) => {
        const btn = document.getElementById(btnId);
        const panel = document.getElementById(panelId);
        if (btn && panel) {
            btn.onclick = () => {
                panel.classList.toggle('active');
            };
        }
    });

    // Close buttons
    document.querySelectorAll('.close-settings, .close-field, .close-research').forEach(btn => {
        btn.onclick = (e) => {
            e.target.closest('.settings-modal').classList.remove('active');
        };
    });

    // Info Icons -> Open Research Lab
    const metricDescriptions = {
        'efficiency': {
            title: 'Efficiency Index (AdjEM)',
            desc: 'The gold standard of predictability. It measures the per-possession points margin adjusted for strength of schedule. High weights here lead to a "chalkier" bracket.'
        },
        'sos': {
            title: 'Strength of Schedule',
            desc: 'A multiplier that rewards teams battle-tested in heavy conferences. High SOS prevents teams with inflated win records from overachieving.'
        }
    };

    document.querySelectorAll('.info-icon').forEach(icon => {
        icon.onclick = () => {
            const key = icon.getAttribute('data-info');
            const info = metricDescriptions[key];
            if (info) {
                const infoPanel = document.getElementById('metric-info-content');
                infoPanel.innerHTML = `<strong>${info.title}</strong><p>${info.desc}</p>`;
                document.getElementById('research-lab-panel').classList.add('active');
            }
        };
    });

    initWeights();
    fetchTeams(appState.year);
    runSimulation();
});

// Expose for debugging/subagents
window.appState = appState;
window.runSimulation = runSimulation;
window.renderBracket = renderBracketWaterfall;
