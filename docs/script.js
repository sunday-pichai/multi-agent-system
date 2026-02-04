// Dark mode toggle functionality
const darkModeToggle = document.getElementById("darkModeToggle");
if (darkModeToggle) {
  // Check for saved dark mode preference or default to light mode
  const savedDarkMode = localStorage.getItem("darkMode") === "true";
  if (savedDarkMode) {
    document.body.classList.add("dark-mode");
    darkModeToggle.textContent = "☀️";
  }

  darkModeToggle.addEventListener("click", () => {
    document.body.classList.toggle("dark-mode");
    const isDarkMode = document.body.classList.contains("dark-mode");
    localStorage.setItem("darkMode", isDarkMode);
    darkModeToggle.textContent = isDarkMode ? "☀️" : "🌙";
  });
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

const flowButtons = document.querySelectorAll("[data-flow]");
const flowChart = document.getElementById("flowChart");
const flowChartCaption = document.getElementById("flowChartCaption");

function drawFlowChart(active) {
  if (!flowChart) return;
  const ctx = flowChart.getContext("2d");
  ctx.clearRect(0, 0, flowChart.width, flowChart.height);
  const bg = ctx.createLinearGradient(0, 0, flowChart.width, flowChart.height);
  bg.addColorStop(0, "#0f1318");
  bg.addColorStop(1, "#18202a");
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, flowChart.width, flowChart.height);

  const nodes = [
    { key: "plan", label: "Plan", x: 60, y: 70 },
    { key: "symmetry", label: "Symmetry", x: 300, y: 70 },
    { key: "verify", label: "Verify", x: 300, y: 190 },
    { key: "refine", label: "Refine", x: 60, y: 190 },
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

  arrow(200, 95, 300, 95);
  arrow(370, 120, 370, 190);
  arrow(300, 215, 200, 215);
  arrow(130, 190, 130, 120);

  nodes.forEach((n) => {
    const isActive = n.key === active;
    const w = 160;
    const h = 56;
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
    ctx.font = "600 16px 'Space Grotesk', sans-serif";
    ctx.fillText(n.label, n.x + 20, n.y + 32);
  });
}

function updateFlow(active) {
  flowButtons.forEach((b) => b.classList.toggle("is-active", b.dataset.flow === active));
  const captions = {
    plan: "Plan: Cooperative A* + CBS generates conflict-free paths.",
    symmetry: "Symmetry: role-orbit reduction and canonicalization.",
    verify: "Verify: bounded safety checks on the quotient model.",
    refine: "Refine: constraints injected from counterexamples.",
  };
  flowChartCaption.textContent = captions[active] || "";
  drawFlowChart(active);
}

flowButtons.forEach((btn) => {
  btn.addEventListener("click", () => updateFlow(btn.dataset.flow));
});

updateFlow("plan");

// Canvas interactive explainer
const canvas = document.getElementById("flowCanvas");
const caption = document.getElementById("canvasCaption");
const modeButtons = document.querySelectorAll(".chip");
const playBtn = document.getElementById("playBtn");
const stepBtn = document.getElementById("stepBtn");
const resetBtn = document.getElementById("resetBtn");

if (canvas) {
  const ctx = canvas.getContext("2d");
  const W = canvas.width;
  const H = canvas.height;

  const gridSize = 8;
  const cell = 40;
  const margin = 20;
  const gridW = gridSize * cell;
  const gridH = gridSize * cell;
  const gridX = (W - gridW) / 2;
  const gridY = (H - gridH) / 2;

  const baseAgents = [
    { id: 0, x: 1, y: 1, dir: 1, group: 0 },
    { id: 1, x: 1, y: 6, dir: 1, group: 0 },
    { id: 2, x: 3, y: 2, dir: 1, group: 1 },
    { id: 3, x: 3, y: 5, dir: 1, group: 1 },
  ];

  const shelves = [
    { x: 2, y: 3 }, { x: 2, y: 4 }, { x: 4, y: 3 }, { x: 4, y: 4 },
  ];

  const goals = [
    { x: 6, y: 2 },
    { x: 6, y: 5 },
  ];

  const paths = {
    0: [{ x: 1, y: 1 }, { x: 2, y: 1 }, { x: 3, y: 1 }, { x: 4, y: 1 }, { x: 5, y: 1 }, { x: 6, y: 1 }, { x: 6, y: 2 }],
    1: [{ x: 1, y: 6 }, { x: 2, y: 6 }, { x: 3, y: 6 }, { x: 4, y: 6 }, { x: 5, y: 6 }, { x: 6, y: 6 }, { x: 6, y: 5 }],
    2: [{ x: 3, y: 2 }, { x: 3, y: 3 }, { x: 3, y: 4 }, { x: 4, y: 4 }, { x: 5, y: 4 }, { x: 6, y: 4 }, { x: 6, y: 5 }],
    3: [{ x: 3, y: 5 }, { x: 3, y: 4 }, { x: 3, y: 3 }, { x: 4, y: 3 }, { x: 5, y: 3 }, { x: 6, y: 3 }, { x: 6, y: 2 }],
  };

  let mode = "plan";
  let stepIndex = 0;
  let playing = false;
  let lastTick = 0;

  function toPx(pos) {
    return {
      x: gridX + pos.x * cell + cell / 2,
      y: gridY + pos.y * cell + cell / 2,
    };
  }

  function drawGrid() {
    ctx.strokeStyle = "rgba(255,255,255,0.08)";
    for (let x = gridX; x <= gridX + gridW; x += cell) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, H);
      ctx.stroke();
    }
    for (let y = gridY; y <= gridY + gridH; y += cell) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(W, y);
      ctx.stroke();
    }
  }

  function drawShelves() {
    shelves.forEach((s) => {
      const p = toPx(s);
      ctx.fillStyle = "#2aa775";
      ctx.fillRect(p.x - 10, p.y - 10, 20, 20);
    });
  }

  function drawGoals() {
    ctx.fillStyle = "#44546a";
    goals.forEach((g) => {
      const p = toPx(g);
      ctx.beginPath();
      ctx.arc(p.x, p.y, 8, 0, Math.PI * 2);
      ctx.fill();
    });
  }

  function drawAgents(highlightGroups) {
    baseAgents.forEach((a, i) => {
      const path = paths[a.id];
      const pos = path[Math.min(stepIndex, path.length - 1)];
      const p = toPx(pos);
      ctx.fillStyle = "#f08c3a";
      ctx.beginPath();
      ctx.arc(p.x, p.y, 12, 0, Math.PI * 2);
      ctx.fill();
      if (highlightGroups) {
        const stroke = a.group === 0 ? "#4fc3f7" : "#ffd166";
        ctx.strokeStyle = stroke;
        ctx.lineWidth = 3;
        ctx.stroke();
      }

      ctx.fillStyle = "#0f1318";
      ctx.beginPath();
      ctx.moveTo(p.x + 6, p.y);
      ctx.lineTo(p.x - 4, p.y - 4);
      ctx.lineTo(p.x - 4, p.y + 4);
      ctx.fill();
    });
  }

  function drawPaths() {
    ctx.strokeStyle = "rgba(240,140,58,0.6)";
    ctx.lineWidth = 2;
    baseAgents.forEach((a) => {
      const path = paths[a.id];
      ctx.beginPath();
      const start = toPx(path[0]);
      ctx.moveTo(start.x, start.y);
      for (let k = 1; k < path.length; k += 1) {
        const p = toPx(path[k]);
        ctx.lineTo(p.x, p.y);
      }
      ctx.stroke();
    });
  }

  function drawVerification() {
    ctx.strokeStyle = "#ef5350";
    ctx.lineWidth = 3;
    const p = toPx({ x: 3, y: 3 });
    ctx.strokeRect(p.x - 20, p.y - 20, 40, 40);
  }

  function drawRefinement() {
    ctx.strokeStyle = "#66bb6a";
    ctx.lineWidth = 4;
    ctx.beginPath();
    const a = toPx({ x: 3, y: 3 });
    const b = toPx({ x: 4, y: 4 });
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.stroke();
  }

  function render() {
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = "#0f1318";
    ctx.fillRect(0, 0, W, H);
    drawGrid();
    drawShelves();
    drawGoals();

    if (mode === "plan") {
      drawPaths();
      drawAgents(false);
      caption.textContent = "Planning: cooperative paths with reservations and conflict-free routes.";
    } else if (mode === "symmetry") {
      drawAgents(true);
      caption.textContent = "Symmetry: agents grouped by role orbits.";
    } else if (mode === "verify") {
      drawPaths();
      drawVerification();
      drawAgents(false);
      caption.textContent = "Verification: detect unsafe regions and minimum separation violations.";
    } else if (mode === "refine") {
      drawPaths();
      drawRefinement();
      drawAgents(false);
      caption.textContent = "Refinement: add constraints and replan around conflicts.";
    }
  }

  function tick(ts) {
    if (!lastTick) lastTick = ts;
    const elapsed = ts - lastTick;
    if (playing && elapsed > 500) {
      stepIndex = (stepIndex + 1) % 8;
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
    });
  });

  playBtn.addEventListener("click", () => {
    playing = !playing;
    playBtn.textContent = playing ? "Pause" : "Play";
  });

  stepBtn.addEventListener("click", () => {
    stepIndex = (stepIndex + 1) % 8;
  });

  resetBtn.addEventListener("click", () => {
    stepIndex = 0;
    playing = false;
    playBtn.textContent = "Play";
  });
}

