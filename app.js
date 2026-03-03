/**
 * Profile Picture Generator - App UI
 */

const canvas = document.getElementById('avatarCanvas');
const generateBtn = document.getElementById('generateBtn');
const downloadBtn = document.getElementById('downloadBtn');
const loadingOverlay = document.getElementById('loadingOverlay');
const traitDisplay = document.getElementById('traitDisplay');
const traitSelectors = document.getElementById('traitSelectors');

let currentCombination = null;

function showLoading(show) {
  loadingOverlay.classList.toggle('hidden', !show);
}

function formatTraitName(id) {
  return id
    .replace(/^(bg|face|eyes|mouth|hair|acc|special)-/, '')
    .replace(/-/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase());
}

function updateTraitDisplay(combo) {
  if (!combo) {
    traitDisplay.textContent = '';
    return;
  }
  const parts = Object.entries(combo)
    .filter(([, v]) => v && !v.includes('none'))
    .map(([k, v]) => `${formatTraitName(k)}: ${formatTraitName(v)}`);
  traitDisplay.textContent = parts.join(' • ');
}

async function generateAvatar() {
  showLoading(true);
  try {
    currentCombination = await generateRandomAvatar(canvas);
    updateTraitDisplay(currentCombination);
    updateSelectorsFromCombo(currentCombination);
  } catch (err) {
    console.error('Generation failed:', err);
    traitDisplay.textContent = 'Error: ' + err.message;
  } finally {
    showLoading(false);
  }
}

function updateSelectorsFromCombo(combo) {
  const selects = traitSelectors.querySelectorAll('select');
  selects.forEach(select => {
    const category = select.dataset.category;
    if (combo[category]) {
      select.value = combo[category];
    }
  });
}

async function buildTraitSelectors() {
  const traits = await getAllTraits();
  traitSelectors.innerHTML = '';

  const labels = {
    background: 'Background',
    face: 'Face',
    eyes: 'Eyes',
    mouth: 'Mouth',
    hair: 'Hair',
    accessory: 'Accessory',
    special: 'Special'
  };

  for (const category of Object.keys(traits)) {
    const options = traits[category];
    if (!options || options.length === 0) continue;

    const div = document.createElement('div');
    div.className = 'trait-group';
    div.innerHTML = `
      <label>${labels[category] || category}</label>
      <select data-category="${category}">
        ${options.map(t => `<option value="${t}">${formatTraitName(t)}</option>`).join('')}
      </select>
    `;
    traitSelectors.appendChild(div);
  }

  traitSelectors.querySelectorAll('select').forEach(select => {
    select.addEventListener('change', async () => {
      const combo = getComboFromSelectors();
      showLoading(true);
      try {
        await renderCombination(canvas, combo);
        currentCombination = combo;
        updateTraitDisplay(combo);
      } catch (err) {
        console.error('Render failed:', err);
      } finally {
        showLoading(false);
      }
    });
  });
}

function getComboFromSelectors() {
  const combo = {};
  traitSelectors.querySelectorAll('select').forEach(select => {
    combo[select.dataset.category] = select.value;
  });
  return combo;
}

function init() {
  generateBtn.addEventListener('click', generateAvatar);
  downloadBtn.addEventListener('click', () => {
    if (!currentCombination) return;
    const name = Object.values(currentCombination).filter(Boolean).join('-') || 'avatar';
    downloadCanvas(canvas, `${name}.png`);
  });

  buildTraitSelectors().then(() => {
    generateAvatar();
  });
}

init();
