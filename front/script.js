document.addEventListener("DOMContentLoaded", async () => {
    if (!window.location.pathname.endsWith("comparison.html")) return;

    const f1 = localStorage.getItem("fighter1");
    const f2 = localStorage.getItem("fighter2");

    if (!f1 || !f2) {
        document.body.innerHTML =
            "<h2 style='color:white'>Нет данных для сравнения</h2>";
        return;
    }

    try {
        const data = await fetchPredictionWithPolling(f1, f2);
        console.log("✅ FINAL RESULT:", data);

        renderFighter("red", data.fighter_1);
        renderFighter("blue", data.fighter_2);

        renderProbability(data);
        highlightWinner(data);

        renderShapGrid(data.shap);
        renderShapBars(data.shap);
        renderDecisionSummary(data);

        loadHistory(data.fighter_1.name, ".fighter-history.red tbody");
        loadHistory(data.fighter_2.name, ".fighter-history.blue tbody");

    } catch (err) {
        console.error("❌ FRONT ERROR:", err);
        document.body.innerHTML =
            "<h2 style='color:red'>Ошибка загрузки данных</h2>";
    }
});

/* ================= POLLING ================= */

async function fetchPredictionWithPolling(f1, f2) {
    const maxAttempts = 10;
    const delayMs = 700;

    for (let i = 0; i < maxAttempts; i++) {
        const res = await fetch("/api/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ fighter1: f1, fighter2: f2 })
        });

        const data = await res.json();

        if (res.status === 200) return data;

        if (res.status === 202) {
            console.log(`⏳ ожидание результата (${i + 1}/${maxAttempts})`);
            await new Promise(r => setTimeout(r, delayMs));
            continue;
        }

        throw new Error("Unexpected response");
    }

    throw new Error("Model timeout");
}

/* ================= UI ================= */

function renderProbability(data) {
    document.querySelector(".prob-left").innerText =
        Math.round(data.probability.red * 100) + "%";
    document.querySelector(".prob-right").innerText =
        Math.round(data.probability.blue * 100) + "%";
}

function highlightWinner(data) {
    const winnerIsRed = data.winner === data.fighter_1.name;
    document
        .querySelector(winnerIsRed
            ? ".fighter-card:first-child"
            : ".fighter-card:last-child")
        .classList.add("winner");
}

function renderFighter(side, data) {
    const safe = v => v ?? "-";

    document.querySelector(`.${side}-name`).innerText =
        data.name.toUpperCase();

    document.querySelector(`.${side}-nickname`).innerText =
        data.nickname && data.nickname !== "No Nickname"
            ? `"${data.nickname}"`
            : "";

    document.querySelector(`.${side}-record`).innerText = safe(data.record);
    document.querySelector(`.${side}-height`).innerText = safe(data.height);
    document.querySelector(`.${side}-reach`).innerText = safe(data.reach);
    document.querySelector(`.${side}-stance`).innerText = safe(data.stance);
    document.querySelector(`.${side}-weight`).innerText = safe(data.weight);
}

/* ================= SHAP ================= */

function renderShapGrid(shap) {
    const grid = document.querySelector(".shap-grid");
    grid.innerHTML = "";

    shap.forEach(f => {
        const div = document.createElement("div");
        div.className =
            "shap-factor " + (f.value >= 0 ? "positive" : "negative");

        div.innerHTML = `
            <h3>${f.feature}</h3>
            <span>${f.value >= 0 ? "+" : ""}${f.value.toFixed(4)}</span>
        `;
        grid.appendChild(div);
    });
}

function renderShapBars(shap) {
    const bars = document.querySelector(".shap-bars");
    if (!bars) return;

    bars.innerHTML = "";

    const maxAbs = Math.max(...shap.map(f => Math.abs(f.value)));

    shap.slice(0, 10).forEach(f => {
        const row = document.createElement("div");
        row.className = "shap-bar-row";

        const label = document.createElement("div");
        label.className = "shap-bar-label";
        label.innerText = f.feature;

        const barWrap = document.createElement("div");
        barWrap.className = "shap-bar-wrap";

        const bar = document.createElement("div");
        bar.className = "shap-bar";
        bar.style.width = `${Math.abs(f.value) / maxAbs * 100}%`;
        bar.style.background =
            f.value >= 0
                ? "linear-gradient(90deg,#ff4d4d,#ff9999)"
                : "linear-gradient(90deg,#4da6ff,#99ccff)";

        bar.innerText =
            (f.value > 0 ? "+" : "") + f.value.toFixed(3);

        barWrap.appendChild(bar);
        row.append(label, barWrap);
        bars.appendChild(row);
    });
}

/* ================= HISTORY ================= */

async function loadHistory(name, selector) {
    const res = await fetch(
        `/api/fighter-history/${encodeURIComponent(name)}`
    );
    const data = await res.json();

    const tbody = document.querySelector(selector);
    tbody.innerHTML = "";

    data.forEach(f => {
        const tr = document.createElement("tr");
        tr.className = f.result === "WIN" ? "win" : "loss";

        tr.innerHTML = `
            <td>${f.result === "WIN" ? "ПОБЕДА" : "ПОРАЖЕНИЕ"}</td>
            <td>${f.opponent}</td>
            <td>${f.method}</td>
            <td>R${f.round}</td>
        `;
        tbody.appendChild(tr);
    });
}

/* ================= index.html ================= */

function compareFighters() {
    const f1 = document.getElementById("fighter1").value.trim();
    const f2 = document.getElementById("fighter2").value.trim();

    if (!f1 || !f2) {
        alert("Введите двух бойцов");
        return;
    }

    localStorage.setItem("fighter1", f1);
    localStorage.setItem("fighter2", f2);
    window.location.href = "/comparison.html";
}
function renderDecisionSummary(data) {
    const list = document.querySelector(".decision-list");
    if (!list) return;

    list.innerHTML = "";

    const winner =
        data.winner === data.fighter_1.name
            ? data.fighter_1.name
            : data.fighter_2.name;

    const topFactors = [...data.shap]
        .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
        .slice(0, 5);

    topFactors.forEach(f => {
        const li = document.createElement("li");

        const positive = f.value >= 0;

        li.innerHTML = `
            <span class="decision-icon">
                ${positive ? "⬆️" : "⬇️"}
            </span>
            <strong>${f.feature}</strong> 
            ${positive
                ? "сыграл ключевую роль в победе"
                : "не был в пользу победителя, но не перекрыл другие преимущества"}
        `;

        li.className = positive ? "positive" : "negative";
        list.appendChild(li);
    });

    const footer = document.createElement("li");
    footer.className = "decision-footer";
    footer.innerHTML = `
        <em>
            Итог: победа <strong>${winner}</strong> — результат совокупности факторов,
            а не одного показателя.
        </em>
    `;
    list.appendChild(footer);
}