// Algorithm demo canvas
const algoCanvas = document.getElementById("algoCanvas");
const algoCaption = document.getElementById("algoCaption");
const algoButtons = document.querySelectorAll("[data-algo]");
const algoPlayBtn = document.getElementById("algoPlayBtn");
const algoStepBtn = document.getElementById("algoStepBtn");
const algoResetBtn = document.getElementById("algoResetBtn");

if (algoCanvas) {
  const ctx = algoCanvas.getContext("2d");
  const grid = 10;
  const cell = 28;
  const offsetX = 40;
  const offsetY = 20;
  let algoMode = "astar";
  let tick = 0;
  let algoPlaying = false;
  let lastAlgoTick = 0;

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

  const cbsAgentA = [
    { x: 1, y: 4 }, { x: 2, y: 4 }, { x: 3, y: 4 }, { x: 4, y: 4 },
  ];
  const cbsAgentB = [
    { x: 4, y: 4 }, { x: 3, y: 4 }, { x: 2, y: 4 }, { x: 1, y: 4 },
  ];
  const cbsReplanA = [
    { x: 1, y: 3 }, { x: 2, y: 3 }, { x: 3, y: 3 }, { x: 4, y: 3 },
  ];
  const cbsReplanB = [
    { x: 4, y: 5 }, { x: 3, y: 5 }, { x: 2, y: 5 }, { x: 1, y: 5 },
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
    const t = Math.min(tick, cbsAgentA.length - 1);
    const conflictPos = cbsAgentA[2];
    drawCell(conflictPos, "rgba(239,83,80,0.6)");

    const a = cbsAgentA[t];
    const b = cbsAgentB[t];
    drawCell(a, "#f08c3a");
    drawCell(b, "#4fc3f7");

    if (tick > 3) {
      const rt = Math.min(tick - 4, cbsReplanA.length - 1);
      drawCell(cbsReplanA[rt], "#f08c3a");
      drawCell(cbsReplanB[rt], "#4fc3f7");
      algoCaption.textContent = "CBS: detect conflict (red), add constraint, replan around it.";
    } else {
      algoCaption.textContent = "CBS: agents approach the same cell (conflict).";
    }
  }

  function renderAlgo() {
    ctx.clearRect(0, 0, algoCanvas.width, algoCanvas.height);
    ctx.fillStyle = "#0f1318";
    ctx.fillRect(0, 0, algoCanvas.width, algoCanvas.height);
    drawGrid();
    if (algoMode === "astar") {
      drawAStar();
    } else {
      drawCBS();
    }
  }

  function algoTick(ts) {
    if (!lastAlgoTick) lastAlgoTick = ts;
    const elapsed = ts - lastAlgoTick;
    if (algoPlaying && elapsed > 500) {
      tick = (tick + 1) % 10;
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
    });
  });

  algoPlayBtn.addEventListener("click", () => {
    algoPlaying = !algoPlaying;
    algoPlayBtn.textContent = algoPlaying ? "Pause" : "Play";
  });

  algoStepBtn.addEventListener("click", () => {
    tick = (tick + 1) % 10;
  });

  algoResetBtn.addEventListener("click", () => {
    tick = 0;
    algoPlaying = false;
    algoPlayBtn.textContent = "Play";
  });

  requestAnimationFrame(algoTick);
}
