export async function requestJson(path, options = {}) {
  let response;
  try {
    const timeout = AbortSignal.timeout(15000);
    response = await fetch(path, {
      ...options,
      signal: options.signal ? AbortSignal.any([options.signal, timeout]) : timeout,
      headers: { Accept: 'application/json', ...options.headers },
    });
  } catch (error) {
    if (options.signal?.aborted) throw error;
    throw new Error('The prediction service could not be reached. Check that the app server is running, then retry.');
  }
  if (!response.headers.get('content-type')?.includes('application/json')) {
    throw new Error('The prediction service returned an unexpected response. Check the app server and retry.');
  }
  const body = await response.json();
  if (!response.ok) {
    const message = typeof body.detail === 'string' ? body.detail
      : Array.isArray(body.detail) ? body.detail.map((item) => item.msg).join('; ')
      : 'The prediction could not be completed. Please try again.';
    throw new Error(message);
  }
  return body;
}
