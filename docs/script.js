// ==================== Dark Mode Toggle ====================
// Dark mode toggle functionality
const darkModeToggle = document.getElementById("darkModeToggle");
const mobileThemeToggle = document.getElementById("mobileThemeToggle");

function toggleDarkMode() {
  document.body.classList.toggle("dark-mode");
  const isDarkMode = document.body.classList.contains("dark-mode");
  localStorage.setItem("darkMode", isDarkMode);
}

if (darkModeToggle) {
  // Check for saved dark mode preference or default to light mode
  const savedDarkMode = localStorage.getItem("darkMode") === "true";
  if (savedDarkMode) {
    document.body.classList.add("dark-mode");
  }

  darkModeToggle.addEventListener("click", toggleDarkMode);

  // Show toggle only when scrolled down
  window.addEventListener("scroll", () => {
    if (window.scrollY > 300) {
      darkModeToggle.classList.add("visible");
    } else {
      darkModeToggle.classList.remove("visible");
    }
  });
}

if (mobileThemeToggle) {
  // Check for saved dark mode preference
  const savedDarkMode = localStorage.getItem("darkMode") === "true";
  if (savedDarkMode) {
    document.body.classList.add("dark-mode");
  }

  mobileThemeToggle.addEventListener("click", toggleDarkMode);
}

// ==================== Mobile Menu Toggle ====================
const mobileMenuToggle = document.getElementById("mobileMenuToggle");
const sidebar = document.getElementById("sidebar");
const sidebarToggle = document.getElementById("sidebarToggle");
const sidebarOverlay = document.getElementById("sidebarOverlay");

function setSidebarOpen(isOpen) {
  if (!sidebar) return;
  sidebar.classList.toggle("is-open", isOpen);
  document.body.classList.toggle("sidebar-open", isOpen);
}

function toggleSidebar() {
  if (!sidebar) return;
  setSidebarOpen(!sidebar.classList.contains("is-open"));
}

if (mobileMenuToggle) {
  mobileMenuToggle.addEventListener("click", toggleSidebar);
}

if (sidebarToggle) {
  sidebarToggle.addEventListener("click", toggleSidebar);
}

if (sidebarOverlay) {
  sidebarOverlay.addEventListener("click", () => setSidebarOpen(false));
}

if (sidebar) {
  sidebar.addEventListener("click", (e) => {
    if (window.innerWidth > 1024) return;
    const target = e.target;
    if (target instanceof Element && target.closest(".nav-link")) {
      setSidebarOpen(false);
    }
  });
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && sidebar?.classList.contains("is-open")) {
    setSidebarOpen(false);
  }
});

window.addEventListener("resize", () => {
  if (window.innerWidth > 1024 && sidebar?.classList.contains("is-open")) {
    setSidebarOpen(false);
  }
});

// ==================== Sidebar Toggle (Mobile) ====================
// Removed - no longer using sidebar

// ==================== Active Link Highlighting ====================
// Removed - no longer using active link highlighting

// ==================== Canvas Demos ====================
const CANVAS_MIN_HEIGHT = (() => {
  if (typeof window === "undefined") {
    return 1444;
  }
  const width = window.innerWidth;
  if (width <= 480) return 420;
  if (width <= 768) return 540;
  if (width <= 1024) return 720;
  return 1444;
})();

function createHiResCanvas(canvas, minHeight = CANVAS_MIN_HEIGHT) {
  const ctx = canvas.getContext("2d");
  let lastWidth = 0;
  let lastHeight = 0;
  let lastScale = 0;

  function resize(force = false) {
    const rect = canvas.getBoundingClientRect();
    if (!rect.width || !rect.height) {
      return { width: 0, height: 0, scale: 1 };
    }

    const dpr = window.devicePixelRatio || 1;
    const scale = Math.max(dpr, minHeight / rect.height);
    const width = Math.max(1, Math.round(rect.width * scale));
    const height = Math.max(1, Math.round(rect.height * scale));

    if (force || width !== lastWidth || height !== lastHeight || scale !== lastScale) {
      canvas.width = width;
      canvas.height = height;
      ctx.setTransform(scale, 0, 0, scale, 0, 0);
      lastWidth = width;
      lastHeight = height;
      lastScale = scale;
    }

    return { width: rect.width, height: rect.height, scale };
  }

  return { ctx, resize };
}

const steps = {
  plan: {
    title: "Plan (Cooperative A* + CBS)",
    text:
      "Each agent plans a time-expanded path using Cooperative A*. CBS resolves conflicts by adding constraints and replanning until paths are consistent.",
    code: `Cooperative A*:
- time-expanded grid
- reservation table

CBS:
- detect conflicts
- add constraint
- replan for agent`,
  },
  symmetry: {
    title: "Symmetry Reduction",
    text:
      "Agents are grouped into role orbits (idle vs carrying requested). Canonicalization maps symmetric permutations to a single quotient state.",
    code: `Orbits:
- group by role
- canonicalize positions
- shrink state space`,
  },
  verify: {
    title: "Verify on Quotient",
    text:
      "Bounded verification checks collisions and minimum separation over the quotient. If unsafe, it returns a counterexample trace.",
    code: `Verify:
- run trials
- track collisions
- compute delta_q`,
  },
  refine: {
    title: "Refine with Constraints",
    text:
      "Counterexamples are converted to hard constraints. The planner avoids these moves and verification repeats.",
    code: `Refine:
- extract conflict
- add constraint
- re-verify`,
  },
};

// ==================== Flow Chart Demo ====================
const flowSection = document.getElementById("refinement");
const flowButtons = flowSection ? flowSection.querySelectorAll("[data-flow]") : [];
const flowChart = document.getElementById("flowChart");
const flowChartCaption = document.getElementById("flowChartCaption");
const flowChartSurface = flowChart ? createHiResCanvas(flowChart) : null;

function drawFlowChart(active) {
  if (!flowChart || !flowChartSurface) return;
  const ctx = flowChartSurface.ctx;
  const size = flowChartSurface.resize();
  const width = size.width;
  const height = size.height;

  ctx.clearRect(0, 0, width, height);
  const bg = ctx.createLinearGradient(0, 0, width, height);
  bg.addColorStop(0, "#0f1318");
  bg.addColorStop(1, "#18202a");
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, width, height);

  // Dynamic positioning based on canvas size
  const centerX = width / 2;
  const centerY = height / 2;
  const spacing = Math.min(width * 0.35, 180);
  const vSpacing = Math.min(height * 0.3, 100);
  
  const nodes = [
    { key: "plan", label: "Plan", x: centerX - spacing, y: centerY - vSpacing },
    { key: "symmetry", label: "Symmetry", x: centerX + spacing * 0.3, y: centerY - vSpacing },
    { key: "verify", label: "Verify", x: centerX + spacing * 0.3, y: centerY + vSpacing * 0.3 },
    { key: "refine", label: "Refine", x: centerX - spacing, y: centerY + vSpacing * 0.3 },
  ];

  function roundedRect(x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
  }

  function arrow(fromX, fromY, toX, toY) {
    ctx.strokeStyle = "rgba(255,255,255,0.35)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(fromX, fromY);
    ctx.lineTo(toX, toY);
    ctx.stroke();
    const angle = Math.atan2(toY - fromY, toX - fromX);
    const head = 8;
    ctx.beginPath();
    ctx.moveTo(toX, toY);
    ctx.lineTo(toX - head * Math.cos(angle - Math.PI / 6), toY - head * Math.sin(angle - Math.PI / 6));
    ctx.lineTo(toX - head * Math.cos(angle + Math.PI / 6), toY - head * Math.sin(angle + Math.PI / 6));
    ctx.closePath();
    ctx.fillStyle = "rgba(255,255,255,0.35)";
    ctx.fill();
  }

  // Draw arrows between nodes
  const w = Math.min(width * 0.25, 140);
  const h = Math.min(height * 0.15, 50);
  
  arrow(nodes[0].x + w, nodes[0].y + h/2, nodes[1].x, nodes[1].y + h/2);
  arrow(nodes[1].x + w/2, nodes[1].y + h, nodes[2].x + w/2, nodes[2].y);
  arrow(nodes[2].x, nodes[2].y + h/2, nodes[3].x + w, nodes[3].y + h/2);
  arrow(nodes[3].x + w/2, nodes[3].y, nodes[0].x + w/2, nodes[0].y + h);

  nodes.forEach((n) => {
    const isActive = n.key === active;
    ctx.save();
    ctx.shadowColor = isActive ? "rgba(255, 214, 102, 0.5)" : "rgba(0,0,0,0.35)";
    ctx.shadowBlur = isActive ? 18 : 12;
    ctx.shadowOffsetY = 6;
    ctx.fillStyle = isActive ? "#c85d3d" : "#1f2a33";
    ctx.strokeStyle = isActive ? "#ffd166" : "#2d3a45";
    ctx.lineWidth = 2;
    roundedRect(n.x, n.y, w, h, 12);
    ctx.fill();
    ctx.stroke();
    ctx.restore();

    ctx.fillStyle = "#f2f2f2";
    const fontSize = Math.max(12, Math.min(16, width * 0.028));
    ctx.font = `600 ${fontSize}px 'Space Grotesk', sans-serif`;
    const textX = n.x + w * 0.15;
    const textY = n.y + h * 0.6;
    ctx.fillText(n.label, textX, textY);
  });
}

