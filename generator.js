/**
 * Profile Picture Generator - Layers SVG traits into composite avatars
 * All traits use viewBox="0 0 100 100" for consistent layering
 */

const LAYER_ORDER = ['background', 'face', 'eyes', 'mouth', 'hair', 'accessory', 'special'];
const TRAIT_BASE = 'traits';

// Map category names to folder paths
const CATEGORY_PATHS = {
  background: 'backgrounds',
  face: 'faces',
  eyes: 'eyes',
  mouth: 'mouths',
  hair: 'hair',
  accessory: 'accessories',
  special: 'special'
};

let manifest = null;

async function loadManifest() {
  if (manifest) return manifest;
  const res = await fetch(`${TRAIT_BASE}/manifest.json`);
  manifest = await res.json();
  return manifest;
}

function getTraitPath(category, traitId) {
  const folder = CATEGORY_PATHS[category];
  return `${TRAIT_BASE}/${folder}/${traitId}.svg`;
}

/**
 * Load SVG as string and render to canvas
 */
async function loadAndDrawLayer(ctx, category, traitId, width, height) {
  const path = getTraitPath(category, traitId);
  const res = await fetch(path);
  const svgText = await res.text();

  return new Promise((resolve, reject) => {
    const img = new Image();
    const blob = new Blob([svgText], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);

    img.onload = () => {
      ctx.drawImage(img, 0, 0, width, height);
      URL.revokeObjectURL(url);
      resolve();
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error(`Failed to load ${path}`));
    };
    img.src = url;
  });
}

/**
 * Generate a random combination respecting compatibility rules
 */
function getRandomCombination() {
  const { traits, compatibility } = manifest;
  const combo = {};

  for (const category of LAYER_ORDER) {
    let options = traits[category];
    if (!options || options.length === 0) continue;

    // Apply compatibility constraints
    const face = combo.face || '';
    if (compatibility && compatibility[face]) {
      const compat = compatibility[face];
      if (compat[category]) {
        options = options.filter(t => compat[category].includes(t));
        if (options.length === 0) options = traits[category];
      }
    }

    combo[category] = options[Math.floor(Math.random() * options.length)];
  }

  return combo;
}

/**
 * Render avatar from trait combination to canvas
 */
async function renderAvatar(canvas, combination) {
  const ctx = canvas.getContext('2d');
  const width = canvas.width;
  const height = canvas.height;

  ctx.clearRect(0, 0, width, height);

  for (const category of LAYER_ORDER) {
    const traitId = combination[category];
    if (!traitId) continue;

    await loadAndDrawLayer(ctx, category, traitId, width, height);
  }
}

/**
 * Generate and return a random avatar combination
 */
async function generateRandomAvatar(canvas) {
  await loadManifest();
  const combination = getRandomCombination();
  await renderAvatar(canvas, combination);
  return combination;
}

/**
 * Render a specific combination (for custom selection)
 */
async function renderCombination(canvas, combination) {
  await loadManifest();
  await renderAvatar(canvas, combination);
}

/**
 * Get all available traits from manifest
 */
async function getAllTraits() {
  await loadManifest();
  return manifest.traits;
}

/**
 * Download canvas as PNG
 */
function downloadCanvas(canvas, filename = 'avatar.png') {
  const link = document.createElement('a');
  link.download = filename;
  link.href = canvas.toDataURL('image/png');
  link.click();
}
