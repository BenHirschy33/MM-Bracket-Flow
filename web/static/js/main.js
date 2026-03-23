console.log("[MM-Bracket-Flow] main.js loaded v1.2");

const appState = {
    mode: 'balanced', // standard, average, balanced, perfect
    showSettings: false,
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
        efficiency_weight: 0.25,
        momentum_weight: 0.15,
        sos_weight: 0.4,
        intuition_factor_weight: 0.8,
        upset_delta_weight: 0.9,
        composure_index_weight: 0.7,
        three_point_dominance: 0.14,
        orb_weight: 0.38,
        ts_weight: 0.85,
        defense_premium: 8.9,
        rim_protection_weight: 0.12,
        defensive_grit_bias: 0.39,
        experience_weight: 10.5,
        cinderella_factor: 4.3,
        luck_regression_weight: 0.06
    },
    teams: {},
    currentData: null,
    simTimer: null,
    zoom: {
        scale: 0.45,
        x: 0,
        y: 0,
        isPanning: false,
        startX: 0,
        startY: 0
    },
    bracketData: null,
    locksInitialized: false,
    mode: 'current', // Standard Overview by default
    volatility: 0,
    year: 2026,
    activeMatchup: null, // Track currently open modal for live updates
    activeWeights: {},   // Comprehensive weight set (140+ variables)
    hasSimulated: false
};

// Expose for browser agent and HTML onclick handlers early
window.appState = appState;

// Define global handlers early so they are available for HTML onclick
const zoomToRound = (round) => {
    const vH = window.innerHeight;
    const vW = window.innerWidth;
    if (round === 'all') {
        const scaleH = (vH - 250) / 1920;
        const scaleW = (vW - 100) / 3560;
        appState.zoom.scale = Math.min(scaleH, scaleW, 0.45);
        appState.zoom.x = (vW - (3560 * appState.zoom.scale)) / 2;
        appState.zoom.y = 10;
        appState.filter.region = 'all';
    } else {
        appState.zoom.scale = 0.8;
        appState.zoom.x = 20;
        appState.zoom.y = 20;
    }
    applyZoom();
};
window.zoomToRound = zoomToRound;

window.globalZoomOverview = function (round) {
    const container = document.getElementById('bracket-container');
    if (!container) return;

    const overviewBtn = document.getElementById('overview-btn');
    if (overviewBtn) {
        if (round === 'all') overviewBtn.classList.add('active');
        else overviewBtn.classList.remove('active');
    }

    if (round === 'all') {
        const vH = window.innerHeight;
        const vW = window.innerWidth;
        // The Quad Grid is 2840px wide x 1920px high
        // Calculate scale to fit within viewport
        const scaleH = (vH - 250) / 1920;
        const scaleW = (vW - 100) / 2840;
        // Centering calculation for 5-column layout (approx 3500px total)
        appState.zoom.scale = Math.min(scaleH, scaleW, 0.48); /* Slightly tighter fit */
        appState.zoom.x = (vW - (3560 * appState.zoom.scale)) / 2;
        appState.zoom.y = 10;
    } else {
        appState.zoom.scale = 0.8;
        appState.zoom.x = 0;
        appState.zoom.y = 0;
    }

    applyZoom();

    const viewport = document.querySelector('.full-viewport');
    if (viewport) {
        viewport.scrollTo({ top: 0, left: 0, behavior: 'smooth' });
    }
}

window.globalResetUI = function () {
    console.trace('[Reset] Trace:');
    appState.locks = {
        regions: {},
        final_four: {},
        championship: {}
    };
    appState.currentData = null;
    appState.hasSimulated = false; // V4: Reset stale yellow state

    // Clear the visual bracket
    renderMMBracket();

    // Also reset any active button states
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector('.tab-btn[data-mode="custom"]')?.classList.add('active');
    appState.mode = 'custom';

    const liveIndicator = document.getElementById('live-indicator');
    if (liveIndicator) liveIndicator.style.display = 'none';

    console.log('[Reset] Simulation state and locks cleared.');
}

window.globalResetOptimal = function () {
    const weights = appState.optimalWeights || {};
    const mapping = {
        'weight-sos': weights.sos,
        'weight-trb': weights.trb,
        'weight-to': weights.to,
        'weight-eff': weights.efficiency,
        'weight-momentum': weights.momentum,
        'weight-ft': weights.ft,
        'weight-def-premium': weights.def_premium,
        'weight-intuition-factor': 0,
        'weight-composure-index-weight': 0,
        'weight-upset-delta-weight': 0
    };

    for (const [id, val] of Object.entries(mapping)) {
        const finalVal = val !== undefined ? val : 0;
        const slider = document.getElementById(id);
        const statName = id.replace('weight-', '');
        const numInput = document.getElementById('num-' + statName);
        const valLabel = document.getElementById('val-' + statName);

        if (slider) slider.value = finalVal;
        if (numInput) numInput.value = finalVal;
        if (valLabel) valLabel.textContent = finalVal;
    }

    appState.volatility = 0;
    const volSlider = document.getElementById('weight-volatility');
    if (volSlider) volSlider.value = 0;
    const volVal = document.getElementById('val-volatility');
    if (volVal) volVal.textContent = '0';

    runSimulation();
}

// --- Core Logic ---

function debounceSim() {
    if (appState.isApplyingPreset) return;
    clearTimeout(appState.simTimer);
    appState.simTimer = setTimeout(runSimulation, 400);
}

// Logic moved to window.resetToOptimal

function applyWeights(weights) {
    if (!weights) return;
    appState.isApplyingPreset = true; // Guard against slider event loops
    
    // Store the FULL object (140+ variables) for simulation use
    appState.activeWeights = { ...weights };

    // V4 Slider Mapping (subset for UI display)
    const uiMapping = {
        'weight-eff': weights.efficiency_weight || weights.efficiency || 0.86,
        'weight-three-point-dominance': weights.three_point_dominance || 0,
        'weight-orb': weights.orb_weight || 0.38,
        'weight-ts': weights.ts_weight || 0.85,
        'weight-def-premium': weights.defense_premium || 3.3,
        'weight-rim-protection': weights.rim_protection_weight || 0.44,
        'weight-defensive-grit-bias': weights.defensive_grit_bias || 0.6,
        'weight-volatility': weights.volatility || 0,
        'weight-sos': weights.sos_weight || weights.sos || 7.6,
        'weight-experience': weights.experience_weight || 7.6,
        'weight-cinderella-factor': weights.cinderella_factor || 3.6,
        'weight-luck-regression': weights.luck_regression_weight || 0.09,
        'weight-sq-margin': weights.sq_margin_weight || 1.0,
        'weight-kill-shot-momentum': weights.kill_shot_momentum_weight || 1.0,
        'weight-rim-3-volatility': weights.rim_3_volatility_weight || 1.0,
        'weight-seed': weights.seed_weight || 1.0,
        'weight-to': weights.to_weight || 1.0,
        'weight-late-round-def': weights.late_round_def_premium || 1.0,
        'weight-coach-tournament': weights.coach_tournament_weight || 1.0,
        'weight-intuition-factor': weights.intuition_factor_weight || 1.0,
        'weight-blue-blood': weights.blue_blood_bonus || 1.0,
        'weight-tempo-upset': weights.tempo_upset_weight || 1.0,
        'weight-bench-rest': weights.bench_rest_bonus || 1.0,
        'weight-trb': weights.trb_weight || 0.55,
        'weight-momentum': weights.momentum_weight || 0.12
    };

    for (const [id, val] of Object.entries(uiMapping)) {
        const slider = document.getElementById(id);
        const statName = id.replace('weight-', '');
        const numInput = document.getElementById('num-' + statName);
        const valLabel = document.getElementById('val-' + statName);

        if (slider) {
            slider.value = val;
            if (numInput) numInput.value = val;
            if (valLabel) valLabel.textContent = val;
        }
    }

    if (uiMapping['weight-volatility'] !== undefined) {
        appState.volatility = uiMapping['weight-volatility'];
    }

    setTimeout(() => { 
        appState.isApplyingPreset = false; 
        debounceSim();
    }, 100);
}