// Redraw on resize for responsive behavior
window.addEventListener('resize', () => {
  const activeBtn = document.querySelector('[data-flow].is-active');
  if (activeBtn && flowChart) {
    drawFlowChart(activeBtn.dataset.flow);
  }
});

function updateFlow(active) {
  flowButtons.forEach((b) => b.classList.toggle("is-active", b.dataset.flow === active));
  const captions = {
    plan: "Plan: Cooperative A* + CBS generates conflict-free paths.",
    symmetry: "Symmetry: role-orbit reduction and canonicalization.",
    verify: "Verify: bounded safety checks on the quotient model.",
    refine: "Refine: constraints injected from counterexamples.",
  };
  if (flowChartCaption) {
    flowChartCaption.textContent = steps[active]?.title || captions[active] || "";
  }
  drawFlowChart(active);
}

flowButtons.forEach((btn) => {
  btn.addEventListener("click", () => updateFlow(btn.dataset.flow));
});

updateFlow("plan");

// Canvas interactive explainer - minimal design
const canvas = document.getElementById("flowCanvas");
const caption = document.getElementById("canvasCaption");
const modeButtons = document.querySelectorAll("[data-mode]");

if (canvas) {
  const ctx = canvas.getContext("2d");
  const W = canvas.width;
  const H = canvas.height;

  // Simplified grid - 6x4
  const gridSize = 6;
  const cellSize = 60;
  const gridX = (W - gridSize * cellSize) / 2;
  const gridY = (H - 4 * cellSize) / 2;

  // Minimal agent data - 2 agents with original and refined paths
  const agent1PathOriginal = [
    { x: 0, y: 1 }, { x: 1, y: 1 }, { x: 2, y: 1 }, { x: 3, y: 1 }, { x: 4, y: 1 }, { x: 5, y: 1 }
  ];
  const agent2PathOriginal = [
    { x: 0, y: 2 }, { x: 1, y: 2 }, { x: 2, y: 2 }, { x: 3, y: 2 }, { x: 4, y: 2 }, { x: 5, y: 2 }
  ];
  
  // Refined paths that avoid conflict zone
  const agent1PathRefined = [
    { x: 0, y: 1 }, { x: 1, y: 1 }, { x: 2, y: 0 }, { x: 3, y: 0 }, { x: 4, y: 1 }, { x: 5, y: 1 }
  ];
  const agent2PathRefined = [
    { x: 0, y: 2 }, { x: 1, y: 2 }, { x: 2, y: 3 }, { x: 3, y: 3 }, { x: 4, y: 2 }, { x: 5, y: 2 }
  ];

  // Verify paths - agents stop before hitting obstacle
  const agent1PathVerify = [
    { x: 0, y: 1 }, { x: 1, y: 1 }
  ];
  const agent2PathVerify = [
    { x: 0, y: 2 }, { x: 1, y: 2 }
  ];

  let mode = "plan";
  let stepIndex = 0;
  let playing = true;
  let lastTick = 0;

  function toPx(gx, gy) {
    return {
      x: gridX + gx * cellSize + cellSize / 2,
      y: gridY + gy * cellSize + cellSize / 2,
    };
  }

  function drawMinimalGrid() {
    ctx.strokeStyle = "rgba(255,255,255,0.1)";
    ctx.lineWidth = 1;
    for (let i = 0; i <= gridSize; i++) {
      ctx.beginPath();
      ctx.moveTo(gridX + i * cellSize, gridY);
      ctx.lineTo(gridX + i * cellSize, gridY + 4 * cellSize);
      ctx.stroke();
    }
    for (let j = 0; j <= 4; j++) {
      ctx.beginPath();
      ctx.moveTo(gridX, gridY + j * cellSize);
      ctx.lineTo(gridX + gridSize * cellSize, gridY + j * cellSize);
      ctx.stroke();
    }
  }

  function drawPath(path, color, opacity = 0.5) {
    ctx.strokeStyle = color;
    ctx.globalAlpha = opacity;
    ctx.lineWidth = 2;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    const start = toPx(path[0].x, path[0].y);
    ctx.moveTo(start.x, start.y);
    for (let i = 1; i < path.length; i++) {
      const p = toPx(path[i].x, path[i].y);
      ctx.lineTo(p.x, p.y);
    }
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.globalAlpha = 1;
  }

  function drawAgent(path, color, label) {
    const pos = path[Math.min(stepIndex, path.length - 1)];
    const p = toPx(pos.x, pos.y);
    
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 18, 0, Math.PI * 2);
    ctx.fill();
    
    ctx.fillStyle = "#fff";
    ctx.font = "bold 14px Arial";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(label, p.x, p.y);
  }

  function drawGoal(x, y, label) {
    const p = toPx(x, y);
    ctx.strokeStyle = "#ffd166";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 8, 0, Math.PI * 2);
    ctx.stroke();
    
    ctx.fillStyle = "#ffd166";
    ctx.font = "9px Arial";
    ctx.textAlign = "center";
    ctx.fillText(label, p.x, p.y - 15);
  }

  function drawConflictZone() {
    const p = toPx(2.5, 1.5);
    ctx.strokeStyle = "#ef5350";
    ctx.fillStyle = "rgba(239, 83, 80, 0.15)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 18, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
  }

  function drawObstacle() {
    const p1 = toPx(2, 1);
    const p2 = toPx(3, 2);
    ctx.fillStyle = "#555";
    ctx.strokeStyle = "#888";
    ctx.lineWidth = 2;
    ctx.fillRect(p1.x - 12, p1.y - 12, 24, 24);
    ctx.fillRect(p2.x - 12, p2.y - 12, 24, 24);
    ctx.strokeRect(p1.x - 12, p1.y - 12, 24, 24);
    ctx.strokeRect(p2.x - 12, p2.y - 12, 24, 24);
  }

  function drawSymmetryGroup() {
    // Group 1
    const p1 = toPx(agent1PathOriginal[stepIndex].x, agent1PathOriginal[stepIndex].y);
    const p2 = toPx(agent2PathOriginal[stepIndex].x, agent2PathOriginal[stepIndex].y);
    
    ctx.strokeStyle = "#4fc3f7";
    ctx.lineWidth = 3;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  function render() {
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = "#0a0e13";
    ctx.fillRect(0, 0, W, H);
    
    drawMinimalGrid();

    if (mode === "plan") {
      drawPath(agent1PathOriginal, "#66bb6a", 0.6);
      drawPath(agent2PathOriginal, "#4fc3f7", 0.6);
      drawGoal(5, 1, "G1");
      drawGoal(5, 2, "G2");
      drawAgent(agent1PathOriginal, "#66bb6a", "1");
      drawAgent(agent2PathOriginal, "#4fc3f7", "2");
      caption.textContent = "Plan: Agents follow conflict-free paths to their goals.";
    } else if (mode === "symmetry") {
      drawAgent(agent1PathOriginal, "#66bb6a", "1");
      drawAgent(agent2PathOriginal, "#4fc3f7", "2");
      drawSymmetryGroup();
      caption.textContent = "Symmetry: Agents in the same role are grouped (blue connection).";
    } else if (mode === "verify") {
      drawPath(agent1PathVerify, "#66bb6a", 0.4);
      drawPath(agent2PathVerify, "#4fc3f7", 0.4);
      drawObstacle();
      drawConflictZone();
      drawAgent(agent1PathVerify, "#66bb6a", "1");
      drawAgent(agent2PathVerify, "#4fc3f7", "2");
      caption.textContent = "Verify: Agents stop - detected obstacles (gray) blocking paths.";
    } else if (mode === "refine") {
      // Show old paths in faded color
      drawPath(agent1PathOriginal, "#888", 0.2);
      drawPath(agent2PathOriginal, "#888", 0.2);
      
      // Show new refined paths
      drawPath(agent1PathRefined, "#66bb6a", 0.7);
      drawPath(agent2PathRefined, "#4fc3f7", 0.7);
      
      drawAgent(agent1PathRefined, "#66bb6a", "1");
      drawAgent(agent2PathRefined, "#4fc3f7", "2");
      
      caption.textContent = "Refine: New paths (colored) avoid conflict zone, old paths (gray) discarded.";
    }
  }

  function tick(ts) {
    if (!lastTick) lastTick = ts;
    const elapsed = ts - lastTick;
    if (playing && elapsed > 600) {
      stepIndex++;
      lastTick = ts;
    }
    render();
    requestAnimationFrame(tick);
  }

  requestAnimationFrame(tick);

  modeButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      modeButtons.forEach((b) => b.classList.remove("is-active"));
      btn.classList.add("is-active");
      mode = btn.dataset.mode;
      stepIndex = 0;
    });
  });
}

// ==================== Shared Scenario Data (Global Scope) ====================
// Declare these as global variables so all canvas sections can access them
let symmetryScenarios, quotientComparisonScenarios, verificationScenarios, refinementScenarios;

