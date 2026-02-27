/**
 * Replicated Pin Module - Tests
 */

const { ReplicatedPinModule, ReplicatedPin, pinHash } = require('./ReplicatedPinModule');

function assert(condition, msg) {
  if (!condition) throw new Error(`Assertion failed: ${msg}`);
}

// Test pinHash
assert(typeof pinHash('QmTest123') === 'string', 'pinHash returns string');
assert(pinHash('QmTest123') === pinHash('QmTest123'), 'pinHash is deterministic');

// Test ReplicatedPin
const pin = new ReplicatedPin('QmFoo', { replicationFactor: 3 });
assert(pin.cid === 'QmFoo', 'pin stores cid');
assert(pin.replicationFactor === 3, 'pin stores replicationFactor');
assert(pin.id === pinHash('QmFoo'), 'pin id matches hash');

const roundtrip = ReplicatedPin.fromJSON(pin.toJSON());
assert(roundtrip.cid === pin.cid, 'JSON roundtrip preserves cid');

// Test ReplicatedPinModule
const pinModule = new ReplicatedPinModule({ peerId: 'peer-1' });

pinModule.add('QmPin1');
pinModule.add('QmPin2', { replicationFactor: 2, metadata: { name: 'test' } });

assert(pinModule.list().length === 2, 'module holds 2 pins');
assert(pinModule.get('QmPin1') !== null, 'get by cid works');
assert(pinModule.remove('QmPin1') === true, 'remove returns true');
assert(pinModule.list().length === 1, 'remove reduces count');

// Test merge (replication)
const remote = new ReplicatedPinModule({ peerId: 'peer-2' });
remote.add('QmRemote1');
remote.add('QmRemote2');

pinModule.merge(remote.export());
assert(pinModule.list().length === 3, 'merge adds remote pins');

// Test events
let addedCount = 0;
pinModule.on('pin:added', () => addedCount++);
pinModule.add('QmNew');
assert(addedCount === 1, 'pin:added event fires');

console.log('All tests passed ✓');
