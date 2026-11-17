import test from 'node:test';
import assert from 'node:assert/strict';
import { requestJson } from '../src/api.js';

test('JSON requests preserve caller method, body and headers', async (t) => {
  t.mock.method(globalThis, 'fetch', async (path, options) => {
    assert.equal(path, '/api/predict');
    assert.equal(options.method, 'POST');
    assert.equal(options.headers['Content-Type'], 'application/json');
    assert.equal(JSON.parse(options.body).home, 'Arsenal');
    return Response.json({ probabilities: [0.5, 0.25, 0.25] });
  });
  const result = await requestJson('/api/predict', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ home: 'Arsenal', away: 'Chelsea' }),
  });
  assert.equal(result.probabilities.reduce((a, b) => a + b), 1);
});

test('validation errors become readable messages', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => Response.json({
    detail: [{ msg: 'Choose two different teams.' }],
  }, { status: 422 }));
  await assert.rejects(requestJson('/api/predict'), /Choose two different teams/);
});

test('service unavailable messages are retained', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => Response.json({
    detail: 'Model is unavailable. Restore the project assets.',
  }, { status: 503 }));
  await assert.rejects(requestJson('/api/meta'), /Model is unavailable/);
});

test('an HTML response cannot be mistaken for prediction data', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => new Response('<html>App</html>', {
    headers: { 'Content-Type': 'text/html' },
  }));
  await assert.rejects(requestJson('/api/meta'), /unexpected response/);
});

test('network errors offer a recovery message', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => { throw new TypeError('fetch failed'); });
  await assert.rejects(requestJson('/api/meta'), /could not be reached/);
});

test('caller cancellation remains an AbortError', async (t) => {
  const controller = new AbortController();
  controller.abort();
  t.mock.method(globalThis, 'fetch', async () => { throw controller.signal.reason; });
  await assert.rejects(requestJson('/api/meta', { signal: controller.signal }), { name: 'AbortError' });
});