// Algorithm demo canvas
const algoCanvas = document.getElementById("algoCanvas");
const algoCaption = document.getElementById("algoCaption");
const algoSection = document.getElementById("planning");
const algoButtons = algoSection ? algoSection.querySelectorAll("[data-algo]") : [];
const algoSurface = algoCanvas ? createHiResCanvas(algoCanvas) : null;

const debugDiv = document.getElementById('debugStatus');
if (debugDiv) {
  setTimeout(() => {
    debugDiv.innerHTML = `
      algoCanvas: ${algoCanvas ? '✓' : '✗'}<br>
      symmetryCanvas: ${document.getElementById('symmetryCanvas') ? '✓' : '✗'}<br>
      verifyCanvas: ${document.getElementById('verifyCanvas') ? '✓' : '✗'}<br>
      symmetryScenarios: ${typeof symmetryScenarios !== 'undefined' && symmetryScenarios ? symmetryScenarios.length + ' items' : '✗ UNDEFINED'}<br>
      Animation: ${algoPlaying ? '✓ Running' : '✗ Stopped'}
    `;
  }, 1000);
}

console.log('algoCanvas:', algoCanvas, 'algoCaption:', algoCaption, 'algoButtons:', algoButtons.length);

if (algoCanvas) {
  console.log('Initializing algoCanvas...');
  const ctx = algoSurface.ctx;
  const grid = 10;
  const cell = 32;
  let canvasWidth = 0;
  let canvasHeight = 0;
  let offsetX = 0;
  let offsetY = 0;
  let algoMode = "astar";
  let tick = 0;
  let algoPlaying = true;
  let lastAlgoTick = 0;

  function updateAlgoLayout() {
    const size = algoSurface.resize();
    canvasWidth = size.width;
    canvasHeight = size.height;
    offsetX = (canvasWidth - grid * cell) / 2;
    offsetY = (canvasHeight - grid * cell) / 2;
    return size;
  }

  const astarStart = { x: 1, y: 1 };
  const astarGoal = { x: 8, y: 7 };
  const astarWalls = [
    { x: 3, y: 1 }, { x: 3, y: 2 }, { x: 3, y: 3 }, { x: 3, y: 4 },
    { x: 5, y: 5 }, { x: 6, y: 5 }, { x: 7, y: 5 },
  ];
  const astarPath = [
    { x: 1, y: 1 }, { x: 2, y: 1 }, { x: 2, y: 2 }, { x: 2, y: 3 }, { x: 2, y: 4 },
    { x: 2, y: 5 }, { x: 3, y: 5 }, { x: 4, y: 5 }, { x: 4, y: 6 }, { x: 5, y: 6 },
    { x: 6, y: 6 }, { x: 7, y: 6 }, { x: 8, y: 6 }, { x: 8, y: 7 },
  ];

  // CBS Demo: Warehouse scenario with two agents fetching shelves
  // Agent 1 (orange): moves to shelf at (2,5), then to goal at (8,1)
  // Agent 2 (blue): moves to shelf at (7,3), then to goal at (1,8)
  // They conflict at position (5,5) at the same time
  
  const cbsAgent1Shelf = { x: 2, y: 5, label: "S1" }; // Shelf 1
  const cbsAgent1Goal = { x: 8, y: 1, label: "G1" };  // Goal 1
  const cbsAgent2Shelf = { x: 7, y: 3, label: "S2" }; // Shelf 2
  const cbsAgent2Goal = { x: 1, y: 8, label: "G2" };  // Goal 2
  
  // Initial conflicting paths (both agents pass through (5,5) at same time step)
  const cbsAgent1Initial = [
    { x: 1, y: 7 }, { x: 2, y: 6 }, { x: 2, y: 5 }, { x: 3, y: 5 }, { x: 4, y: 5 }, 
    { x: 5, y: 5 }, { x: 6, y: 5 }, { x: 7, y: 4 }, { x: 8, y: 3 }, { x: 8, y: 2 }, { x: 8, y: 1 }
  ];
  const cbsAgent2Initial = [
    { x: 9, y: 2 }, { x: 8, y: 3 }, { x: 7, y: 4 }, { x: 6, y: 5 }, { x: 5, y: 5 },
    { x: 4, y: 5 }, { x: 3, y: 6 }, { x: 2, y: 7 }, { x: 1, y: 7 }, { x: 1, y: 8 }
  ];
  
  // Replanned paths after CBS adds constraint to avoid (5,5)
  const cbsAgent1Replanned = [
    { x: 1, y: 7 }, { x: 2, y: 6 }, { x: 2, y: 5 }, { x: 3, y: 5 }, { x: 4, y: 5 },
    { x: 4, y: 4 }, { x: 5, y: 4 }, { x: 6, y: 4 }, { x: 7, y: 3 }, { x: 8, y: 2 }, { x: 8, y: 1 }
  ];
  const cbsAgent2Replanned = [
    { x: 9, y: 2 }, { x: 8, y: 3 }, { x: 7, y: 4 }, { x: 6, y: 5 }, { x: 5, y: 6 },
    { x: 4, y: 6 }, { x: 3, y: 6 }, { x: 2, y: 7 }, { x: 1, y: 7 }, { x: 1, y: 8 }
  ];

  // Symmetry Reduction Demo
  // Accurately show how agents are grouped into orbits by role and canonicalized
  symmetryScenarios = [
    {
      // Scenario 1: Initial state with labeled agents
      agents: [
        { x: 2, y: 3, role: 'idle', id: 'A', dir: '→' },
        { x: 6, y: 5, role: 'idle', id: 'B', dir: '↓' },
        { x: 4, y: 2, role: 'idle', id: 'C', dir: '←' },
      ],
      text: "Original State with 3 Idle Agents",
      caption: "State 1: Three idle agents → A at (2,3), B at (6,5), C at (4,2) with directions.",
    },
    {
      // Scenario 2: Detect role orbits
      agents: [
        { x: 2, y: 3, role: 'idle', id: 'A', dir: '→', highlight: true },
        { x: 6, y: 5, role: 'idle', id: 'B', dir: '↓', highlight: true },
        { x: 4, y: 2, role: 'idle', id: 'C', dir: '←', highlight: true },
      ],
      text: "Orbit Detection: All roles = IDLE (0,0)",
      caption: "Group agents by role type. All agents idle → Single orbit (green highlight).",
    },
    {
      // Scenario 3: Extract tuples
      agents: [
        { x: 2, y: 3, role: 'idle', id: 'A', dir: '→', showTuple: true },
        { x: 6, y: 5, role: 'idle', id: 'B', dir: '↓', showTuple: true },
        { x: 4, y: 2, role: 'idle', id: 'C', dir: '←', showTuple: true },
      ],
      text: "Extract Tuples: (x, y, dir, role)",
      tuples: ["A: (2, 3, 0, 0)", "B: (6, 5, 2, 0)", "C: (4, 2, 1, 0)"],
      caption: "Encode each agent as tuple (x-pos, y-pos, direction-code, role-code).",
    },
    {
      // Scenario 4: Sort tuples
      agents: [
        { x: 2, y: 3, role: 'idle', id: '1', dir: '→', canonical: true },
        { x: 4, y: 2, role: 'idle', id: '2', dir: '←', canonical: true },
        { x: 6, y: 5, role: 'idle', id: '3', dir: '↓', canonical: true },
      ],
      text: "Canonical Ordering (Sorted)",
      tuples: ["(2, 3, 0, 0)", "(4, 2, 1, 0)", "(6, 5, 2, 0)"],
      sorted: true,
      caption: "Sort tuples lexicographically → Canonical representative for quotient state.",
    },
    {
      // Scenario 5: Different permutation (State 2)
      agents: [
        { x: 4, y: 2, role: 'idle', id: 'A', dir: '←' },
        { x: 2, y: 3, role: 'idle', id: 'B', dir: '→' },
        { x: 6, y: 5, role: 'idle', id: 'C', dir: '↓' },
      ],
      text: "Different Agent Labels (Permutation)",
      caption: "State 2: Same positions, different naming → A(4,2), B(2,3), C(6,5).",
    },
    {
      // Scenario 6: Same orbit
      agents: [
        { x: 4, y: 2, role: 'idle', id: 'A', dir: '←', highlight: true },
        { x: 2, y: 3, role: 'idle', id: 'B', dir: '→', highlight: true },
        { x: 6, y: 5, role: 'idle', id: 'C', dir: '↓', highlight: true },
      ],
      text: "Orbit Detection: All roles = IDLE (0,0)",
      caption: "Re-check orbits. All idle again → Same single orbit (green highlight).",
    },
    {
      // Scenario 7: Extract and sort - same result
      agents: [
        { x: 2, y: 3, role: 'idle', id: '1', dir: '→', canonical: true },
        { x: 4, y: 2, role: 'idle', id: '2', dir: '←', canonical: true },
        { x: 6, y: 5, role: 'idle', id: '3', dir: '↓', canonical: true },
      ],
      text: "SAME Canonical Form After Sort",
      tuples: ["(2, 3, 0, 0)", "(4, 2, 1, 0)", "(6, 5, 2, 0)"],
      sorted: true,
      caption: "Extract & sort → IDENTICAL canonical form as State 1!",
    },
    {
      // Scenario 8: Equivalence
      agents: [
        { x: 4, y: 4, role: 'idle', id: '✓', size: 'large' },
      ],
      text: "State 1 ≡ State 2 (Symmetry Detected)",
      stateCount: "3! = 6 permutations",
      quotientCount: "→ 1 quotient state",
      caption: "Both states are symmetric permutations → Mapped to same quotient state!",
    },
    {
      // Scenario 9: Mixed roles example
      agents: [
        { x: 2, y: 2, role: 'idle', id: 'A', dir: '→' },
        { x: 6, y: 2, role: 'idle', id: 'B', dir: '←' },
        { x: 2, y: 6, role: 'carrying', id: 'C', dir: '↑' },
        { x: 6, y: 6, role: 'carrying', id: 'D', dir: '↓' },
      ],
      text: "Multi-Role Scenario",
      caption: "New state: 2 idle agents (blue) + 2 carrying agents (orange).",
    },
    {
      // Scenario 10: Separate orbits
      agents: [
        { x: 2, y: 2, role: 'idle', id: 'A', dir: '→', orbitA: true },
        { x: 6, y: 2, role: 'idle', id: 'B', dir: '←', orbitA: true },
        { x: 2, y: 6, role: 'carrying', id: 'C', dir: '↑', orbitB: true },
        { x: 6, y: 6, role: 'carrying', id: 'D', dir: '↓', orbitB: true },
      ],
      text: "Orbit 1 (IDLE) | Orbit 2 (CARRYING)",
      caption: "Different roles → Two separate orbits. Blue border = idle, orange = carrying.",
    },
    {
      // Scenario 11: Canonicalize each orbit
      agents: [
        { x: 2, y: 2, role: 'idle', id: '1', dir: '→', orbitA: true, canonical: true },
        { x: 6, y: 2, role: 'idle', id: '2', dir: '←', orbitA: true, canonical: true },
        { x: 2, y: 6, role: 'carrying', id: '1', dir: '↑', orbitB: true, canonical: true },
        { x: 6, y: 6, role: 'carrying', id: '2', dir: '↓', orbitB: true, canonical: true },
      ],
      text: "Canonicalize Each Orbit Independently",
      tuples: ["Idle orbit: [(2,2,0,0), (6,2,1,0)]", "Carry orbit: [(2,6,3,1), (6,6,2,1)]"],
      caption: "Sort tuples within each orbit separately to get canonical form.",
    },
    {
      // Scenario 12: State space reduction
      agents: [
        { x: 4, y: 4, role: 'idle', id: '✓', size: 'large' },
      ],
      text: "Symmetry Reduction Achieved",
      stateCount: "2! × 2! = 4 permutations",
      quotientCount: "→ 1 quotient state",
      caption: "4 possible labelings of (2 idle + 2 carrying) → Reduced to 1 quotient state!",
    },
  ];

  function toCell(px, py) {
    return {
      x: offsetX + px * cell,
      y: offsetY + py * cell,
    };
  }

  function drawGrid() {
    ctx.strokeStyle = "rgba(255,255,255,0.08)";
    for (let i = 0; i <= grid; i++) {
      const x = offsetX + i * cell;
      ctx.beginPath();
      ctx.moveTo(x, offsetY);
      ctx.lineTo(x, offsetY + grid * cell);
      ctx.stroke();
      const y = offsetY + i * cell;
      ctx.beginPath();
      ctx.moveTo(offsetX, y);
      ctx.lineTo(offsetX + grid * cell, y);
      ctx.stroke();
    }
  }

  function drawCell(pos, color) {
    const p = toCell(pos.x, pos.y);
    ctx.fillStyle = color;
    ctx.fillRect(p.x + 2, p.y + 2, cell - 4, cell - 4);
  }

  function drawAStar() {
    astarWalls.forEach((w) => drawCell(w, "#26323c"));
    drawCell(astarStart, "#66bb6a");
    drawCell(astarGoal, "#ffd166");

    const frontierCount = Math.min(tick + 2, astarPath.length);
    for (let i = 0; i < frontierCount; i++) {
      drawCell(astarPath[i], "rgba(79,195,247,0.8)");
    }
    if (frontierCount >= astarPath.length) {
      astarPath.forEach((p) => drawCell(p, "rgba(255,200,100,0.7)"));
    }
    algoCaption.textContent = "A*: frontier expansion (blue) and final path (amber).";
  }

  function drawCBS() {
    // Phase 1 (tick 0-8): Show initial conflicting paths
    // Phase 2 (tick 9-18): Show replanned conflict-free paths
    const phase1Duration = 9;
    const phase2Duration = 10;
    const totalDuration = phase1Duration + phase2Duration;
    
    const currentTick = tick % totalDuration;
    const isPhase1 = currentTick < phase1Duration;
    
    if (isPhase1) {
      // Phase 1: Show initial paths with conflict
      const t = Math.min(currentTick, cbsAgent1Initial.length - 1);
      
      // Draw shelves and goals
      const pS1 = toCell(cbsAgent1Shelf.x, cbsAgent1Shelf.y);
      const pG1 = toCell(cbsAgent1Goal.x, cbsAgent1Goal.y);
      const pS2 = toCell(cbsAgent2Shelf.x, cbsAgent2Shelf.y);
      const pG2 = toCell(cbsAgent2Goal.x, cbsAgent2Goal.y);
      
      // Draw shelf locations (green)
      ctx.fillStyle = "#66bb6a";
      ctx.fillRect(pS1.x + 4, pS1.y + 4, cell - 8, cell - 8);
      ctx.fillStyle = "#fff";
      ctx.font = "10px monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("S1", pS1.x + cell/2, pS1.y + cell/2);
      
      ctx.fillStyle = "#66bb6a";
      ctx.fillRect(pS2.x + 4, pS2.y + 4, cell - 8, cell - 8);
      ctx.fillStyle = "#fff";
      ctx.fillText("S2", pS2.x + cell/2, pS2.y + cell/2);
      
      // Draw goal locations (gold outline)
      ctx.strokeStyle = "#ffd166";
      ctx.lineWidth = 2;
      ctx.strokeRect(pG1.x + 4, pG1.y + 4, cell - 8, cell - 8);
      ctx.fillStyle = "#fff";
      ctx.font = "10px monospace";
      ctx.fillText("G1", pG1.x + cell/2, pG1.y + cell/2);
      
      ctx.strokeStyle = "#ffd166";
      ctx.strokeRect(pG2.x + 4, pG2.y + 4, cell - 8, cell - 8);
      ctx.fillText("G2", pG2.x + cell/2, pG2.y + cell/2);
      
      // Draw full paths in faint colors
      cbsAgent1Initial.forEach((p) => {
        drawCell(p, "rgba(240,140,58,0.15)");
      });
      cbsAgent2Initial.forEach((p) => {
        drawCell(p, "rgba(79,195,247,0.15)");
      });
      
      // Highlight conflict zone prominently at (5,5)
      drawCell({ x: 5, y: 5 }, "rgba(239,83,80,0.9)");
      
      // Draw current agent positions with labels
      const a = cbsAgent1Initial[t];
      const b = cbsAgent2Initial[t];
      const pA = toCell(a.x, a.y);
      const pB = toCell(b.x, b.y);
      
      // Agent 1 (orange) - fetching from shelf
      ctx.fillStyle = "#f08c3a";
      ctx.beginPath();
      ctx.arc(pA.x + cell/2, pA.y + cell/2, 15, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.fillStyle = "#fff";
      ctx.font = "bold 16px monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("1", pA.x + cell/2, pA.y + cell/2);
      
      // Agent 2 (blue) - fetching from shelf
      ctx.fillStyle = "#4fc3f7";
      ctx.beginPath();
      ctx.arc(pB.x + cell/2, pB.y + cell/2, 15, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.fillStyle = "#fff";
      ctx.font = "bold 16px monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("2", pB.x + cell/2, pB.y + cell/2);
      
      if (t >= 5) {
        algoCaption.textContent = "CBS Phase 1: Collision detected! Both agents at (5,5) at time step " + t + ".";
      } else {
        algoCaption.textContent = "CBS Phase 1: Agents moving to shelves - conflicting paths detected.";
      }
    } else {
      // Phase 2: Show replanned paths
      const t = Math.min(currentTick - phase1Duration, cbsAgent1Replanned.length - 1);
      
      // Draw shelves and goals
      const pS1 = toCell(cbsAgent1Shelf.x, cbsAgent1Shelf.y);
      const pG1 = toCell(cbsAgent1Goal.x, cbsAgent1Goal.y);
      const pS2 = toCell(cbsAgent2Shelf.x, cbsAgent2Shelf.y);
      const pG2 = toCell(cbsAgent2Goal.x, cbsAgent2Goal.y);
      
      // Draw shelf locations (green)
      ctx.fillStyle = "#66bb6a";
      ctx.fillRect(pS1.x + 4, pS1.y + 4, cell - 8, cell - 8);
      ctx.fillStyle = "#fff";
      ctx.font = "10px monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("S1", pS1.x + cell/2, pS1.y + cell/2);
      
      ctx.fillStyle = "#66bb6a";
      ctx.fillRect(pS2.x + 4, pS2.y + 4, cell - 8, cell - 8);
      ctx.fillStyle = "#fff";
      ctx.fillText("S2", pS2.x + cell/2, pS2.y + cell/2);
      
      // Draw goal locations (gold outline)
      ctx.strokeStyle = "#ffd166";
      ctx.lineWidth = 2;
      ctx.strokeRect(pG1.x + 4, pG1.y + 4, cell - 8, cell - 8);
      ctx.fillStyle = "#fff";
      ctx.font = "10px monospace";
      ctx.fillText("G1", pG1.x + cell/2, pG1.y + cell/2);
      
      ctx.strokeStyle = "#ffd166";
      ctx.strokeRect(pG2.x + 4, pG2.y + 4, cell - 8, cell - 8);
      ctx.fillText("G2", pG2.x + cell/2, pG2.y + cell/2);
      
      // Draw old conflicting paths in very faint gray
      cbsAgent1Initial.forEach((p) => {
        drawCell(p, "rgba(150,150,150,0.08)");
      });
      cbsAgent2Initial.forEach((p) => {
        drawCell(p, "rgba(150,150,150,0.08)");
      });
      
      // Draw new replanned paths with full color
      cbsAgent1Replanned.forEach((p, i) => {
        if (i < t) {
          drawCell(p, "rgba(240,140,58,0.4)");
        }
      });
      cbsAgent2Replanned.forEach((p, i) => {
        if (i < t) {
          drawCell(p, "rgba(79,195,247,0.4)");
        }
      });
      
      // Draw constraint zone (the avoided conflict area) with warning color
      drawCell({ x: 5, y: 5 }, "rgba(255,152,0,0.4)");
      
      // Draw current agent positions
      const a = cbsAgent1Replanned[t];
      const b = cbsAgent2Replanned[t];
      const pA = toCell(a.x, a.y);
      const pB = toCell(b.x, b.y);
      
      // Agent 1 (orange)
      ctx.fillStyle = "#f08c3a";
      ctx.beginPath();
      ctx.arc(pA.x + cell/2, pA.y + cell/2, 15, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.fillStyle = "#fff";
      ctx.font = "bold 16px monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("1", pA.x + cell/2, pA.y + cell/2);
      
      // Agent 2 (blue)
      ctx.fillStyle = "#4fc3f7";
      ctx.beginPath();
      ctx.arc(pB.x + cell/2, pB.y + cell/2, 15, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.fillStyle = "#fff";
      ctx.font = "bold 16px monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("2", pB.x + cell/2, pB.y + cell/2);
      
      if (t < 4) {
        algoCaption.textContent = "CBS Phase 2: Replanning with constraints - agents taking modified paths, avoiding (5,5).";
      } else {
        algoCaption.textContent = "CBS Phase 2: Conflict resolved! Agents reach goals safely without colliding.";
      }
    }
  }

  function drawSymmetry() {
    const scenarioIndex = tick % symmetryScenarios.length;
    const scenario = symmetryScenarios[scenarioIndex];
    
    // Draw agents
    scenario.agents.forEach((agent) => {
      const p = toCell(agent.x, agent.y);
      
      // Determine color based on role
      let color = agent.role === 'carrying' ? '#f08c3a' : '#4fc3f7';
      
      // Draw highlighting for orbit grouping
      if (agent.highlight) {
        ctx.fillStyle = 'rgba(102,187,106,0.3)';
        ctx.fillRect(p.x - 2, p.y - 2, cell + 4, cell + 4);
      }
      
      // Draw orbit borders
      if (agent.orbitA) {
        ctx.strokeStyle = '#4fc3f7';
        ctx.lineWidth = 2;
        ctx.strokeRect(p.x - 2, p.y - 2, cell + 4, cell + 4);
      }
      
      if (agent.orbitB) {
        ctx.strokeStyle = '#f08c3a';
        ctx.lineWidth = 2;
        ctx.strokeRect(p.x - 2, p.y - 2, cell + 4, cell + 4);
      }
      
      // Draw agent circle
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(p.x + cell/2, p.y + cell/2, agent.size === "large" ? 18 : 15, 0, Math.PI * 2);
      ctx.fill();
      
      // Draw direction arrow or ID
      ctx.fillStyle = '#fff';
      ctx.font = agent.canonical ? 'bold 20px monospace' : 'bold 20px monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      
      if (agent.canonical) {
        ctx.fillStyle = '#66bb6a';
      }
      
      ctx.fillText(agent.id, p.x + cell/2, p.y + cell/2);
      
      // Draw direction below agent for tuple scenarios
      if (agent.dir && agent.showTuple) {
        ctx.fillStyle = 'rgba(255,255,255,0.6)';
        ctx.font = '11px monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillText(agent.dir, p.x + cell/2, p.y + cell + 3);
      }
    });
    
    // Draw text label (for role info)
    if (scenario.text) {
      ctx.fillStyle = 'rgba(255,255,255,0.95)';
      ctx.font = "bold 13px monospace";
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillText(scenario.text, canvasWidth / 2, 20);
    }
    
    // Draw tuples - positioned in lower section
    if (scenario.tuples) {
      ctx.fillStyle = scenario.sorted ? '#66bb6a' : 'rgba(255,255,255,0.85)';
      ctx.font = "14px monospace";
      ctx.textAlign = 'left';
      ctx.textBaseline = 'top';
      
      const startX = 80;
      const startY = 450;
      
      scenario.tuples.forEach((tuple, i) => {
        const y = startY + i * 38;
        ctx.fillText(tuple, startX, y);
      });
      
      if (scenario.sorted) {
        // Draw "sorted" arrow and label
        ctx.strokeStyle = '#66bb6a';
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.moveTo(50, startY - 25);
        ctx.lineTo(50, startY - 5);
        ctx.stroke();
        
        // Arrowhead
        ctx.beginPath();
        ctx.moveTo(50, startY - 5);
        ctx.lineTo(44, startY - 15);
        ctx.lineTo(56, startY - 15);
        ctx.closePath();
        ctx.fillStyle = '#66bb6a';
        ctx.fill();
        
        ctx.fillStyle = '#66bb6a';
        ctx.font = "bold 13px monospace";
        ctx.textAlign = 'center';
        ctx.textBaseline = 'bottom';
        ctx.fillText('SORTED', 50, startY - 32);
      }
    }
    
    // Draw state space reduction info
    if (scenario.stateCount) {
      ctx.fillStyle = 'rgba(255,255,255,0.95)';
      ctx.font = "bold 16px monospace";
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(scenario.stateCount, canvasWidth / 2, 200);
      
      // Draw arrow
      ctx.strokeStyle = '#66bb6a';
      ctx.lineWidth = 5;
      ctx.beginPath();
      ctx.moveTo(canvasWidth / 2, 230);
      ctx.lineTo(canvasWidth / 2, 280);
      ctx.stroke();
      
      // Draw arrowhead
      ctx.beginPath();
      ctx.moveTo(canvasWidth / 2, 280);
      ctx.lineTo(canvasWidth / 2 - 12, 265);
      ctx.lineTo(canvasWidth / 2 + 12, 265);
      ctx.closePath();
      ctx.fillStyle = '#66bb6a';
      ctx.fill();
      
      ctx.fillStyle = '#66bb6a';
      ctx.font = "bold 16px monospace";
      ctx.fillText(scenario.quotientCount, canvasWidth / 2, 315);
    }
    
    algoCaption.textContent = scenario.caption;
  }

  // Quotient State Comparison scenarios
  quotientComparisonScenarios = [
    {
      agents: [
        { x: 1, y: 1, id: 'A' },
        { x: 3, y: 3, id: 'B' },
      ],
      caption: "Initial quotient state: Two agents at positions A(1,1) and B(3,3).",
    },
    {
      agents: [
        { x: 2, y: 2, id: 'A' },
        { x: 4, y: 4, id: 'B' },
      ],
      caption: "Quotient transition: Agents move closer to their goals.",
    },
    {
      agents: [
        { x: 3, y: 3, id: 'A' },
        { x: 5, y: 5, id: 'B' },
      ],
      caption: "Final quotient state: Agents reach their goal positions.",
    },
  ];

  // Verification Demo scenarios
  verificationScenarios = [
    {
      obstacles: [
        { x: 3, y: 3 },
        { x: 5, y: 5 },
      ],
      agents: [
        { x: 1, y: 1, id: 'A' },
        { x: 7, y: 7, id: 'B' },
      ],
      caption: "Verification: Initial state with agents and obstacles (gray blocks).",
    },
    {
      obstacles: [
        { x: 3, y: 3 },
        { x: 5, y: 5 },
      ],
      agents: [
        { x: 2, y: 2, id: 'A', stopped: true },
        { x: 6, y: 6, id: 'B', stopped: true },
      ],
      caption: "Verification: Agents (red) stop before obstacles - safety verified!",
    },
  ];

  refinementScenarios = [
    {
      unsafe: true,
      path: [
        { x: 1, y: 1 }, { x: 2, y: 1 }, { x: 3, y: 1 }, { x: 4, y: 1 }, { x: 5, y: 1 }
      ],
      constraint: null,
      caption: "Refinement Step 1: Unsafe path detected during verification.",
    },
    {
      unsafe: true,
      path: [
        { x: 1, y: 1 }, { x: 2, y: 1 }, { x: 3, y: 1 }, { x: 4, y: 1 }, { x: 5, y: 1 }
      ],
      constraint: { x: 3, y: 1, t: 2, label: "Constraint:\n(3,1,t=2)" },
      caption: "Refinement Step 2: Extract constraint from counterexample - block (3,1) at time step 2.",
    },
    {
      unsafe: false,
      path: [
        { x: 1, y: 1 }, { x: 2, y: 1 }, { x: 2, y: 2 }, { x: 3, y: 2 }, { x: 4, y: 2 }, { x: 5, y: 2 }
      ],
      constraint: { x: 3, y: 1, t: 2, label: "Constraint:\n(3,1,t=2)" },
      caption: "Refinement Step 3: Replan path avoiding constraint - new safe path found!",
    },
    {
      unsafe: false,
      path: [
        { x: 1, y: 1 }, { x: 2, y: 1 }, { x: 2, y: 2 }, { x: 3, y: 2 }, { x: 4, y: 2 }, { x: 5, y: 2 }
      ],
      constraint: { x: 3, y: 1, t: 2, label: "Constraint:\n(3,1,t=2)" },
      caption: "Refinement Step 4: Verification on new plan passes - refinement complete!",
    },
  ];

  function drawQuotientComparison() {
    const scenarioIndex = tick % quotientComparisonScenarios.length;
    const scenario = quotientComparisonScenarios[scenarioIndex];
    
    scenario.agents.forEach((agent) => {
      const p = toCell(agent.x, agent.y);
      
      // Draw agent circle
      ctx.fillStyle = "#4fc3f7";
      ctx.beginPath();
      ctx.arc(p.x + cell/2, p.y + cell/2, 15, 0, Math.PI * 2);
      ctx.fill();
      
      // Draw agent ID
      ctx.fillStyle = "#fff";
      ctx.font = "bold 12px monospace";
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(agent.id, p.x + cell/2, p.y + cell/2);
    });
    
    algoCaption.textContent = scenario.caption;
  }

  function drawVerification() {
    const scenarioIndex = tick % verificationScenarios.length;
    const scenario = verificationScenarios[scenarioIndex];
    
    // Draw obstacles
    scenario.obstacles.forEach((obs) => {
      const p = toCell(obs.x, obs.y);
      ctx.fillStyle = "#555";
      ctx.strokeStyle = "#888";
      ctx.lineWidth = 2;
      ctx.fillRect(p.x + 4, p.y + 4, cell - 8, cell - 8);
      ctx.strokeRect(p.x + 4, p.y + 4, cell - 8, cell - 8);
    });
    
    // Draw agents
    scenario.agents.forEach((agent) => {
      const p = toCell(agent.x, agent.y);
      
      // Draw agent circle
      ctx.fillStyle = agent.stopped ? "#ef5350" : "#4fc3f7";
      ctx.beginPath();
      ctx.arc(p.x + cell/2, p.y + cell/2, 15, 0, Math.PI * 2);
      ctx.fill();
      
      // Draw agent ID
      ctx.fillStyle = "#fff";
      ctx.font = "bold 12px monospace";
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(agent.id, p.x + cell/2, p.y + cell/2);
    });
    
    algoCaption.textContent = scenario.caption;
  }

  function drawRefinement() {
    const scenarioIndex = tick % refinementScenarios.length;
    const scenario = refinementScenarios[scenarioIndex];
    
    // Draw path cells
    scenario.path.forEach((p, i) => {
      const cellPos = toCell(p.x, p.y);
      
      if (scenario.unsafe && i === 2) {
        // Highlight unsafe cell at time step 2
        ctx.fillStyle = "rgba(239,83,80,0.7)";
        ctx.fillRect(cellPos.x + 2, cellPos.y + 2, cell - 4, cell - 4);
      } else if (!scenario.unsafe) {
        // Safe path - show in green
        ctx.fillStyle = "rgba(102,187,106,0.3)";
        ctx.fillRect(cellPos.x + 2, cellPos.y + 2, cell - 4, cell - 4);
      } else {
        // Unsafe path - show faded
        ctx.fillStyle = "rgba(79,195,247,0.2)";
        ctx.fillRect(cellPos.x + 2, cellPos.y + 2, cell - 4, cell - 4);
      }
      
      // Draw time label on top-right of cell
      ctx.fillStyle = "rgba(255,255,255,0.7)";
      ctx.font = "13px monospace";
      ctx.textAlign = "right";
      ctx.textBaseline = "top";
      ctx.fillText("t=" + i, cellPos.x + cell - 5, cellPos.y + 3);
    });
    
    // Draw current agent position
    const current = scenario.path[0];
    const pCurrent = toCell(current.x, current.y);
    
    ctx.fillStyle = scenario.unsafe ? "#ef5350" : "#66bb6a";
    ctx.beginPath();
    ctx.arc(pCurrent.x + cell/2, pCurrent.y + cell/2, 12, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = "#fff";
    ctx.lineWidth = 3;
    ctx.stroke();
    ctx.fillStyle = "#fff";
    ctx.font = "bold 12px monospace";
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText("A", pCurrent.x + cell/2, pCurrent.y + cell/2);
    
    // Draw constraint visualization if present
    if (scenario.constraint) {
      const pConstraint = toCell(scenario.constraint.x, scenario.constraint.y);
      
      // Draw constraint zone
      ctx.strokeStyle = "#ff9800";
      ctx.lineWidth = 3;
      ctx.setLineDash([4, 4]);
      ctx.strokeRect(pConstraint.x + 1, pConstraint.y + 1, cell - 2, cell - 2);
      ctx.setLineDash([]);
      
      // Draw constraint label above the constraint box
      ctx.fillStyle = "#ff9800";
      ctx.font = "bold 13px monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "bottom";
      const constraintText = "Constraint: (3,1,t=2)";
      ctx.fillText(constraintText, pConstraint.x + cell/2, pConstraint.y - 5);
    }
    
    // Draw status indicators at top
    ctx.fillStyle = scenario.unsafe ? "#ef5350" : "#66bb6a";
    ctx.font = "bold 16px monospace";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.fillText(scenario.unsafe ? "Status: UNSAFE" : "Status: SAFE", canvasWidth / 2, 15);
    
    algoCaption.textContent = scenario.caption;
  }

  function renderAlgo() {
    const size = updateAlgoLayout();
    if (!size.width || !size.height) {
      return;
    }
    ctx.clearRect(0, 0, canvasWidth, canvasHeight);
    ctx.fillStyle = "#0f1318";
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);
    
    if (algoMode !== "symmetry") {
      drawGrid();
    }
    
    if (algoMode === "astar") {
      drawAStar();
    } else if (algoMode === "cbs") {
      drawCBS();
    } else if (algoMode === "symmetry") {
      drawSymmetry();
    } else if (algoMode === "quotient") {
      drawQuotientComparison();
    } else if (algoMode === "verification") {
      drawVerification();
    } else if (algoMode === "refinement") {
      drawRefinement();
    }
  }

  function algoTick(ts) {
    if (!lastAlgoTick) lastAlgoTick = ts;
    const elapsed = ts - lastAlgoTick;
    
    // Different timing for different algorithms
    const delay = algoMode === "symmetry" ? 6000 : 
                  (algoMode === "cbs" ? 3000 : 
                  (algoMode === "quotient" ? 3500 : 
                  (algoMode === "verification" ? 3000 : 
                  (algoMode === "refinement" ? 3500 : 500))));
    
    if (algoPlaying && elapsed > delay) {
      // Different tick limits for different algorithms
      let maxTick = 10;
      if (algoMode === "cbs") maxTick = 16;
      if (algoMode === "symmetry") maxTick = symmetryScenarios.length;
      if (algoMode === "quotient") maxTick = quotientComparisonScenarios.length;
      if (algoMode === "verification") maxTick = verificationScenarios.length;
      if (algoMode === "refinement") maxTick = refinementScenarios.length;
      
      tick = (tick + 1) % maxTick;
      lastAlgoTick = ts;
    }
    renderAlgo();
    requestAnimationFrame(algoTick);
  }

  algoButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      algoButtons.forEach((b) => b.classList.remove("is-active"));
      btn.classList.add("is-active");
      algoMode = btn.dataset.algo;
      tick = 0;
      lastAlgoTick = 0;
      
      // Update caption immediately on mode change
      if (algoCaption) {
        if (algoMode === "astar") {
          algoCaption.textContent = "A*: frontier expansion (blue) and final path (amber).";
        } else if (algoMode === "cbs") {
          algoCaption.textContent = "CBS Phase 1: Agents moving to shelves - conflicting paths detected.";
        } else if (algoMode === "symmetry") {
          algoCaption.textContent = symmetryScenarios[0].caption;
        } else if (algoMode === "quotient") {
          algoCaption.textContent = quotientComparisonScenarios[0].caption;
        } else if (algoMode === "verification") {
          algoCaption.textContent = verificationScenarios[0].caption;
        } else if (algoMode === "refinement") {
          algoCaption.textContent = refinementScenarios[0].caption;
        }
      }
      renderAlgo(); // Immediately render new mode
    });
  });

  // Initialize with first render
  renderAlgo();
  requestAnimationFrame(algoTick);
}