function initWeightListeners() {
    // Range -> Number & Run Sim
    document.querySelectorAll('input[type="range"][id^="weight-"]').forEach(slider => {
        const statName = slider.id.replace('weight-', '');
        const numInput = document.getElementById('num-' + statName);
        const valLabel = document.getElementById('val-' + statName);

        slider.addEventListener('input', (e) => {
            const val = e.target.value;
            if (numInput) numInput.value = val;
            if (valLabel) valLabel.textContent = val;

            if (slider.id === 'weight-volatility') {
                appState.volatility = parseFloat(val);
                const label = document.getElementById('val-volatility');
                if (label) label.textContent = val;
            }

            switchToCustom();
            debounceSim();
            if (appState.activeMatchup) debounceModalUpdate();
        });
    });

    // Number -> Range & Run Sim
    document.querySelectorAll('input[type="number"][id^="num-"]').forEach(numInput => {
        const statName = numInput.id.replace('num-', '');
        const slider = document.getElementById('weight-' + statName);

        numInput.addEventListener('input', (e) => {
            const val = parseFloat(e.target.value);
            if (slider) slider.value = val;

            if (numInput.id === 'num-volatility') {
                appState.volatility = val;
            }

            switchToCustom();
            debounceSim();
            if (appState.activeMatchup) debounceModalUpdate();
        });
    });

    // Reset Optimal Button
    const btnResetOptimal = document.getElementById('reset-optimal');
    if (btnResetOptimal) {
        btnResetOptimal.addEventListener('click', () => {
            applyWeights(appState.optimalWeights);
            renderMMBracket();
        });
    }
}

let modalUpdateTimer = null;
function debounceModalUpdate() {
    clearTimeout(modalUpdateTimer);
    modalUpdateTimer = setTimeout(() => {
        if (appState.activeMatchup) {
            updateModalLive();
        }
    }, 300);
}

function switchToCustom() {
    if (appState.mode !== 'custom') {
        appState.mode = 'custom';
        document.querySelectorAll('.tab-btn').forEach(b => {
            b.classList.toggle('active', b.getAttribute('data-mode') === 'custom');
        });
    }
}

function toggleLock(region, round, teamName) {
    if (isTeamActual(region, round, teamName)) {
        console.log(`[Lock] Skipping ${teamName} - already an actual result.`);
        return;
    }

    if (region === 'final_four' || region === 'championship') {
        if (!appState.locks[region]) appState.locks[region] = {};
        if (appState.locks[region][teamName]) {
            delete appState.locks[region][teamName];
        } else {
            // Check for opponent to clear their lock
            appState.locks[region] = { [teamName]: true };
        }
    } else {
        if (!appState.locks.regions) appState.locks.regions = {};
        if (!appState.locks.regions[region]) appState.locks.regions[region] = {};
        if (!appState.locks.regions[region][round]) appState.locks.regions[region][round] = {};

        const isCurrentlyLocked = appState.locks.regions[region][round][teamName];

        if (isCurrentlyLocked) {
            // Unlocking logic: cascade clear LOCKS
            for (let r = round; r <= 6; r++) {
                if (appState.locks.regions[region]?.[r]) {
                    delete appState.locks.regions[region][r][teamName];
                }
            }
            if (appState.locks.final_four) delete appState.locks.final_four[teamName];
            if (appState.locks.championship) delete appState.locks.championship[teamName];

            // V4: Also clear the name from subsequent SLOTS in currentData
            clearTeamFromFutureRounds(region, round, teamName);
        } else {
            // Locking logic
            const opponent = findOpponent(region, round, teamName);
            if (opponent) delete appState.locks.regions[region][round][opponent];
            appState.locks.regions[region][round][teamName] = true;
        }
    }

    // Partial Locking: Snappy UI
    if (appState.currentData) {
        propagateLocksLocally(appState.currentData, appState.locks);
        renderBracketWaterfall(appState.currentData);
    }
}

function findOpponent(region, round, teamName) {
    const currentMatchups = appState.currentData?.regions?.[region]?.[round - 1]?.matchups;
    if (currentMatchups) {
        const matchup = currentMatchups.find(m => m.team_a === teamName || m.team_b === teamName);
        if (matchup) {
            return matchup.team_a === teamName ? matchup.team_b : matchup.team_a;
        }
    }
    return null;
}

function isTeamActual(region, round, teamName) {
    // Check if the game has already happened in the backend data
    const rd = appState.bracketData?.regions?.[region]?.[round - 1];
    if (rd) {
        const m = rd.matchups.find(m => (m.team_a === teamName || m.team_b === teamName) && m.is_actual && m.winner === teamName);
        if (m) return true;
    }
    return false;
}

function clearTeamFromFutureRounds(region, round, teamName) {
    if (!appState.currentData) return;

    // Also clear winner in the current round if it was a manual lock — prevents re-propagation
    if (appState.currentData.regions[region]) {
        const currentRd = appState.currentData.regions[region][round - 1];
        if (currentRd) {
            currentRd.matchups.forEach(m => {
                if ((m.team_a === teamName || m.team_b === teamName) && m.winner === teamName && !m.is_actual) {
                    m.winner = null;
                }
            });
        }
    }

    // Clear in subsequent region rounds
    if (appState.currentData.regions[region]) {
        for (let r = round; r < 4; r++) {
            const nextRd = appState.currentData.regions[region][r];
            if (nextRd) {
                nextRd.matchups.forEach(m => {
                    if (m.team_a === teamName) { m.team_a = "TBD"; m.seed_a = null; m.winner = null; }
                    if (m.team_b === teamName) { m.team_b = "TBD"; m.seed_b = null; m.winner = null; }
                    if (m.winner === teamName) m.winner = null;
                });
            }
        }
    }

    // Clear in Final Four
    if (appState.currentData.final_four) {
        appState.currentData.final_four.forEach(m => {
            if (m.team_a === teamName) { m.team_a = "TBD"; m.seed_a = null; m.winner = null; }
            if (m.team_b === teamName) { m.team_b = "TBD"; m.seed_b = null; m.winner = null; }
            if (m.winner === teamName) m.winner = null;
        });
    }

    // Clear in Championship
    if (appState.currentData.championship) {
        const c = appState.currentData.championship;
        if (c.team_a === teamName) { c.team_a = "TBD"; c.seed_a = null; c.winner = null; }
        if (c.team_b === teamName) { c.team_b = "TBD"; c.seed_b = null; c.winner = null; }
        if (c.winner === teamName) c.winner = null;
    }
}

