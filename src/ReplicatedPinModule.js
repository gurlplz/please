/**
 * Replicated Pin Module
 * 
 * Replicates pin state across multiple peers using CRDT-inspired conflict-free
 * replication. Suitable for IPFS pinning, content-addressed storage, and
 * distributed blockchain data availability.
 * 
 * @module ReplicatedPinModule
 */

const crypto = require('crypto');

/**
 * Generates a deterministic hash for pin identification
 * @param {string} cid - Content identifier (e.g., IPFS CID)
 * @param {object} metadata - Optional pin metadata
 * @returns {string} Hash identifier
 */
function pinHash(cid, metadata = {}) {
  return crypto
    .createHash('sha256')
    .update(JSON.stringify({ cid, ...metadata }))
    .digest('hex');
}

/**
 * ReplicatedPin - Represents a single pin with replication metadata
 */
class ReplicatedPin {
  constructor(cid, options = {}) {
    this.cid = cid;
    this.replicationFactor = options.replicationFactor ?? 1;
    this.metadata = options.metadata ?? {};
    this.timestamp = options.timestamp ?? Date.now();
    this.peerId = options.peerId ?? null;
    this.id = pinHash(cid, this.metadata);
  }

  toJSON() {
    return {
      id: this.id,
      cid: this.cid,
      replicationFactor: this.replicationFactor,
      metadata: this.metadata,
      timestamp: this.timestamp,
      peerId: this.peerId,
    };
  }

  static fromJSON(json) {
    return new ReplicatedPin(json.cid, {
      replicationFactor: json.replicationFactor,
      metadata: json.metadata,
      timestamp: json.timestamp,
      peerId: json.peerId,
    });
  }
}

/**
 * ReplicatedPinModule - Manages replicated pinset with CRDT-like merge semantics
 */
class ReplicatedPinModule {
  constructor(options = {}) {
    this.peerId = options.peerId ?? crypto.randomUUID();
    this.pins = new Map(); // id -> ReplicatedPin
    this.replicationFactor = options.replicationFactor ?? 2;
    this.listeners = new Map();
  }

  /**
   * Add a pin to the replicated set
   * @param {string} cid - Content identifier
   * @param {object} options - Pin options
   * @returns {ReplicatedPin} The added pin
   */
  add(cid, options = {}) {
    const pin = new ReplicatedPin(cid, {
      replicationFactor: options.replicationFactor ?? this.replicationFactor,
      metadata: options.metadata ?? {},
      peerId: this.peerId,
    });

    const existing = this.pins.get(pin.id);
    if (existing && existing.timestamp > pin.timestamp) {
      return existing; // Last-write-wins for updates
    }

    this.pins.set(pin.id, pin);
    this._emit('pin:added', pin);
    return pin;
  }

  /**
   * Remove a pin from the replicated set
   * @param {string} cidOrId - Content ID or pin hash
   * @returns {boolean} Whether the pin was removed
   */
  remove(cidOrId) {
    let removed = false;
    for (const [id, pin] of this.pins) {
      if (id === cidOrId || pin.cid === cidOrId) {
        this.pins.delete(id);
        this._emit('pin:removed', pin);
        removed = true;
        break;
      }
    }
    return removed;
  }

  /**
   * Get a pin by CID or ID
   * @param {string} cidOrId - Content ID or pin hash
   * @returns {ReplicatedPin|null}
   */
  get(cidOrId) {
    for (const [id, pin] of this.pins) {
      if (id === cidOrId || pin.cid === cidOrId) return pin;
    }
    return null;
  }

  /**
   * List all pins
   * @returns {ReplicatedPin[]}
   */
  list() {
    return Array.from(this.pins.values());
  }

  /**
   * Merge remote pinset into local (CRDT-style merge)
   * @param {Array} remotePins - Array of pin objects from remote peer
   */
  merge(remotePins) {
    for (const p of remotePins) {
      const pin = p instanceof ReplicatedPin ? p : ReplicatedPin.fromJSON(p);
      const existing = this.pins.get(pin.id);
      if (!existing || pin.timestamp > existing.timestamp) {
        this.pins.set(pin.id, pin);
        if (!existing) this._emit('pin:synced', pin);
      }
    }
  }

  /**
   * Export pinset for replication to peers
   * @returns {Array} Serializable pin array
   */
  export() {
    return this.list().map((p) => p.toJSON());
  }

  /**
   * Subscribe to pin events
   * @param {string} event - Event name (pin:added, pin:removed, pin:synced)
   * @param {Function} handler - Callback
   */
  on(event, handler) {
    if (!this.listeners.has(event)) this.listeners.set(event, []);
    this.listeners.get(event).push(handler);
  }

  /**
   * Unsubscribe from events
   */
  off(event, handler) {
    const handlers = this.listeners.get(event);
    if (handlers) {
      const idx = handlers.indexOf(handler);
      if (idx >= 0) handlers.splice(idx, 1);
    }
  }

  _emit(event, data) {
    const handlers = this.listeners.get(event) ?? [];
    handlers.forEach((h) => h(data));
  }

  /**
   * Get replication status summary
   */
  getStatus() {
    return {
      peerId: this.peerId,
      pinCount: this.pins.size,
      pins: this.list().map((p) => p.toJSON()),
    };
  }
}

module.exports = {
  ReplicatedPinModule,
  ReplicatedPin,
  pinHash,
};