// ==================== Symmetry Canvas Setup ====================
const symmetryCanvas = document.getElementById("symmetryCanvas");
const symmetryCaption = document.getElementById("symmetryCaption");
const symmetrySection = document.getElementById("symmetry");
const symmetryButtons = symmetrySection
  ? symmetrySection.querySelectorAll("[data-algo='symmetry'], [data-algo='quotient']")
  : [];
const symmetrySurface = symmetryCanvas ? createHiResCanvas(symmetryCanvas) : null;

console.log('symmetryCanvas:', symmetryCanvas, 'symmetryCaption:', symmetryCaption);

if (symmetryCanvas) {
  console.log('Initializing symmetryCanvas...');
  const sctx = symmetrySurface.ctx;
  const sgrid = 10;
  const scell = 32;
  let sWidth = 0;
  let sHeight = 0;
  let soffsetX = 0;
  let soffsetY = 0;
  let sMode = "symmetry";
  let sTickCount = 0;
  let sLastTick = 0;

  function updateSymmetryLayout() {
    const size = symmetrySurface.resize();
    sWidth = size.width;
    sHeight = size.height;
    soffsetX = (sWidth - sgrid * scell) / 2;
    soffsetY = (sHeight - sgrid * scell) / 2;
    return size;
  }
  
  function sToCell(px, py) {
    return {
      x: soffsetX + px * scell,
      y: soffsetY + py * scell,
    };
  }
  
  function sDrawGrid() {
    sctx.strokeStyle = "rgba(255,255,255,0.08)";
    for (let i = 0; i <= sgrid; i++) {
      const x = soffsetX + i * scell;
      sctx.beginPath();
      sctx.moveTo(x, soffsetY);
      sctx.lineTo(x, soffsetY + sgrid * scell);
      sctx.stroke();
      const y = soffsetY + i * scell;
      sctx.beginPath();
      sctx.moveTo(soffsetX, y);
      sctx.lineTo(soffsetX + sgrid * scell, y);
      sctx.stroke();
    }
  }
  
  function sRenderSymmetry() {
    sctx.clearRect(0, 0, sWidth, sHeight);
    sctx.fillStyle = "#0f1318";
    sctx.fillRect(0, 0, sWidth, sHeight);
    
    const scenarioIndex = sTickCount % symmetryScenarios.length;
    const scenario = symmetryScenarios[scenarioIndex];
    
    // Draw agents
    scenario.agents.forEach((agent) => {
      const p = sToCell(agent.x, agent.y);
      
      let color = agent.role === 'carrying' ? '#f08c3a' : '#4fc3f7';
      
      if (agent.highlight) {
        sctx.fillStyle = 'rgba(102,187,106,0.3)';
        sctx.fillRect(p.x - 2, p.y - 2, scell + 4, scell + 4);
      }
      
      if (agent.orbitA) {
        sctx.strokeStyle = '#4fc3f7';
        sctx.lineWidth = 2;
        sctx.strokeRect(p.x - 2, p.y - 2, scell + 4, scell + 4);
      }
      
      if (agent.orbitB) {
        sctx.strokeStyle = '#f08c3a';
        sctx.lineWidth = 2;
        sctx.strokeRect(p.x - 2, p.y - 2, scell + 4, scell + 4);
      }
      
      sctx.fillStyle = color;
      sctx.beginPath();
      sctx.arc(p.x + scell/2, p.y + scell/2, agent.size === "large" ? 18 : 15, 0, Math.PI * 2);
      sctx.fill();
      
      sctx.fillStyle = '#fff';
      sctx.font = "bold 13px monospace";
      sctx.textAlign = 'center';
      sctx.textBaseline = 'middle';
      sctx.fillText(agent.id, p.x + scell/2, p.y + scell/2);
    });
    
    if (scenario.text) {
      sctx.fillStyle = 'rgba(255,255,255,0.95)';
      sctx.font = "bold 13px monospace";
      sctx.textAlign = 'center';
      sctx.textBaseline = 'top';
      sctx.fillText(scenario.text, sWidth / 2, 20);
    }
    
    if (scenario.tuples) {
      sctx.fillStyle = scenario.sorted ? '#66bb6a' : 'rgba(255,255,255,0.85)';
      sctx.font = "14px monospace";
      sctx.textAlign = 'left';
      sctx.textBaseline = 'top';
      
      const startX = 80;
      const startY = 450;
      
      scenario.tuples.forEach((tuple, i) => {
        const y = startY + i * 38;
        sctx.fillText(tuple, startX, y);
      });
      
      if (scenario.sorted) {
        sctx.strokeStyle = '#66bb6a';
        sctx.lineWidth = 4;
        sctx.beginPath();
        sctx.moveTo(50, startY - 25);
        sctx.lineTo(50, startY - 5);
        sctx.stroke();
        
        sctx.beginPath();
        sctx.moveTo(50, startY - 5);
        sctx.lineTo(44, startY - 15);
        sctx.lineTo(56, startY - 15);
        sctx.closePath();
        sctx.fillStyle = '#66bb6a';
        sctx.fill();
        
        sctx.fillStyle = '#66bb6a';
        sctx.font = "bold 13px monospace";
        sctx.textAlign = 'center';
        sctx.textBaseline = 'bottom';
        sctx.fillText('SORTED', 50, startY - 32);
      }
    }
    
    if (scenario.stateCount) {
      sctx.fillStyle = 'rgba(255,255,255,0.95)';
      sctx.font = "bold 16px monospace";
      sctx.textAlign = 'center';
      sctx.textBaseline = 'middle';
      sctx.fillText(scenario.stateCount, sWidth / 2, 200);
      
      sctx.strokeStyle = '#66bb6a';
      sctx.lineWidth = 5;
      sctx.beginPath();
      sctx.moveTo(sWidth / 2, 230);
      sctx.lineTo(sWidth / 2, 280);
      sctx.stroke();
      
      sctx.beginPath();
      sctx.moveTo(sWidth / 2, 280);
      sctx.lineTo(sWidth / 2 - 12, 265);
      sctx.lineTo(sWidth / 2 + 12, 265);
      sctx.closePath();
      sctx.fillStyle = '#66bb6a';
      sctx.fill();
      
      sctx.fillStyle = '#66bb6a';
      sctx.font = "bold 16px monospace";
      sctx.fillText(scenario.quotientCount, sWidth / 2, 315);
    }
    
    if (symmetryCaption) {
      symmetryCaption.textContent = scenario.caption;
    }
  }
  
  function sRenderQuotient() {
    sctx.clearRect(0, 0, sWidth, sHeight);
    sctx.fillStyle = "#0f1318";
    sctx.fillRect(0, 0, sWidth, sHeight);
    
    sDrawGrid();
    
    const scenarioIndex = sTickCount % quotientComparisonScenarios.length;
    const scenario = quotientComparisonScenarios[scenarioIndex];
    
    scenario.agents.forEach((agent) => {
      const p = sToCell(agent.x, agent.y);
      
      sctx.fillStyle = "#4fc3f7";
      sctx.beginPath();
      sctx.arc(p.x + scell/2, p.y + scell/2, 15, 0, Math.PI * 2);
      sctx.fill();
      
      sctx.fillStyle = "#fff";
      sctx.font = "bold 12px monospace";
      sctx.textAlign = 'center';
      sctx.textBaseline = 'middle';
      sctx.fillText(agent.id, p.x + scell/2, p.y + scell/2);
    });
    
    if (symmetryCaption) {
      symmetryCaption.textContent = scenario.caption;
    }
  }
  
  function sRender() {
    const size = updateSymmetryLayout();
    if (!size.width || !size.height) {
      return;
    }
    if (sMode === "symmetry") {
      sRenderSymmetry();
    } else if (sMode === "quotient") {
      sRenderQuotient();
    }
  }
  
  function sAnimationLoop(ts) {
    if (!sLastTick) sLastTick = ts;
    const elapsed = ts - sLastTick;
    
    const delay = sMode === "symmetry" ? 6000 : 3500;
    
    if (elapsed > delay) {
      const maxTick = sMode === "symmetry" ? symmetryScenarios.length : quotientComparisonScenarios.length;
      sTickCount = (sTickCount + 1) % maxTick;
      sLastTick = ts;
    }
    sRender();
    requestAnimationFrame(sAnimationLoop);
  }
  
  // Handle button clicks
  symmetryButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      sMode = btn.dataset.algo;
      sTickCount = 0;
      sLastTick = 0;
      sRender();
    });
  });
  
  sRender();
  requestAnimationFrame(sAnimationLoop);
}