function propagateLocksLocally(data, locks) {
    if (!data) return;

    const regions = ['East', 'South', 'Midwest', 'West'];
    regions.forEach(region => {
        if (!data.regions[region]) return;

        for (let r = 1; r <= 4; r++) {
            const rd = data.regions[region][r - 1];
            if (!rd) continue;

            rd.matchups.forEach((m, idx) => {
                // Priority 1: Actual Results (Green)
                if (m.is_actual && m.winner) {
                    // Winner is already set by backend for actual results
                }
                // Priority 2: Manual Locks (Red)
                else {
                    const lockedInThisRound = locks.regions?.[region]?.[r];
                    if (lockedInThisRound) {
                        if (lockedInThisRound[m.team_a]) m.winner = m.team_a;
                        else if (lockedInThisRound[m.team_b]) m.winner = m.team_b;
                    }
                }

                // Propagate forward locally
                if (m.winner && r < 4) {
                    const nextRd = data.regions[region][r];
                    if (nextRd) {
                        const nextM = nextRd.matchups[Math.floor(idx / 2)];
                        const isTeamA = idx % 2 === 0;
                        if (isTeamA) {
                            nextM.team_a = m.winner;
                            nextM.seed_a = m.winner === m.team_a ? m.seed_a : m.seed_b;
                        } else {
                            nextM.team_b = m.winner;
                            nextM.seed_b = m.winner === m.team_a ? m.seed_a : m.seed_b;
                        }
                    }
                }
            });
        }
    });

    // F4 propagation
    if (data.final_four) {
        data.final_four.forEach((m, idx) => {
            const r = 5;
            // Priority 1: Actual
            if (m.is_actual && m.winner) { }
            // Priority 2: Lock
            else {
                const lockedInThisRound = locks.final_four;
                if (lockedInThisRound) {
                    if (lockedInThisRound[m.team_a]) m.winner = m.team_a;
                    else if (lockedInThisRound[m.team_b]) m.winner = m.team_b;
                }
            }

            if (m.winner && data.championship) {
                const isTeamA = idx === 0;
                if (isTeamA) {
                    data.championship.team_a = m.winner;
                    data.championship.seed_a = m.winner === m.team_a ? m.seed_a : m.seed_b;
                } else {
                    data.championship.team_b = m.winner;
                    data.championship.seed_b = m.winner === m.team_a ? m.seed_a : m.seed_b;
                }
            }
        });
    }

    // Champ propagation
    if (data.championship) {
        // Priority 1: Actual
        if (data.championship.is_actual && data.championship.winner) { }
        // Priority 2: Lock
        else {
            const lockedInThisRound = locks.championship;
            if (lockedInThisRound) {
                if (lockedInThisRound[data.championship.team_a]) data.championship.winner = data.championship.team_a;
                else if (lockedInThisRound[data.championship.team_b]) data.championship.winner = data.championship.team_b;
            }
        }
    }
}

function isLocked(region, round, team) {
    if (region === 'final_four') return !!appState.locks.final_four[team];
    if (region === 'championship') return !!appState.locks.championship[team];
    return !!appState.locks.regions[region]?.[round]?.[team];
}

async function fetchBracketData(forceRefresh = false) {
    if (appState.bracketData && !forceRefresh) return appState.bracketData;

    try {
        const response = await fetch(`/api/bracket/${appState.year}`);
        const data = await response.json();

        if (data.error) {
            console.error("Bracket load error:", data.error);
            return null;
        }

        appState.bracketData = data;

        // Initialize locks only once from backend actual results
        if (!appState.locksInitialized || forceRefresh) {
            for (const [reg, rounds] of Object.entries(data.regions)) {
                rounds.forEach(r => {
                    r.matchups.forEach(m => {
                        // V4: Only lock if they actually WON this specific game
                        if (m.is_actual && m.winner) {
                            if (!appState.locks.regions[reg]) appState.locks.regions[reg] = {};
                            if (!appState.locks.regions[reg][r.round]) appState.locks.regions[reg][r.round] = {};
                            appState.locks.regions[reg][r.round][m.winner] = true;
                        }
                    });
                });
            }
            if (data.final_four) {
                data.final_four.forEach(m => {
                    if (m.is_actual && m.winner) {
                        if (!appState.locks.final_four) appState.locks.final_four = {};
                        appState.locks.final_four[m.winner] = true;
                    }
                });
            }
            if (data.championship && data.championship.is_actual && data.championship.winner) {
                if (!appState.locks.championship) appState.locks.championship = {};
                appState.locks.championship[data.championship.winner] = true;
            }
            appState.locksInitialized = true;
        }
        return data;
    } catch (err) {
        console.error("Failed to fetch bracket data", err);
        return null;
    }
}

/**
 * V4: Merges 'is_actual' truth from ground-truth bracketData into simulation results.
 * This prevents Green games from turning Red after simulation.
 */
function stampActualFlags(simData, bracketData) {
    if (!simData || !bracketData) return;

    // Helper for a single round
    const stampRound = (simRoundMatchups, bracketRoundMatchups) => {
        if (!simRoundMatchups || !bracketRoundMatchups) return;
        simRoundMatchups.forEach((simM, idx) => {
            const bracketM = bracketRoundMatchups[idx];
            if (bracketM && bracketM.is_actual) {
                simM.is_actual = true;
                // Ensure winner is synced if ground truth exists
                if (bracketM.winner) simM.winner = bracketM.winner;
            }
        });
    };

    // 1. Regions
    for (const regName in simData.regions) {
        const simRounds = simData.regions[regName];
        const bracketRounds = bracketData.regions[regName];
        if (!simRounds || !bracketRounds) continue;
        simRounds.forEach((simR, idx) => {
            const bracketR = bracketRounds[idx];
            if (bracketR) stampRound(simR.matchups, bracketR.matchups);
        });
    }

    // 2. Center Stage
    stampRound(simData.final_four, bracketData.final_four);
    if (simData.championship && bracketData.championship && bracketData.championship.is_actual) {
        simData.championship.is_actual = true;
        if (bracketData.championship.winner) simData.championship.winner = bracketData.championship.winner;
    }
}

async function renderMMBracket() {
    console.log("[MM-Bracket-Flow] Executing renderMMBracket");
    const data = await fetchBracketData();
    if (!data) return;

    // Transform into a TBD-filled structure for rendering
    const initialData = {
        regions: {},
        final_four: null,
        championship: null
    };

    for (const [reg, rounds] of Object.entries(data.regions)) {
        initialData.regions[reg] = rounds.map(r => ({
            round: r.round,
            matchups: r.matchups.map(m => ({ ...m }))
        }));
    }

    if (data.final_four) {
        initialData.final_four = data.final_four.map(m => ({ ...m }));
    }

    if (data.championship) {
        initialData.championship = { ...data.championship };
    }

    appState.currentData = initialData;
    renderBracketWaterfall(initialData);

    // Ensure we zoom out to overview on first load
    setTimeout(() => {
        if (typeof globalZoomOverview === 'function') {
            globalZoomOverview('all');
        } else if (typeof zoomToRound === 'function') {
            zoomToRound('all');
        }
    }, 300);
}

// --- API Calls ---

