import genanki

CSS = """
html, body {
    min-height: 100%;
    overflow-x: hidden;
    margin: 0;
    padding: 0;
}

/* ---------- shared: outfit stage + floating controls ---------- */

.stage {
    position: relative;
    width: 100%;
    height: 100%;
}

.outfit-container {
    position: absolute;
    inset: 0;
    display: grid;
    overflow: hidden;
}

.outfit {
    position: relative;
    grid-area: 1 / 1;
    width: 100%;
    height: 100%;
    min-width: 0;
    min-height: 0;
}

.outfit.hidden {
    visibility: hidden;
}

.outfit img {
    display: block;

    width: 100%;
    height: 100%;

    object-fit: contain;
}

.outfit-file-link {
    position: absolute;
    top: 14px;
    right: 14px;

    padding: 6px 12px;
    border-radius: 999px;

    background: rgba(0, 0, 0, 0.5);
    color: #fff;
    font-size: 12px;
    text-decoration: none;

    touch-action: manipulation;
    -webkit-tap-highlight-color: transparent;
    transition: background 0.08s ease, transform 0.08s ease;
}

.outfit-file-link:active {
    background: rgba(0, 0, 0, 0.75);
    transform: scale(0.94);
}

.outfit-controls {
    position: absolute;
    left: 50%;
    bottom: 20px;
    transform: translateX(-50%);

    width: max-content;
    white-space: nowrap;
    text-align: center;
}

.outfit-controls button {
    position: relative;

    font-size: 16px;
    font-weight: 600;
    margin: 0 8px;
    padding: 10px 18px;
    border: none;
    border-radius: 999px;

    background: rgba(0, 0, 0, 0.55);
    color: #fff;
    cursor: pointer;

    touch-action: manipulation;
    -webkit-tap-highlight-color: transparent;
    transition: transform 0.08s ease, background 0.08s ease;
}

.outfit-controls button:active {
    transform: scale(0.9);
    background: rgba(0, 0, 0, 0.8);
}

.outfit-controls button::after {
    content: "";
    position: absolute;
    inset: -24px;
}

.outfit-counter {
    display: inline-block;
    min-width: 36px;

    color: #fff;
    font-size: 14px;
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.6);
    vertical-align: middle;
}

/* ---------- front ---------- */

.frontbg {
    height: 100vh;
    height: 100dvh;
    height: var(--vh100, 100vh);
    overflow: hidden;
}

/* ---------- back ---------- */

.backbg {
    display: flex;
    flex-wrap: wrap;
    gap: 40px;
    padding: 20px;
    justify-content: center;
}

.back-left,
.back-right {
    flex: 1 1 320px;
    min-width: 0;
}

.back-left .stage {
    height: calc(100vh - 40px);
    height: calc(100dvh - 40px);
    height: calc(var(--vh100, 100vh) - 40px);
}

.name {
    font-size: 48px;
    font-weight: bold;
    margin-bottom: 25px;
}

table.infobox {
    border-collapse: collapse;
}

table.infobox td {
    font-size: 24px;
    padding: 6px 20px 6px 0;
}

a {
    color: #66ccff;
    text-decoration: none;
}

@media (max-width: 700px) {
    .backbg {
        gap: 20px;
        padding: 0;
    }

    .back-left .stage {
        height: 100vh;
        height: 100dvh;
        height: var(--vh100, 100vh);
    }

    .back-right {
        padding: 0 20px 20px;
    }
}
"""

model = genanki.Model(
	1749272174,
	"Umamusume Model",
	fields=[
		{"name": "ID"},
		{"name": "Image Tag"},
		{"name": "Name"},
		{"name": "Attributes"},
		{"name": "Has Multiple Outfits"},
	],
	templates=[
		{
			"name": "Card 1",
			"qfmt": """
<div class="frontbg">
    <div class="stage">
        <div class="outfit-container">
            {{Image Tag}}
        </div>

        {{#Has Multiple Outfits}}
        <div class="outfit-controls">
            <button onclick="previousOutfit()">Previous</button>
            <span class="outfit-counter"></span>
            <button onclick="nextOutfit()">Next</button>
        </div>
        {{/Has Multiple Outfits}}
    </div>
</div>

<script>
(function() {
    function setViewportHeight() {
        document.documentElement.style.setProperty("--vh100", window.innerHeight + "px");
    }
    setViewportHeight();
    window.addEventListener("resize", setViewportHeight);
    window.addEventListener("orientationchange", setViewportHeight);
})();

(function() {
    const id = "{{ID}}";
    const root = document.querySelector(".outfit-container");
    if (!root)
        return;

    const outfits = root.querySelectorAll(".outfit");
    let index = Number(sessionStorage.getItem("outfit-" + id) ?? 0);

    function show(i) {
        index = Math.max(0, Math.min(i, outfits.length - 1));

        sessionStorage.setItem("outfit-" + id, index);

		outfits.forEach((el, n) => {
			el.classList.toggle("hidden", n !== index);
		});

        const counter = document.querySelector(".outfit-counter");
        if (counter)
            counter.textContent = `${index + 1}/${outfits.length}`;
    }

    window.nextOutfit = () => show(index + 1);
    window.previousOutfit = () => show(index - 1);

    show(index);
})();
</script>
""",
			"afmt": """
<div class="backbg">

<div class="back-left">
    <div class="stage">
        <div class="outfit-container">
            {{Image Tag}}
        </div>

        {{#Has Multiple Outfits}}
        <div class="outfit-controls">
            <button onclick="previousOutfit()">Previous</button>
            <span class="outfit-counter"></span>
            <button onclick="nextOutfit()">Next</button>
        </div>
        {{/Has Multiple Outfits}}
    </div>
</div>

<div class="back-right">
    <div class="name">{{Name}}</div>
    {{Attributes}}
</div>

</div>


<script>
(function() {
    function setViewportHeight() {
        document.documentElement.style.setProperty("--vh100", window.innerHeight + "px");
    }
    setViewportHeight();
    window.addEventListener("resize", setViewportHeight);
    window.addEventListener("orientationchange", setViewportHeight);
})();

(function() {
    const id = "{{ID}}";
    const root = document.querySelector(".outfit-container");
    if (!root)
        return;

    const outfits = root.querySelectorAll(".outfit");

    let index = Number(sessionStorage.getItem("outfit-" + id) ?? 0);

    function show(i) {
        index = Math.max(0, Math.min(i, outfits.length - 1));

        sessionStorage.setItem("outfit-" + id, index);

		outfits.forEach((el, n) => {
			el.classList.toggle("hidden", n !== index);
		});

        const counter = document.querySelector(".outfit-counter");
        if (counter)
            counter.textContent = `${index + 1}/${outfits.length}`;
    }

    window.nextOutfit = () => show(index + 1);
    window.previousOutfit = () => show(index - 1);

	show(index);
})();
</script>
""",
		}
	],
	css=CSS,
)