// ==================== Verification Canvas Setup ====================
const verifyCanvas = document.getElementById("verifyCanvas");
const verifyCaption = document.getElementById("verifyCaption");
const verifySection = document.getElementById("verification");
const verifyButtons = verifySection
  ? verifySection.querySelectorAll("[data-algo='verification'], [data-algo='refinement']")
  : [];
const verifySurface = verifyCanvas ? createHiResCanvas(verifyCanvas) : null;

console.log('verifyCanvas:', verifyCanvas, 'verifyCaption:', verifyCaption);

if (verifyCanvas) {
  console.log('Initializing verifyCanvas...');
  const vctx = verifySurface.ctx;
  const vgrid = 10;
  let vcell = 32;
  let vWidth = 0;
  let vHeight = 0;
  let voffsetX = 0;
  let voffsetY = 0;
  let vHeaderY = 0;
  let vFooterY = 0;
  let vHeaderHeight = 0;
  let vFooterHeight = 0;
  let vPadding = 0;
  let vLegendX = 0;
  let vLegendY = 0;
  let vLegendWidth = 0;
  let vMode = "verification";
  let vTickCount = 0;
  let vLastTick = 0;
  let vTime = 0;
  let vScenarioStart = 0;

  function updateVerifyLayout() {
    const size = verifySurface.resize();
    vWidth = size.width;
    vHeight = size.height;
    vPadding = 0;
    vHeaderHeight = 0;
    vFooterHeight = 0;
    vLegendWidth = 0;

    const maxCell = 32;
    vcell = Math.max(18, Math.min(maxCell, Math.floor(Math.min(vWidth, vHeight) / vgrid)));
    const gridWidth = vcell * vgrid;
    const gridHeight = vcell * vgrid;

    voffsetX = Math.max(0, (vWidth - gridWidth) / 2);
    voffsetY = Math.max(0, (vHeight - gridHeight) / 2);

    vHeaderY = 0;
    vFooterY = vHeight;
    vLegendX = 0;
    vLegendY = 0;
    return size;
  }
  
  function vToCell(px, py) {
    return {
      x: voffsetX + px * vcell,
      y: voffsetY + py * vcell,
    };
  }
  
  function vDrawGrid() {
    vctx.strokeStyle = "rgba(255,255,255,0.08)";
    for (let i = 0; i <= vgrid; i++) {
      const x = voffsetX + i * vcell;
      vctx.beginPath();
      vctx.moveTo(x, voffsetY);
      vctx.lineTo(x, voffsetY + vgrid * vcell);
      vctx.stroke();
      const y = voffsetY + i * vcell;
      vctx.beginPath();
      vctx.moveTo(voffsetX, y);
      vctx.lineTo(voffsetX + vgrid * vcell, y);
      vctx.stroke();
    }
  }

  function vRoundRect(x, y, w, h, r) {
    if (typeof vctx.roundRect === "function") {
      vctx.beginPath();
      vctx.roundRect(x, y, w, h, r);
      return;
    }
    const radius = Math.min(r, w / 2, h / 2);
    vctx.beginPath();
    vctx.moveTo(x + radius, y);
    vctx.lineTo(x + w - radius, y);
    vctx.quadraticCurveTo(x + w, y, x + w, y + radius);
    vctx.lineTo(x + w, y + h - radius);
    vctx.quadraticCurveTo(x + w, y + h, x + w - radius, y + h);
    vctx.lineTo(x + radius, y + h);
    vctx.quadraticCurveTo(x, y + h, x, y + h - radius);
    vctx.lineTo(x, y + radius);
    vctx.quadraticCurveTo(x, y, x + radius, y);
  }
  
  function vRenderVerification() {
    vctx.clearRect(0, 0, vWidth, vHeight);
    vctx.fillStyle = "#0f1318";
    vctx.fillRect(0, 0, vWidth, vHeight);

    vDrawGrid();
    
    const scenarioIndex = vTickCount % verificationScenarios.length;
    const scenario = verificationScenarios[scenarioIndex];
    
    scenario.obstacles.forEach((obs) => {
      const p = vToCell(obs.x, obs.y);
      vctx.fillStyle = "#555";
      vctx.strokeStyle = "#888";
      vctx.lineWidth = 2;
      vctx.fillRect(p.x + 4, p.y + 4, vcell - 8, vcell - 8);
      vctx.strokeRect(p.x + 4, p.y + 4, vcell - 8, vcell - 8);
    });
    
    scenario.agents.forEach((agent) => {
      const p = vToCell(agent.x, agent.y);
      
      vctx.fillStyle = agent.stopped ? "#ef5350" : "#4fc3f7";
      vctx.beginPath();
      vctx.arc(p.x + vcell/2, p.y + vcell/2, 15, 0, Math.PI * 2);
      vctx.fill();
      
      vctx.fillStyle = "#fff";
      vctx.font = "bold 12px monospace";
      vctx.textAlign = 'center';
      vctx.textBaseline = 'middle';
      vctx.fillText(agent.id, p.x + vcell/2, p.y + vcell/2);
    });
    
    if (verifyCaption) {
      verifyCaption.textContent = scenario.caption;
    }
  }
  
  function vRenderRefinement() {
    vctx.clearRect(0, 0, vWidth, vHeight);
    vctx.fillStyle = "#0f1318";
    vctx.fillRect(0, 0, vWidth, vHeight);

    vDrawGrid();
    
    const scenarioIndex = vTickCount % refinementScenarios.length;
    const scenario = refinementScenarios[scenarioIndex];

    const stepDelay = 450;
    const stepIndex = Math.min(
      Math.floor((vTime - vScenarioStart) / stepDelay),
      scenario.path.length - 1
    );

    // Draw path line
    vctx.strokeStyle = scenario.unsafe ? "rgba(239,83,80,0.6)" : "rgba(102,187,106,0.55)";
    vctx.lineWidth = Math.max(2, vcell * 0.12);
    vctx.lineCap = "round";
    vctx.lineJoin = "round";
    vctx.beginPath();
    scenario.path.forEach((p, i) => {
      const cellPos = vToCell(p.x, p.y);
      const cx = cellPos.x + vcell / 2;
      const cy = cellPos.y + vcell / 2;
      if (i === 0) {
        vctx.moveTo(cx, cy);
      } else {
        vctx.lineTo(cx, cy);
      }
    });
    vctx.stroke();

    // Draw step markers
    scenario.path.forEach((p, i) => {
      const cellPos = vToCell(p.x, p.y);
      const cx = cellPos.x + vcell / 2;
      const cy = cellPos.y + vcell / 2;
      const isActive = i === stepIndex;
      vctx.fillStyle = isActive ? "#ffffff" : "rgba(255,255,255,0.4)";
      vctx.beginPath();
      vctx.arc(cx, cy, isActive ? Math.max(6, vcell * 0.2) : Math.max(3, vcell * 0.12), 0, Math.PI * 2);
      vctx.fill();

    });

    const current = scenario.path[Math.max(0, stepIndex)];
    const pCurrent = vToCell(current.x, current.y);

    vctx.fillStyle = scenario.unsafe ? "#ef5350" : "#66bb6a";
    vctx.beginPath();
    vctx.arc(pCurrent.x + vcell / 2, pCurrent.y + vcell / 2, Math.max(10, vcell * 0.3), 0, Math.PI * 2);
    vctx.fill();
    vctx.strokeStyle = "rgba(255,255,255,0.9)";
    vctx.lineWidth = 2.5;
    vctx.stroke();
    vctx.fillStyle = "#0f1318";
    vctx.font = "700 12px 'Space Grotesk', sans-serif";
    vctx.textAlign = "center";
    vctx.textBaseline = "middle";
    vctx.fillText("A", pCurrent.x + vcell / 2, pCurrent.y + vcell / 2);
    
    if (scenario.constraint) {
      const pConstraint = vToCell(scenario.constraint.x, scenario.constraint.y);

      vctx.fillStyle = "rgba(255,152,0,0.12)";
      vctx.fillRect(pConstraint.x + 2, pConstraint.y + 2, vcell - 4, vcell - 4);
      vctx.strokeStyle = "#ffb74d";
      vctx.lineWidth = 2.5;
      vctx.setLineDash([6, 4]);
      vctx.strokeRect(pConstraint.x + 2, pConstraint.y + 2, vcell - 4, vcell - 4);
      vctx.setLineDash([]);

    }
    
    if (verifyCaption) {
      verifyCaption.textContent = scenario.caption;
    }
  }
  
  function vRender() {
    const size = updateVerifyLayout();
    if (!size.width || !size.height) {
      return;
    }
    if (vMode === "verification") {
      vRenderVerification();
    } else if (vMode === "refinement") {
      vRenderRefinement();
    }
  }
  
  function vAnimationLoop(ts) {
    vTime = ts;
    if (!vLastTick) {
      vLastTick = ts;
      if (!vScenarioStart) {
        vScenarioStart = ts;
      }
    }
    const elapsed = ts - vLastTick;
    
    const delay = 3000;
    
    if (elapsed > delay) {
      const maxTick = vMode === "verification" ? verificationScenarios.length : refinementScenarios.length;
      vTickCount = (vTickCount + 1) % maxTick;
      vLastTick = ts;
      vScenarioStart = ts;
    }
    vRender();
    requestAnimationFrame(vAnimationLoop);
  }
  
  // Handle button clicks
  verifyButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      vMode = btn.dataset.algo;
      vTickCount = 0;
      vLastTick = 0;
      vScenarioStart = performance.now();
      vRender();
    });
  });
  
  vRender();
  requestAnimationFrame(vAnimationLoop);
}