async function initWeights() {
    try {
        // Fetch preset profiles in parallel
        const [avgRes, champRes, balancedRes] = await Promise.all([
            fetch('/api/weights/preset?mode=avg'),
            fetch('/api/weights/preset?mode=champion'),
            fetch('/api/weights/preset?mode=balanced')
        ]);
        const avgData = await avgRes.json();
        const champData = await champRes.json();
        const balancedData = await balancedRes.json();

        // Store the full weight dicts for each mode
        appState.optimalWeights = avgData.weights || {};
        appState.perfectWeights = champData.weights || {};
        appState.balancedWeights = balancedData.weights || {};

        // V4: Initialize activeWeights with current mode
        const initialWeights = (appState.mode === 'perfect') ? appState.perfectWeights : 
                              (appState.mode === 'average') ? appState.optimalWeights : 
                               appState.balancedWeights;
        appState.activeWeights = { ...initialWeights };

        console.log('[Weights] Loaded presets. System monitoring 140+ variables.');

        // V4: Ensure UI sliders reflect the initial mode on load
        if (appState.mode === 'average' || appState.mode === 'perfect' || appState.mode === 'balanced') {
            applyWeights(appState.activeWeights);
        }
    } catch (err) {
        console.error("Failed to fetch preset weights", err);
    }
}

