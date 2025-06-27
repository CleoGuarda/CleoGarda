const suppressedPatterns = [
  /WalletConnectionError: Connection rejected/,
  /Connection rejected/,
  /User denied the request/,
  /Transaction was not confirmed/
];

function shouldSuppress(args: unknown[]): boolean {
  return args.some(arg => {
    const text = String(arg);
    return suppressedPatterns.some(rx => rx.test(text));
  });
}

if (typeof window !== 'undefined') {
  const _consoleError = console.error;
  console.error = (...args: unknown[]) => {
    if (shouldSuppress(args)) return;
    // send uncaught errors to remote logger
    try {
      fetch(process.env.ERROR_MONITOR_URL || '', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ts: new Date().toISOString(), error: args })
      });
    } catch {}
    _consoleError.apply(console, args);
  };
}

export {};