async function fetchTeams(year) {
    const teamList = document.getElementById('team-list');
    if (teamList) teamList.innerHTML = '<div class="loading-spinner"></div>';

    try {
        const response = await fetch(`/api/teams/${year}`);
        const teams = await response.json();

        if (teamList) teamList.innerHTML = '';
        appState.teams = {};
        teams.forEach(t => appState.teams[t.name] = t);

        if (teamList) {
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
                            <div class="stat-tag">Eff: ${team.off_efficiency || 'N/A'}</div>
                        </div>
                    </div>
                `;
                teamList.appendChild(item);
            });
        }
    } catch (err) {
        if (teamList) teamList.innerHTML = `<div class="error">Failed to load teams: ${err.message}</div>`;
    }
}

async function runSimulation() {
    // Sync sliders to activeWeights (allows user overrides)
    const weightInputs = document.querySelectorAll('input[id^="weight-"]');
    weightInputs.forEach(input => {
        const id = input.id.replace('weight-', '').replace(/-/g, '_');
        let key = id;
        if (key === 'eff') key = 'efficiency_weight'; // Use standard config names
        if (!key.endsWith('_weight') && !['three_point_dominance', 'defensive_grit_bias', 'volatility', 'cinderella_factor', 'defense_premium'].includes(key)) {
            // Append _weight if missing and not a direct name
            if (appState.activeWeights[key + '_weight'] !== undefined) key += '_weight';
        }
        appState.activeWeights[key] = parseFloat(input.value);
    });

    try {
        const useLive = (appState.mode === 'current');
        const response = await fetch(`/api/simulation/full`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                year: parseInt(appState.year),
                mode: 'monte_carlo',
                volatility: appState.volatility / 100,
                weights: appState.activeWeights, // Send the full merged set
                locks: appState.locks,
                use_live_results: useLive
            })
        });
        const data = await response.json();
        appState.hasSimulated = true;

        // V4: Simulation Overrides Logic
        // Enforce actual results (Green) and locks (Red) over simulation
        stampActualFlags(data, appState.bracketData);
        propagateLocksLocally(data, appState.locks);

        console.log("[UI] Simulation complete. Applying new bracket results.", data);
        renderBracketWaterfall(data);

        // Update Live Indicator
        const liveIndicator = document.getElementById('live-indicator');
        if (liveIndicator) {
            liveIndicator.style.display = useLive ? 'flex' : 'none';
        }
    } catch (err) {
        console.error("Simulation failed", err);
    }
}

/**
 * Auto-fills the bracket deterministically based on current weights.
 * Used when switching modes (Balanced/Average/Perfect) — no randomness.
 */
async function autoFillBracket() {
    const weights = {};
    document.querySelectorAll('input[id^="weight-"]').forEach(input => {
        const id = input.id.replace('weight-', '').replace(/-/g, '_');
        weights[id === 'eff' ? 'efficiency' : id] = parseFloat(input.value);
    });
    try {
        const response = await fetch('/api/simulation/full', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                year: parseInt(appState.year),
                mode: 'deterministic',  // Always pick the favorite — no randomness
                volatility: 0,
                weights,
                locks: appState.locks,
                use_live_results: false
            })
        });
        const data = await response.json();
        stampActualFlags(data, appState.bracketData);
        propagateLocksLocally(data, appState.locks);
        appState.hasSimulated = true;
        renderBracketWaterfall(data);
    } catch (err) {
        console.error('Auto-fill failed', err);
    }
}

// --- Rendering ---

function renderBracketWaterfall(data) {
    const container = document.getElementById('bracket-container');
    if (!container) return;
    container.innerHTML = '';

    const quadGrid = document.createElement('div');
    quadGrid.className = 'quad-grid';
    container.appendChild(quadGrid);

    // Regions Placement Mapping
    const regionConfigs = {
        'East': { col: 1, row: 1, mirrored: false },
        'South': { col: 1, row: 2, mirrored: false },
        'West': { col: 3, row: 1, mirrored: true },
        'Midwest': { col: 3, row: 2, mirrored: true }
    };

    const regionsOrder = ['East', 'South', 'West', 'Midwest'];

    // Create Center Stage
    const centerStage = document.createElement('div');
    centerStage.className = 'center-stage';
    quadGrid.appendChild(centerStage);

    // Populate Regional Rounds (1-4)
    regionsOrder.forEach((regionName) => {
        const config = regionConfigs[regionName];
        let rounds = data.regions[regionName];
        if (!rounds) return;

        // Ensure rounds have the .round property attached for UI rendering
        if (Array.isArray(rounds)) {
            rounds = rounds.map((r, i) => r.round ? r : { round: i + 1, matchups: r.matchups || r });
        }

        const regContainer = document.createElement('div');
        regContainer.className = `region-container ${config.mirrored ? 'mirrored' : ''}`;
        regContainer.style.gridColumn = config.col;
        regContainer.style.gridRow = config.row;
        quadGrid.appendChild(regContainer);

        // Region Label
        const label = document.createElement('div');
        label.className = 'region-label-v2';
        label.style.pointerEvents = 'none';
        if (config.mirrored) label.style.right = '2rem'; else label.style.left = '2rem';
        label.textContent = regionName;
        regContainer.appendChild(label);

        // Create 4 columns for this region
        const columns = [];
        for (let i = 1; i <= 4; i++) {
            const col = document.createElement('div');
            col.className = `round-column round-${i}`;
            columns.push(col);
            regContainer.appendChild(col);
        }

        rounds.forEach((r) => {
            const col = columns[r.round - 1];
            if (!col) return;
            const span = Math.pow(2, r.round);

            r.matchups.forEach((m, mIdx) => {
                const mCard = document.createElement('div');
                mCard.className = 'matchup-card';

                // Add top/bottom class for connectors
                const isTop = (mIdx % 2 === 0);
                mCard.classList.add(isTop ? 'm-top' : 'm-bottom');

                const span = Math.pow(2, r.round);
                const start = (mIdx * span) + 1;
                mCard.style.gridRow = `${start} / span ${span}`;
                mCard.style.setProperty('--span-height', `${span * 60}px`);

                const vol = appState.volatility / 100;
                let probA = m.probability || 0.5;
                let blendedA = ((1.0 - vol) * probA) + (vol * 0.5);

                const isA = (m.team_a === m.winner);
                const isActualA = isA && m.is_actual;
                const isActualB = !isA && m.is_actual;

                mCard.appendChild(createTeamLine(regionName, r.round, m.team_a, m.seed_a, isA, isA ? m.probability : null, m.is_actual));
                mCard.appendChild(createTeamLine(regionName, r.round, m.team_b, m.seed_b, !isA, (!isA && m.probability != null) ? (1 - m.probability) : null, m.is_actual));

                mCard.style.cursor = 'pointer';

                // V4: Explicit Matchup Intelligence Button
                const infoBtn = document.createElement('div');
                infoBtn.className = 'matchup-info-btn';
                infoBtn.innerHTML = '💡';
                infoBtn.title = 'View Matchup Intelligence';
                infoBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    openMatchupModal(m);
                });
                mCard.appendChild(infoBtn);

                col.appendChild(mCard);
            });
        });
    });

    // Populate Center Stage (Final Four & Championship)
    if (data.final_four) {
        const leftF4 = document.createElement('div');
        leftF4.className = 'ff-games-stack ff-left';
        const rightF4 = document.createElement('div');
        rightF4.className = 'ff-games-stack ff-right';

        // Create Championship centerpiece
        const champContainer = document.createElement('div');
        champContainer.className = 'hero-champ-container';

        // Order: Left FF -> Champ -> Right FF
        centerStage.appendChild(leftF4);
        centerStage.appendChild(champContainer);
        centerStage.appendChild(rightF4);

        data.final_four.forEach((m, idx) => {
            const mCard = document.createElement('div');
            mCard.className = `matchup-card ff-matchup`;
            mCard.style.width = '280px';

            const isA = (m.team_a === m.winner);
            const isActualA = isA && m.is_actual;
            const isActualB = !isA && m.is_actual;

            mCard.appendChild(createTeamLine('final_four', 5, m.team_a, m.seed_a, isA, isA ? m.probability : null, isActualA));
            mCard.appendChild(createTeamLine('final_four', 5, m.team_b, m.seed_b, !isA, (!isA && m.probability != null) ? (1 - m.probability) : null, isActualB));

            mCard.style.cursor = 'default';

            // V4: Info Button for FF
            const infoBtn = document.createElement('div');
            infoBtn.className = 'matchup-info-btn';
            infoBtn.innerHTML = '💡';
            infoBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                openMatchupModal(m);
            });
            mCard.appendChild(infoBtn);

            if (idx === 0) leftF4.appendChild(mCard); else rightF4.appendChild(mCard);
        });

        if (data.championship) {
            const m = data.championship;
            const mCard = document.createElement('div');
            mCard.className = 'matchup-card championship-box';
            mCard.style.width = '320px';

            const isA = (m.team_a === m.winner);
            const isActualA = isA && m.is_actual;
            const isActualB = !isA && m.is_actual;

            mCard.appendChild(createTeamLine('championship', 6, m.team_a, m.seed_a, isA, isA ? m.probability : null, isActualA));
            mCard.appendChild(createTeamLine('championship', 6, m.team_b, m.seed_b, !isA, (!isA && m.probability != null) ? (1 - m.probability) : null, isActualB));

            mCard.style.cursor = 'default';

            // V4: Info Button for Champ
            const infoBtn = document.createElement('div');
            infoBtn.className = 'matchup-info-btn';
            infoBtn.innerHTML = '💡';
            infoBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                openMatchupModal(m);
            });
            mCard.appendChild(infoBtn);

            champContainer.appendChild(mCard);
        }
    }

    if (appState.filter.region !== 'all') {
        zoomToRound('all');
    }
}

function createTeamLine(region, round, teamName, seed, isWinner, prob, isActual = false) {
    const line = document.createElement('div');
    const team = teamName || "TBD";
    // V4: Don't apply locked class if this is an actual result — actual-result CSS takes priority
    const userLocked = !isActual && isLocked(region, round, team);
    const lockedClass = userLocked ? 'locked' : '';
    // Simulated winner: the team is the winner but it wasn't manually locked or an actual result
    // V4: Only show yellow if simulation has actually run
    const isSimulatedWinner = appState.hasSimulated && isWinner && !userLocked && !isActual && team !== "TBD";
    const isActualWinner = isActual && isWinner;
    line.className = `team-line ${isWinner ? 'winner' : ''} ${lockedClass} ${isSimulatedWinner ? 'sim-winner' : ''} ${team === "TBD" ? 'tbd' : ''} ${isActualWinner ? 'actual-result' : ''}`;

    let displayName = team.replace(/^\d+\s+/, '');
    const displaySeed = (team === "TBD") ? '' : (seed || '?');

    line.style.cursor = isActual ? 'default' : 'pointer';
    if (isActual) line.style.pointerEvents = 'none'; // Disable clicks for BOTH winner and loser

    line.innerHTML = `
        <span class="team-content">
            <span class="seed">${displaySeed}</span>
            <span class="name">${displayName}</span>
            ${team !== "TBD" ? `<span class="lock-icon ${(lockedClass || isActualWinner) ? 'active' : ''} ${isActualWinner ? 'is-actual' : ''}" title="${isActual ? 'Actual Tournament Result' : 'Lock team to advance'}">🔒</span>` : ''}
        </span>
        ${isWinner && prob ? `<span class="prob-tag">${(parseFloat(prob) * 100).toFixed(0)}%</span>` : ''}
    `;

    if (team !== "TBD") {
        line.addEventListener('click', async (e) => {
            e.stopPropagation(); // Prevent matchup-card from opening modal

            // Prioritize Actual Results: If it's actual, don't allow toggling manual locks
            if (isActual) {
                console.log("[UX] Actual result clicked - cannot toggle manual lock.");
                return;
            }

            if (e.target.classList.contains('lock-icon')) {
                toggleLock(region, round, team);
            } else {
                // V4: Rapid Advance Promotion
                // If it's already locked in this round, lock it in the NEXT round too
                if (userLocked) {
                    toggleLockPromotion(region, round, team);
                } else {
                    toggleLock(region, round, team);
                }
            }
        });
    }
    return line;
}

// --- Navigation & UX ---

// Navigation & UX logic moved to top for global availability

// --- Simulation Control ---

// Reset logic moved to top for global availability

function applyZoom() {
    const container = document.getElementById('bracket-container');
    const proxy = document.getElementById('zoom-container');
    const viewport = document.querySelector('.full-viewport');
    if (!container || !proxy || !viewport) return;

    // Clamp movement
    const vW = window.innerWidth;
    const vH = window.innerHeight;
    const gridW = 3560 * appState.zoom.scale; /* Updated for gaps */
    const gridH = 1920 * appState.zoom.scale;

    // Minimal bleed for tight focus
    const margin = 50;
    const minX = vW - gridW - margin;
    const maxX = margin;
    const minY = vH - gridH - margin;
    const maxY = margin;

    appState.zoom.x = Math.min(Math.max(appState.zoom.x, minX), maxX);
    appState.zoom.y = Math.min(Math.max(appState.zoom.y, minY), maxY);

    // Scale the visual
    container.style.transform = `translate(${appState.zoom.x}px, ${appState.zoom.y}px) scale(${appState.zoom.scale})`;

    // Precise bounds
    proxy.style.width = (3560 * appState.zoom.scale + 100) + "px";
    proxy.style.height = (1920 * appState.zoom.scale + 100) + "px";
}

function initInteractiveZoom() {
    const viewport = document.querySelector('.full-viewport');
    if (!viewport) return;

    viewport.addEventListener('wheel', (e) => {
        if (!e.ctrlKey && !e.metaKey) return;

        e.preventDefault();
        const delta = e.deltaY;
        const zoomSpeed = 0.001;

        // Capture mouse position for potentially centering zoom later
        appState.zoom.scale = Math.min(Math.max(0.1, appState.zoom.scale - delta * zoomSpeed), 3.0);
        applyZoom();
    }, { passive: false });

    // Panning is now primarily native via overflow:auto
    // Removing mousedown/mousemove logic to prevent conflicts
}

async function openMatchupModal(matchup) {
    const modal = document.getElementById('matchup-modal');
    if (!modal) return;

    appState.activeMatchup = matchup; // Store for live updates

    const teamA = appState.teams[matchup.team_a] || { name: matchup.team_a, seed: matchup.seed_a };
    const teamB = appState.teams[matchup.team_b] || { name: matchup.team_b, seed: matchup.seed_b };

    // Populate Modal Content
    const title = modal.querySelector('h2') || modal.querySelector('.modal-title');
    if (title) title.innerHTML = `<span style="color:var(--accent-gold)">${teamA.name}</span> vs <span style="color:var(--accent-gold)">${teamB.name}</span>`;

    const probBadge = document.getElementById('modal-prob');

    // Guard: if either team is TBD, show a placeholder and open modal
    if (!teamA.name || teamA.name === 'TBD' || !teamB.name || teamB.name === 'TBD') {
        if (probBadge) probBadge.textContent = 'N/A';
        const whyContent = document.getElementById('modal-why-content');
        if (whyContent) whyContent.innerHTML = '<p>This matchup has not been determined yet. Lock teams or run the simulation to populate it.</p>';
        const metricsTable = document.getElementById('modal-metrics-table');
        if (metricsTable) metricsTable.innerHTML = '';
        modal.classList.add('active');
        return;
    }

    // For actual results that have already been played, use the simulation's stored probability.
    // Only recalculate if we have both real teams and a live sim hasn't provided a probability.
    let simProbA = matchup.probability || null;

    // Declare blendedA at outer scope with a safe default
    let blendedA = simProbA
        ? ((1.0 - appState.volatility / 100) * simProbA) + ((appState.volatility / 100) * 0.5)
        : 0.5;

    // Show the sim probability immediately (avoids the flash of a wrong number)
    if (probBadge) {
        if (matchup.is_actual) {
            probBadge.textContent = `Actual Result`;
        } else if (simProbA !== null) {
            const edgeText = `(Edge: ${(blendedA * 100).toFixed(1)}%)`;
            probBadge.innerHTML = `Simulated Win Rate: <span style="color:var(--accent-gold)">${(simProbA * 100).toFixed(0)}%</span> <span style="font-size:0.8em; opacity:0.7">${edgeText}</span>`;
        } else {
            probBadge.textContent = 'Calculating Edge...';
        }
    }

    // Fetch live probability based on current sliders — only update if NOT an actual game
    const weights = {};
    document.querySelectorAll('input[id^="weight-"]').forEach(input => {
        const id = input.id.replace('weight-', '').replace(/-/g, '_');
        weights[id === 'eff' ? 'efficiency' : id] = parseFloat(input.value);
    });

    if (!matchup.is_actual) {
        try {
                const response = await fetch(`/api/matchup/detail`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        year: parseInt(appState.year),
                        team_a: teamA.name,
                        team_b: teamB.name,
                        weights: appState.activeWeights,
                        volatility: appState.volatility / 100
                    })
                });
                const detailData = await response.json();
                
                if (detailData && !detailData.error) {
                    const liveProb = detailData.probability;
                    const liveBlended = ((1.0 - appState.volatility / 100) * liveProb) + ((appState.volatility / 100) * 0.5);
                    const simRate = (simProbA !== null) ? (simProbA * 100).toFixed(0) : (liveProb * 100).toFixed(0);
                    const edgeText = `(Edge: ${(liveBlended * 100).toFixed(1)}%)`;
                    
                    if (probBadge) {
                        probBadge.innerHTML = `Win Rate: <span style="color:var(--accent-gold)">${simRate}%</span> <span style="font-size:0.85em; opacity:0.8; margin-left:8px;">${edgeText}</span>`;
                    }

                    if (favorBanner) {
                        const favorite = liveBlended > 0.5 ? teamA : teamB;
                        const favEdge = Math.abs(liveBlended * 100).toFixed(1);
                        favorBanner.innerHTML = `PROJECTED WINNER: <span style="color:var(--accent-gold); font-weight:800; margin-left:8px;">${favorite.name.toUpperCase()}</span> (${favEdge}% Advantage)`;
                        favorBanner.style.display = 'flex'; // Use flex for trophy alignment
                        favorBanner.className = 'projected-winner-banner' + (liveBlended > 0.5 ? ' team-a-fav' : ' team-b-fav');
                    }
                    updateModalIntelligence(detailData, teamA, teamB, liveBlended);
                }
            } catch (err) {
                console.error("Failed to fetch matchup detail", err);
            }
        }

    // Why Analysis (Dynamic summary)
    const whyContent = document.getElementById('modal-why-content');
    if (whyContent) {
        const favorite = blendedA > 0.5 ? teamA : teamB;
        const underdog = blendedA > 0.5 ? teamB : teamA;
        const confText = favorite.is_power_conf ? "power conference powerhouse" : "disciplined contender";

        let keyFactorText = `Verticality and tempo control. ${teamA.name}'s efficiency at ${teamA.off_efficiency?.toFixed(1) || 'N/A'} vs ${teamB.name}'s ${teamB.off_efficiency?.toFixed(1) || 'N/A'} is the primary driver of this projection.`;

        const ksA = (teamA.adj_off_sq - teamA.adj_def_sq) || 0;
        const ksB = (teamB.adj_off_sq - teamB.adj_def_sq) || 0;
        if (Math.abs(ksA - ksB) > 3.0) {
            keyFactorText = `ShotQuality Delta. ${ksA > ksB ? teamA.name : teamB.name} creates significantly higher-quality looks, giving them a structural advantage in the possession-based model.`;
        } else if (Math.abs((teamA.recent_form || 0) - (teamB.recent_form || 0)) > 2.0) {
            keyFactorText = `Late-Season Surge. ${teamA.recent_form > teamB.recent_form ? teamA.name : teamB.name} enters the tournament with superior recent momentum (+${Math.abs(teamA.recent_form - teamB.recent_form).toFixed(1)} Net Rating delta).`;
        } else if (Math.abs((teamA.kill_shots_scored - teamA.kill_shots_conceded) - (teamB.kill_shots_scored - teamB.kill_shots_conceded)) > 2.0) {
            keyFactorText = `Spurtability Trigger. ${(teamA.kill_shots_scored - teamA.kill_shots_conceded) > (teamB.kill_shots_scored - teamB.kill_shots_conceded) ? teamA.name : teamB.name} is analytically more prone to game-breaking 10-0 scoring runs.`;
        }

        whyContent.innerHTML = `
            <p><strong>Scenario Intelligence:</strong> ${favorite.name} enters as the statistical favorite with a ${confText} profile.
            The simulation indicates a ${(Math.abs(blendedA - 0.5) * 200).toFixed(2)}% efficiency advantage in our calibrated Monte Carlo resolution loop.</p>
            <p style="margin-top:0.5rem"><strong>Key Factor:</strong> ${keyFactorText}</p>
        `;
    }

    // Metric Comparison Table
    const metricsTable = document.getElementById('modal-metrics-table');
    if (metricsTable) {
        const metrics = [
            { name: "Seed", a: teamA.seed || '?', b: teamB.seed || '?' },
            { name: "Offensive Eff", a: teamA.off_efficiency?.toFixed(1) || teamA.off_eff?.toFixed(1) || 'N/A', b: teamB.off_efficiency?.toFixed(1) || teamB.off_eff?.toFixed(1) || 'N/A' },
            { name: "Defensive Eff", a: teamA.def_efficiency?.toFixed(1) || teamA.def_eff?.toFixed(1) || 'N/A', b: teamB.def_efficiency?.toFixed(1) || teamB.def_eff?.toFixed(1) || 'N/A' },
            { name: "Adj ShotQuality", a: (teamA.adj_off_sq - teamA.adj_def_sq)?.toFixed(1) || 'N/A', b: (teamB.adj_off_sq - teamB.adj_def_sq)?.toFixed(1) || 'N/A' },
            { name: "Kill Shots (Net)", a: (teamA.kill_shots_scored - teamA.kill_shots_conceded)?.toFixed(1) || (teamA.ks_scored - teamA.ks_conceded)?.toFixed(1) || '0.0', b: (teamB.kill_shots_scored - teamB.kill_shots_conceded)?.toFixed(1) || (teamB.ks_scored - teamB.ks_conceded)?.toFixed(1) || '0.0' },
            { name: "Recent Form", a: (teamA.recent_form > 0 ? '+' : '') + (teamA.recent_form?.toFixed(1) || '0.0'), b: (teamB.recent_form > 0 ? '+' : '') + (teamB.recent_form?.toFixed(1) || '0.0') },
            { name: "Rim & 3 Rate", a: ((teamA.rim_3_rate || 0) * 100).toFixed(0) + '%', b: ((teamB.rim_3_rate || 0) * 100).toFixed(0) + '%' },
            { name: "Adj Tempo", a: teamA.pace?.toFixed(1) || 'N/A', b: teamB.pace?.toFixed(1) || 'N/A' },
            { name: "Season Luck", a: (teamA.luck > 0 ? '+' : '') + (teamA.luck?.toFixed(3) || '0.000'), b: (teamB.luck > 0 ? '+' : '') + (teamB.luck?.toFixed(3) || '0.000') }
        ];

        metricsTable.innerHTML = metrics.map(m => {
            const valA = parseFloat(m.a);
            const valB = parseFloat(m.b);
            let isBetterA = false;
            let isBetterB = false;

            if (m.name === "Seed" || m.name === "Defensive Eff") {
                // Lower is better for Seed and Defensive Efficiency
                isBetterA = valA < valB;
                isBetterB = valB < valA;
            } else if (m.name === "Adj Tempo" || m.name === "Season Luck") {
                // Keep neutral or high highlight if preferred, but usually higher is highlighted for others
                isBetterA = valA > valB;
                isBetterB = valB > valA;
            } else {
                isBetterA = valA > valB;
                isBetterB = valB > valA;
            }

            return `
                <div class="metric-row">
                    <span class="metric-name">${m.name}</span>
                    <span class="metric-val" style="color:${isBetterA ? 'var(--accent-gold)' : 'inherit'}">${m.a}</span>
                    <span class="metric-val" style="color:${isBetterB ? 'var(--accent-gold)' : 'inherit'}">${m.b}</span>
                </div>
            `;
        }).join('');
    }

    modal.classList.add('active');
}

function updateModalIntelligence(detailData, teamA, teamB, blendedA) {
    const whyContent = document.getElementById('modal-why-content');
    if (whyContent && detailData.analysis && detailData.analysis.length > 0) {
        const favoriteName = blendedA > 0.5 ? teamA.name : teamB.name;

        whyContent.innerHTML = `
            <p><strong>Scenario Intelligence:</strong> ${favoriteName} is the statistical favorite in this matchup.</p>
            <p style="margin-top:0.5rem"><strong>Key Factor:</strong> ${detailData.analysis[0].description}</p>
            <div class="analysis-list" style="margin-top:1rem; font-size:0.85rem; opacity:0.8">
                ${detailData.analysis.map(a => `<div class="analysis-item" style="margin-bottom:0.4rem">• ${a.description}</div>`).join('')}
            </div>
        `;
    }
}

function closeMatchupModal() {
    const modal = document.getElementById('matchup-modal');
    if (modal) modal.classList.remove('active');
    appState.activeMatchup = null; // Clear tracking
}

async function updateModalLive() {
    if (!appState.activeMatchup) return;
    const matchup = appState.activeMatchup;
    const teamA = appState.teams[matchup.team_a] || { name: matchup.team_a };
    const teamB = appState.teams[matchup.team_b] || { name: matchup.team_b };
    
    if (matchup.is_actual || !teamA.name || teamA.name === 'TBD' || !teamB.name || teamB.name === 'TBD') return;

    const probBadge = document.getElementById('modal-prob');
    if (probBadge) probBadge.innerHTML = `<span style="display:inline-block; animation: spin 1s linear infinite; margin-right:8px;">↻</span>Recalculating...`;

    const weights = {};
    document.querySelectorAll('input[id^="weight-"]').forEach(input => {
        const id = input.id.replace('weight-', '').replace(/-/g, '_');
        weights[id === 'eff' ? 'efficiency' : id] = parseFloat(input.value);
    });

    try {
        const response = await fetch(`/api/matchup/detail`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                year: parseInt(appState.year),
                team_a: teamA.name,
                team_b: teamB.name,
                weights: weights,
                volatility: appState.volatility / 100
            })
        });
        const detailData = await response.json();
        if (detailData && !detailData.error) {
            const liveProb = detailData.probability;
            const liveBlended = ((1.0 - appState.volatility / 100) * liveProb) + ((appState.volatility / 100) * 0.5);
            
            // simProbA is the one stored when the simulation was run.
            // We use the liveProb for the 'Live Edge' display.
            const simProbA = matchup.probability || liveProb;
            const edgeText = `(Edge: ${(liveBlended * 100).toFixed(1)}%)`;
            
            if (probBadge) {
                probBadge.innerHTML = `Win Rate: <span style="color:var(--accent-gold)">${(simProbA * 100).toFixed(0)}%</span> <span style="font-size:0.85em; opacity:0.8; margin-left:8px;">${edgeText}</span>`;
            }
            updateModalIntelligence(detailData, teamA, teamB, liveBlended);
        }
    } catch (err) {
        console.error("Live modal update failed", err);
    }
}

// --- Initialization ---

document.addEventListener('DOMContentLoaded', () => {
    const yearSelect = document.getElementById('year-select');
    if (yearSelect) {
        appState.year = yearSelect.value;
        yearSelect.addEventListener('change', (e) => {
            appState.year = e.target.value;
            fetchTeams(appState.year);
            renderMMBracket();
        });
    }

    renderMMBracket();

    initInteractiveZoom();

    // Matchup Modal close handlers
    document.getElementById('close-modal')?.addEventListener('click', closeMatchupModal);
    document.getElementById('matchup-modal')?.addEventListener('click', (e) => {
        if (e.target.id === 'matchup-modal') closeMatchupModal();
    });

    document.getElementById('run-simulation-btn')?.addEventListener('click', () => {
        const btn = document.getElementById('run-simulation-btn');
        const originalHtml = btn.innerHTML;
        btn.innerHTML = `<span style="display:inline-block; animation: spin 1s linear infinite; margin-right:8px;">↻</span>SIMULATING...`;
        btn.style.pointerEvents = 'none';

        runSimulation().finally(() => {
            btn.innerHTML = originalHtml;
            btn.style.pointerEvents = 'auto';
        });
    });

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.dataset.mode;
            if (!mode) return;

            // Update app state and UI
            appState.mode = mode;
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            if (mode === 'settings') {
                const panel = document.getElementById('settings-panel');
                if (panel) panel.classList.toggle('active');
                // Don't set mode to 'settings' permanently
                btn.classList.remove('active');
                return;
            }

            // For other modes, ensure settings panel is closed
            document.getElementById('settings-panel')?.classList.remove('active');

            // Track last real mode before overview action clears it
            if (mode === 'overview') {
                btn.classList.remove('active');
                globalZoomOverview('all');
                return;
            }

            // Store last real mode for settings panel reference
            appState.lastMode = mode;

            if (appState.mode === 'average') applyWeights(appState.optimalWeights);
            else if (appState.mode === 'perfect') applyWeights(appState.perfectWeights);
            else if (appState.mode === 'balanced') applyWeights(appState.balancedWeights);

            // Auto-fill bracket deterministically for preset modes
            if (['average', 'perfect', 'balanced'].includes(appState.mode)) {
                setTimeout(() => autoFillBracket(), 350); // Wait for applyWeights guard to clear
            } else {
                renderMMBracket();
            }
        });
    });

    // Consolidated Sync Button
    const btnSyncLive = document.getElementById('btn-sync-current');
    if (btnSyncLive) btnSyncLive.addEventListener('click', () => syncStartRound('live'));

    const btnResetView = document.getElementById('btn-reset-view');
    if (btnResetView) {
        btnResetView.addEventListener('click', async () => {
            // Reset bracket to ground truth (Sync + Locks)
            appState.mode = 'current';
            await fetchBracketData(true);
            if (appState.bracketData) {
                appState.hasSimulated = false; // V4: Reset stale yellow
                renderBracketWaterfall(appState.bracketData);
            }
            setTimeout(() => globalZoomOverview('all'), 200);
        });
    }

    const btnClearLocks = document.getElementById('btn-clear-locks');
    if (btnClearLocks) {
        btnClearLocks.addEventListener('click', () => {
            if (confirm("Are you sure you want to remove ALL manual locks?")) {
                appState.locks = { regions: {}, final_four: {}, championship: {} };
                console.log("[UI] Manual locks cleared.");
                renderMMBracket();
            }
        });
    }

    const btnCloseSettings = document.getElementById('close-settings-btn');
    const panelSettings = document.getElementById('settings-panel');

    if (btnCloseSettings) {
        btnCloseSettings.addEventListener('click', () => {
            if (panelSettings) panelSettings.classList.remove('active');
        });
    }

    // Toggle Panels
    const panels = {
        'field-stats-toggle-btn': 'field-stats-panel',
        'research-lab-toggle-btn': 'research-lab-panel'
    };

    Object.entries(panels).forEach(([btnId, panelId]) => {
        const btn = document.getElementById(btnId);
        const panel = document.getElementById(panelId);
        if (btn && panel) {
            btn.onclick = () => panel.classList.toggle('active');
        }
    });

    // Initial data load
    initWeights();
    initWeightListeners();
    fetchTeams(appState.year);
});

async function syncStartRound(round) {
    let btnId = 'btn-sync-current';
    if (round !== 'live') btnId = `btn-lock-${round}`;
    const btn = document.getElementById(btnId);
    const originalText = btn ? btn.innerHTML : '';

    if (btn) {
        btn.innerHTML = `<span style="display:inline-block; animation: spin 1s linear infinite; margin-right: 8px;">↻</span>${btn.innerText}`;
        btn.style.pointerEvents = 'none';
        btn.style.opacity = '0.7';
    }

    // Artificial delay to ensure spinner renders on localhost
    await new Promise(r => setTimeout(r, 500));

    if (round === 'live') {
        try {
            // Reset manual locks on live sync
            appState.locks = { regions: {}, final_four: {}, championship: {} };
            appState.locksInitialized = false;

            const response = await fetch(`/api/sync/live?year=${appState.year}`, { method: 'POST' });
            const data = await response.json();
            alert(data.message || data.error);
            appState.mode = 'current'; // Force Standard View to show the results
            await fetchBracketData(true);
            if (appState.bracketData) {
                appState.hasSimulated = false; // V4: Reset stale yellow after sync
                renderBracketWaterfall(appState.bracketData);
            }
            // Zoom out to show the updated bracket
            setTimeout(() => globalZoomOverview('all'), 200);
        } catch (err) {
            console.error(err);
            alert("Failed to sync live bracket.");
        } finally {
            if (btn) {
                btn.innerHTML = originalText;
                btn.style.pointerEvents = 'auto';
                btn.style.opacity = '1';
            }
        }
        return;
    }

    try {
        const response = await fetch(`/api/sync/start_round?round=${round}&year=${appState.year}`, {
            method: 'POST'
        });
        const result = await response.json();
        if (response.ok) {
            alert(`Success: ${result.message}`);
            await fetchTeams(appState.year);
            renderMMBracket();
        } else {
            alert(`Error: ${result.error}`);
        }
    } catch (err) {
        console.error("Sync error:", err);
        alert("Failed to start round synchronization");
    } finally {
        if (btn) {
            btn.innerHTML = originalText;
            btn.style.pointerEvents = 'auto';
            btn.style.opacity = '1';
        }
    }
}

async function syncLiveBracket() {
    const btn = document.getElementById('sync-live-btn');
    if (btn) btn.classList.add('spinning');

    try {
        const response = await fetch(`/api/sync/live?year=${appState.year}`, { method: 'POST' });
        if (response.ok) {
            appState.mode = 'standard';
            await renderMMBracket();
            alert("Bracket synced with live data.");
        }
    } catch (err) {
        console.error("Sync failed:", err);
    } finally {
        if (btn) btn.classList.remove('spinning');
    }
}

// Expose for browser agent and HTML onclick handlers
window.appState = appState;
window.globalResetSimulation = () => {
    appState.locks = { regions: {}, final_four: {}, championship: {} };
    renderMMBracket();
};

// Backdrop dismissal for modals
document.addEventListener('click', (e) => {
    const overlay = document.querySelector('.modal-overlay');
    const settings = document.getElementById('settings-panel');
    if (e.target === overlay) {
        overlay.style.display = 'none';
        overlay.classList.remove('active');
    }
    if (e.target === settings) {
        settings.style.display = 'none';
        settings.classList.remove('active');
    }
});
